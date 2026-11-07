"""Pure backend checks for the demo; no Gradio import or model execution."""
from copy import deepcopy
import ast
import json
import os
import runpy
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from fixmarge.demo import DEFAULT_MODEL, DemoService, present_result, source_highlights, target_languages, validate_translation_pair
from fixmarge.rag import LexiconRAG


def entry(identifier, form, english):
    return {"id": identifier, "form": form, "aliases": [],
            "senses": {"en": [english], "ja": ["fixture"], "ko": []},
            "sources": ["fixture"], "status": "fixture"}


def response(translation, ids=(), uncertainties=()):
    return json.dumps({"tentative_translation": translation, "evidence_ids": list(ids),
                       "uncertainties": list(uncertainties)}, ensure_ascii=False)


class FakeRunner:
    def __init__(self, output):
        self.output = output
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.output


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.rag = LexiconRAG(
            entries=[entry("truth", "sinruits", "truth"), entry("blood", "ChiDd", "blood")],
            rules=[], external_dir=Path(__file__).parent / "fixtures" / "missing_external")

    def service(self, output=None, **options):
        runner = FakeRunner(output)
        runner_factory = Mock(return_value=runner)
        rag_factory = Mock(return_value=self.rag)
        options.setdefault('dictionary_first', False)
        options.setdefault('standard_lookup', Mock(return_value={
            'available': False, 'entries': [], 'matched_entry_count': 0, 'attributions': []}))
        service = DemoService(runner_factory=runner_factory, rag_factory=rag_factory, **options)
        return service, runner, runner_factory, rag_factory

    def test_empty_same_language_and_over_limit_inputs_fail_before_loading(self):
        service, _, runner_factory, rag_factory = self.service()
        for text, source, target in [(None, "en", "fix"), ("", "en", "fix"),
                                     ("  \t", "en", "fix"), ("🙂" * 1001, "en", "fix"),
                                     ("truth", "en", "en")]:
            with self.subTest(text=text, source=source, target=target):
                with self.assertRaises(ValueError):
                    service.run(text, source, target)
        runner_factory.assert_not_called()
        rag_factory.assert_not_called()
        allowed = service.run("🙂" * 1000, "en", "fix")
        self.assertEqual(allowed["source_text"], "🙂" * 1000)
        runner_factory.assert_not_called()
        rag_factory.assert_called_once()

    def test_default_lookup_never_loads_or_runs_a_model(self):
        service, runner, runner_factory, rag_factory = self.service()
        result = service.run("truth mystery", "en", "fix")
        self.assertEqual(result["mode"], "lookup")
        self.assertFalse(result["model_loaded"])
        self.assertFalse(result["adapter_loaded"])
        self.assertFalse(result["training_performed"])
        self.assertEqual(result["adapter_training"]["status"], "not_configured")
        self.assertFalse(result["sentence_verified"])
        self.assertNotIn("diagnostic", result)
        self.assertEqual([span["text"] for span in result["source_evidence"]["unmatched_source_spans"]],
                         ["mystery"])
        self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])
        runner_factory.assert_not_called()
        self.assertEqual(runner.prompts, [])
        rag_factory.assert_called_once_with(data_dir=None, external_dir=None)

    def test_exactly_six_of_all_sixteen_product_directions_are_accepted(self):
        allowed = {('fix', 'ko'), ('fix', 'ja'), ('fix', 'en'),
                   ('ko', 'fix'), ('ja', 'fix'), ('en', 'fix')}
        accepted = set()
        for source in ('fix', 'ko', 'ja', 'en'):
            for target in ('fix', 'ko', 'ja', 'en'):
                with self.subTest(source=source, target=target):
                    rag = Mock(wraps=self.rag)
                    rag_factory = Mock(return_value=rag)
                    runner = FakeRunner(response('sinruits' if target == 'fix' else 'truth'))
                    runner_factory = Mock(return_value=runner)
                    standard = Mock(return_value={'available': False, 'entries': [], 'attributions': []})
                    service = DemoService(runner_factory=runner_factory, rag_factory=rag_factory,
                                          standard_lookup=standard, dictionary_first=False)
                    if (source, target) in allowed:
                        result = service.run('sinruits' if source == 'fix' else 'truth',
                                             source, target, generate=True)
                        accepted.add((source, target))
                        self.assertEqual((result['source_language'], result['target_language']), (source, target))
                        rag_factory.assert_called_once()
                        standard.assert_called_once()
                        runner_factory.assert_called_once()
                        self.assertEqual(len(runner.prompts), 1)
                    else:
                        with self.assertRaisesRegex(ValueError, 'fiXmArge'):
                            service.run('truth', source, target, generate=True)
                        rag_factory.assert_not_called()
                        rag.lookup.assert_not_called()
                        standard.assert_not_called()
                        runner_factory.assert_not_called()
                        self.assertEqual(runner.prompts, [])
        self.assertEqual(accepted, allowed)

    def test_unknown_or_non_string_language_codes_fail_before_any_resource_lookup(self):
        for invalid in (None, '', 'fr', 'FIX', ['fix'], {'code': 'fix'}, 1):
            for source, target in ((invalid, 'fix'), ('fix', invalid)):
                with self.subTest(source=source, target=target):
                    standard = Mock()
                    service, runner, runner_factory, rag_factory = self.service(standard_lookup=standard)
                    with self.assertRaisesRegex(ValueError, r'_language ∉'):
                        service.run('truth', source, target, generate=True)
                    standard.assert_not_called()
                    rag_factory.assert_not_called()
                    runner_factory.assert_not_called()
                    self.assertEqual(runner.prompts, [])

    def test_target_languages_is_the_shared_pure_six_direction_contract(self):
        self.assertEqual(target_languages('fix'), ('ko', 'ja', 'en'))
        for source in ('ko', 'ja', 'en'):
            self.assertEqual(target_languages(source), ('fix',))
        for invalid in (None, '', ['fix'], {'code': 'fix'}, 'fr'):
            with self.subTest(source=invalid), self.assertRaises(ValueError):
                target_languages(invalid)

    def test_ui_defaults_and_dynamic_targets_match_all_sixteen_combinations(self):
        app_path = Path(__file__).resolve().parents[1] / 'app.py'
        module = ast.parse(app_path.read_text(), filename=str(app_path))
        selected = [node for node in module.body
                    if (isinstance(node, ast.FunctionDef) and node.name in ('update_target_languages', 'build_demo'))
                    or (isinstance(node, ast.Assign) and any(isinstance(item, ast.Name) and item.id == 'LANGUAGES'
                                                            for item in node.targets))]
        source, target = MagicMock(name='source'), MagicMock(name='target')
        gradio = MagicMock(name='gradio')
        dropdown_options = {}
        def dropdown(choices, **options):
            dropdown_options[options['label']] = {'choices': choices, **options}
            return source if options['label'] == 'Coword →' else target
        gradio.Dropdown.side_effect = dropdown
        gradio.update.side_effect = lambda **options: options
        respond = Mock()
        namespace = {'gr': gradio, 'target_languages': target_languages, 'respond': respond}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(app_path), 'exec'), namespace)
        namespace['build_demo']()
        self.assertEqual(namespace['LANGUAGES'], [('fiXmArge', 'fix'), ('ko', 'ko'), ('ja', 'ja'), ('en', 'en')])
        self.assertEqual(dropdown_options['Coword →']['value'], 'fix')
        self.assertEqual(dropdown_options['→ MeMe']['value'], 'ko')
        self.assertEqual([code for _, code in dropdown_options['Coword →']['choices']], ['fix', 'ko', 'ja', 'en'])
        self.assertEqual([code for _, code in dropdown_options['→ MeMe']['choices']], ['ko', 'ja', 'en'])
        update = namespace['update_target_languages']
        source.change.assert_called_once_with(update, inputs=[source, target], outputs=target,
                                              api_name=False, queue=False, preprocess=False)
        for source_code in ('fix', 'ko', 'ja', 'en'):
            for current in ('fix', 'ko', 'ja', 'en'):
                with self.subTest(source=source_code, current=current):
                    actual = update(source_code, current)
                    valid = target_languages(source_code)
                    self.assertEqual(tuple(code for _, code in actual['choices']), valid)
                    self.assertEqual(actual['value'], current if current in valid else valid[0])
        for registration in (gradio.Button.return_value.click, gradio.Textbox.return_value.submit):
            self.assertIs(registration.call_args.kwargs['preprocess'], False)
        examples = gradio.Examples.call_args.kwargs['examples']
        self.assertEqual(len(examples), 3)
        self.assertTrue(all(source_code == 'fix' for _, source_code, _ in examples))
        for _, source_code, target_code in examples:
            self.assertIn(target_code, target_languages(source_code))
        respond.assert_not_called()

    def test_cloud_route_validation_happens_before_gpu_allocation(self):
        app_path = Path(__file__).resolve().parents[1] / 'app.py'
        module = ast.parse(app_path.read_text(), filename=str(app_path))
        selected = []
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name in ('_respond_inference', 'respond'):
                selected.append(node)
            elif (isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'cloud_mode'
                  and any(isinstance(item, ast.Assign) and any(isinstance(target, ast.Name)
                          and target.id == '_respond_inference' for target in item.targets) for item in node.body)):
                selected.append(node)
        allocated = Mock(return_value=('proposal', [], [], 'status', {}))
        decorator = Mock(return_value=allocated)
        gpu = Mock(return_value=decorator)
        service = Mock()
        namespace = {'cloud_mode': True, 'spaces': SimpleNamespace(GPU=gpu),
                     'validate_translation_pair': validate_translation_pair,
                     'service': service, 'gr': SimpleNamespace(Error=ValueError)}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(app_path), 'exec'), namespace)
        gpu.assert_called_once_with(duration=60)
        self.assertEqual(decorator.call_args.args[0].__name__, '_respond_inference')
        for source in ('fix', 'ko', 'ja', 'en'):
            for target in ('fix', 'ko', 'ja', 'en'):
                with self.subTest(source=source, target=target):
                    allocated.reset_mock()
                    if target in target_languages(source):
                        namespace['respond']('truth', source, target)
                        allocated.assert_called_once()
                    else:
                        with self.assertRaisesRegex(ValueError, 'fiXmArge'):
                            namespace['respond']('truth', source, target)
                        allocated.assert_not_called()
        for invalid in (None, ['fix'], {'code': 'fix'}, ''):
            allocated.reset_mock()
            with self.assertRaises(ValueError):
                namespace['respond']('truth', invalid, 'fix')
            allocated.assert_not_called()
        service.run.assert_not_called()

    def test_cloud_without_domain_dictionary_fails_before_adapter_or_model_loading(self):
        app_path = Path(__file__).resolve().parents[1] / 'app.py'
        for scenario in ('missing', 'empty', 'whitespace', 'bom_only', 'malformed', 'missing_form', 'missing_rules'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                data = Path(directory)
                if scenario != 'missing':
                    contents = {'empty': '', 'whitespace': ' \n\t\n', 'bom_only': '\ufeff \n',
                                'malformed': '{unfinished', 'missing_form': '{}\n',
                                'missing_rules': json.dumps(entry('truth', 'sinruits', 'truth')) + '\n'}
                    (data / 'lexicon.jsonl').write_text(contents[scenario], encoding='utf-8')
                if scenario not in ('missing', 'missing_rules'):
                    (data / 'rules.jsonl').write_text('')
                prepare, factory, model = Mock(), Mock(), Mock()
                environment = {'SPACE_ID': 'fixture', 'FIXMARGE_CLOUD': '1', 'FIXMARGE_DATA_DIR': str(data)}
                with patch.dict(os.environ, environment, clear=True), \
                        patch.object(sys, 'path', list(sys.path)), \
                        patch('fixmarge.cloud.prepare_cloud_adapter', prepare), \
                        patch('fixmarge.demo.DemoService', factory), \
                        patch('fixmarge.infer._load_bundle', model):
                    with self.assertRaisesRegex(RuntimeError, 'FIXMARGE_DATA_DIR'):
                        runpy.run_path(str(app_path), run_name='missing_dictionary_probe')
                prepare.assert_not_called()
                factory.assert_not_called()
                model.assert_not_called()

    def test_generation_preserves_raw_schema_source_gaps_and_output_audit(self):
        tentative = "sinruits [UNRESOLVED: mystery] Bogus"
        raw = response(tentative, ["truth", "invented"], ["Grammar is hypothetical."])
        service, runner, runner_factory, _ = self.service(raw, device="cpu")
        result = service.run("truth mystery", "en", "fix", generate=True)
        diagnostic = result["diagnostic"]
        self.assertEqual(result["mode"], "generate")
        self.assertTrue(result["model_loaded"])
        self.assertTrue(diagnostic["schema_valid"])
        self.assertEqual(diagnostic["raw_output"], raw)
        self.assertEqual(diagnostic["tentative_translation"], tentative)
        self.assertEqual(diagnostic["unsupported_evidence_ids"], ["invented"])
        self.assertEqual([span["text"] for span in diagnostic["registered_output_spans"]], ["sinruits"])
        self.assertEqual([span["text"] for span in diagnostic["unsupported_output_spans"]], ["Bogus"])
        self.assertEqual([span["text"] for span in diagnostic["explicit_gap_placeholders"]],
                         ["[UNRESOLVED: mystery]"])
        self.assertEqual([span["text"] for span in result["source_evidence"]["unmatched_source_spans"]],
                         ["mystery"])
        self.assertEqual(diagnostic["source_evidence"], result["source_evidence"])
        self.assertFalse(diagnostic["sentence_verified"])
        self.assertFalse(diagnostic["output_source_alignment_verified"])
        runner_factory.assert_called_once()
        self.assertEqual(len(runner.prompts), 1)

    def test_single_runner_and_dictionary_are_reused_with_cached_base_model(self):
        service, runner, runner_factory, rag_factory = self.service(
            response("sinruits", ["truth"]), device="cpu")
        first = service.run("truth", "en", "fix", generate=True)
        second = service.run("truth", "en", "fix", generate=True)
        lookup = service.run("truth", "en", "fix")
        runner_factory.assert_called_once()
        options = runner_factory.call_args.kwargs
        self.assertEqual({key: options[key] for key in
                          ("model_name", "adapter", "revision", "device", "allow_download", "load_in_4bit")},
                         {"model_name": DEFAULT_MODEL, "adapter": None,
                          "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
                          "device": "cpu", "allow_download": False, "load_in_4bit": False})
        self.assertGreater(options["max_new_tokens"], 0)
        rag_factory.assert_called_once_with(data_dir=None, external_dir=None)
        self.assertEqual(len(runner.prompts), 2)
        self.assertTrue(first["model_loaded"])
        self.assertTrue(second["model_loaded"])
        self.assertTrue(lookup["model_loaded"])
        self.assertEqual(lookup["mode"], "lookup")
        self.assertNotIn("diagnostic", lookup)

    def test_optional_nf4_is_forwarded_without_changing_default_or_loading_for_lookup(self):
        for enabled in (False, True):
            with self.subTest(load_in_4bit=enabled):
                service, _, runner_factory, _ = self.service(
                    response("真実"), load_in_4bit=enabled, device="cuda")
                lookup = service.run("sinruits", "fix", "ja")
                self.assertEqual(lookup["runtime"], {"device": "cuda", "load_in_4bit": enabled})
                runner_factory.assert_not_called()
                result = service.run("sinruits", "fix", "ja", generate=True)
                self.assertEqual(runner_factory.call_args.kwargs["load_in_4bit"], enabled)
                self.assertEqual(result["runtime"], lookup["runtime"])
                self.assertIsNone(runner_factory.call_args.kwargs["adapter"])
                self.assertFalse(result["training_performed"])
                self.assertFalse(result["sentence_verified"])

    def test_app_nf4_environment_opt_in_without_importing_gradio_or_loading_model(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        module = ast.parse(app_path.read_text(encoding="utf-8"), filename=str(app_path))
        assignment = next(node for node in module.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "service"
                                  for target in node.targets))
        code = compile(ast.Module(body=[assignment], type_ignores=[]), str(app_path), "exec")
        for value, expected in ((None, False), ("0", False), ("true", False), ("1", True)):
            with self.subTest(environment_value=value):
                environment = {} if value is None else {"FIXMARGE_LOAD_IN_4BIT": value}
                factory = Mock()
                namespace = {"os": SimpleNamespace(environ=environment),
                             "DemoService": factory, "allow_download": False,
                             "cloud_mode": False, "adapter_path": None, "service_options": {}}
                exec(code, namespace)
                factory.assert_called_once()
                self.assertEqual(factory.call_args.kwargs["load_in_4bit"], expected)
                self.assertIsNone(factory.call_args.kwargs["adapter"])

    def test_highlight_plain_tuples_preserve_html_characters_and_source_offsets(self):
        service, _, _, _ = self.service()
        text = "<b>sinruits</b> & 🙂 mystery"
        result = service.run(text, "fix", "en")
        evidence = result["source_evidence"]
        before = deepcopy(evidence)
        highlights = source_highlights(evidence)
        self.assertEqual("".join(piece for piece, _ in highlights), text)
        self.assertTrue(any(piece == "sinruits" for piece, _ in highlights))
        self.assertNotIn("&amp;", "".join(piece for piece, _ in highlights))
        self.assertEqual(evidence, before)
        for segment in evidence["lexical_segments"]:
            self.assertEqual(text[segment["start"]:segment["end"]], segment["text"])
        for span in evidence["unmatched_source_spans"]:
            self.assertEqual(text[span["start"]:span["end"]], span["text"])

    def test_presentation_returns_five_fields_with_model_proposal_and_separate_evidence(self):
        service, _, _, _ = self.service(response("sinruits [UNRESOLVED: mystery]", ["truth"]))
        result = service.run("truth mystery", "en", "fix", generate=True)
        proposal, highlights, rows, status, detail = present_result(result)
        self.assertEqual(proposal, "sinruits [UNRESOLVED: mystery]")
        self.assertEqual("".join(piece for piece, _ in highlights), result["source_text"])
        self.assertTrue(all(len(row) == 4 for row in rows))
        self.assertEqual(rows[0][:2], ["truth", "sinruits"])
        self.assertEqual(rows[0][3], "fixture")
        self.assertEqual(rows[1][0], "mystery")
        self.assertNotEqual(rows[0][2], rows[1][2])
        self.assertIsInstance(status, str)
        self.assertTrue(status)
        self.assertIs(detail, result)

    def test_invalid_or_self_certifying_model_output_cannot_change_trusted_metadata(self):
        forged = {
            "tentative_translation": "MODEL_CLAIM",
            "evidence_ids": ["invented"],
            "uncertainties": [],
            "sentence_verified": True,
            "training_performed": True,
            "source_evidence": {"dictionary_assessed": False},
        }
        for raw in ("{unfinished", json.dumps(forged)):
            with self.subTest(raw=raw):
                service, _, _, _ = self.service(raw)
                result = service.run("truth mystery", "en", "fix", generate=True)
                self.assertFalse(result["sentence_verified"])
                self.assertFalse(result["training_performed"])
                self.assertTrue(result["source_evidence"]["dictionary_assessed"])
                self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])
                self.assertEqual([span["text"] for span in result["source_evidence"]["unmatched_source_spans"]],
                                 ["mystery"])
                self.assertFalse(result["diagnostic"]["schema_valid"])
                self.assertFalse(result["diagnostic"]["sentence_verified"])
                self.assertEqual(result["diagnostic"]["raw_output"], raw)
                presented = present_result(result)
                self.assertEqual(len(presented), 5)
                self.assertNotEqual(presented[0], "MODEL_CLAIM")
                self.assertEqual(presented[4]["diagnostic"]["raw_output"], raw)

    def test_missing_dictionary_becomes_a_human_readable_error_without_model_loading(self):
        runner_factory = Mock()
        service = DemoService(
            runner_factory=runner_factory,
            rag_factory=Mock(side_effect=FileNotFoundError("/missing/lexicon.jsonl")))
        with self.assertRaises(ValueError) as error:
            service.run("truth", "en", "fix")
        self.assertIn("fiXmArge", str(error.exception))
        self.assertNotIn("/missing/lexicon.jsonl", str(error.exception))
        runner_factory.assert_not_called()

    def test_adapter_without_config_is_rejected_before_any_load(self):
        with tempfile.TemporaryDirectory() as directory:
            runner_factory, rag_factory = Mock(), Mock()
            for adapter in (Path(directory), Path(directory) / "missing"):
                with self.subTest(adapter=adapter):
                    with self.assertRaisesRegex(ValueError, "adapter_config.json"):
                        DemoService(adapter=adapter, runner_factory=runner_factory, rag_factory=rag_factory)
            runner_factory.assert_not_called()
            rag_factory.assert_not_called()


    @staticmethod
    def training_manifest(steps=17):
        return {
            "training_status": "completed", "optimizer_steps": steps, "train_rows": 80,
            "configuration": {"data_scope": "commercially_reusable_english_japanese_wordnet_lexical_instruction_tuning",
                              "secret_configuration": "DO_NOT_COPY"},
            "data_rights": {"sources": ["oewn:2025", "wnja:1.1"], "notes": "DO_NOT_COPY"},
            "notes": "DO_NOT_COPY", "sentence_verified": True, "training_performed": True,
            "model_self_certificate": "DO_NOT_COPY",
        }

    def test_completed_adapter_metadata_is_allowlisted_and_separate_from_this_request(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory)
            config = adapter / "adapter_config.json"
            config.write_text("{}", encoding="utf-8")
            manifest = adapter / "training_manifest.json"
            manifest.write_text(json.dumps(self.training_manifest()), encoding="utf-8")
            original_files = {path.name: path.read_bytes() for path in (config, manifest)}
            service, _, runner_factory, _ = self.service(response("真実"), adapter=adapter)
            result = service.run("sinruits", "fix", "ja", generate=True)
            self.assertEqual(result["adapter_training"], {
                "status": "completed", "optimizer_steps": 17, "train_rows": 80,
                "data_scope": "commercially_reusable_english_japanese_wordnet_lexical_instruction_tuning",
                "sources": ["oewn:2025", "wnja:1.1"],
                "selected_checkpoint": None, "selected_optimizer_step": None,
                "initial_adapter_source_optimizer_steps": None,
            })
            self.assertTrue(result["adapter_loaded"])
            self.assertFalse(result["training_performed"])
            self.assertFalse(result["sentence_verified"])
            self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])
            self.assertNotIn("DO_NOT_COPY", json.dumps(result["adapter_training"]))
            self.assertEqual(runner_factory.call_args.kwargs["adapter"], str(adapter.resolve()))
            status = present_result(result)[3]
            fields = json.JSONDecoder().raw_decode(status)[0]
            self.assertEqual(fields["adapter_training"]["data_scope"], result["adapter_training"]["data_scope"])
            self.assertEqual(fields["adapter_training"]["optimizer_steps"], 17)
            self.assertFalse(fields["sentence_verified"])
            self.assertFalse(fields["sentence_grammar_verified"])
            self.assertFalse(fields["output_source_alignment_verified"])
            self.assertNotIn("DO_NOT_COPY", status)
            self.assertEqual(original_files, {path.name: path.read_bytes() for path in (config, manifest)})

    def test_selected_checkpoint_is_a_bounded_basename_and_distinct_from_executed_steps(self):
        for selected in ("/local/artifacts/adapter/checkpoint-96", "C:" + chr(92) + "adapter" + chr(92) + "checkpoint-96"):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as directory:
                adapter = Path(directory)
                (adapter / "adapter_config.json").write_text("{}")
                manifest = self.training_manifest(steps=192)
                manifest.update(selected_checkpoint=selected, selected_optimizer_step=192,
                                initial_adapter_source_optimizer_steps=128)
                (adapter / "training_manifest.json").write_text(json.dumps(manifest))
                service, _, runner_factory, _ = self.service(adapter=adapter)
                result = service.run("sinruits", "fix", "ja")
                training = result["adapter_training"]
                self.assertEqual(training["optimizer_steps"], 192)
                self.assertEqual(training["selected_checkpoint"], "checkpoint-96")
                self.assertEqual(training["selected_optimizer_step"], 96)
                self.assertEqual(training["initial_adapter_source_optimizer_steps"], 128)
                status = present_result(result)[3]
                fields = json.JSONDecoder().raw_decode(status)[0]
                self.assertEqual(fields["adapter_selection"], "LoRA · checkpoint-96")
                self.assertEqual(fields["initial_source_steps"], 128)
                self.assertEqual(fields["adapter_training"]["selected_optimizer_step"], 96)
                self.assertNotIn(selected, status)
                runner_factory.assert_not_called()

    def test_invalid_checkpoint_fields_are_ignored_without_rejecting_valid_old_metadata(self):
        invalid = (None, True, 96, [], "checkpoint-96-extra", "checkpoint-x", "checkpoint-96/",
                   "/local/\n/checkpoint-96", "/local/" + chr(127) + "/checkpoint-96",
                   "a" * 1024 + "/checkpoint-96", "checkpoint-" + "9" * 13)
        for selected in invalid:
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as directory:
                adapter = Path(directory)
                (adapter / "adapter_config.json").write_text("{}")
                manifest = self.training_manifest(steps=192)
                manifest.update(selected_checkpoint=selected, selected_optimizer_step=96)
                (adapter / "training_manifest.json").write_text(json.dumps(manifest))
                service, _, _, _ = self.service(adapter=adapter)
                result = service.run("sinruits", "fix", "ja")
                self.assertEqual(result["adapter_training"]["status"], "completed")
                self.assertIsNone(result["adapter_training"]["selected_checkpoint"])
                self.assertIsNone(result["adapter_training"]["selected_optimizer_step"])
                fields = json.JSONDecoder().raw_decode(present_result(result)[3])[0]
                self.assertNotIn("adapter_selection", fields)
                self.assertNotIn("initial_source_steps", fields)

    def test_initial_source_steps_are_optional_strict_nonnegative_integers(self):
        for value in (None, False, True, -1, "128", 128.0, [], 0, 128):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                adapter = Path(directory)
                (adapter / "adapter_config.json").write_text("{}")
                manifest = self.training_manifest()
                manifest["initial_adapter_source_optimizer_steps"] = value
                (adapter / "training_manifest.json").write_text(json.dumps(manifest))
                service, _, _, _ = self.service(adapter=adapter)
                result = service.run("sinruits", "fix", "ja")
                expected = value if type(value) is int and value >= 0 else None
                self.assertEqual(result["adapter_training"]["initial_adapter_source_optimizer_steps"], expected)
                self.assertEqual(result["adapter_training"]["status"], "completed")
                fields = json.JSONDecoder().raw_decode(present_result(result)[3])[0]
                if expected is None:
                    self.assertNotIn("initial_source_steps", fields)
                else:
                    self.assertEqual(fields["initial_source_steps"], expected)

    def test_missing_malformed_or_incomplete_manifest_does_not_block_inference(self):
        incomplete = self.training_manifest()
        incomplete.pop("optimizer_steps")
        invalid_count = self.training_manifest()
        invalid_count["optimizer_steps"] = True
        fake_status = self.training_manifest()
        fake_status["training_status"] = "FI_X_SENTENCE_CERTIFIED"
        for content in (None, "{unfinished", "[]", "{}", "\xff",
                        json.dumps(incomplete), json.dumps(invalid_count), json.dumps(fake_status)):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                adapter = Path(directory)
                (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
                if content is not None:
                    (adapter / "training_manifest.json").write_bytes(content.encode("latin-1"))
                service, _, runner_factory, _ = self.service(response("真実"), adapter=adapter)
                result = service.run("sinruits", "fix", "ja", generate=True)
                self.assertEqual(result["adapter_training"]["status"], "unknown")
                self.assertFalse(result["training_performed"])
                self.assertFalse(result["sentence_verified"])
                self.assertEqual(result["diagnostic"]["tentative_translation"], "真実")
                self.assertEqual(json.JSONDecoder().raw_decode(present_result(result)[3])[0]["adapter_training"]["status"], "unknown")
                runner_factory.assert_called_once()

    def test_manifest_directory_or_oversized_json_does_not_block_lookup(self):
        for oversized in (False, True):
            with self.subTest(oversized=oversized), tempfile.TemporaryDirectory() as directory:
                adapter = Path(directory)
                (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
                manifest = adapter / "training_manifest.json"
                if oversized:
                    manifest.write_text(json.dumps(self.training_manifest()) + " " * (1024 * 1024), encoding="utf-8")
                else:
                    manifest.mkdir()
                service, _, runner_factory, _ = self.service(adapter=adapter)
                result = service.run("sinruits", "fix", "ja")
                self.assertEqual(result["adapter_training"]["status"], "unknown")
                self.assertFalse(result["adapter_loaded"])
                self.assertFalse(json.JSONDecoder().raw_decode(present_result(result)[3])[0]["adapter_loaded"])
                runner_factory.assert_not_called()

    def test_adapter_status_refreshes_without_reloading_or_executing_training(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory)
            (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
            manifest = adapter / "training_manifest.json"
            service, runner, runner_factory, _ = self.service(response("真実"), adapter=adapter)
            before = service.run("sinruits", "fix", "ja", generate=True)
            self.assertEqual(before["adapter_training"]["status"], "unknown")
            manifest.write_text(json.dumps(self.training_manifest(steps=29)), encoding="utf-8")
            after = service.run("sinruits", "fix", "ja")
            self.assertEqual(after["adapter_training"]["optimizer_steps"], 29)
            self.assertEqual(json.JSONDecoder().raw_decode(present_result(after)[3])[0]["adapter_training"]["optimizer_steps"], 29)
            self.assertFalse(after["training_performed"])
            self.assertFalse(after["sentence_verified"])
            runner_factory.assert_called_once()
            self.assertEqual(len(runner.prompts), 1)

    def test_model_cannot_self_certify_adapter_training_without_a_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory)
            (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
            forged = json.loads(response("真実"))
            forged["adapter_training"] = self.training_manifest(steps=999)
            forged["training_performed"] = True
            service, _, _, _ = self.service(json.dumps(forged), adapter=adapter)
            result = service.run("sinruits", "fix", "ja", generate=True)
            self.assertEqual(result["adapter_training"]["status"], "unknown")
            self.assertIsNone(result["adapter_training"]["optimizer_steps"])
            self.assertFalse(result["training_performed"])
            self.assertFalse(result["sentence_verified"])
            self.assertIsNone(json.JSONDecoder().raw_decode(present_result(result)[3])[0]["adapter_training"]["optimizer_steps"])

    @staticmethod
    def standard_context():
        return {
            "available": True, "matched_entry_count": 2,
            "entries": [
                {"entry": {"id": "oewn:test-truth", "language": "en", "lemma": "truth",
                           "reading": "truːθ", "glosses": ["conformity to fact"],
                           "synonyms": ["verity"], "pos": "n", "source": "oewn:2025",
                           "license": "CC-BY-4.0 + WordNet"},
                 "matches": [{"query": "truth", "reasons": ["input"]}]},
                {"entry": {"id": "wnja:test-truth", "language": "ja", "lemma": "真実",
                           "reading": None, "glosses": ["事実に一致すること"],
                           "synonyms": [], "pos": "n", "source": "wnja:1.1",
                           "license": "Japanese-WordNet + WordNet"},
                 "matches": [{"query": "真実", "reasons": ["input"]}]},
            ],
            "attributions": [
                {"source": "oewn:2025", "name": "Open English WordNet", "version": "2025",
                 "license": "CC-BY-4.0 + WordNet", "credit": "Open English WordNet Team; Princeton University WordNet"},
                {"source": "wnja:1.1", "name": "Japanese WordNet", "version": "1.1",
                 "license": "Japanese-WordNet + WordNet", "credit": "Japanese WordNet; Princeton University WordNet"},
            ],
        }

    def test_natural_to_fix_receives_standard_context_with_domain_lookup(self):
        context = self.standard_context()
        before = deepcopy(context)
        standard = Mock(return_value=context)
        raw = response("sinruits", ["oewn:test-truth", "wnja:test-truth", "not-supplied"])
        service, runner, _, rag_factory = self.service(raw, standard_lookup=standard,
                                                      external_dir="/operator/external")
        result = service.run("truth", "en", "fix", generate=True)
        standard.assert_called_once()
        arguments = standard.call_args
        self.assertEqual(arguments.args, ("truth",))
        self.assertEqual(arguments.kwargs["external_dir"], "/operator/external")
        self.assertEqual(arguments.kwargs["languages"], ("en", "ja"))
        self.assertEqual(list(arguments.kwargs["extra_queries"]), [])
        self.assertEqual(result["standard_dictionary"], before)
        self.assertEqual(result["source_evidence"]["standard_dictionary"], before)
        self.assertTrue(result["source_evidence"]["dictionary_assessed"])
        self.assertEqual(result["source_evidence"]["unmatched_source_spans"], [])
        payload = json.loads(runner.prompts[0][1]["content"])
        standard_prompt = json.dumps(payload["evidence"]["standard_dictionary"], ensure_ascii=False)
        for value in ("oewn:test-truth", "wnja:test-truth", "conformity to fact",
                      "事実に一致すること", "CC-BY-4.0 + WordNet", "Japanese-WordNet + WordNet"):
            self.assertIn(value, standard_prompt)
        self.assertEqual(result["diagnostic"]["model_domain_evidence_ids"], [])
        self.assertEqual(result["diagnostic"]["model_standard_evidence_ids"],
                         ["oewn:test-truth", "wnja:test-truth"])
        self.assertEqual(result["diagnostic"]["unsupported_evidence_ids"], ["not-supplied"])
        self.assertFalse(result["diagnostic"]["sentence_verified"])
        self.assertEqual(context, before)
        rag_factory.assert_called_once()

    def test_fix_pair_keeps_domain_and_standard_evidence_separate_in_prompt_and_result(self):
        context = self.standard_context()
        standard = Mock(return_value=context)
        service, runner, _, _ = self.service(
            response("truth", ["truth", "oewn:test-truth", "wnja:test-truth", "invented"]),
            standard_lookup=standard)
        result = service.run("sinruits", "fix", "en", generate=True)
        queries = list(standard.call_args.kwargs["extra_queries"])
        self.assertIn("truth", [query for query, _ in queries])
        self.assertEqual(result["source_evidence"]["lexical_segments"][0]["entry_ids"], ["truth"])
        self.assertEqual(result["source_evidence"]["standard_dictionary"], context)
        payload = json.loads(runner.prompts[0][1]["content"])
        self.assertEqual(payload["evidence"]["lexical_segments"][0]["entry_ids"], ["truth"])
        self.assertIn("oewn:test-truth", json.dumps(payload["evidence"]["standard_dictionary"]))
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["model_domain_evidence_ids"], ["truth"])
        self.assertEqual(diagnostic["model_standard_evidence_ids"],
                         ["oewn:test-truth", "wnja:test-truth"])
        self.assertEqual(diagnostic["unsupported_evidence_ids"], ["invented"])
        self.assertFalse(diagnostic["output_source_alignment_verified"])
        self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])
        presentation = present_result(result)
        self.assertEqual(presentation[2][0][:2], ["sinruits", "truth"])
        self.assertTrue(any("oewn:2025" in row[3] for row in presentation[2]))
        self.assertTrue(any("wnja:1.1" in row[3] for row in presentation[2]))
        self.assertEqual(json.JSONDecoder().raw_decode(presentation[3])[0]["standard_dictionary"]["languages"], ["en", "ja"])

    def test_missing_standard_index_remains_explicit_and_does_not_load_model(self):
        context = {"available": False, "entries": [], "matched_entry_count": 0, "attributions": []}
        standard = Mock(return_value=context)
        service, _, runner_factory, rag_factory = self.service(standard_lookup=standard)
        result = service.run("truth", "en", "fix")
        self.assertFalse(result["standard_dictionary"]["available"])
        self.assertEqual(result["source_evidence"]["standard_dictionary"]["entries"], [])
        self.assertTrue(result["source_evidence"]["dictionary_assessed"])
        self.assertFalse(result["sentence_verified"])
        standard.assert_called_once()
        runner_factory.assert_not_called()
        rag_factory.assert_called_once()



    def test_standard_dictionary_follows_custom_data_root_unless_explicitly_overridden(self):
        data_dir = Path("/operator/private/processed")
        for external_dir, expected in ((None, data_dir.parent / "external"),
                                       (Path("/operator/other-wordnet"), Path("/operator/other-wordnet"))):
            with self.subTest(external_dir=external_dir):
                standard = Mock(return_value={"available": False, "entries": [],
                                               "matched_entry_count": 0, "attributions": []})
                service, _, runner_factory, rag_factory = self.service(
                    data_dir=data_dir, external_dir=external_dir, standard_lookup=standard)
                service.run("truth", "en", "fix")
                standard.assert_called_once()
                self.assertEqual(standard.call_args.kwargs["external_dir"], expected)
                runner_factory.assert_not_called()
                rag_factory.assert_called_once()

    def test_presentation_exposes_unmatched_output_and_malformed_gap_without_hiding_raw(self):
        tentative = "sinruits Bogus [UNRESOLVED: mystery"
        raw = response(tentative, ["truth"])
        service, _, _, _ = self.service(raw)
        result = service.run("truth mystery", "en", "fix", generate=True)
        diagnostic = result["diagnostic"]
        self.assertTrue(diagnostic["registered_output_spans"])
        self.assertIn("Bogus", [span["text"] for span in diagnostic["unsupported_output_spans"]])
        self.assertEqual([span["text"] for span in diagnostic["malformed_gap_placeholders"]],
                         ["[UNRESOLVED: mystery"])
        proposal, _, _, status, detail = present_result(result)
        self.assertEqual(proposal, tentative)
        self.assertIn("Bogus", status)
        self.assertIn("[UNRESOLVED: mystery", status)
        fields = json.JSONDecoder().raw_decode(status)[0]
        self.assertIn("Bogus", fields["unsupported_output_spans"])
        self.assertFalse(fields["output_source_alignment_verified"])
        self.assertEqual(detail["diagnostic"]["raw_output"], raw)

    def test_entirely_unmatched_fix_output_is_not_presented_as_a_translation(self):
        raw = response("真実", ["truth"])
        service, _, _, _ = self.service(raw)
        result = service.run("truth", "en", "fix", generate=True)
        diagnostic = result["diagnostic"]
        self.assertTrue(diagnostic["schema_valid"])
        self.assertEqual(diagnostic["registered_output_spans"], [])
        self.assertEqual([span["text"] for span in diagnostic["unsupported_output_spans"]], ["真実"])
        proposal, _, _, status, detail = present_result(result)
        self.assertEqual(proposal, "⚠ fiXmArge · MeMe · ∅ · {}")
        self.assertNotEqual(proposal, "真実")
        self.assertIn("真実", status)
        self.assertEqual(detail["diagnostic"]["tentative_translation"], "真実")
        self.assertEqual(detail["diagnostic"]["raw_output"], raw)



if __name__ == "__main__":
    unittest.main()
