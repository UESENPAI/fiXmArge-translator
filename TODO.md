# fiXmArge · ConWas

```json
{
  "snapshot": "2026-11-07",
  "status": {
    "WordNet_restore": "verified",
    "GPU_inference": "verified",
    "local_Gradio": "running_expanded_397_entry_RAG_same_original_BF16_base_no_adapter",
    "WordNet_LoRA": {
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
    "HF_adapter": "old_WordNet_adapter_only_uploaded_private",
    "cloud": {
      "space_created": false,
      "creation_HTTP_status": 402,
      "eligibility_authority": "Hugging_Face_server",
      "eligibility_verified_email_and_account_age_sufficient_to_predict": false,
      "hardware": "zero-a10g",
      "visibility": "private",
      "sdk": "gradio",
      "gradio_version": "5.49.1",
      "python_version": "3.12",
      "paid_hardware_or_subscription_or_storage_selected": false,
      "automatic_hardware_or_visibility_fallback": false,
      "cloud_startup_and_generation_verified": false,
      "existing_staging_and_ZIP": "historical_source_snapshot_rebuild_required",
      "staging_nonempty_output": "reject_without_overwrite",
      "wordnet_resources_in_bundle": true,
      "fix_lexicon_in_bundle": false,
      "FIXMARGE_DATA_DIR": "operator_reviewed_local_lexicon.jsonl_and_rules.jsonl_required",
      "missing_empty_invalid_lexicon_or_missing_rules": "stop_before_adapter_download_and_model_preload",
      "natural_language_fallback": false
    },
    "new_fixmarge_adapter": "phase2_completed_selected_checkpoint96_generation_comparison_completed_local_only_not_default_not_uploaded",
    "dictionary_first_RAG": {
      "implementation": "completed",
      "runtime_validation": "completed_295_unit_10_forward_runtime_5_API_cases_accuracy_not_established",
      "previous_runtime_validation": "completed_cached_base_266_tests_and_actual_generation_no_model_download",
      "current_change_scope": ["fix-to-ko", "fix-to-ja", "fix-to-en"],
      "reverse_direction_improvements": "excluded_existing_HEAD_behavior_retained",
      "Korean_gloss_bridge": "implemented_separate_EN_JA_to_Korean_paraphrase_not_restored_dictionary",
      "Korean_gloss_retry": "Korean_prompt_general_water_example_at_most_two_validation_attempts_all_raw_outputs_preserved",
      "Korean_response_extraction": "complete_typed_object_with_at_most_three_surplus_closing_delimiters_or_quotes_raw_json_valid_false_extraction_method_and_raw_output_preserved",
      "Korean_model_IDs": "short_aliases_exact_model_id_map_to_original_IDs",
      "related_gloss_support": "separate_shared_Japanese_gloss_English_hints_not_verified_entry_equivalence",
      "dictionary_import": "registry_CSV_claims_JSON_pinned_local_inputs_new_exclusive_output_no_network",
      "expanded_dictionary": "data/processed/rag-expanded-v1_387_to_397_entries_10_new_forms_0_to_10_Korean_claim_entries",
      "source_difference_counts": "Asankilp_263_lexical_rows_262_forms_151_English_source_set_differences_unresolved_entries_111_to_189_not_new_correct_meanings",
      "runtime_precision": "BF16_same_cached_backbone_previous_smoke_NF4_no_model_weight_or_LoRA_change",
      "latest_unit_tests_passed": 295,
      "Korean_semantic_quality": "basic_lexical_errors_remain_not_guaranteed",
      "default_adapter": null,
      "new_training_or_model_download": false,
      "source_dictionaries_and_LoRA_artifacts": "preserved",
      "reference": "docs/RAG.md"
    }
  },
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
    "fix_adapter_artifact_candidate": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v2",
    "translation_strategy": "dictionary_first_RAG",
    "direct_single_lexical_answer": "all_dictionary_candidates_no_model_generation",
    "no_domain_evidence": "after_optional_Korean_query_bridge_abstain_without_final_translation_generation",
    "sentence_proposal": "model_with_retrieved_dictionary_unverified",
    "Korean_indirect_bridge": "EN_JA_machine_queries_actual_dictionary_lookup_original_unknown_spans_retained_unverified",
    "Korean_target_lexical_bridge": "retrieved_EN_JA_glosses_to_Korean_options_actual_IDs_and_source_senses_preserved",
    "Korean_single_lexical_paraphrase": "one_gloss_stage_up_to_two_generation_attempts_when_complete_nonconflicting_not_explicitly_uncertain_never_direct_dictionary_answer",
    "Korean_sentence_paraphrase": "separate_sentence_stage_with_machine_Korean_options_and_source_uncertainties",
    "single_headword_source_alternatives": "dictionary_claims_answer_all_target_claims_⚠_no_model_original_contract_null_conflicts_unresolved",
    "Korean_conflicting_lexical_paraphrases": "retain_source_conflict_IDs_and_multiple_Korean_options_never_promote_to_verified_dictionary",
    "active_expanded_dictionary_environment": "explicit_FIXMARGE_DATA_DIR_rag-expanded-v1_and_FIXMARGE_EXTERNAL_DIR_data/external",
    "source_conflicts_unmatched_spans_and_raw_model_output": "details_preserved"
  },
  "hosts": {
    "GitHub": "source_code_documents_configs_tests",
    "Hugging_Face": "old_WordNet_adapter_weights_model_card_evaluation_only",
    "current_Gradio_host": "local",
    "GitHub_Pages": "static_only_no_Python_server_no_GPU_inference"
  },
  "reproduction_tasks": {
    "01_environment": [
      "Python_3.12_project_venv",
      "python_-m_pip_install_-e_.",
      "requirements-train.txt",
      "PyTorch_2.8.0_CUDA_12.8",
      "doctor_GPU_VRAM_torch_CUDA_package_versions",
      "unittest_without_model_download",
      "GPU_load_success_not_translation_quality"
    ],
    "02_dictionaries": [
      "prepare_external_lexicons.py",
      "configs/external-sources.lock.json_SHA256",
      "sufficient_download_and_temporary_disk_budget",
      "private_move_data_processed_research_curation_raw_only_if_needed",
      "source_snapshot_hash_change_reason_and_date",
      "prepare_data.py_report_sources_conflicts_rights",
      "query_actual_en_and_ja"
    ],
    "03_frozen_model_evaluation": [
      "same_model_same_data_same_limits_plain_vs_RAG",
      "first_10_examples_for_load_memory_character_preservation",
      "optional_NF4",
      "local_ignored_runs_only",
      "preserve_case_middle_dot_apostrophe_whitespace",
      "inspect_unknowns_polysemy_15_conflict_items",
      "draft_lexical_reference_score_not_sentence_quality"
    ],
    "04_OP_sentence_evaluation": [
      "distinguish_original_game_version_and_official_parallel",
      "priority_LaVI-Bavellabion_and_MAdEaR_MAdEaR",
      "private_segment_ID_timestamp_source_official_ja_reviewed_ko_en_alignment",
      "no_full_lyrics_in_repository",
      "deduplicate_refrains",
      "record_spelling_pronunciation_version_variants",
      "same_song_refrain_never_cross_splits",
      "bloom_separate_language_and_credits_not_automatic_fix_reference",
      "review_multiple_metaphorical_poetic_translations",
      "no_lexical_exact_match_as_lyric_metric"
    ],
    "05_Japanese_readings": [
      "UniDic_2.1.2_source_README_CSV_lemma_lForm_review",
      "download_and_actual_CSV_conversion_not_verified",
      "official_TLS_failure_no_TLS_bypass",
      "140517811_bytes_exceeds_128_MiB",
      "preserve_BSD_and_AUTHORS",
      "actual_deduplication_reverse_reading_checks",
      "reading_JSONL_to_RAG_and_actual_kana_kanji_integration_pending"
    ],
    "06_future_fix_training": [
      "independent_permission_basis_required",
      "eligible_fix_train_validation_0_0",
      "historical_research_candidates_1740_242_excluded",
      "actual_authorized_parallel_or_self_authored_sentences_only",
      "split_leakage_token_length_assistant_only_loss_checks",
      "GPU_1_step_smoke_before_full_training",
      "evaluation_model_card_base_NOTICE_and_data_conditions_before_publish",
      "weights_excluded_from_GitHub",
      "bounded_local_lexical_fact_experiment_now_running_separate_from_default_eligible_gate"
    ],
    "07_deployment": [
      "regenerate_and_verify_new_six_route_staging_ZIP",
      "separately_connect_reviewed_fix_dictionary",
      "do_not_commit_raw_sources"
    ]
  },
  "dictionaries": {
    "senses": 550128,
    "search_keys": 2632218,
    "JWN_1_1_readings": "all_missing",
    "kanji_to_kana_support_complete": false,
    "UniDic_verified": false
  },
  "historical_GPU_model_guess_RTX_5070_or_5060": "unverified_at_that_step_actual_environment_in_VALIDATION.md",
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

```powershell
python scripts/evaluate.py --dataset data/research/validation_candidates.jsonl --mode plain --dry-run
python scripts/evaluate.py --dataset data/research/validation_candidates.jsonl --mode rag --dry-run
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "python -m pip install -e .",
    "requirements-train.txt",
    "python scripts/doctor.py --json",
    "python -m unittest discover -s tests -v",
    "python scripts/prepare_external_lexicons.py",
    "data/processed",
    "data/research",
    "data/curation",
    "data/raw",
    "python scripts/prepare_data.py",
    "data/processed/report.json",
    "--generate --model ...",
    "runs/",
    "LaVI-Bavellabion",
    "MAdEaR MAdEaR",
    "bloom",
    "lemma",
    "lForm"
  ]
}
```

## 🔗 · WiD

- [↗ 01](https://huggingface.co/uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge)
- [↗ 02](docs/WORDNET_LORA.md)
- [↗ 03](spaces/DEPLOY.cloud.md)
- [↗ 04](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [↗ 05](docs/TRAINING.md)
- [↗ 06](configs/external-sources.lock.json)
- [↗ 07](data/source-lock.json)
- [↗ 08](docs/EVALUATION.md)
- [↗ 09](data/evaluation_sources.json)
- [↗ 10](scripts/prepare_japanese_readings.py)
- [↗ 11](https://manosaba.com/guidelines)
- [↗ 12](docs/VALIDATION.md)
- [↗ 13](docs/SOURCES.md)

## ⚖️

공개 재배포 허가를 받은 자료라고 표시하지 않는다.

모델의 Apache-2.0은 게임 유래 데이터에 허가를 부여하지 않는다.

팬 전사나 합성 확장으로 금지를 우회했다고 판단하지 않는다.

[🧪 Coword](docs/FIXMARGE_LORA.md)
