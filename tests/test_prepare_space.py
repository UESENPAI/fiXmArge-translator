"""Code-only Space packaging rejects data, credentials and unsafe paths."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_space


class PrepareSpaceTests(unittest.TestCase):
    EXPECTED_PAYLOAD = {
        '.gitignore', 'DEPLOY.md', 'LICENSE', 'README.md', 'app.py', 'requirements.txt',
        'src/fixmarge/__init__.py', 'src/fixmarge/demo.py', 'src/fixmarge/grounding.py',
        'src/fixmarge/infer.py', 'src/fixmarge/rag.py', 'src/fixmarge/sentence_diagnostics.py',
        'src/fixmarge/standard_dictionary.py',
    }

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.project = self.folder / 'project'
        self.project.mkdir()
        self.output = self.folder / 'stage'
        for relative in prepare_space.ALLOWLIST.values():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative.startswith('spaces/') or relative == 'LICENSE':
                path.write_bytes((ROOT / relative).read_bytes())
            else:
                path.write_text('# Allowed fixture code: ' + relative + '\n', encoding='utf-8')

    def build(self):
        return prepare_space.prepare_space(self.project, self.output)

    def test_only_explicit_code_payload_is_selected_and_hashed(self):
        forbidden = [
            '.env', '.env.production', 'token', '.git/config', '.cache/huggingface/token',
            'data/raw/source.csv', 'data/processed/lexicon.jsonl', 'data/research/train.jsonl',
            'data/training/train.jsonl', 'data/curation/ko_glosses.json',
            'data/external/lexicons.sqlite3', 'data/external/raw/wn-wikt-kor.tab',
            'data/external/licenses/Princeton-WordNet.txt', 'runs/diagnostic.json',
            'models/model.safetensors', 'weights/model.pt',
            'src/fixmarge/private_extension.py', 'untracked-private-notes.txt',
        ]
        for relative in forbidden:
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('LOCAL_SECRET_AND_RESEARCH_SENTINEL\n')
        manifest = self.build()
        staged = {path.relative_to(self.output).as_posix() for path in self.output.rglob('*') if path.is_file()}
        self.assertEqual(set(prepare_space.ALLOWLIST), self.EXPECTED_PAYLOAD)
        self.assertEqual(staged, self.EXPECTED_PAYLOAD | {'manifest.json'})
        self.assertFalse(manifest['contains_weights'])
        self.assertFalse(manifest['contains_research_data'])
        self.assertFalse(manifest['contains_credentials'])
        self.assertFalse(manifest['upload_performed'])
        for record in manifest['files']:
            content = (self.output / record['path']).read_bytes()
            self.assertEqual(content, (self.project / record['source']).read_bytes())
            self.assertEqual(record['sha256'], hashlib.sha256(content).hexdigest())
            self.assertEqual(record['bytes'], len(content))
        for path in self.output.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'LOCAL_SECRET_AND_RESEARCH_SENTINEL', path.read_bytes())
        self.assertEqual(prepare_space.verify_staging(self.output), manifest)
        self.assertTrue((self.project / '.env').exists())

    def test_nonempty_output_is_preserved(self):
        self.output.mkdir()
        existing = self.output / 'user-work.txt'
        existing.write_text('keep my work')
        with self.assertRaisesRegex(ValueError, 'existing files are preserved'):
            self.build()
        self.assertEqual(existing.read_text(), 'keep my work')
        self.assertEqual(list(self.output.iterdir()), [existing])

    def test_empty_output_can_be_used(self):
        self.output.mkdir()
        self.build()
        self.assertTrue((self.output / 'app.py').is_file())
        self.assertTrue((self.output / 'manifest.json').is_file())

    def test_symlinked_source_cannot_copy_a_credential(self):
        secret = self.project / '.env'
        secret.write_text('credential must stay local')
        app = self.project / 'app.py'
        app.unlink()
        app.symlink_to(secret)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build()
        self.assertFalse(self.output.exists())
        self.assertEqual(secret.read_text(), 'credential must stay local')

    def test_symlinked_source_parent_is_rejected(self):
        external = self.folder / 'external-source'
        shutil.move(self.project / 'src', external)
        (self.project / 'src').symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_symlinked_destination_is_rejected(self):
        external = self.folder / 'private-output'
        external.mkdir()
        (external / 'token').write_text('keep private')
        self.output.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build()
        self.assertEqual((external / 'token').read_text(), 'keep private')
        self.assertFalse((external / 'app.py').exists())

    def test_missing_source_fails_before_creating_staging(self):
        (self.project / 'src/fixmarge/demo.py').unlink()
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_missing_standard_dictionary_fails_before_creating_staging(self):
        (self.project / 'src/fixmarge/standard_dictionary.py').unlink()
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_verify_rejects_changed_standard_dictionary(self):
        self.build()
        (self.output / 'src/fixmarge/standard_dictionary.py').write_text('changed helper')
        with self.assertRaisesRegex(ValueError, 'differs from its manifest'):
            prepare_space.verify_staging(self.output)

    def test_oversize_source_is_not_packaged_as_code(self):
        (self.project / 'app.py').write_bytes(b'x' * (prepare_space.MAX_SOURCE_BYTES + 1))
        with self.assertRaisesRegex(ValueError, 'size limit'):
            self.build()
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'Named pipes require a POSIX filesystem')
    def test_named_pipe_source_is_rejected_without_blocking(self):
        path = self.project / 'app.py'
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_unexpected_yaml_cannot_preload_a_model(self):
        readme = self.project / 'spaces/README.md'
        readme.write_text(readme.read_text().replace('sdk: gradio', 'sdk: gradio\npreload_from_hub: author/model', 1))
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_unpinned_dependency_is_rejected(self):
        requirements = self.project / 'spaces/requirements.txt'
        requirements.write_text(requirements.read_text().replace('gradio==5.49.1', 'gradio>=5.49.1'))
        with self.assertRaisesRegex(ValueError, 'exact dependency pins'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_verify_rejects_added_sensitive_file(self):
        self.build()
        (self.output / '.env').write_text('do not upload')
        with self.assertRaisesRegex(ValueError, 'extra or missing'):
            prepare_space.verify_staging(self.output)
        self.assertEqual((self.output / '.env').read_text(), 'do not upload')

    def test_verify_rejects_modified_code(self):
        self.build()
        (self.output / 'app.py').write_text('changed after manifest')
        with self.assertRaisesRegex(ValueError, 'differs from its manifest'):
            prepare_space.verify_staging(self.output)


if __name__ == '__main__':
    unittest.main()
