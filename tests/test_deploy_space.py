"""No-network checks for the separate, explicitly mapped cloud deployment."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import deploy_space as deploy
from scripts import prepare_space


class DeploySpaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'project'
        self.root.mkdir()
        self.stage = Path(temporary.name) / 'stage'
        for source in deploy.CODE_FILES.values():
            path = self.root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            if source == 'spaces/README.cloud.md':
                content = b'---\ntitle: Fixture Space\nsdk: gradio\nsdk_version: "5.49.1"\npython_version: "3.12"\napp_file: app.py\n---\nCode fixture.\n'
            elif source == 'spaces/requirements-cloud.txt':
                content = ('\n'.join(name + '==' + version for name, version in deploy.CLOUD_PINNED_REQUIREMENTS.items()) + '\n').encode()
            else:
                content = ('# Explicit code fixture: ' + source + '\n').encode()
            path.write_bytes(content)
        self.map = self.root / 'runs/space-resources-en-ja/file-map.json'
        records = []
        for name in sorted(deploy.RESOURCE_FILES):
            source = deploy.RESOURCE_SOURCE_PREFIX + name
            path = self.root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Reviewed WordNet fixture: ' + name + '\n')
            hashed = deploy.fingerprint(path)
            records.append({'source': source, 'path_in_repo': name,
                            'sha256': hashed['sha256'], 'bytes': hashed['bytes'],
                            'source_id': ['wnja:1.1', 'oewn:2025'],
                            'license': ['Japanese-WordNet + WordNet', 'CC-BY-4.0 + WordNet']})
        self.map.parent.mkdir(parents=True, exist_ok=True)
        self.map.write_text(json.dumps({'schema_version': 1, 'files': records}))

    def build(self):
        return deploy.prepare_deployment(self.root, self.map, self.stage)

    def api(self, *, hardware='zero-a10g', private=True):
        info = SimpleNamespace(private=private, sdk='gradio',
                               runtime=SimpleNamespace(hardware=hardware, requested_hardware=hardware))
        api = SimpleNamespace(repo_info=Mock(return_value=info),
                              create_repo=Mock(return_value='created'),
                              list_repo_files=Mock(return_value=['.gitattributes', 'README.md']),
                              create_commit=Mock(return_value=SimpleNamespace(oid='commit-fixture')),
                              add_space_secret=Mock(), add_space_variable=Mock(),
                              request_space_hardware=Mock(), restart_space=Mock(),
                              pause_space=Mock(), upload_folder=Mock(), delete_file=Mock())
        def metadata(**kwargs):
            manifest = deploy.verify_deployment(self.stage)
            records = manifest['files'] + [{'path': deploy.MANIFEST,
                                           **deploy.fingerprint(self.stage / deploy.MANIFEST)}]
            return [SimpleNamespace(path=record['path'], size=record['bytes'],
                                    blob_id=record['git_blob_sha1'],
                                    lfs=SimpleNamespace(sha256=record['sha256']) if record['path'].endswith('.sqlite3') else None)
                    for record in records]
        api.get_paths_info = Mock(side_effect=metadata)
        return api

    def test_strict_cloud_and_eight_resource_files_do_not_widen_code_only_policy(self):
        before = dict(prepare_space.ALLOWLIST)
        for name in ('.env', 'token', 'data/raw/fan.csv', 'data/processed/lexicon.jsonl',
                     'data/research/corpus.jsonl', 'data/training/train.jsonl',
                     'data/curation/ko_glosses.json', 'models/model.safetensors',
                     '.cache/huggingface/token', '.git/config'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('PRIVATE_CONTENT_NOT_TO_UPLOAD')
        manifest = self.build()
        self.assertEqual(len(deploy.CODE_FILES), 14)
        self.assertEqual(len(manifest['files']), 22)
        actual = {path.relative_to(self.stage).as_posix() for path in self.stage.rglob('*') if path.is_file()}
        self.assertEqual(actual, set(deploy.CODE_FILES) | deploy.RESOURCE_FILES | {deploy.MANIFEST})
        self.assertEqual(prepare_space.ALLOWLIST, before)
        self.assertEqual(len(before), 13)
        self.assertEqual(deploy.CODE_FILES['DEPLOY.md'], 'spaces/DEPLOY.cloud.md')
        self.assertEqual(prepare_space.ALLOWLIST['DEPLOY.md'], 'spaces/DEPLOY.md')
        for path in self.stage.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'PRIVATE_CONTENT_NOT_TO_UPLOAD', path.read_bytes())
        self.assertFalse(manifest['contains_base_model_weights'])
        self.assertFalse(manifest['contains_game_dictionary_data'])
        self.assertFalse(manifest['contains_credentials'])
        self.assertEqual(deploy.verify_deployment(self.stage), manifest)

    def test_cloud_dependency_policy_is_separate_and_exact(self):
        requirements = self.root / 'spaces/requirements-cloud.txt'
        self.assertIn('bitsandbytes', prepare_space.PINNED_REQUIREMENTS)
        self.assertNotIn('bitsandbytes', deploy.CLOUD_PINNED_REQUIREMENTS)
        self.assertEqual(deploy.CLOUD_PINNED_REQUIREMENTS['spaces'], '0.51.3')
        requirements.write_text(requirements.read_text() + 'bitsandbytes==0.48.1\n')
        with self.assertRaisesRegex(deploy.DeploymentError, 'BF16 dependency snapshot'):
            self.build()
        self.assertFalse(self.stage.exists())

    def test_resource_map_cannot_redirect_to_a_credential_or_an_unapproved_destination(self):
        value = json.loads(self.map.read_text())
        original = json.loads(self.map.read_text())
        value['files'][0]['source'] = '.env'
        self.map.write_text(json.dumps(value))
        with self.assertRaisesRegex(deploy.DeploymentError, 'independently prepared'):
            self.build()
        self.assertFalse(self.stage.exists())
        original['files'][0]['path_in_repo'] = '../token'
        self.map.write_text(json.dumps(original))
        with self.assertRaisesRegex(deploy.DeploymentError, 'destinations'):
            self.build()
        self.assertFalse(self.stage.exists())

    def test_resource_hash_mismatch_and_symlink_are_rejected(self):
        record = json.loads(self.map.read_text())['files'][0]
        source = self.root / record['source']
        source.write_text('changed resource')
        with self.assertRaisesRegex(deploy.DeploymentError, 'hash or size'):
            self.build()
        source.unlink()
        secret = self.root / '.env'
        secret.write_text('secret')
        source.symlink_to(secret)
        with self.assertRaisesRegex(deploy.DeploymentError, 'Symlink'):
            self.build()

    def test_existing_stage_is_preserved_and_manifest_digest_is_required_for_operations(self):
        self.stage.mkdir()
        previous = self.stage / 'user-work.txt'
        previous.write_text('keep')
        with self.assertRaisesRegex(deploy.DeploymentError, 'preserved'):
            self.build()
        self.assertEqual(previous.read_text(), 'keep')
        previous.unlink()
        self.build()
        factory = Mock()
        with self.assertRaisesRegex(deploy.DeploymentError, 'approved digest'):
            deploy.commit_operations(self.stage, 'wrong-digest', operation_factory=factory)
        factory.assert_not_called()

    def test_create_is_private_gradio_zerogpu_without_cpu_or_paid_fallback(self):
        api = self.api()
        self.assertEqual(deploy.create_private_space(api), 'created')
        api.create_repo.assert_called_once_with(repo_id=deploy.REPO_ID, repo_type='space', private=True,
                                               exist_ok=False, space_sdk='gradio', space_hardware='zero-a10g')
        api.request_space_hardware.assert_not_called()
        api.restart_space.assert_not_called()
        api.pause_space.assert_not_called()
        api.create_repo.side_effect = RuntimeError('remote rejected free tier')
        with self.assertRaises(deploy.DeploymentError):
            deploy.create_private_space(api)
        self.assertEqual(api.create_repo.call_count, 2)

    def test_upload_uses_only_explicit_add_operations_and_verifies_git_and_lfs_hashes(self):
        self.build()
        api = self.api()
        digest = deploy.fingerprint(self.stage / deploy.MANIFEST)['sha256']
        operation_factory = lambda **values: SimpleNamespace(**values)
        result = deploy.upload_deployment(api, self.stage, digest, operation_factory=operation_factory)
        operations = api.create_commit.call_args.kwargs['operations']
        self.assertEqual({value.path_in_repo for value in operations}, set(deploy.CODE_FILES) | deploy.RESOURCE_FILES | {deploy.MANIFEST})
        self.assertTrue(all(Path(value.path_or_fileobj).is_relative_to(self.stage) for value in operations))
        self.assertTrue(result['remote_hashes_verified'])
        self.assertEqual(len(result['verified_files']), 23)
        self.assertEqual(api.get_paths_info.call_args.kwargs['revision'], 'commit-fixture')
        api.upload_folder.assert_not_called()
        api.delete_file.assert_not_called()
        api.request_space_hardware.assert_not_called()
        api.restart_space.assert_not_called()

    def test_private_and_free_hardware_are_required_before_upload_or_secret_changes(self):
        self.build()
        digest = deploy.fingerprint(self.stage / deploy.MANIFEST)['sha256']
        for api in (self.api(hardware='cpu-basic'), self.api(hardware='a10g-small'), self.api(private=False)):
            with self.subTest(api=api), self.assertRaises(deploy.DeploymentError):
                deploy.upload_deployment(api, self.stage, digest, operation_factory=lambda **values: values)
            api.create_commit.assert_not_called()
            with self.assertRaises(deploy.DeploymentError):
                deploy.set_runtime_read_secret(api, token_getter=lambda: 'hf_' + 'A' * 30)
            api.add_space_secret.assert_not_called()

    def test_unapproved_remote_files_are_not_silently_kept_or_deleted(self):
        self.build()
        api = self.api()
        api.list_repo_files.return_value = ['README.md', '.env']
        with self.assertRaisesRegex(deploy.DeploymentError, 'unapproved files'):
            deploy.upload_deployment(api, self.stage, deploy.fingerprint(self.stage / deploy.MANIFEST)['sha256'])
        api.create_commit.assert_not_called()
        api.delete_file.assert_not_called()

    def test_remote_hash_failure_is_reported(self):
        self.build()
        api = self.api()
        api.get_paths_info.return_value = [SimpleNamespace(path='app.py', size=1, blob_id='bad', lfs=None)]
        api.get_paths_info.side_effect = None
        with self.assertRaisesRegex(deploy.DeploymentError, 'missing or differs in size'):
            deploy.verify_remote_files(api, self.stage, revision='commit-fixture')

    def test_token_is_only_passed_to_secret_api_and_never_printed_or_returned(self):
        api = self.api()
        token = 'hf_' + 'A' * 30
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            result = deploy.set_runtime_read_secret(api, token_getter=lambda: token)
        self.assertNotIn(token, output.getvalue())
        self.assertNotIn(token, json.dumps(result))
        api.add_space_secret.assert_called_once_with(repo_id=deploy.REPO_ID, key='HF_TOKEN', value=token,
                                                    description='Read the operator-reviewed private LoRA repository at runtime')
        api.add_space_variable.assert_not_called()
        api.add_space_secret.side_effect = RuntimeError('server echoed ' + token)
        with self.assertRaises(deploy.DeploymentError) as caught:
            deploy.set_runtime_read_secret(api, token_getter=lambda: token)
        self.assertNotIn(token, str(caught.exception))

    def test_public_variables_cannot_receive_token_names_or_values(self):
        api = self.api()
        for variables in ({'HF_TOKEN': 'secret'}, {'FIXMARGE_MODEL': 'hf_' + 'A' * 30}):
            with self.subTest(variables=variables), self.assertRaises(deploy.DeploymentError):
                deploy.set_public_variables(api, variables)
        api.add_space_variable.assert_not_called()
        result = deploy.set_public_variables(api, {'FIXMARGE_DEVICE': 'cpu'})
        self.assertEqual(result['configured_variable_names'], ['FIXMARGE_DEVICE'])
        api.add_space_variable.assert_called_once_with(repo_id=deploy.REPO_ID, key='FIXMARGE_DEVICE', value='cpu')


if __name__ == '__main__':
    unittest.main()
