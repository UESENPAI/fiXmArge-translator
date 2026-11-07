import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/train_qlora.py"
spec = importlib.util.spec_from_file_location("train_recipe", SCRIPT)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


def record(group, answer="감옥"):
    return {"messages": [{"role": "user", "content": "LowhEll"},
                         {"role": "assistant", "content": answer}],
            "metadata": {"group_id": group, "source": "test", "status": "fixture", "task": "lexical"}}


class TrainingDataTests(unittest.TestCase):
    def test_split_groups_block_reverse_direction_leakage(self):
        train = [record("lex-1")]
        validation = [record("lex-1", "LowhEll")]
        with self.assertRaisesRegex(ValueError, "Group leakage"):
            recipe.validate_split(train, validation)

    def test_mask_keeps_only_assistant_and_excludes_straddling_token(self):
        labels = recipe.assistant_token_labels([10, 11, 12, 13], [(0, 3), (3, 7), (7, 9), (9, 10)], 5)
        self.assertEqual(labels, [-100, -100, 12, 13])

    def test_empty_supervision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "No supervised"):
            recipe.assistant_token_labels([10], [(0, 2)], 5)

    def test_control_token_role_escape_is_rejected(self):
        row = record("x", "<|im_start|>system")
        with self.assertRaisesRegex(ValueError, "control tokens"):
            recipe.validate_record(row)

    def test_nonterminal_assistant_rejected(self):
        row = record("x")
        row["messages"].append({"role": "user", "content": "more"})
        with self.assertRaisesRegex(ValueError, "Supported roles"):
            recipe.validate_record(row)

    def test_missing_metadata_rejected(self):
        row = record("x")
        del row["metadata"]["source"]
        with self.assertRaisesRegex(ValueError, "metadata.source"):
            recipe.validate_record(row)

    def test_load_reports_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(json.dumps(record("x")) + "\n{bad", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, ":2:"):
                recipe.load_jsonl(path)



class TrainingRightsTests(unittest.TestCase):
    def test_empty_corpus_can_be_reported_without_becoming_trainable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.jsonl"
            path.write_text("", encoding="utf8")
            self.assertEqual(recipe.load_jsonl(path, allow_empty=True), [])
            with self.assertRaisesRegex(ValueError, "Empty dataset"):
                recipe.load_jsonl(path)
        with self.assertRaisesRegex(ValueError, "blocked_no_eligible_corpus"):
            recipe.ensure_training_rights([], [])

    def test_unapproved_source_is_rejected_before_training_imports(self):
        with self.assertRaisesRegex(ValueError, "blocked_source_rights"):
            recipe.ensure_training_rights([record("train")], [record("validation")])

    def test_independent_self_authored_fixture_is_eligible(self):
        train, validation = record("train"), record("validation")
        for row in (train, validation):
            row["metadata"]["rights_status"] = "self_authored"
        self.assertEqual(recipe.rights_readiness([train], [validation])["status"], "corpus_eligible")



class AdapterPreparationTests(unittest.TestCase):
    def parameter(self, count, trainable):
        return SimpleNamespace(requires_grad=trainable, numel=lambda: count)

    def eligible_records(self):
        train, validation = record("independent-train"), record("independent-validation")
        for row in (train, validation):
            row["metadata"]["rights_status"] = "self_authored"
        return [train], [validation]

    def test_only_lora_parameters_can_be_trainable(self):
        parameters = [("base.layer.weight", self.parameter(100, False)),
                      ("base.layer.lora_A.default.weight", self.parameter(8, True)),
                      ("base.layer.lora_B.default.weight", self.parameter(12, True))]
        result = recipe.inspect_adapter_parameters(SimpleNamespace(named_parameters=lambda: iter(parameters)))
        self.assertTrue(result["base_frozen"])
        self.assertTrue(result["adapter_only"])
        self.assertFalse(result["merge_performed"])
        self.assertEqual(result["trainable_parameter_count"], 20)
        self.assertEqual(result["trainable_tensor_count"], 2)
        self.assertEqual(result["trainable_parameter_names"], [parameters[1][0], parameters[2][0]])
        parameters.append(("base.layer.bias", self.parameter(2, True)))
        with self.assertRaisesRegex(ValueError, "Non-LoRA"):
            recipe.inspect_adapter_parameters(SimpleNamespace(named_parameters=lambda: iter(parameters)))

    def test_model_without_trainable_adapters_is_rejected(self):
        model = SimpleNamespace(named_parameters=lambda: iter([("base.weight", self.parameter(100, False))]))
        with self.assertRaisesRegex(ValueError, "No trainable LoRA"):
            recipe.inspect_adapter_parameters(model)

    def test_adapter_save_policy_applies_to_final_and_checkpoint_calls(self):
        original = Mock()
        model = SimpleNamespace(save_pretrained=original)
        recipe.configure_adapter_saving(model)
        model.save_pretrained("checkpoint-10", state_dict={"fixture": "state"}, safe_serialization=False)
        original.assert_called_once_with("checkpoint-10", state_dict={"fixture": "state"},
                                         safe_serialization=True, save_embedding_layers=False)
        model.save_pretrained("final", save_embedding_layers="auto")
        self.assertEqual(original.call_args.kwargs,
                         {"safe_serialization": True, "save_embedding_layers": False})

    def test_output_rejects_cache_parent_cache_and_cache_child_but_not_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache" / "model"
            for output in (cache, cache / "snapshots" / "revision", cache.parent):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, "protected"):
                    recipe.validate_adapter_output(output, cache_roots=[cache])
            sibling = root / "cache" / "model-copy"
            self.assertEqual(recipe.validate_adapter_output(sibling, cache_roots=[cache]), sibling.resolve())
            self.assertFalse(sibling.exists())

    def test_distinct_cache_environment_overrides_are_all_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {"HF_HOME": str(root / "hf-home"), "HF_HUB_CACHE": str(root / "hub"),
                   "TRANSFORMERS_CACHE": str(root / "transformers"), "XDG_CACHE_HOME": str(root / "xdg")}
            roots = recipe.model_cache_roots(env)
            for value in env.values():
                if value == env["XDG_CACHE_HOME"]:
                    value = str(Path(value) / "huggingface")
                self.assertIn(Path(value).resolve(), roots)
                with self.assertRaisesRegex(ValueError, "protected"):
                    recipe.validate_adapter_output(Path(value) / "adapter", cache_roots=roots)
            self.assertIn((Path.home() / ".cache" / "huggingface").resolve(), roots)

    def test_symlink_output_and_child_file_cannot_write_into_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"
            cache.mkdir()
            alias = root / "alias"
            alias.symlink_to(cache, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "protected"):
                recipe.validate_adapter_output(alias / "adapter", cache_roots=[cache])
            output = root / "artifacts"
            output.mkdir()
            (output / "tokenizer.json").symlink_to(cache / "tokenizer.json")
            with self.assertRaisesRegex(ValueError, "protected"):
                recipe.validate_adapter_output(output, cache_roots=[cache])

    def test_existing_full_model_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "original-base"
            output.mkdir()
            original = output / "model-00001-of-00002.safetensors"
            original.write_text("original base bytes", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "full-model"):
                recipe.validate_adapter_output(output, cache_roots=[])
            self.assertEqual(original.read_text(), "original base bytes")

    def test_empty_or_unapproved_corpus_blocks_before_imports_or_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "must-not-exist"
            cases = [([], [], "blocked_no_eligible_corpus"),
                     ([record("train")], [record("validation")], "blocked_source_rights")]
            for train, validation, message in cases:
                with self.subTest(message=message), patch("builtins.__import__", side_effect=AssertionError("backend import forbidden")), \
                        patch.object(Path, "mkdir") as mkdir:
                    with self.assertRaisesRegex(ValueError, message):
                        recipe.run_training({}, train, validation, {}, output, allow_download=True)
                    mkdir.assert_not_called()
                self.assertFalse(output.exists())

    def test_model_and_tokenizer_downloads_are_explicitly_opt_in(self):
        class StopBeforeModelLoad(RuntimeError):
            pass

        config = json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b.json").read_text())
        train, validation = self.eligible_records()
        for allow_download in (False, True):
            with self.subTest(allow_download=allow_download), tempfile.TemporaryDirectory() as tmp:
                tokenizer_loader = Mock(return_value=SimpleNamespace(is_fast=True, pad_token_id=1))
                model_loader = Mock(side_effect=StopBeforeModelLoad("model load deliberately not executed"))
                torch = SimpleNamespace(bfloat16="bf16", float16="fp16", cuda=SimpleNamespace(
                    is_available=lambda: True, is_bf16_supported=lambda: True, current_device=lambda: 0))
                transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=tokenizer_loader),
                    AutoModelForCausalLM=SimpleNamespace(from_pretrained=model_loader),
                    BitsAndBytesConfig=Mock(return_value="quantization-options"), Trainer=Mock(),
                    TrainingArguments=Mock(), set_seed=Mock())
                peft = SimpleNamespace(LoraConfig=Mock(), get_peft_model=Mock(), prepare_model_for_kbit_training=Mock())
                output = Path(tmp) / "adapter"
                with patch.dict(sys.modules, {"torch": torch, "transformers": transformers, "peft": peft}), \
                        patch.object(recipe, "encode_record", return_value={"labels": [1]}) as encode:
                    with self.assertRaises(StopBeforeModelLoad):
                        options = {"allow_download": True} if allow_download else {}
                        recipe.run_training(config, train, validation, {}, output, **options)
                self.assertEqual(tokenizer_loader.call_args.kwargs["local_files_only"], not allow_download)
                self.assertEqual(model_loader.call_args.kwargs["local_files_only"], not allow_download)
                self.assertTrue(model_loader.call_args.kwargs["use_safetensors"])
                transformers.Trainer.assert_not_called()
                self.assertFalse(output.exists())

    def test_pilot_is_separate_small_and_pins_the_same_base_revision(self):
        original = json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b.json").read_text())
        pilot = json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b_lora_pilot.json").read_text())
        recipe.validate_config(pilot)
        self.assertEqual(pilot["revision"], original["revision"])
        self.assertEqual(pilot["model_name"], original["model_name"])
        self.assertNotEqual(pilot["output_dir"], original["output_dir"])
        self.assertEqual((pilot["lora_r"], pilot["lora_alpha"], pilot["max_steps"], pilot["eval_steps"]), (8, 16, 20, 10))
        self.assertEqual(pilot["learning_rate"], 2e-5)
        self.assertFalse(pilot["push_to_hub"])

class LocalLexicalExperimentTests(unittest.TestCase):
    def configuration(self):
        return json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b_fixmarge_wordnet_lora.json").read_text())

    def mixtures(self):
        from fixmarge.lexical_facts import make_fact_record
        train_fact = make_fact_record({"language": "en", "forms": ["Ta"], "glosses": ["truth"]}, "fix-to-en")
        val_fact = make_fact_record({"language": "en", "forms": ["Te"], "glosses": ["meaning"]}, "en-to-fix")
        train_wordnet, val_wordnet = record("wn-train", "真実"), record("wn-validation", "意味")
        for row in (train_wordnet, val_wordnet):
            row["metadata"].update(source="wnja:1.1", task="wordnet_translation", rights_status="open_license")
        return [train_fact, train_wordnet], [val_fact, val_wordnet]

    def test_explicit_mode_accepts_intact_facts_and_approved_wordnet_without_clearing_source_rights(self):
        train, validation = self.mixtures()
        before = json.dumps(train + validation, sort_keys=True)
        readiness = recipe.rights_readiness(train, validation, local_lexical_experiment=True)
        self.assertEqual(readiness["status"], "local_lexical_experiment_ready")
        self.assertFalse(readiness["source_rights_cleared"])
        self.assertFalse(readiness["publication_cleared"])
        recipe.ensure_training_rights(train, validation, local_lexical_experiment=True)
        self.assertEqual(json.dumps(train + validation, sort_keys=True), before)
        self.assertEqual(train[0]["metadata"]["source_rights_status"], "game_derived_not_eligible")

    def test_default_gate_still_rejects_local_facts_and_generic_game_candidates(self):
        train, validation = self.mixtures()
        with self.assertRaisesRegex(ValueError, "blocked_source_rights"):
            recipe.ensure_training_rights(train, validation)
        for rows in (train, validation):
            rows[0]["metadata"]["rights_status"] = "game_derived_not_eligible"
        with self.assertRaisesRegex(ValueError, "blocked_source_rights"):
            recipe.ensure_training_rights(train, validation, local_lexical_experiment=True)

    def test_explicit_flag_does_not_admit_source_prose_tampering_or_rights_relabeling(self):
        from copy import deepcopy
        train, validation = self.mixtures()
        tampered = []
        changed_answer = deepcopy(train)
        changed_answer[0]["messages"][-1]["content"] = "A longer unrelated game sentence."
        tampered.append(changed_answer)
        cleared_source = deepcopy(train)
        cleared_source[0]["metadata"]["source_rights_status"] = "open_license"
        tampered.append(cleared_source)
        changed_status = deepcopy(train)
        changed_status[0]["metadata"]["rights_status"] = "permission_granted"
        tampered.append(changed_status)
        extra_prose = deepcopy(train)
        extra_prose[0]["metadata"]["notes"] = "Source explanation or script text"
        tampered.append(extra_prose)
        generic = deepcopy(train)
        generic[0] = record("generic-game", "A source sentence")
        generic[0]["metadata"]["rights_status"] = recipe.LOCAL_FACT_RIGHTS
        tampered.append(generic)
        for rows in tampered:
            with self.subTest(rows=rows[0]["metadata"]), self.assertRaisesRegex(ValueError, "blocked_source_rights"):
                recipe.ensure_training_rights(rows, validation, local_lexical_experiment=True)

    def test_experiment_must_include_both_declared_components_in_each_split(self):
        train, validation = self.mixtures()
        for a, b in ((train[1:], validation), (train, validation[:1]), (train[:1], validation[:1])):
            with self.subTest(a=len(a), b=len(b)), self.assertRaisesRegex(ValueError, "blocked_local_experiment_mixture"):
                recipe.ensure_training_rights(a, b, local_lexical_experiment=True)

    def test_config_requires_explicit_isolated_cached_nonpublishing_scope(self):
        config = self.configuration()
        recipe.validate_config(config)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "new-adapter"
            with self.assertRaisesRegex(ValueError, "explicit --local-lexical-experiment"):
                recipe.validate_local_experiment_options(config, output)
            recipe.validate_local_experiment_options(config, output, local_lexical_experiment=True)
            for key, value in (("local_only", False), ("publication_allowed", True), ("push_to_hub", True),
                               ("local_lexical_experiment", False), ("data_scope", "generic_text")):
                changed = {**config, key: value}
                with self.subTest(key=key), self.assertRaises(ValueError):
                    recipe.validate_local_experiment_options(changed, output, local_lexical_experiment=True)
            for options in ({"resume": "checkpoint-256"}, {"allow_download": True}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    recipe.validate_local_experiment_options(config, output, local_lexical_experiment=True, **options)
            self.assertFalse(output.exists())

    def test_existing_adapter_is_preserved_before_any_ml_import(self):
        config = self.configuration()
        train, validation = self.mixtures()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing-adapter"
            output.mkdir()
            weights = output / "adapter_model.safetensors"
            weights.write_bytes(b"existing adapter must remain unchanged")
            with patch("builtins.__import__", side_effect=AssertionError("ML import forbidden")), \
                    self.assertRaisesRegex(ValueError, "new nonexistent"):
                recipe.run_training(config, train, validation, {}, output, local_lexical_experiment=True)
            self.assertEqual(weights.read_bytes(), b"existing adapter must remain unchanged")
            self.assertEqual(sorted(p.name for p in output.iterdir()), [weights.name])

    def test_local_training_direct_call_cannot_bypass_group_leakage_check(self):
        train, validation = self.mixtures()
        validation[1]["metadata"]["group_id"] = train[1]["metadata"]["group_id"]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "never-created"
            with patch("builtins.__import__", side_effect=AssertionError("ML import forbidden")), \
                    self.assertRaisesRegex(ValueError, "Group leakage"):
                recipe.run_training(self.configuration(), train, validation, {}, output, local_lexical_experiment=True)
            self.assertFalse(output.exists())

    def test_manifest_reports_original_ineligible_source_and_local_mode_truthfully(self):
        train, validation = self.mixtures()
        report = recipe.data_rights_report(train, validation, self.configuration(), local_lexical_experiment=True)
        self.assertTrue(report["game_derived_candidates_included"])
        self.assertIn("game_derived_not_eligible", report["source_rights_statuses"])
        self.assertIn(recipe.LOCAL_FACT_RIGHTS, report["recorded_statuses"])
        self.assertEqual(report["bounded_local_lexical_fact_rows"], 2)
        self.assertTrue(report["local_lexical_experiment"])
        self.assertFalse(report["source_rights_relabeling_performed"])
        self.assertFalse(report["source_rights_cleared_by_local_experiment"])
        self.assertFalse(report["publication_approved_by_this_run"])
        wordnet_only = recipe.data_rights_report(train[1:], validation[1:], {})
        self.assertFalse(wordnet_only["game_derived_candidates_included"])
        self.assertFalse(wordnet_only["local_lexical_experiment"])

    def test_component_validation_preserves_pairing_and_requires_two_partitions(self):
        _, validation = self.mixtures()
        encoded = [{"fixture": "fix"}, {"fixture": "wordnet"}]
        self.assertEqual(recipe.component_validation_sets(validation, encoded),
                         {"fix": [encoded[0]], "wordnet": [encoded[1]]})
        with self.assertRaisesRegex(ValueError, "nonempty"):
            recipe.component_validation_sets(validation[:1], encoded[:1])
        with self.assertRaisesRegex(ValueError, "differ in length"):
            recipe.component_validation_sets(validation, encoded[:1])

    def test_training_records_separate_component_losses_without_changing_combined_selection(self):
        config = self.configuration()
        train, validation = self.mixtures()
        original_save = Mock()
        parameters = [("base.weight", SimpleNamespace(requires_grad=False, numel=lambda: 100)),
                      ("layer.lora_A.default.weight", SimpleNamespace(requires_grad=True, numel=lambda: 8)),
                      ("layer.lora_B.default.weight", SimpleNamespace(requires_grad=True, numel=lambda: 8))]
        model = SimpleNamespace(config=SimpleNamespace(use_cache=True, _commit_hash=config["revision"]),
                                named_parameters=lambda: iter(parameters), save_pretrained=original_save)
        tokenizer = SimpleNamespace(is_fast=True, pad_token_id=1, save_pretrained=Mock())
        trainer = Mock()
        trainer.state = SimpleNamespace(global_step=128, best_model_checkpoint="checkpoint-128", best_metric=2.0)
        trainer.train.return_value = SimpleNamespace(metrics={"train_loss": 1.5})
        losses = {"base_eval": 5.0, "base_fix_eval": 6.0, "base_wordnet_eval": 4.0,
                  "eval": 2.0, "fix_eval": 1.0, "wordnet_eval": 3.0}
        def evaluate(**kwargs):
            prefix = kwargs.get("metric_key_prefix", "eval")
            return {prefix + "_loss": losses[prefix]}
        trainer.evaluate.side_effect = evaluate
        torch = SimpleNamespace(bfloat16="bf16", float16="fp16", cuda=SimpleNamespace(
            is_available=lambda: True, is_bf16_supported=lambda: True, current_device=lambda: 0,
            get_device_name=lambda _: "fixture CUDA", get_device_properties=lambda _: SimpleNamespace(total_memory=16),
            max_memory_allocated=lambda: 5, max_memory_reserved=lambda: 6))
        transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=tokenizer)),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=Mock(return_value=model)),
            BitsAndBytesConfig=Mock(), Trainer=Mock(return_value=trainer), TrainingArguments=Mock(), set_seed=Mock())
        peft = SimpleNamespace(LoraConfig=Mock(), get_peft_model=lambda value, *a, **kw: value,
                               prepare_model_for_kbit_training=lambda value, **kw: value)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "new-adapter"
            with patch.dict(sys.modules, {"torch": torch, "transformers": transformers, "peft": peft}), \
                    patch.object(recipe, "encode_record", return_value={"input_ids": [1], "attention_mask": [1], "labels": [1]}):
                recipe.run_training(config, train, validation, {"evaluation_scope": config["evaluation_scope"]}, output,
                                    local_lexical_experiment=True)
            manifest = json.loads((output / "training_manifest.json").read_text())
            self.assertEqual(manifest["component_evaluations"]["baseline"]["fix"]["base_fix_eval_loss"], 6.0)
            self.assertEqual(manifest["component_evaluations"]["final"]["fix"]["fix_eval_loss"], 1.0)
            self.assertEqual(manifest["component_evaluations"]["final"]["wordnet"]["wordnet_eval_loss"], 3.0)
            self.assertEqual(manifest["optimizer_steps"], 128)
            self.assertTrue(manifest["base_frozen"])
            self.assertTrue(manifest["data_rights"]["game_derived_candidates_included"])
            self.assertEqual(trainer.evaluate.call_count, 6)
            self.assertEqual(transformers.TrainingArguments.call_args.kwargs["metric_for_best_model"], "eval_loss")
            original_save.assert_called_once_with(str(output), safe_serialization=True, save_embedding_layers=False)


class WeightsOnlyInitializationTests(unittest.TestCase):
    def make_initial(self, directory):
        import hashlib
        source = Path(directory) / "initial-adapter"
        source.mkdir()
        names = ("base_model.model.layer.q_proj.lora_A.weight", "base_model.model.layer.q_proj.lora_B.weight")
        header = {names[0]: {"dtype": "F32", "shape": [8, 1], "data_offsets": [0, 32]},
                  names[1]: {"dtype": "F32", "shape": [1, 8], "data_offsets": [32, 64]}}
        encoded = json.dumps(header, separators=(",", ":")).encode()
        blob = len(encoded).to_bytes(8, "little") + encoded + bytes(range(64))
        (source / "adapter_model.safetensors").write_bytes(blob)
        config = json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b_fixmarge_wordnet_lora_v2.json").read_text())
        old_config = json.loads((SCRIPT.parents[1] / "configs/train_qwen3_4b_fixmarge_wordnet_lora.json").read_text())
        adapter = {"base_model_name_or_path": config["model_name"], "revision": config["revision"],
                   "peft_type": "LORA", "task_type": "CAUSAL_LM", "bias": "none", "r": 8,
                   "lora_alpha": 16, "target_modules": sorted(recipe.LORA_TARGETS)}
        manifest = {"training_status": "completed", "training_performed": True, "optimizer_steps": 128,
                    "base_frozen": True, "adapter_only": True, "merge_performed": False,
                    "local_lexical_experiment": True, "configuration": old_config,
                    "trainable_tensor_count": 2, "trainable_parameter_count": 16}
        (source / "adapter_config.json").write_text(json.dumps(adapter))
        (source / "training_manifest.json").write_text(json.dumps(manifest))
        config.update(initial_adapter_path=str(source), initial_adapter_sha256=hashlib.sha256(blob).hexdigest())
        return source, config

    def test_completed_pinned_safe_weights_are_validated_with_no_ml_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            with patch("builtins.__import__", side_effect=AssertionError("ML import forbidden")):
                initial = recipe.validate_initial_adapter(config, source, Path(tmp) / "new-output")
            self.assertEqual(initial["source_optimizer_steps"], 128)
            self.assertEqual(initial["tensor_count"], 2)
            self.assertEqual(initial["parameter_count"], 16)
            self.assertEqual(initial["weight_sha256"], config["initial_adapter_sha256"])
            status = recipe.local_initialization_report(initial)
            self.assertEqual(status["baseline_model"], "original_base_plus_initial_adapter")
            self.assertEqual(status["initial_global_step"], 0)
            self.assertFalse(status["optimizer_state_reused"])
            self.assertFalse(status["scheduler_state_reused"])

    def test_warmstart_stays_explicit_local_only_and_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            output = Path(tmp) / "new-output"
            with self.assertRaisesRegex(ValueError, "requires explicit --init-adapter"):
                recipe.validate_local_experiment_options(config, output, local_lexical_experiment=True)
            with self.assertRaisesRegex(ValueError, "requires explicit --local-lexical-experiment"):
                recipe.validate_local_experiment_options(config, output, init_adapter=source)
            for kwargs in ({"resume": "old-checkpoint"}, {"allow_download": True}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    recipe.validate_local_experiment_options(config, output, local_lexical_experiment=True,
                                                              init_adapter=source, **kwargs)
            recipe.validate_local_experiment_options(config, output, local_lexical_experiment=True, init_adapter=source)
            self.assertFalse(output.exists())

    def test_bad_pin_base_rank_modules_manifest_and_payload_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            output = Path(tmp) / "new-output"
            bad = {**config, "initial_adapter_sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "SHA256"):
                recipe.validate_initial_adapter(bad, source, output)
            adapter_path = source / "adapter_config.json"
            original = json.loads(adapter_path.read_text())
            for key, value in (("revision", "wrong"), ("r", 16), ("lora_alpha", 32),
                               ("target_modules", ["lm_head"]), ("modules_to_save", ["embed_tokens"])):
                adapter_path.write_text(json.dumps({**original, key: value}))
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "configuration"):
                    recipe.validate_initial_adapter(config, source, output)
            adapter_path.write_text(json.dumps(original))
            manifest_path = source / "training_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest_path.write_text(json.dumps({**manifest, "training_status": "running"}))
            with self.assertRaisesRegex(ValueError, "completed"):
                recipe.validate_initial_adapter(config, source, output)
            manifest_path.write_text(json.dumps(manifest))
            weights = source / "adapter_model.safetensors"
            before = weights.read_bytes()
            weights.write_bytes(before[:-1] + b"x")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                recipe.validate_initial_adapter(config, source, output)
            weights.write_bytes(b"not safe tensor bytes")
            with self.assertRaisesRegex(ValueError, "header"):
                recipe.validate_initial_adapter(config, source, output)

    def test_initial_source_cannot_overlap_output_or_protected_base_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            for output in (source, source / "new-output", source.parent):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, "overlap"):
                    recipe.validate_initial_adapter(config, source, output)
            with patch.object(recipe, "model_cache_roots", return_value=[source]), \
                    self.assertRaisesRegex(ValueError, "protected"):
                recipe.validate_initial_adapter(config, source, Path(tmp) / "new-output")

    def test_source_hash_guard_detects_changes_without_writing_to_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            initial = recipe.validate_initial_adapter(config, source, Path(tmp) / "new-output")
            recipe.verify_initial_adapter_unchanged(initial)
            (source / "training_manifest.json").write_text("{}")
            with self.assertRaisesRegex(RuntimeError, "changed"):
                recipe.verify_initial_adapter_unchanged(initial)

    def mocked_training(self, initial_global_step=0):
        with tempfile.TemporaryDirectory() as tmp:
            source, config = self.make_initial(tmp)
            train, validation = LocalLexicalExperimentTests().mixtures()
            initial_hashes = {p.name: recipe.sha256(p) for p in source.iterdir()}
            original_save = Mock()
            parameters = [("base.weight", SimpleNamespace(requires_grad=False, numel=lambda: 100)),
                          ("layer.lora_A.default.weight", SimpleNamespace(requires_grad=True, numel=lambda: 8)),
                          ("layer.lora_B.default.weight", SimpleNamespace(requires_grad=True, numel=lambda: 8))]
            model = SimpleNamespace(config=SimpleNamespace(use_cache=True, _commit_hash=config["revision"]),
                                    named_parameters=lambda: iter(parameters), save_pretrained=original_save)
            tokenizer = SimpleNamespace(is_fast=True, pad_token_id=1, save_pretrained=Mock())
            trainer = Mock()
            self.last_trainer = trainer
            trainer.state = SimpleNamespace(global_step=initial_global_step, best_model_checkpoint="checkpoint-192", best_metric=1.0)
            def train_call(**kwargs):
                self.assertIsNone(kwargs["resume_from_checkpoint"])
                self.assertEqual(trainer.state.global_step, 0)
                trainer.state.global_step = 192
                return SimpleNamespace(metrics={"train_loss": 1.0})
            trainer.train.side_effect = train_call
            trainer.evaluate.side_effect = lambda **kw: {kw.get("metric_key_prefix", "eval") + "_loss": 1.0}
            torch = SimpleNamespace(bfloat16="bf16", float16="fp16", cuda=SimpleNamespace(
                is_available=lambda: True, is_bf16_supported=lambda: True, current_device=lambda: 0,
                get_device_name=lambda _: "fixture CUDA", get_device_properties=lambda _: SimpleNamespace(total_memory=16),
                max_memory_allocated=lambda: 5, max_memory_reserved=lambda: 6))
            transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=tokenizer)),
                AutoModelForCausalLM=SimpleNamespace(from_pretrained=Mock(return_value=model)),
                BitsAndBytesConfig=Mock(), Trainer=Mock(return_value=trainer), TrainingArguments=Mock(), set_seed=Mock())
            peft_loader = Mock(return_value=model)
            get_peft_model = Mock(side_effect=AssertionError("Fresh LoRA must not replace the initial adapter"))
            peft = SimpleNamespace(LoraConfig=Mock(), get_peft_model=get_peft_model,
                prepare_model_for_kbit_training=lambda value, **kw: value,
                PeftModel=SimpleNamespace(from_pretrained=peft_loader))
            output = Path(tmp) / "new-output"
            with patch.dict(sys.modules, {"torch": torch, "transformers": transformers, "peft": peft}), \
                    patch.object(recipe, "encode_record", return_value={"input_ids": [1], "attention_mask": [1], "labels": [1]}):
                recipe.run_training(config, train, validation, {"evaluation_scope": config["evaluation_scope"]}, output,
                                    local_lexical_experiment=True, init_adapter=source)
            peft_loader.assert_called_once_with(model, str(source), is_trainable=True, local_files_only=True)
            get_peft_model.assert_not_called()
            self.assertEqual({p.name: recipe.sha256(p) for p in source.iterdir()}, initial_hashes)
            return json.loads((output / "training_manifest.json").read_text())

    def test_weights_only_load_resets_steps_and_preserves_initial_adapter(self):
        manifest = self.mocked_training()
        self.assertEqual(manifest["optimizer_steps"], 192)
        self.assertEqual(manifest["initial_adapter_source_optimizer_steps"], 128)
        self.assertEqual(manifest["initial_global_step"], 0)
        self.assertEqual(manifest["baseline_model"], "original_base_plus_initial_adapter")
        self.assertFalse(manifest["optimizer_state_reused"])
        self.assertFalse(manifest["scheduler_state_reused"])
        self.assertTrue(manifest["initial_adapter_files_sha256_unchanged"])
        self.assertEqual(len(manifest["initial_adapter_files_sha256"]), 3)

    def test_nonzero_trainer_start_state_is_rejected_before_evaluation_or_training(self):
        with self.assertRaisesRegex(ValueError, "global_step of zero"):
            self.mocked_training(initial_global_step=128)
        self.last_trainer.evaluate.assert_not_called()
        self.last_trainer.train.assert_not_called()


if __name__ == "__main__":
    unittest.main()
