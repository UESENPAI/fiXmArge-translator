"""Pinned cloud adapter checks using synthetic bytes; no network or models."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from functools import partial
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from fixmarge.cloud import prepare_cloud_adapter


ADAPTER_REPO = "uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge"
ADAPTER_REVISION = "c17943bf523779fb2dd75078148a50816dd52ed7"
BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
BASE_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
ALLOWED_FILES = {"adapter_config.json", "adapter_model.safetensors", "training_manifest.json",
                 "README.md", "LICENSE", "NOTICE"}


class CloudAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.snapshot = Path(self.temporary.name)
        self.weight_bytes = b"synthetic-adapter-bytes-not-a-real-model"
        self.config = {"peft_type": "LORA", "base_model_name_or_path": BASE_MODEL,
                       "revision": BASE_REVISION}
        self.manifest = {
            "training_status": "completed", "optimizer_steps": 256,
            "base_frozen": True, "adapter_only": True, "merge_performed": False,
            "adapter_sha256": hashlib.sha256(self.weight_bytes).hexdigest(),
            "data_rights": {"sources": ["fixture:licensed-wordnet"],
                            "recorded_statuses": ["open_license"]},
        }
        self.write_metadata()
        (self.snapshot / "adapter_model.safetensors").write_bytes(self.weight_bytes)
        for name in ("README.md", "LICENSE", "NOTICE"):
            (self.snapshot / name).write_text("Synthetic test fixture only.\n", encoding="utf-8")
        self.loader = Mock(return_value=str(self.snapshot))

    def write_metadata(self):
        for name, data in (("adapter_config.json", self.config),
                           ("training_manifest.json", self.manifest)):
            (self.snapshot / name).write_text(json.dumps(data), encoding="utf-8")

    def prepare(self):
        return prepare_cloud_adapter(snapshot_loader=self.loader)

    def test_valid_snapshot_uses_pinned_repo_revision_and_exact_file_allowlist(self):
        before = {path.name: path.read_bytes() for path in self.snapshot.iterdir()}
        result = self.prepare()
        self.assertIsInstance(result, Path)
        self.assertEqual(result, self.snapshot)
        self.loader.assert_called_once()
        options = self.loader.call_args.kwargs
        self.assertEqual(options["repo_id"], ADAPTER_REPO)
        self.assertEqual(options["revision"], ADAPTER_REVISION)
        self.assertEqual(set(options["allow_patterns"]), ALLOWED_FILES)
        self.assertEqual(len(options["allow_patterns"]), len(ALLOWED_FILES))
        self.assertNotIn("token", options)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.snapshot.iterdir()})

    def test_snapshot_loader_can_return_a_path(self):
        self.loader.return_value = self.snapshot
        self.assertEqual(self.prepare(), self.snapshot)

    def test_wrong_base_model_revision_or_adapter_type_is_rejected(self):
        for key, value in (("base_model_name_or_path", "unreviewed/wrong-base"),
                           ("revision", "main"), ("revision", None),
                           ("peft_type", "PROMPT_TUNING")):
            with self.subTest(key=key, value=value):
                original = self.config[key]
                try:
                    self.config[key] = value
                    self.write_metadata()
                    with self.assertRaises(ValueError):
                        self.prepare()
                finally:
                    self.config[key] = original
        self.write_metadata()

    def test_incomplete_or_non_preserving_training_record_is_rejected(self):
        changes = [("training_status", "running"), ("training_status", "failed"),
                   ("optimizer_steps", 255), ("optimizer_steps", "256"),
                   ("base_frozen", False), ("base_frozen", "true"), ("base_frozen", 1),
                   ("adapter_only", False), ("adapter_only", "true"), ("adapter_only", 1),
                   ("merge_performed", True), ("merge_performed", "false"),
                   ("merge_performed", 0)]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                original = self.manifest[key]
                try:
                    self.manifest[key] = value
                    self.write_metadata()
                    with self.assertRaises(ValueError):
                        self.prepare()
                finally:
                    self.manifest[key] = original
        self.write_metadata()

    def test_tampered_weights_or_missing_digest_are_rejected(self):
        weights = self.snapshot / "adapter_model.safetensors"
        weights.write_bytes(self.weight_bytes + b"modified")
        with self.assertRaises(ValueError):
            self.prepare()
        weights.write_bytes(self.weight_bytes)
        self.manifest.pop("adapter_sha256")
        self.write_metadata()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_mismatched_digest_is_rejected(self):
        self.manifest["adapter_sha256"] = "0" * 64
        self.write_metadata()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_missing_required_files_fail_as_value_errors(self):
        for name in ("adapter_config.json", "training_manifest.json", "adapter_model.safetensors"):
            with self.subTest(name=name):
                file = self.snapshot / name
                original = file.read_bytes()
                try:
                    file.unlink()
                    with self.assertRaises(ValueError):
                        self.prepare()
                finally:
                    file.write_bytes(original)

    def test_malformed_or_non_object_json_fails_as_value_errors(self):
        for name in ("adapter_config.json", "training_manifest.json"):
            file = self.snapshot / name
            original = file.read_bytes()
            try:
                for raw in (b"{unfinished", b"[]", b"null", b"\xff"):
                    with self.subTest(name=name, raw=raw):
                        file.write_bytes(raw)
                        with self.assertRaises(ValueError):
                            self.prepare()
            finally:
                file.write_bytes(original)

    def test_download_error_is_safe_and_does_not_echo_credentials(self):
        secret_marker = "SENSITIVE_LOADER_DIAGNOSTIC"
        self.loader.side_effect = RuntimeError(secret_marker)
        with self.assertRaises(ValueError) as raised:
            self.prepare()
        self.assertNotIn(secret_marker, str(raised.exception))

    def test_missing_or_invalid_snapshot_path_is_a_safe_value_error(self):
        for path in (None, 7, self.snapshot / "missing", self.snapshot / "README.md"):
            with self.subTest(path=path):
                self.loader.return_value = path
                with self.assertRaises(ValueError):
                    self.prepare()

    def test_import_does_not_download_or_prepare_an_adapter(self):
        source = Path(__file__).resolve().parents[1] / "src/fixmarge/cloud.py"
        loader = Mock(side_effect=AssertionError("No download during import"))
        spec = importlib.util.spec_from_file_location("fixmarge._cloud_import_probe", source)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"huggingface_hub": SimpleNamespace(snapshot_download=loader)}):
            spec.loader.exec_module(module)
        loader.assert_not_called()
        self.assertTrue(callable(module.prepare_cloud_adapter))


class CloudLifecycleTests(unittest.TestCase):
    def test_preload_is_idempotent_and_forbidden_pair_stays_rejected(self):
        from fixmarge.demo import DemoService

        runner = Mock()
        runner.generate.return_value = json.dumps({
            "tentative_translation": "真実", "evidence_ids": [], "uncertainties": []})
        runner_factory = Mock(return_value=runner)
        rag_factory = Mock(side_effect=AssertionError("No domain dictionary during preload"))
        standard_lookup = Mock(return_value={
            "available": False, "entries": [], "matched_entry_count": 0, "attributions": []})
        service = DemoService(runner_factory=runner_factory, rag_factory=rag_factory,
                              standard_lookup=standard_lookup, device="cuda")
        service.preload()
        service.preload()
        runner_factory.assert_called_once()
        runner.generate.assert_not_called()
        rag_factory.assert_not_called()
        standard_lookup.assert_not_called()
        self.assertEqual(runner_factory.call_args.kwargs["revision"], BASE_REVISION)
        with self.assertRaises(ValueError):
            service.run("truth", "en", "ja", generate=True)
        runner_factory.assert_called_once()
        runner.generate.assert_not_called()
        rag_factory.assert_not_called()
        standard_lookup.assert_not_called()
        self.assertIs(service._runner, runner)

    @staticmethod
    def write_cloud_dictionary(directory):
        entry = {"id": "fixture:truth", "form": "sinruits", "aliases": [],
                 "senses": {"en": ["truth"], "ja": ["真実"], "ko": ["진실"]},
                 "sources": ["synthetic-fixture"], "status": "fixture"}
        (directory / "lexicon.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")
        (directory / "rules.jsonl").write_text("", encoding="utf-8")

    def test_cloud_app_bootstrap_preloads_and_validates_before_gpu_calls(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        data_directory = Path(temporary.name)
        self.write_cloud_dictionary(data_directory)
        events = []
        adapter = Path("/synthetic/pinned-cloud-adapter")
        service = Mock()
        service.preload.side_effect = lambda: events.append("preload")
        factory = Mock(side_effect=lambda **options: events.append("service") or service)
        prepare = Mock(side_effect=lambda: events.append("prepare") or adapter)
        runner_factory = Mock(name="ModelRunner")
        wrapped_response = Mock(name="gpu_wrapped_inference")
        decorator = Mock(side_effect=lambda function: events.append("decorate") or wrapped_response)
        gpu = Mock(side_effect=lambda **options: events.append("gpu") or decorator)
        gradio = MagicMock(name="gradio")

        class GradioInputError(ValueError):
            pass

        gradio.Error = GradioInputError
        environment = {"SPACE_ID": "fixture", "FIXMARGE_CLOUD": "1",
                       "FIXMARGE_DATA_DIR": str(data_directory),
                       "FIXMARGE_DEVICE": "cpu", "FIXMARGE_LOAD_IN_4BIT": "1",
                       "FIXMARGE_ADAPTER_PATH": "/ignored/local-adapter"}
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(sys, "path", list(sys.path)), \
                patch.dict(sys.modules, {"gradio": gradio, "spaces": SimpleNamespace(GPU=gpu)}), \
                patch("fixmarge.demo.DemoService", factory), \
                patch("fixmarge.cloud.prepare_cloud_adapter", prepare), \
                patch("fixmarge.infer.ModelRunner", runner_factory), \
                patch("fixmarge.infer._load_bundle", side_effect=AssertionError("No actual model load")):
            namespace = runpy.run_path(str(app_path), run_name="fixmarge_cloud_smoke")
        prepare.assert_called_once_with()
        factory.assert_called_once()
        options = factory.call_args.kwargs
        self.assertEqual(options["adapter"], str(adapter))
        self.assertEqual(options["data_dir"], str(data_directory))
        self.assertEqual(options["model_name"], BASE_MODEL)
        self.assertEqual(options["device"], "cuda")
        self.assertIs(options["allow_download"], True)
        self.assertIs(options["load_in_4bit"], False)
        selected_factory = options["runner_factory"]
        self.assertIsInstance(selected_factory, partial)
        self.assertIs(selected_factory.func, runner_factory)
        self.assertEqual(selected_factory.keywords, {"device_map": "cuda"})
        service.preload.assert_called_once_with()
        service.run.assert_not_called()
        runner_factory.assert_not_called()
        gpu.assert_called_once_with(duration=60)
        decorator.assert_called_once()
        self.assertEqual(decorator.call_args.args[0].__name__, "_respond_inference")
        self.assertIs(namespace["_respond_inference"], wrapped_response)
        self.assertIsNot(namespace["respond"], wrapped_response)
        self.assertEqual(events, ["prepare", "service", "preload", "gpu", "decorate"])
        namespace["demo"].launch.assert_not_called()
        self.assertIs(gradio.Button.return_value.click.call_args.args[0], namespace["respond"])
        self.assertIs(gradio.Textbox.return_value.submit.call_args.args[0], namespace["respond"])
        languages = ("fix", "ko", "ja", "en")
        invalid_pairs = [(source, target) for source in languages for target in languages
                         if source == target or "fix" not in (source, target)]
        invalid_pairs += [(None, "fix"), (["fix"], "ko"), ("fix", {"ko": True})]
        for source, target in invalid_pairs:
            with self.subTest(source=source, target=target), self.assertRaises(GradioInputError):
                namespace["respond"]("synthetic input", source, target)
        wrapped_response.assert_not_called()
        service.run.assert_not_called()
        runner_factory.assert_not_called()
        expected = ("synthetic proposal", [], [], "unverified", {})
        wrapped_response.return_value = expected
        self.assertEqual(namespace["respond"]("sinruits", "fix", "ko"), expected)
        wrapped_response.assert_called_once_with("sinruits", "fix", "ko", "generate")

    def test_cloud_missing_dictionary_stops_before_adapter_preload_or_gpu_setup(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        for problem in ("missing_directory", "missing_lexicon", "empty_lexicon", "missing_rules"):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                self.write_cloud_dictionary(directory)
                if problem == "missing_directory":
                    configured_directory = directory / "not-created"
                else:
                    configured_directory = directory
                    if problem == "missing_lexicon":
                        (directory / "lexicon.jsonl").unlink()
                    elif problem == "empty_lexicon":
                        (directory / "lexicon.jsonl").write_text("", encoding="utf-8")
                    else:
                        (directory / "rules.jsonl").unlink()
                prepare, factory, service, gpu, runner = Mock(), Mock(), Mock(), Mock(), Mock()
                factory.return_value = service
                environment = {"SPACE_ID": "fixture", "FIXMARGE_CLOUD": "1",
                               "FIXMARGE_DATA_DIR": str(configured_directory)}
                with patch.dict(os.environ, environment, clear=True), \
                        patch.object(sys, "path", list(sys.path)), \
                        patch.dict(sys.modules, {"gradio": MagicMock(), "spaces": SimpleNamespace(GPU=gpu)}), \
                        patch("fixmarge.cloud.prepare_cloud_adapter", prepare), \
                        patch("fixmarge.demo.DemoService", factory), \
                        patch("fixmarge.infer.ModelRunner", runner), \
                        patch("fixmarge.infer._load_bundle", side_effect=AssertionError("No actual model load")):
                    with self.assertRaisesRegex(RuntimeError, "FIXMARGE_DATA_DIR"):
                        runpy.run_path(str(app_path), run_name="fixmarge_cloud_missing_dictionary")
                prepare.assert_not_called()
                factory.assert_not_called()
                service.preload.assert_not_called()
                runner.assert_not_called()
                gpu.assert_not_called()


if __name__ == "__main__":
    unittest.main()
