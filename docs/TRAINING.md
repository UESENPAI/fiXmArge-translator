# fiXmArge · ConWas

```json
{
  "product": {
    "product_routes": [
      "fix-to-ko",
      "ko-to-fix",
      "fix-to-ja",
      "ja-to-fix",
      "fix-to-en",
      "en-to-fix"
    ],
    "default_route": "fix-to-ko",
    "same_language_routes": "blocked",
    "natural_language_only_routes": "blocked",
    "fix_training_performed": true,
    "sentence_translation_improvement": "not_demonstrated",
    "sentence_grammar_verified": false,
    "fix_training_status": "completed",
    "fix_training_scope": "bounded_dictionary_correspondences_no_grammar_or_Korean_targets",
    "fix_adapter_artifact_candidate": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v2"
  },
  "completed_WordNet_training": {
    "status": "completed",
    "date": "2026-11-06",
    "optimizer_steps": 256,
    "epochs": 1,
    "train_rows": 4096,
    "validation_rows": 256,
    "test_rows": 256,
    "seed": 42,
    "target_language_ratio_en_ja": "1:1",
    "trainable_lora_parameters": 16515072,
    "runtime_seconds": 2079.02,
    "selected_checkpoint": "checkpoint-256",
    "validation_loss_base": 5.2263,
    "validation_loss_adapter": 1.9733,
    "loss_scope": "dictionary_lexical_and_definition_tasks",
    "sentence_translation_accuracy": "not_measured",
    "train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "eval_batch_size": 4,
    "learning_rate": 2e-05,
    "lora_r": 8,
    "lora_alpha": 16,
    "max_sequence_length": 384,
    "observed_max_tokenizer_length": 163,
    "test_used_for_training_or_checkpoint_selection": false
  },
  "model": {
    "base_model": "Qwen/Qwen3-4B-Instruct-2507",
    "base_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
    "adapter_repo": "uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge",
    "adapter_weights_revision": "c17943bf523779fb2dd75078148a50816dd52ed7",
    "adapter_path": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "base_frozen": true,
    "merged_into_base": false,
    "base_files_before_after_sha256_equal": 12
  },
  "publication": {
    "HF_repo": "WordNet_adapter_only_public",
    "GitHub": "no_weights_or_local_data",
    "WordNet_repo": "uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge",
    "new_fixmarge_adapter": "local_only_not_uploaded"
  },
  "base_models": {
    "Qwen3_4B_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
    "Qwen3_1_7B_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "fiXmArge_support_assumed": false,
    "4bit_weights_size_equals_training_VRAM": false,
    "MADLAD_400_3B_MT": "Apache_2_0_T5_comparison_candidate_no_training_code",
    "Qwen_choice": "chat_context_for_dictionary_etymology_rules_uncertainty_not_measured_fix_quality"
  },
  "environment": {
    "OS": [
      "Linux",
      "WSL2"
    ],
    "GPU": "NVIDIA_CUDA",
    "Python": "3.10_to_3.12",
    "torch": "2.8.0",
    "RTX_50_candidate_wheel": "cu128",
    "compatibility": "doctor_actual_GPU_VRAM_and_short_training_required",
    "OS_or_driver_changed": false,
    "dependencies": "direct_version_snapshot_not_all_platform_transitive_lock",
    "records": [
      "pip_freeze",
      "nvidia-smi"
    ]
  },
  "adapter_safety": {
    "pilot_config": "configs/train_qwen3_4b_lora_pilot.json",
    "pilot_max_steps": 20,
    "WordNet_config": "configs/train_qwen3_4b_wordnet_lora.json",
    "empty_eligible_fix_dataset": "stop_before_model_import_or_output_creation",
    "new_source_discovery_implies_training_permission": false,
    "loader_default": "local_files_only_True",
    "download_opt_in": "--allow-download",
    "output_overlap_with_cache_or_existing_full_model": "reject",
    "trainable_parameter_guard": "LoRA_modules_only_before_Trainer",
    "checkpoint_and_final_saves": "adapter_safetensors_only",
    "embedding_saving": false,
    "backbone_merge": false,
    "manifest": [
      "base_state",
      "trainable_parameters",
      "adapter_saved"
    ],
    "local_fix_config": "configs/train_qwen3_4b_fixmarge_wordnet_lora.json",
    "local_fix_explicit_flag": "--local-lexical-experiment",
    "local_fix_existing_output_resume_or_download": "reject"
  },
  "eligible_conversation": {
    "required_fields": [
      "messages",
      "metadata.group_id",
      "metadata.source",
      "metadata.status",
      "metadata.task"
    ],
    "turns": [
      "optional_system",
      "user",
      "final_assistant"
    ],
    "group_or_identical_chat_split_overlap": "reject",
    "overlength": "reject_without_truncating_answer",
    "game_candidate_copy_to_eligible_path": "not_allowed"
  },
  "default_fix_recipe": {
    "quantization": "NF4_4bit_double_quantization",
    "lora_r": 16,
    "target_modules": "attention_and_MLP_projections",
    "gradient_checkpointing": true,
    "precision": "BF16_if_supported_else_FP16",
    "chat_template": "actual_tokenizer_template_full_chat_and_generation_prefix",
    "checks": [
      "generation_prefix_match",
      "token_offsets"
    ],
    "loss_tokens": "assistant_answer_and_end_tokens_only",
    "dry_run_downloads_tokenizer": false,
    "mask_validation": "actual_training_start"
  },
  "training_progression": {
    "first_steps": 5,
    "inspect": [
      "loss",
      "generation_samples",
      "VRAM"
    ],
    "large_repetition": "overfitting_risk",
    "same_headword_reverse_punctuation_variants": "same_split",
    "synthetic_rule_examples": "reported_separately_from_attested_sentences",
    "lexical_holdout_loss": "not_sentence_translation_quality",
    "independent_sentence_eval": [
      "human_review",
      "unknowns",
      "negation",
      "possession",
      "word_order",
      "multiword"
    ],
    "RAG_conditions": "heldout_reference_entry_access_separate"
  },
  "historical_tokenizer_check": {
    "date": "2026-11-05",
    "transformers": "4.57.1",
    "Jinja2": "3.1.6",
    "GPU": false,
    "base_models": 2,
    "languages": [
      "ko",
      "ja",
      "en"
    ],
    "cases": 6,
    "checks": [
      "generation_prefix",
      "answer_tokens",
      "prompt_loss_mask",
      "EOS_supervision"
    ],
    "weights_or_torch_downloaded": false,
    "GPU_training_or_quality_verified": false
  },
  "publication_controls": {
    "automatic_Hub_upload": false,
    "model_card_template": "templates/MODEL_CARD.md",
    "publication_review.json": "actual_source_rights_and_evaluation_review_required",
    "allowlist_excludes": [
      "optimizer_state",
      "checkpoints",
      "tokens",
      "training_raw_data"
    ],
    "GitHub_weights": false
  },
  "publication_legal_record": {
    "required_files": [
      "model_card",
      "Apache_2_0_LICENSE",
      "applicable_NOTICE"
    ],
    "publication_review.json_pending_until_actual_review": true
  },
  "fixmarge_local_lexical_training": {
    "status": "completed",
    "training_performed": true,
    "planned_steps": 192,
    "optimizer_steps": 192,
    "observed_optimizer_steps_at_least": 192,
    "configuration": "configs/train_qwen3_4b_fixmarge_wordnet_lora_v2.json",
    "artifact_path": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v2",
    "data_directory": "data/training/fixmarge-wordnet-v2",
    "documentation": "docs/FIXMARGE_LORA.md",
    "initialization": "weights_only_from_completed_local_phase1_fresh_optimizer_scheduler_global_step_zero",
    "corpus": {
      "lexical_entries": 270,
      "included_families": 244,
      "train": {
        "fix": 3352,
        "fix_unique": 838,
        "fix_repeat_factor": 4,
        "wordnet": 128,
        "unique_total": 966,
        "total": 3480
      },
      "validation": {
        "fix": 103,
        "wordnet": 128,
        "total": 231
      },
      "test": {
        "fix": 126,
        "wordnet": 128,
        "total": 254
      },
      "fix_directions": [
        "fix-to-ja",
        "ja-to-fix",
        "fix-to-en",
        "en-to-fix"
      ],
      "korean_targets": false,
      "sentence_or_grammar_targets": false,
      "source_notes_examples_lyrics_or_etymology_included": false,
      "new_model_generated_words_or_translation_targets": false,
      "grouping": "shared_individual_glosses_and_case_punctuation_alias_variants_connected_before_filtering",
      "same_group_and_reverse_alternatives": "same_split",
      "cross_split_group_or_identical_chat_overlap": 0,
      "test_used_for_training_or_checkpoint_selection": false,
      "validation_and_test_bytes_identical_to_phase1": true
    },
    "source_rights": {
      "original_source_status": "game_derived_not_eligible",
      "bounded_fact_record_status": "lexical_facts_local_experiment",
      "original_source_rights_relabelled_or_cleared": false,
      "source_permission_or_open_license_claimed": false,
      "default_licensed_training_gate_changed": false,
      "default_eligible_fix_training_rows": 0,
      "explicit_local_experiment_fix_training_rows": 838,
      "explicit_local_experiment_fix_training_presentations": 3352
    },
    "local_only": true,
    "HF_uploaded": false,
    "publication_cleared": false,
    "model_access": "existing_cache_only_no_download",
    "base_model": {
      "name": "Qwen/Qwen3-4B-Instruct-2507",
      "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
      "frozen": true,
      "merge_performed": false,
      "final_hash_preservation": "verified",
      "unchanged_file_count": 12
    },
    "existing_wordnet_adapter": {
      "path": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
      "modified_by_new_training": false,
      "final_hash_preservation": "verified",
      "unchanged_file_count": 15
    },
    "validation_losses": {
      "baseline_fix": 3.254272699356079,
      "baseline_wordnet": 1.9898017644882202,
      "final_fix": 4.049633026123047,
      "final_wordnet": 2.123688220977783,
      "corpus": "new_fixed_validation_split",
      "combined_loss_checkpoint_selection": "unchanged",
      "scope": "heldout_lexical_tasks_not_sentence_accuracy",
      "baseline_combined": 2.391603708267212,
      "final_combined": 2.7306790351867676,
      "baseline_model": "original_base_plus_phase1_adapter",
      "combined_vs_phase1": "higher_worse",
      "fix_vs_phase1": "higher_worse",
      "wordnet_vs_phase1": "higher_worse",
      "improvement_over_phase1": false
    },
    "selected_checkpoint": "checkpoint-96",
    "sentence_accuracy": null,
    "sentence_translation_improvement": "not_demonstrated",
    "demo_automatic_adapter_switch_during_training": false,
    "train_runtime_seconds": 1732.448,
    "epochs": 0.8827586206896552,
    "best_combined_validation_loss": 2.7306790351867676,
    "new_adapter_weight_sha256": "2bcd148d1dcf9d88cb44c444d69343b74bb474c2e3b1f9e73d272b95643f0377",
    "nonzero_lora_B_tensors": 252,
    "integrity_record": "runs/fixmarge-wordnet-lora-2026-11-07/integrity-after-v2.json",
    "initial_adapter_path": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v1",
    "initial_adapter_sha256": "c2acaf0fdf69578f0bb7ac7dccc01f85d506a0a2264c5c3c5d74552b0cb8e79f",
    "initial_global_step": 0,
    "optimizer_state_reused": false,
    "scheduler_state_reused": false,
    "baseline_model": "original_base_plus_initial_adapter",
    "selected_checkpoint_optimizer_steps": 96,
    "executed_optimizer_steps_by_phase": [
      128,
      192
    ],
    "total_executed_optimizer_steps": 320,
    "selected_weight_training_lineage_steps": [
      128,
      96
    ],
    "selected_weight_lineage_steps_total": 224,
    "selected_checkpoint_sha256_matches_root": true,
    "generation_evaluation_status": "completed",
    "phase1_history": {
      "status": "completed",
      "training_performed": true,
      "planned_steps": 128,
      "optimizer_steps": 128,
      "observed_optimizer_steps_at_least": 128,
      "configuration": "configs/train_qwen3_4b_fixmarge_wordnet_lora.json",
      "artifact_path": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v1",
      "data_directory": "data/training/fixmarge-wordnet-v1",
      "documentation": "docs/FIXMARGE_LORA.md",
      "initialization": "new_separate_LoRA_on_original_cached_Qwen_not_resume_or_merge_of_old_adapter",
      "corpus": {
        "lexical_entries": 270,
        "included_families": 244,
        "train": {
          "fix": 838,
          "wordnet": 1024,
          "total": 1862
        },
        "validation": {
          "fix": 103,
          "wordnet": 128,
          "total": 231
        },
        "test": {
          "fix": 126,
          "wordnet": 128,
          "total": 254
        },
        "fix_directions": [
          "fix-to-ja",
          "ja-to-fix",
          "fix-to-en",
          "en-to-fix"
        ],
        "korean_targets": false,
        "sentence_or_grammar_targets": false,
        "source_notes_examples_lyrics_or_etymology_included": false,
        "new_model_generated_words_or_translation_targets": false,
        "grouping": "shared_individual_glosses_and_case_punctuation_alias_variants_connected_before_filtering",
        "same_group_and_reverse_alternatives": "same_split",
        "cross_split_group_or_identical_chat_overlap": 0,
        "test_used_for_training_or_checkpoint_selection": false
      },
      "source_rights": {
        "original_source_status": "game_derived_not_eligible",
        "bounded_fact_record_status": "lexical_facts_local_experiment",
        "original_source_rights_relabelled_or_cleared": false,
        "source_permission_or_open_license_claimed": false,
        "default_licensed_training_gate_changed": false,
        "default_eligible_fix_training_rows": 0,
        "explicit_local_experiment_fix_training_rows": 838
      },
      "local_only": true,
      "HF_uploaded": false,
      "publication_cleared": false,
      "model_access": "existing_cache_only_no_download",
      "base_model": {
        "name": "Qwen/Qwen3-4B-Instruct-2507",
        "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
        "frozen": true,
        "merge_performed": false,
        "final_hash_preservation": "verified",
        "unchanged_file_count": 12
      },
      "existing_wordnet_adapter": {
        "path": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
        "modified_by_new_training": false,
        "final_hash_preservation": "verified",
        "unchanged_file_count": 15
      },
      "validation_losses": {
        "baseline_fix": 11.098934173583984,
        "baseline_wordnet": 5.309939384460449,
        "final_fix": 3.254272699356079,
        "final_wordnet": 1.9898017644882202,
        "corpus": "new_fixed_validation_split",
        "combined_loss_checkpoint_selection": "unchanged",
        "scope": "heldout_lexical_tasks_not_sentence_accuracy",
        "baseline_combined": 7.165548324584961,
        "final_combined": 2.391603708267212
      },
      "selected_checkpoint": "checkpoint-128",
      "sentence_accuracy": null,
      "sentence_translation_improvement": "not_demonstrated",
      "demo_automatic_adapter_switch_during_training": false,
      "train_runtime_seconds": 1016.3475,
      "epochs": 1.094420600858369,
      "best_combined_validation_loss": 2.391603708267212,
      "new_adapter_weight_sha256": "c2acaf0fdf69578f0bb7ac7dccc01f85d506a0a2264c5c3c5d74552b0cb8e79f",
      "new_adapter_differs_from_existing": true,
      "nonzero_lora_B_tensors": 252,
      "integrity_record": "runs/fixmarge-wordnet-lora-2026-11-07/integrity-after.json"
    },
    "initial_fix_adapter": {
      "path": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v1",
      "modified_by_phase2": false,
      "final_hash_preservation": "verified",
      "unchanged_file_count": 16
    },
    "new_adapter_differs_from_initial": true,
    "generation_observations": {
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
}
```

## ⚙️ · ConWas

### 01

```bash
python -m venv .venv
# Linux/WSL
source .venv/bin/activate
python -m pip install -r requirements-train.txt
```

### 02

```bash
python scripts/train_qlora.py --config configs/train_qwen3_4b_lora_pilot.json --dry-run
```

### 03

```bash
python scripts/train_qlora.py --dry-run
python scripts/train_qlora.py --config configs/train_qwen3_1_7b.json --dry-run
# 아래 명령은 적격 train/validation 코퍼스가 확보된 뒤에만 실행 가능하다.
python scripts/train_qlora.py --run-training --max-steps 5
```

### 04

```json
{
  "source_rights_status": "cleared",
  "evaluation_status": "reviewed"
}
```

### 05

```bash
python scripts/publish_adapter.py artifacts/qwen3-4b-wordnet-en-ja-lora-v1
# 새 배포를 명시적으로 요청할 때만 실행한다. 기존 v1 업로드는 이미 완료됐다.
# HF_TOKEN 또는 기존 HF 로그인을 사용한다.
python scripts/publish_adapter.py artifacts/qwen3-4b-wordnet-en-ja-lora-v1 --repo-id YOUR_NAME/qwen3-4b-wordnet-en-ja-lora --upload
# 공개 저장소를 새로 만들려면 --public 추가. 기존 저장소 공개설정을 바꾸지는 않는다.
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "data/research/train_candidates.jsonl",
    "data/research/validation_candidates.jsonl",
    "data/training",
    "rights_status",
    "self_authored",
    "open_license",
    "permission_granted",
    "data/training/train.jsonl",
    "data/training/validation.jsonl",
    "blocked_no_eligible_corpus",
    "data/training/wordnet-en-ja-v1",
    "--run-training",
    "cdbee75f17c01a7cc42f958dc650907174af0554",
    "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "python scripts/doctor.py --json",
    "python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128",
    "torch_cuda.available",
    "pip freeze",
    "nvidia-smi",
    "configs/train_qwen3_4b_lora_pilot.json",
    "configs/train_qwen3_4b_wordnet_lora.json",
    "local_files_only=True",
    "--allow-download",
    "requires_grad=True",
    "messages",
    "metadata.group_id/source/status/task",
    "artifacts/...",
    "templates/MODEL_CARD.md",
    "publication_review.json",
    "pending"
  ]
}
```

## 🔗 · WiD

- [↗ 01](WORDNET_LORA.md)
- [↗ 02](https://manosaba.com/guidelines)
- [↗ 03](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [↗ 04](https://huggingface.co/Qwen/Qwen3-1.7B)
- [↗ 05](https://huggingface.co/Qwen/Qwen3-1.7B/tree/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e)
- [↗ 06](https://huggingface.co/google/madlad400-3b-mt)
- [↗ 07](https://pytorch.org/get-started/locally/)
- [↗ 08](https://pytorch.org/get-started/previous-versions/)
- [↗ 09](BACKBONE_LICENSE.md)
- [↗ 10](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/trainer)
- [↗ 11](https://huggingface.co/docs/transformers/en/chat_templating)
- [↗ 12](https://huggingface.co/docs/peft/developer_guides/quantization)
- [↗ 13](https://huggingface.co/Qwen/Qwen3-1.7B/blob/main/tokenizer_config.json)

## ⚖️

2026-11-05 확인한 [공식 가이드라인](https://manosaba.com/guidelines)의 제6항(최종 갱신 2026-10-21)은 게임의 공식 이미지·영상·음성·악곡·시나리오·텍스트 등을 생성형 AI·기계학습 모델의 학습 데이터로 사용하거나 제공하는 행위를 금지한다. 베이스 모델의 Apache-2.0 라이선스나 팬 전사본의 공개 여부가 이 제한을 해소하지 않는다.

`open_license`는 원권리까지 해당 이용을 허용하는 경우여야 하며, 게임에서 파생한 팬 자료에 임의로 붙이는 표지가 아니다.

학습을 시작하려면 독립적으로 자작한 자료, 학습을 허용하는 공개 라이선스 자료, 또는 실제 개별 허가를 확보해야 한다.

모델 라이선스는 게임·가사·사전·파생 학습 데이터의 이용 조건을 대신하지 않는다.

조사한 새 출처를 자동으로 학습 허가 자료로 바꾸지 않습니다.

원본 CSV나 RAG 전체를 무조건 어댑터 라이선스로 다시 허가하지 않는다.

[🧪 Coword](FIXMARGE_LORA.md)
