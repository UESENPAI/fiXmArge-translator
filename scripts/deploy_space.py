#!/usr/bin/env python3
"""Explicit cloud-code and licensed WordNet deployment package.

The CLI prepares/verifies local files only. Remote helpers require a caller-
provided authenticated API and are deliberately never called by main().
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO_ID = 'uesenpai/fixmarge-translator'
HARDWARE = 'zero-a10g'
MANIFEST = 'deploy-manifest.json'
CODE_FILES = {
    '.gitignore': 'spaces/.gitignore', 'DEPLOY.md': 'spaces/DEPLOY.cloud.md',
    'LICENSE': 'LICENSE', 'README.md': 'spaces/README.cloud.md',
    'requirements.txt': 'spaces/requirements-cloud.txt', 'app.py': 'app.py',
    'src/fixmarge/__init__.py': 'src/fixmarge/__init__.py',
    'src/fixmarge/infer.py': 'src/fixmarge/infer.py',
    'src/fixmarge/rag.py': 'src/fixmarge/rag.py',
    'src/fixmarge/grounding.py': 'src/fixmarge/grounding.py',
    'src/fixmarge/sentence_diagnostics.py': 'src/fixmarge/sentence_diagnostics.py',
    'src/fixmarge/demo.py': 'src/fixmarge/demo.py',
    'src/fixmarge/standard_dictionary.py': 'src/fixmarge/standard_dictionary.py',
    'src/fixmarge/cloud.py': 'src/fixmarge/cloud.py',
}
RESOURCE_FILES = frozenset({
    'data/external/lexicons.sqlite3', 'data/external/NOTICE.txt',
    'data/external/README.md', 'data/external/resource-manifest.json',
    'data/external/licenses/Japanese-WordNet.txt',
    'data/external/licenses/Princeton-WordNet.txt',
    'data/external/licenses/Open-English-WordNet.md',
    'data/external/licenses/OEWN-WNDB-License.txt',
})
RESOURCE_SOURCE_PREFIX = 'runs/space-resources-en-ja/'
SOURCE_IDS = {'wnja:1.1', 'oewn:2025'}
CLOUD_PINNED_REQUIREMENTS = {
    'torch': '2.8.0', 'transformers': '4.57.1', 'peft': '0.17.1',
    'accelerate': '1.10.1', 'safetensors': '0.6.2',
    'huggingface-hub': '0.35.3', 'jinja2': '3.1.6', 'gradio': '5.49.1',
    'spaces': '0.51.3',
}
PUBLIC_VARIABLES = {
    'FIXMARGE_CLOUD', 'FIXMARGE_MODEL', 'FIXMARGE_ADAPTER_REPO',
    'FIXMARGE_ADAPTER_REVISION', 'FIXMARGE_DEVICE', 'FIXMARGE_LOAD_IN_4BIT',
    'FIXMARGE_ALLOW_MODEL_DOWNLOAD', 'FIXMARGE_DATA_DIR', 'FIXMARGE_EXTERNAL_DIR',
    'HF_HOME', 'GRADIO_ANALYTICS_ENABLED', 'HF_HUB_DISABLE_TELEMETRY',
}


class DeploymentError(ValueError):
    """An intentionally credential-free deployment error."""


def _no_symlinks(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise DeploymentError('Symlink paths are not allowed in a deployment package')


def fingerprint(path: Path) -> dict:
    _no_symlinks(path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise DeploymentError('Deployment inputs must be regular files')
        sha256 = hashlib.sha256()
        git = hashlib.sha1(f'blob {info.st_size}\0'.encode())
        count = 0
        while chunk := stream.read(4 * 1024 * 1024):
            sha256.update(chunk)
            git.update(chunk)
            count += len(chunk)
    if count != info.st_size:
        raise DeploymentError('Deployment input changed size while being read')
    return {'bytes': count, 'sha256': sha256.hexdigest(), 'git_blob_sha1': git.hexdigest()}


def _json(path: Path) -> dict:
    _no_symlinks(path)
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise DeploymentError('Expected a small regular JSON manifest')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise DeploymentError('Expected an object manifest')
    return value


def _cloud_metadata(readme: bytes, requirements: bytes) -> None:
    from scripts.prepare_space import PINNED_REQUIREMENTS, _validate_metadata
    # Reuse the unchanged YAML policy with its original dependency snapshot.
    # Cloud BF16 has a separate exact snapshot: no bitsandbytes, plus spaces.
    original_pins = '\n'.join(name + '==' + version for name, version in PINNED_REQUIREMENTS.items()) + '\n'
    _validate_metadata(readme, original_pins.encode())
    pins = {}
    for line in requirements.decode('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)', line)
        if not match:
            raise DeploymentError('Cloud requirements must use explicit dependency pins')
        name = match[1].lower().replace('_', '-')
        if name in pins:
            raise DeploymentError('Cloud requirements contain a duplicate pin')
        pins[name] = match[2]
    if pins != CLOUD_PINNED_REQUIREMENTS:
        raise DeploymentError('Cloud requirements differ from the reviewed BF16 dependency snapshot')


def _resource_map(source_root: Path, path: Path) -> tuple[list[dict], str]:
    mapped = _json(path)
    records = mapped.get('files')
    if mapped.get('schema_version') != 1 or not isinstance(records, list) or len(records) != 8:
        raise DeploymentError('The reviewed WordNet map must enumerate exactly eight files')
    if {record.get('path_in_repo') for record in records} != RESOURCE_FILES:
        raise DeploymentError('Resource map has extra, missing, or duplicate destinations')
    for record in records:
        destination = record['path_in_repo']
        if record.get('source') != RESOURCE_SOURCE_PREFIX + destination:
            raise DeploymentError('Only the independently prepared WordNet resource bundle is accepted')
        identifiers, licences = record.get('source_id'), record.get('license')
        if not isinstance(identifiers, list) or not identifiers or not all(isinstance(value, str) and value in SOURCE_IDS for value in identifiers):
            raise DeploymentError('Resource provenance must identify the reviewed WordNet sources')
        if not isinstance(licences, list) or not licences or not all(isinstance(value, str) and value for value in licences):
            raise DeploymentError('Resource licence metadata is required')
        actual = fingerprint(source_root / record['source'])
        if actual['sha256'] != record.get('sha256') or actual['bytes'] != record.get('bytes'):
            raise DeploymentError('Reviewed WordNet resource hash or size does not match: ' + destination)
    return records, fingerprint(path)['sha256']


def prepare_deployment(source_root: Path, resource_map: Path, output: Path) -> dict:
    source_root, resource_map, output = map(lambda value: Path(value).absolute(), (source_root, resource_map, output))
    _no_symlinks(source_root)
    _no_symlinks(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise DeploymentError('Choose a new or empty deployment directory; existing files are preserved')
    code = {}
    for target, source in sorted(CODE_FILES.items()):
        path = source_root / source
        info = fingerprint(path)
        if info['bytes'] > 1_000_000:
            raise DeploymentError('Code payload exceeds its size limit: ' + target)
        code[target] = {'source': path, 'kind': 'code', **info}
    _cloud_metadata(code['README.md']['source'].read_bytes(), code['requirements.txt']['source'].read_bytes())
    resources, map_hash = _resource_map(source_root, resource_map)
    files = dict(code)
    for record in resources:
        files[record['path_in_repo']] = {'source': source_root / record['source'], 'kind': 'licensed_wordnet_resource',
                                        'source_id': record['source_id'], 'license': record['license'],
                                        **fingerprint(source_root / record['source'])}
    manifest = {
        'schema_version': 1, 'repo_id': REPO_ID, 'repo_type': 'space', 'private': True,
        'sdk': 'gradio', 'sdk_version': '5.49.1', 'python_version': '3.12', 'hardware': HARDWARE,
        'resource_map_sha256': map_hash,
        'files': [{'path': target, **{key: value for key, value in record.items() if key != 'source'}}
                  for target, record in sorted(files.items())],
        'manifest_self_hash_included': False,
        'contains_base_model_weights': False, 'contains_training_corpus': False,
        'contains_game_dictionary_data': False, 'contains_private_curation': False,
        'contains_credentials': False, 'runtime_adapter_weights_included': False,
        'remote_mutation_performed_by_preparation': False,
        'hardware_fallback_allowed': False, 'unpause_or_restart_requested': False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.space-deploy-', dir=output.parent))
    try:
        for target, record in files.items():
            destination = temporary / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(record['source'], destination)
        (temporary / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        verify_deployment(temporary)
        if output.exists():
            output.rmdir()
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest


def verify_deployment(stage: Path, approved_manifest_sha256: str | None = None) -> dict:
    stage = Path(stage).absolute()
    _no_symlinks(stage)
    manifest_path = stage / MANIFEST
    manifest = _json(manifest_path)
    if approved_manifest_sha256 is not None and fingerprint(manifest_path)['sha256'] != approved_manifest_sha256:
        raise DeploymentError('Deployment manifest differs from the explicitly approved digest')
    records = manifest.get('files', [])
    expected = set(CODE_FILES) | RESOURCE_FILES
    if len(records) != len(expected) or {record.get('path') for record in records} != expected:
        raise DeploymentError('Deployment manifest differs from the strict file allowlist')
    if manifest.get('repo_id') != REPO_ID or manifest.get('private') is not True or manifest.get('hardware') != HARDWARE:
        raise DeploymentError('Only the designated private ZeroGPU Space is allowed')
    for flag in ('contains_base_model_weights', 'contains_training_corpus', 'contains_game_dictionary_data',
                 'contains_private_curation', 'contains_credentials', 'runtime_adapter_weights_included',
                 'remote_mutation_performed_by_preparation', 'hardware_fallback_allowed', 'unpause_or_restart_requested'):
        if manifest.get(flag) is not False:
            raise DeploymentError('Unexpected deployment policy flag: ' + flag)
    actual = set()
    for path in stage.rglob('*'):
        if path.is_symlink():
            raise DeploymentError('Deployment stage contains a symlink')
        if path.is_file():
            actual.add(path.relative_to(stage).as_posix())
        elif not path.is_dir():
            raise DeploymentError('Deployment stage contains a non-regular entry')
    if actual != expected | {MANIFEST}:
        raise DeploymentError('Deployment stage has extra or missing files')
    for record in records:
        if fingerprint(stage / record['path']) != {key: record[key] for key in ('bytes', 'sha256', 'git_blob_sha1')}:
            raise DeploymentError('Deployment file changed: ' + record['path'])
    _cloud_metadata((stage / 'README.md').read_bytes(), (stage / 'requirements.txt').read_bytes())
    return manifest


def _remote(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except Exception as error:
        # SDK error bodies or request details must never print credential values.
        raise DeploymentError('Hugging Face operation failed (' + type(error).__name__ + ')') from None


def create_private_space(api):
    """Caller-triggered creation only; no paid/CPU fallback or restart operation."""
    return _remote(api.create_repo, repo_id=REPO_ID, repo_type='space', private=True,
                   exist_ok=False, space_sdk='gradio', space_hardware=HARDWARE)


def assert_private_zerogpu(api):
    info = _remote(api.repo_info, repo_id=REPO_ID, repo_type='space')
    runtime = getattr(info, 'runtime', None)
    current = getattr(runtime, 'hardware', None)
    requested = getattr(runtime, 'requested_hardware', None)
    if getattr(info, 'private', None) is not True or getattr(info, 'sdk', 'gradio') != 'gradio':
        raise DeploymentError('Refusing a non-private or non-Gradio Space')
    if not ({current, requested} <= {None, HARDWARE} and HARDWARE in (current, requested)):
        raise DeploymentError('Refusing unverified or paid hardware; no fallback is permitted')
    return info


def commit_operations(stage: Path, approved_manifest_sha256: str, *, operation_factory=None) -> list:
    stage = Path(stage).absolute()
    manifest = verify_deployment(stage, approved_manifest_sha256)
    if operation_factory is None:
        from huggingface_hub import CommitOperationAdd
        operation_factory = CommitOperationAdd
    names = [record['path'] for record in manifest['files']] + [MANIFEST]
    return [operation_factory(path_in_repo=name, path_or_fileobj=str(Path(stage) / name)) for name in names]


def verify_remote_files(api, stage: Path, *, revision: str) -> dict:
    manifest = verify_deployment(stage)
    records = manifest['files'] + [{'path': MANIFEST, **fingerprint(Path(stage) / MANIFEST)}]
    names = [record['path'] for record in records]
    metadata = _remote(api.get_paths_info, repo_id=REPO_ID, paths=names, repo_type='space', revision=revision)
    remote = {item.path: item for item in metadata}
    verified = []
    for record in records:
        item = remote.get(record['path'])
        if item is None or getattr(item, 'size', None) != record['bytes']:
            raise DeploymentError('Remote deployment file is missing or differs in size: ' + record['path'])
        lfs = getattr(item, 'lfs', None)
        remote_hash = lfs.get('sha256') if isinstance(lfs, dict) else getattr(lfs, 'sha256', None)
        matches = remote_hash == record['sha256'] if remote_hash is not None else getattr(item, 'blob_id', None) == record['git_blob_sha1']
        if not matches:
            raise DeploymentError('Remote deployment file hash differs: ' + record['path'])
        verified.append(record['path'])
    return {'revision': revision, 'verified_files': verified, 'remote_hashes_verified': True}


def upload_deployment(api, stage: Path, approved_manifest_sha256: str, *, operation_factory=None) -> dict:
    assert_private_zerogpu(api)
    manifest = verify_deployment(stage, approved_manifest_sha256)
    expected = {record['path'] for record in manifest['files']} | {MANIFEST, '.gitattributes'}
    existing = set(_remote(api.list_repo_files, repo_id=REPO_ID, repo_type='space'))
    if existing - expected:
        raise DeploymentError('Remote repo has unapproved files; no deletion or full-repo upload is attempted')
    operations = commit_operations(stage, approved_manifest_sha256, operation_factory=operation_factory)
    result = _remote(api.create_commit, repo_id=REPO_ID, repo_type='space', operations=operations,
                     commit_message='Deploy reviewed code and licensed English/Japanese lexical resources')
    revision = getattr(result, 'oid', None)
    if not isinstance(revision, str) or not revision:
        raise DeploymentError('Commit completed but its revision is unavailable; verify manually')
    return verify_remote_files(api, stage, revision=revision)


def set_runtime_read_secret(api, *, token_getter=None) -> dict:
    """Root/operator calls this separately. Secret value never enters a manifest."""
    assert_private_zerogpu(api)
    if token_getter is None:
        from huggingface_hub import get_token
        token_getter = get_token
    try:
        token = token_getter()
    except Exception:
        raise DeploymentError('Cannot read the existing Hugging Face authentication') from None
    if not isinstance(token, str) or not token:
        raise DeploymentError('Existing HF_TOKEN_PATH authentication is unavailable')
    _remote(api.add_space_secret, repo_id=REPO_ID, key='HF_TOKEN', value=token,
            description='Read the operator-reviewed private LoRA repository at runtime')
    return {'secret_key': 'HF_TOKEN', 'configured': True, 'value_included': False}


def set_public_variables(api, variables: dict[str, str]) -> dict:
    assert_private_zerogpu(api)
    if not isinstance(variables, dict) or not set(variables) <= PUBLIC_VARIABLES:
        raise DeploymentError('Only reviewed non-sensitive runtime variable names are allowed')
    if any(not isinstance(value, str) or re.search(r'hf_[A-Za-z0-9]{20,}', value) for value in variables.values()):
        raise DeploymentError('Public variables must not contain authentication values')
    for key, value in variables.items():
        _remote(api.add_space_variable, repo_id=REPO_ID, key=key, value=value)
    return {'configured_variable_names': sorted(variables)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--resource-map', type=Path, default=ROOT / 'runs/space-resources-en-ja/file-map.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/space-deployment')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        manifest = verify_deployment(args.output) if args.verify_only else prepare_deployment(args.source_root, args.resource_map, args.output)
        print(json.dumps({'stage': str(args.output.absolute()), 'repo_id': REPO_ID, 'hardware': HARDWARE,
                          'payload_files': len(manifest['files']),
                          'approved_manifest_sha256': fingerprint(args.output / MANIFEST)['sha256'],
                          'remote_mutation_performed': False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Deployment preparation failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
