# fiXmArge · Coword · MeMe

```json
{
  "status": "completed",
  "artifact": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v2",
  "configuration": "configs/train_qwen3_4b_fixmarge_wordnet_lora_v2.json",
  "data_directory": "data/training/fixmarge-wordnet-v2",
  "phases": [
    {
      "optimizer_steps_executed": 128,
      "selected_checkpoint": "checkpoint-128",
      "baseline_model": "original_base",
      "train_rows": 1862,
      "fix_rows": 838,
      "wordnet_rows": 1024,
      "final_component_evaluations": {
        "baseline": {
          "fix": {
            "base_fix_eval_loss": 11.098934173583984,
            "base_fix_eval_model_preparation_time": 0.0064,
            "base_fix_eval_runtime": 11.0504,
            "base_fix_eval_samples_per_second": 9.321,
            "base_fix_eval_steps_per_second": 2.353
          },
          "wordnet": {
            "base_wordnet_eval_loss": 5.309939384460449,
            "base_wordnet_eval_model_preparation_time": 0.0064,
            "base_wordnet_eval_runtime": 13.5427,
            "base_wordnet_eval_samples_per_second": 9.452,
            "base_wordnet_eval_steps_per_second": 2.363
          }
        },
        "final": {
          "fix": {
            "fix_eval_loss": 3.254272699356079,
            "fix_eval_model_preparation_time": 0.0064,
            "fix_eval_runtime": 17.6329,
            "fix_eval_samples_per_second": 5.841,
            "fix_eval_steps_per_second": 1.475,
            "epoch": 1.094420600858369
          },
          "wordnet": {
            "wordnet_eval_loss": 1.9898017644882202,
            "wordnet_eval_model_preparation_time": 0.0064,
            "wordnet_eval_runtime": 21.8692,
            "wordnet_eval_samples_per_second": 5.853,
            "wordnet_eval_steps_per_second": 1.463,
            "epoch": 1.094420600858369
          }
        }
      }
    },
    {
      "optimizer_steps_executed": 192,
      "selected_checkpoint": "checkpoint-96",
      "baseline_model": "original_base_plus_phase1_adapter",
      "initial_global_step": 0,
      "optimizer_state_reused": false,
      "train_presentations": 3480,
      "train_unique": 966,
      "fix_presentations": 3352,
      "fix_unique": 838,
      "wordnet_rows": 128,
      "final_component_evaluations": {
        "baseline": {
          "fix": {
            "base_fix_eval_loss": 3.254272699356079,
            "base_fix_eval_model_preparation_time": 0.0076,
            "base_fix_eval_runtime": 9.8302,
            "base_fix_eval_samples_per_second": 10.478,
            "base_fix_eval_steps_per_second": 2.645
          },
          "wordnet": {
            "base_wordnet_eval_loss": 1.9898017644882202,
            "base_wordnet_eval_model_preparation_time": 0.0076,
            "base_wordnet_eval_runtime": 10.885,
            "base_wordnet_eval_samples_per_second": 11.759,
            "base_wordnet_eval_steps_per_second": 2.94
          }
        },
        "final": {
          "fix": {
            "fix_eval_loss": 4.049633026123047,
            "fix_eval_model_preparation_time": 0.0076,
            "fix_eval_runtime": 11.7285,
            "fix_eval_samples_per_second": 8.782,
            "fix_eval_steps_per_second": 2.217,
            "epoch": 0.8827586206896552
          },
          "wordnet": {
            "wordnet_eval_loss": 2.123688220977783,
            "wordnet_eval_model_preparation_time": 0.0076,
            "wordnet_eval_runtime": 14.804,
            "wordnet_eval_samples_per_second": 8.646,
            "wordnet_eval_steps_per_second": 2.162,
            "epoch": 0.8827586206896552
          }
        }
      }
    }
  ],
  "total_optimizer_steps_executed": 320,
  "selected_weight_update_lineage": [
    128,
    96
  ],
  "new_words_or_sentence_targets_invented": false,
  "Korean_supervised_targets": 0,
  "grammar_supervision": 0,
  "notes_lyrics_and_sentence_examples_used": false,
  "source_rights_relabelled_or_cleared": false,
  "local_experiment_only": true,
  "original_source_status": "game_derived_not_eligible",
  "bounded_fact_status": "lexical_facts_local_experiment",
  "HF_new_adapter_uploaded": false,
  "downloads": 0,
  "originals_preserved": {
    "protected_files_sha256_unchanged": {
      "original_base": 12,
      "wordnet_adapter": 15,
      "phase1_fix_adapter": 16
    },
    "new_adapter_weight": {
      "bytes": 66126768,
      "sha256": "2bcd148d1dcf9d88cb44c444d69343b74bb474c2e3b1f9e73d272b95643f0377"
    },
    "new_adapter_differs_from_initial": true,
    "optimizer_steps": 192,
    "initialization": {
      "initial_adapter_path": "/home/user/code/fiXmArge-translator/artifacts/qwen3-4b-fixmarge-wordnet-lora-v1",
      "initial_adapter_sha256": "c2acaf0fdf69578f0bb7ac7dccc01f85d506a0a2264c5c3c5d74552b0cb8e79f",
      "initial_adapter_source_optimizer_steps": 128,
      "initial_global_step": 0,
      "optimizer_state_reused": false,
      "scheduler_state_reused": false,
      "baseline_model": "original_base_plus_initial_adapter"
    },
    "base_frozen": true,
    "merge_performed": false,
    "tensor_count": 504,
    "parameter_count": 16515072,
    "b_tensors": 252,
    "nonzero_b_tensors": 252
  },
  "observations": {
    "status": "completed",
    "trained_source_candidate_matches": {
      "base": 0,
      "phase1": 0,
      "phase2": 3,
      "cases": 4
    },
    "heldout_source_candidate_matches": {
      "base": 0,
      "phase1": 0,
      "phase2": 0,
      "directional_cases": 8,
      "independent_families": 7
    },
    "source_candidate_matches_are_translation_accuracy": false,
    "general_controls": {
      "cases": 4,
      "meaning_change_observed": false,
      "ja_register_change_observed": true,
      "global_quality_guaranteed": false
    },
    "sentence": {
      "source": "sINeEy Iz'u Nii riEl",
      "independent_sentences": 1,
      "target_directions": 3,
      "source_status": "secondary_fan_quote",
      "official_parallel_reference": false,
      "trained_lexical_tokens": [
        "riEl"
      ],
      "excluded_lexical_tokens": {
        "sINeEy": "explicit_uncertainty",
        "Iz'u": "source_conflict",
        "Nii": "source_conflict"
      },
      "riEl_direct_ja_gloss": [
        "帰る"
      ],
      "riEl_direct_en_gloss": [],
      "full_sentence_supervision": false,
      "model_schema_valid": 1,
      "model_cases": 3,
      "results": [
        {
          "direction": "fix-to-ja",
          "base_translation": "姉は違う",
          "adapter_translation": null,
          "adapter_raw_output": "姉は帰る",
          "adapter_schema_valid": false
        },
        {
          "direction": "fix-to-en",
          "base_translation": "Sister is not different",
          "adapter_translation": "is not sister",
          "adapter_raw_output": "{ \"tentative_translation\": \"is not sister\", \"evidence_ids\": [\"fx-84a7955ffac17756\", \"fx-f151c99a460401fc\", \"fx-2b8bacf36013f2d7\", \"fx-c1ad1fc9048451ef\"], \"uncertainties\": [\"ambiguous\", \"unverified_sentence\"] }",
          "adapter_schema_valid": true
        },
        {
          "direction": "fix-to-ko",
          "base_translation": null,
          "adapter_translation": null,
          "adapter_raw_output": "다른가",
          "adapter_schema_valid": false
        }
      ],
      "accuracy": null,
      "translation_improvement": "not_demonstrated"
    },
    "deployment": {
      "new_adapter_default": false,
      "demo_adapter": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
      "reason": "sentence_response_schema_regression",
      "new_adapter_role": "local_comparison_artifact",
      "HF_new_adapter_uploaded": false
    },
    "report": "reports/fixmarge-lora-training.md"
  }
}
```

## ⚙️ · ConWas

```bash
.venv/bin/python scripts/evaluate_fixmarge_adapter.py \
  --train data/training/fixmarge-wordnet-v2/train.jsonl \
  --test data/training/fixmarge-wordnet-v2/test.jsonl \
  --adapter artifacts/qwen3-4b-fixmarge-wordnet-lora-v2 \
  --max-new-tokens 32 --generate --output runs/fixmarge-comparison-repro.json
```

[🧪 MeMe](../reports/fixmarge-lora-training.md) · [⚙️ ConWas](../scripts/prepare_fixmarge_training.py) · [⚖️](BACKBONE_LICENSE.md)
