# fiXmArge · sinruits

```json
{
  "current_product_snapshot": "2026-11-07",
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
  "historical_records": {
    "2026_11_06_Gradio_WordNet_context": {
      "layout": "side_by_side_input_output_closed_details_single_generation_button",
      "standard_lookup": "existing_en_ja_WordNet_context_in_actual_prompt_empty_lookup_preserved",
      "fix_bridge": "recorded_en_ja_glosses",
      "evidence_IDs": "separate_model_standard_and_domain_IDs_unsupported_claims_retained",
      "Korean_dictionary": false,
      "natural_language_control_not_assessed": "domain_status_independent_of_standard_context",
      "base_weights_changed": false,
      "optimizer_during_UI_work": false,
      "new_GPU_quality_result_in_that_step": false
    },
    "2026_11_06_initial_Gradio_and_discovery": {
      "Gradio": "5.49.1",
      "HTTP_and_settings_API": "verified_local_and_Windows_host_200",
      "lookup_model_loaded": false,
      "cached_base_sentence": {
        "source": "나는 진실을 알고 싶다.",
        "proposal": "I want to know the truth."
      },
      "sentence_accuracy_judgment": false,
      "dependency_changes": "Gradio_only_torch_transformers_peft_preserved",
      "CPU_tests": 123,
      "dependency_check": "pass",
      "original_sources_investigated": 28,
      "Korean_fan_posts": 5,
      "Korean_lexical_correspondences": 10,
      "English_dictionary_rows_including_sections": 264,
      "Japanese_official_parallel_video_candidates": "found",
      "permission_status_automatically_changed": false,
      "pilot_safety": "cached_only_LoRA_only_adapter_save_cache_output_protection",
      "eligible_fix_train_validation": [
        0,
        0
      ],
      "empty_training": "blocked_before_import_or_output",
      "optimizer_steps": 0,
      "training_adapter_created": false,
      "historical_Space_payload_files": 12,
      "Space_created_uploaded_hardware_changed": false,
      "HF_deploy_token_at_that_step": "not_available",
      "records": [
        "runs/gradio-demo-2026-11-06/",
        "runs/data-discovery-2026-11-06/",
        "runs/space-staging-final/"
      ]
    },
    "2026_11_06_sentence_controls": {
      "model": "Qwen3-4B-Instruct-2507_pinned_base",
      "training_optimizer_steps": 0,
      "adapter_loaded": false,
      "downloads_or_new_packages": 0,
      "research_directions": 12,
      "natural_language_control_directions": 6,
      "domain_control_status": "not_assessed",
      "fix_directions_with_lookup": 6,
      "self_authored_natural_inputs": 3,
      "fix_source": "sINeEy Iz'u Nii riEl",
      "fix_source_location": "Japanese_wordbook_G273_secondary_quote",
      "official_source_snapshot_or_verified_parallel": "not_locally_available",
      "fan_full_sentence_notes_in_prompt": false,
      "proposal_verified": false,
      "grammar_word_order_negation_scope_alignment": "unverified",
      "English_case": {
        "source": "I want to know the truth.",
        "matched": [
          "I",
          "want",
          "truth"
        ],
        "unmatched": [
          "to",
          "know",
          "the"
        ],
        "proposal": "WAirTell wAsHe sinruits",
        "I_and_want_conflicts": true
      },
      "missing_Korean_sense_layer": true,
      "Japanese_continuous_sentence": "私は真実を知りたい。",
      "Japanese_boundary_matcher_misses_真実": true,
      "quoted_word_lookup_control": "recorded",
      "unmatched_implies_word_absent": false,
      "fix_to_ko_proposal": "姉?는 아니야",
      "fix_to_ja_proposal": "姉？はない帰る",
      "natural_language_control_issues": "viewpoint_omissions",
      "accuracy_calculated": false,
      "initial_ko_JSON_token_limit": 256,
      "same_input_evidence_retry_token_limit": 512,
      "initial_and_retry_raw_outputs": "both_preserved",
      "total_model_calls": 13,
      "final_JSON_valid": [
        12,
        12
      ],
      "CPU_tests": 90,
      "lexical_guard_preserved": true,
      "HTTP_attempts": 0,
      "downloads": 0,
      "weights_file_list_and_sizes": "unchanged",
      "full_weight_SHA256_recheck": false,
      "training_uploads": false,
      "records": "runs/sentence-test-2026-11-06/"
    },
    "2026_11_06_grounding_fix": {
      "model": "same_pinned_Qwen_base_BF16",
      "GPU_cases": 6,
      "install_download_train_upload": false,
      "HTTP": "blocked_0_attempts",
      "contract": "per_input_span_target_senses_all_same_span_reverse_forms_no_cross_span_sentence_join",
      "validation": "actual_lookup_recomputed_candidates_target_language_unknowns_evidence_IDs",
      "outputs": [
        "generation",
        "generation_raw"
      ],
      "verified_model_analysis": false,
      "raw_fixed_cases": {
        "truth": "sinruits",
        "真実": "sinRuit / sinruits",
        "maybe": "Owk / meKaMo",
        "能力": "AbiRyok / AbiRyoku"
      },
      "partial_case": {
        "input": "truth blood",
        "raw": "arbitrary_word_combination",
        "grounded_translation": null,
        "segments": {
          "truth": "sinruits",
          "blood": "ChiDd"
        }
      },
      "Syu_Tain": "開廷_閉廷_conflict_candidates_retained_translation_null",
      "raw_contract_pass": [
        5,
        6
      ],
      "grounded_contract_pass": [
        6,
        6
      ],
      "contract_pass_equals_model_accuracy": false,
      "CPU_tests": 66,
      "forward_separator": "; ",
      "reverse_separator": " / ",
      "final_code_reprocessing": "same_6_results",
      "weights_list_and_sizes": "unchanged",
      "full_weight_hash_recheck": false,
      "records": "runs/grounding-fix-2026-11-06/",
      "remaining_withhold_cases": [
        "multi_span",
        "source_conflict",
        "case_conflict",
        "missing_target_sense"
      ]
    },
    "2026_11_06_WSL_restore": {
      "environment": {
        "python": "3.12.15",
        "GPU": "RTX_5060_Ti_16GB",
        "torch": "2.8.0+cu128",
        "transformers": "4.57.1",
        "CUDA_BF16": "verified"
      },
      "training_or_HF_upload_at_that_step": false,
      "Hecate_rows": 331,
      "Japanese_wordbook_rows": 337,
      "domain_entries": 387,
      "RAG_documents": 387,
      "Hecate_LF_and_Read_Me_CSV_hashes": "original_lock_match",
      "new_XLSX_binary": "different_old_lock_preserved_actual_hash_and_337_normalized_rows_separately_recorded",
      "XLSX_semantic_identity": "not_asserted",
      "source_record": "runs/restore-2026-11-06/source-verification.json",
      "prior_curation_recovered": false,
      "Korean_senses": 0,
      "grammar_rules": 0,
      "unresolved_conflicts": 111,
      "research_train_validation": [
        853,
        118
      ],
      "eligible_train_validation": [
        0,
        0
      ],
      "WordNet_originals": 2,
      "WordNet_notices": 4,
      "source_locked_hashes": "verified",
      "WordNet_senses": 550128,
      "search_keys": 2632218,
      "CPU_tests": 33,
      "actual_dictionary_tests": 14,
      "standard_search_fix": "canonical_headword_priority_before_candidate_limit_cat_synonym_ID_order_regression",
      "en_casefold_ja_synonym_fallback": "regression_checked",
      "prompt_sense_hypothesis_rights_unknowns": "separated",
      "GPU_cases": 7,
      "covered_directions": 6,
      "same_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
      "precision": "BF16",
      "known_lexical_outputs": {
        "sinruits": [
          "真実",
          "truth"
        ],
        "cOnzAI": "guilty"
      },
      "Korean_directions": "withheld_missing_senses_evidence",
      "raw_failures": {
        "真実": "omitted_sinRuit_and_sinruits",
        "truth_to_fix": "wrong_target_真実"
      },
      "singular_plural_model_claims": "not_verified_grammar",
      "expanded_plain_RAG_scoring": "stopped_after_failures",
      "records": "runs/restore-2026-11-06/"
    },
    "2026_11_05_preparation": {
      "model_weights_download_GPU_training_HF_upload": false,
      "CPU_tests": 32,
      "tested": [
        "whitespace",
        "punctuation",
        "case",
        "six_directions",
        "unknowns",
        "external_SQLite",
        "lemma_rule_splits",
        "reverse_ambiguity",
        "assistant_only_loss",
        "data_rights",
        "plain_RAG_evaluation",
        "model_reuse"
      ],
      "official_tokenizer_cases": 6,
      "tokenizer_models": 2,
      "languages": [
        "ko",
        "ja",
        "en"
      ],
      "tokenizer_checks": [
        "answer_preservation",
        "prompt_loss_mask",
        "EOS"
      ],
      "record": "tokenizer_qa.json",
      "WordNet_senses": 550128,
      "search_keys": 2632218,
      "actual_readonly_SQLite_sources_and_licenses": "verified",
      "research_candidates": [
        1740,
        242
      ],
      "eligible_train_validation": [
        0,
        0
      ],
      "training_status": "blocked_no_eligible_corpus_before_download",
      "environment": "bundled_Python_3.12.14_no_torch_no_CUDA",
      "gaming_PC_GPU_and_VRAM": "doctor_and_smoke_test_required",
      "pipeline_preparation_equals_fix_sentence_quality_or_publication_permission": false
    }
  },
  "paired_fix_sentence_comparison": {
    "status": "completed",
    "script": "scripts/compare_fixmarge_sentences.py",
    "generation": "explicit_--generate",
    "model_access": "existing_cache_only_no_download",
    "precision": "NF4_4bit",
    "comparison_order": [
      "frozen_original_base",
      "same_base_with_separate_LoRA"
    ],
    "same_RAG_prompt_and_generation_settings": true,
    "attested_input_sentences": 1,
    "target_languages": [
      "ko",
      "ja",
      "en"
    ],
    "source_status": "secondary_fan_quoted_sentence_not_verified_official_parallel",
    "source": "sINeEy Iz'u Nii riEl",
    "word_only_examples": false,
    "independent_reference_sentence_available": false,
    "sentence_accuracy_score": "not_computable_from_available_references",
    "raw_output_comparison": "observable_changes_only_not_quality_proof",
    "translation_improvement": "not_established",
    "training_or_base_weight_changes": false,
    "generated_outputs": 6,
    "schema_valid_outputs": 6,
    "same_translation_directions": [
      "ja"
    ],
    "changed_translation_directions": [
      "en",
      "ko"
    ],
    "base_abstention_to_lora_question": [
      "ko"
    ],
    "published_record": "reports/fixmarge-sentence-comparison.json",
    "base_and_adapter_weight_sha256_unchanged": true,
    "HTTP_attempts": 0
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

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "scripts/test_sentence.py",
    "ModelRunner",
    "lexicon.jsonl",
    "rules.jsonl",
    "standard_dictionary",
    "model_standard_evidence_ids",
    "model_domain_evidence_ids",
    "not_assessed",
    "나는 진실을 알고 싶다.→I want to know the truth.",
    "runs/gradio-demo-2026-11-06/",
    "runs/data-discovery-2026-11-06/",
    "runs/space-staging-final/",
    "sINeEy Iz'u Nii riEl",
    "tentative_translation",
    "I want to know the truth.",
    "WAirTell wAsHe sinruits",
    "私は真実を知りたい。",
    "姉?는 아니야",
    "姉？はない帰る",
    "--generate",
    "runs/sentence-test-2026-11-06/",
    "generation",
    "generation_raw",
    "truth→sinruits",
    "真実→sinRuit / sinruits",
    "maybe→Owk / meKaMo",
    "能力→AbiRyok / AbiRyoku",
    "truth blood",
    "translation: null",
    "blood→ChiDd",
    "Syu Tain",
    "; ",
    " / ",
    "runs/grounding-fix-2026-11-06/",
    "runs/restore-2026-11-06/source-verification.json",
    "cat",
    "cdbee75f17c01a7cc42f958dc650907174af0554",
    "sinruits→真実/truth",
    "cOnzAI→guilty",
    "真実",
    "sinRuit/sinruits",
    "truth→fiXmArge",
    "runs/restore-2026-11-06/",
    "tokenizer_qa.json",
    "blocked_no_eligible_corpus"
  ]
}
```


## 🧪 · sinruits

```bash
python scripts/compare_fixmarge_sentences.py --generate --output runs/fixmarge-sentence-comparison-2026-11-07/results.json
```

[🧪 MeMe](../reports/fixmarge-sentence-comparison.md)

[🧪 Coword](FIXMARGE_LORA.md)
