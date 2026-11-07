#!/usr/bin/env python3
"""Prepare a code-only Hugging Face Space using an explicit file allowlist.

This command never imports the app, contacts Hugging Face, installs packages,
reads credentials, downloads a model, creates a repository, or changes hardware.
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
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_BYTES = 1_000_000
MANIFEST_NAME = 'manifest.json'
# Destination -> source. No directory copying, globbing, or Git discovery.
ALLOWLIST = {
    '.gitignore': 'spaces/.gitignore',
    'DEPLOY.md': 'spaces/DEPLOY.md',
    'LICENSE': 'LICENSE',
    'README.md': 'spaces/README.md',
    'app.py': 'app.py',
    'requirements.txt': 'spaces/requirements.txt',
    'src/fixmarge/__init__.py': 'src/fixmarge/__init__.py',
    'src/fixmarge/demo.py': 'src/fixmarge/demo.py',
    'src/fixmarge/grounding.py': 'src/fixmarge/grounding.py',
    'src/fixmarge/infer.py': 'src/fixmarge/infer.py',
    'src/fixmarge/rag.py': 'src/fixmarge/rag.py',
    'src/fixmarge/sentence_diagnostics.py': 'src/fixmarge/sentence_diagnostics.py',
    'src/fixmarge/standard_dictionary.py': 'src/fixmarge/standard_dictionary.py',
}
PINNED_REQUIREMENTS = {
    'torch': '2.8.0', 'transformers': '4.57.1', 'peft': '0.17.1',
    'accelerate': '1.10.1', 'bitsandbytes': '0.48.1', 'safetensors': '0.6.2',
    'huggingface-hub': '0.35.3', 'jinja2': '3.1.6', 'gradio': '5.49.1',
}
YAML_KEYS = {'title', 'emoji', 'colorFrom', 'colorTo', 'sdk', 'sdk_version',
             'python_version', 'app_file', 'pinned'}


def _reject_symlinks(path: Path, boundary: Path | None = None) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise ValueError('Symlink paths are not accepted: ' + str(current))
        if current == boundary or current == current.parent:
            break
        current = current.parent


def _read_regular(path: Path, boundary: Path) -> bytes:
    _reject_symlinks(path, boundary)
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except OSError as exc:
        raise ValueError('Required regular source file is unavailable: ' + str(path)) from exc
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Source must be a regular file: ' + str(path))
        if info.st_size > MAX_SOURCE_BYTES:
            raise ValueError('Source exceeds the code-only size limit: ' + str(path))
        content = stream.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError('Source exceeds the code-only size limit: ' + str(path))
    return content


def _validate_metadata(readme: bytes, requirements: bytes) -> None:
    text = readme.decode('utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError('Space README must begin with YAML frontmatter.')
    frontmatter = text[4:].split('\n---\n', 1)[0]
    fields = {}
    for line in frontmatter.splitlines():
        if not line or line != line.lstrip() or ':' not in line:
            raise ValueError('Space YAML must contain flat, explicit metadata.')
        key, value = line.split(':', 1)
        if key not in YAML_KEYS or key in fields:
            raise ValueError('Unexpected or duplicate Space YAML key: ' + key)
        fields[key] = value.strip().strip('"\'')
    expected = {'sdk': 'gradio', 'sdk_version': '5.49.1',
                'python_version': '3.12', 'app_file': 'app.py'}
    if not fields.get('title') or any(fields.get(key) != value for key, value in expected.items()):
        raise ValueError('Space YAML must pin Gradio 5.49.1, Python 3.12, and app.py.')
    pins = {}
    for line in requirements.decode('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)', line)
        if not match:
            raise ValueError('Only exact dependency pins are accepted: ' + line)
        name = match[1].lower().replace('_', '-')
        if name in pins:
            raise ValueError('Duplicate requirement: ' + name)
        pins[name] = match[2]
    if pins != PINNED_REQUIREMENTS:
        raise ValueError('Space requirements differ from the reviewed dependency snapshot.')


def verify_staging(output: Path) -> dict:
    """Check every staged file, rejecting extras, symlinks and hash changes."""
    output = Path(output).absolute()
    _reject_symlinks(output)
    if not output.is_dir():
        raise ValueError('Staging directory does not exist: ' + str(output))
    manifest = json.loads(_read_regular(output / MANIFEST_NAME, output).decode('utf-8'))
    records = manifest.get('files', [])
    if not isinstance(records, list) or len(records) != len(ALLOWLIST):
        raise ValueError('Manifest must enumerate exactly the allowed payload files.')
    if {record.get('path') for record in records} != set(ALLOWLIST):
        raise ValueError('Manifest contains missing, duplicate, or unapproved file paths.')
    actual = set()
    for path in output.rglob('*'):
        if path.is_symlink():
            raise ValueError('Staging contains a symlink: ' + str(path))
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
        elif not path.is_dir():
            raise ValueError('Staging contains a non-regular filesystem entry.')
    if actual != set(ALLOWLIST) | {MANIFEST_NAME}:
        raise ValueError('Staging contains extra or missing files; prepare a fresh directory.')
    for record in records:
        if record.get('source') != ALLOWLIST[record['path']]:
            raise ValueError('Manifest source mapping differs from the allowlist.')
        content = _read_regular(output / record['path'], output)
        if record.get('bytes') != len(content) or record.get('sha256') != hashlib.sha256(content).hexdigest():
            raise ValueError('Staged file differs from its manifest: ' + record['path'])
    for flag in ('contains_weights', 'contains_research_data', 'contains_credentials',
                 'upload_performed', 'model_download_performed', 'hardware_changed'):
        if manifest.get(flag) is not False:
            raise ValueError('Manifest policy flag is not false: ' + flag)
    _validate_metadata((output / 'README.md').read_bytes(), (output / 'requirements.txt').read_bytes())
    return manifest


def prepare_space(source_root: Path = ROOT, output: Path | None = None) -> dict:
    source_root = Path(source_root).absolute()
    _reject_symlinks(source_root)
    if not source_root.is_dir():
        raise ValueError('Project root does not exist: ' + str(source_root))
    output = Path(output).absolute() if output is not None else source_root / 'runs/space-staging'
    _reject_symlinks(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Output must be new or empty; existing files are preserved: ' + str(output))
    # Read and validate everything before creating or changing the output folder.
    payload = {target: _read_regular(source_root / relative, source_root)
               for target, relative in sorted(ALLOWLIST.items())}
    _validate_metadata(payload['README.md'], payload['requirements.txt'])
    manifest = {
        'schema_version': 1, 'selection': 'explicit_file_allowlist',
        'sdk': 'gradio', 'sdk_version': '5.49.1', 'python_version': '3.12',
        'files': [{'path': target, 'source': ALLOWLIST[target], 'bytes': len(content),
                   'sha256': hashlib.sha256(content).hexdigest()}
                  for target, content in payload.items()],
        'manifest_file': MANIFEST_NAME, 'manifest_self_hash_included': False,
        'contains_weights': False, 'contains_research_data': False,
        'contains_credentials': False, 'upload_performed': False,
        'model_download_performed': False, 'hardware_changed': False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.fixmarge-space-', dir=output.parent))
    try:
        for relative, content in payload.items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (temporary / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        verify_staging(temporary)
        if output.exists():
            output.rmdir()  # Only the preflight-approved empty directory can be removed.
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)  # Only this invocation's fresh temporary directory.
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/space-staging',
                        help='New or empty staging directory; existing contents are never overwritten')
    parser.add_argument('--verify-only', action='store_true', help='Verify the existing staging manifest without modifying files')
    args = parser.parse_args(argv)
    try:
        manifest = verify_staging(args.output) if args.verify_only else prepare_space(output=args.output)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, 'Space preparation failed: ' + str(exc) + '\n')
    print(json.dumps({'output': str(args.output.absolute()), 'files': len(manifest['files']),
                      'contains_weights': manifest['contains_weights'],
                      'contains_research_data': manifest['contains_research_data'],
                      'upload_performed': manifest['upload_performed']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
