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
    "fix_adapter_artifact_candidate": "artifacts/qwen3-4b-fixmarge-wordnet-lora-v2",
    "translation_strategy": "dictionary_first_RAG",
    "default_adapter": null,
    "preserved_LoRA_artifacts": "comparison_only_optional_explicit_selection",
    "current_change_scope": ["fix-to-ko", "fix-to-ja", "fix-to-en"],
    "reverse_direction_improvements": "excluded_existing_behavior_retained"
  },
  "project_status": {
    "unofficial_fan_project": true,
    "domain": "fiXmArge_Magical_Girl_Witch_Trials",
    "implemented": [
      "dictionary_processing",
      "lexical_exercise_preparation",
      "RAG",
      "English_Japanese_WordNet_LoRA",
      "local_bounded_fiXmArge_lexical_LoRA_experiment_completed_comparison_only"
    ],
    "verified_fix_sentence_model": false,
    "lexical_exercises_count_as_real_parallel_sentences": false
  },
  "WordNet_training": {
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
    "adapter_usage": "preserved_optional_not_default_runtime",
    "base_frozen": true,
    "merged_into_base": false,
    "base_files_before_after_sha256_equal": 12
  },
  "setup": {
    "python_min": "3.10",
    "training_python_recommended": "3.12",
    "training_dependencies": "requirements-train.txt",
    "empty_default_fix_training": "blocked_before_model_download",
    "inference_generation": "explicit_--generate_only",
    "default_model_access": "cache_only",
    "dry_run": "lookup_evidence_and_prompt_only_not_generated_translation"
  },
  "lexical_contract": {
    "full_input_single_headword_or_gloss_span_only": true,
    "target_language_senses_only": true,
    "reverse_alternatives": "retain_all_canonical_forms_for_same_span",
    "join_multiple_lookup_spans_into_sentence": false,
    "generation": "grounded_JSON_string",
    "generation_raw": "unchanged_model_text",
    "grounding": "correction_reasons_and_candidate_omissions",
    "alternatives": "per_span_candidates_and_sources",
    "conflicts_ambiguous_case_missing_target_partial_input": "translation_null_with_candidates"
  },
  "demo": {
    "URL": "http://127.0.0.1:7860",
    "layout": "input_and_result_side_by_side",
    "generation_button": "ConWas",
    "default_action": "dictionary_first_RAG",
    "dictionary_full_single_span": "all_direct_target_alternatives_without_model_generation",
    "no_fiXmArge_lexical_evidence": "Korean_query_rewrite_then_actual_dictionary_lookup_other_sources_abstain_without_final_translation_generation",
    "sentence_or_language_bridge": "cached_model_with_retrieved_dictionary_unverified_proposal",
    "fix_to_Korean_lexical_bridge": "actual_EN_JA_senses_to_Korean_paraphrases_separate_from_sentence_grammar_verification",
    "Korean_bridge_evidence": "source_evidence.korean_lexical_bridge_original_source_glosses_IDs_and_raw_output_preserved",
    "Korean_bridge_single_lexical_answer": "model_with_dictionary_korean_lexical_paraphrase_not_restored_Korean_dictionary",
    "Korean_bridge_sentence_answer": "machine_Korean_options_then_tentative_sentence_preserving_unknowns_conflicts_and_questions",
    "Korean_bridge_alignment_verified": false,
    "Korean_bridge_prompt": "Korean_instructions_general_water_example_no_dictionary_edit",
    "Korean_bridge_attempts": "at_most_two_after_schema_or_language_validation_failure_all_raw_attempts_preserved",
    "Korean_bridge_response_extraction": "complete_typed_object_before_at_most_three_extra_closing_delimiters_or_quotes_raw_json_valid_false_json_extraction_and_original_response_preserved",
    "Korean_bridge_extraction_rejects": "meaningful_trailing_text_second_JSON_unknown_IDs_and_non_Korean_output",
    "Korean_bridge_model_IDs": "short_g0_aliases_exact_model_id_map_to_original_entry_IDs",
    "Korean_related_gloss_support": "separate_shared_Japanese_gloss_English_hints_question_removed_lookup_marked_hypothesis_no_direct_sense_mutation",
    "Korean_bridge_runtime_validation": "expanded_dictionary_BF16_validation_pending",
    "dictionary_claims_answer": "single_fiXmArge_headword_direct_target_alternatives_with_⚠_no_model_original_contract_null_preserved_conflicts_resolved_false",
    "dictionary_import_registry": "configs/rag-dictionary-imports.json",
    "dictionary_import_CLI": "scripts/import_rag_dictionaries.py",
    "local_expanded_dictionary": "data/processed/rag-expanded-v1_397_entries_10_new_forms_10_Korean_fan_claim_entries",
    "expanded_dictionary_environment": "set_FIXMARGE_DATA_DIR_and_explicit_FIXMARGE_EXTERNAL_DIR_data/external",
    "source_claim_differences": "English_151_source_set_differences_not_new_correct_meanings_conflict_or_difference_entries_111_to_189",
    "current_validation_precision": "BF16_same_cached_base_weights_previous_NF4_smoke_not_a_controlled_precision_matched_comparison",
    "Korean_semantic_quality": "not_guaranteed_basic_lexical_errors_remain",
    "Korean_to_fix_indirect_retrieval": "model_EN_JA_lookup_queries_then_actual_fiXmArge_dictionary_candidates",
    "indirect_query_translation_and_source_alignment": "unverified_original_unmatched_spans_retained",
    "details": "closed_accordion",
    "details_fields": [
      "dictionary_evidence",
      "uncertainties",
      "raw_model_output",
      "korean_lexical_bridge",
      "korean_bridge_performed",
      "korean_bridge_attempts"
    ],
    "model_load": "first_request_requiring_model_then_reuse",
    "model_access": "cache_only",
    "standard_dictionary_languages": [
      "en",
      "ja"
    ],
    "Korean_dictionary_loaded": false,
    "expanded_fiXmArge_lexicon_Korean_fan_claim_entries": 10,
    "Korean_claims_are_official_dictionary": false,
    "Korean_translation_language_enabled": true,
    "standard_prompt_fields": [
      "definitions",
      "synonyms",
      "sources",
      "license_labels"
    ],
    "empty_standard_lookup": "explicit_empty_result_and_status",
    "fix_input_extra_queries": "recorded_en_ja_glosses",
    "fix_raw_input_WordNet_search": false,
    "English_spelling_policy": "fiXmArge_gloss_only_queries_prefer_exact_lemma_or_synonym_spelling_casefold_fallback_retained_natural_input_unchanged",
    "answer_source": ["dictionary", "dictionary_claims", "model_with_dictionary", "abstained"],
    "RAG_reference": "RAG.md",
    "standard_context_proves_new_fix_meaning_morphology_grammar": false,
    "model_standard_evidence_ids": "separate_from_model_domain_evidence_ids",
    "base_weights_changed": false,
    "sentence_grammar_alignment": "unverified",
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
    "prepare_space": "local_code_only_no_upload_no_data_no_weights_no_tokens",
    "host_cache_and_reviewed_dictionary": "separate_required_inputs"
  },
  "research_sentence_CLI": {
    "script": "scripts/test_sentence.py",
    "different_language_pairs": 12,
    "product_routes": 6,
    "natural_language_controls": "research_only_not_product_routes",
    "default": "dry_run_no_model_load",
    "generate": "cached_model_only_no_additional_download",
    "domain_state_for_natural_language_controls": "not_assessed",
    "empty_unknown_spans": "does_not_imply_all_words_verified",
    "reported_separately": [
      "sentence_proposal",
      "direct_lookup_segments",
      "unmatched_spans",
      "missing_target_senses",
      "source_conflicts",
      "unverified_grammar"
    ],
    "registered_output_word": "does_not_certify_grammar_word_order_or_source_alignment"
  },
  "data_paths": {
    "data/raw": "ignored_original_snapshots",
    "data/sources.json": "sources_fixed_revisions_rights_status",
    "data/curation": "ignored_local_source_corrections_machine_Korean_drafts_review_records_not_official",
    "data/processed/lexicon.jsonl": "canonical_forms_aliases_language_senses_readings_POS_etymology_hypotheses_sources",
    "data/processed/rules.jsonl": "explicit_source_rules_and_confidence",
    "data/processed/rag_documents.jsonl_and_rag.sqlite3": "RAG_transfer_documents",
    "data/training/train.jsonl_and_validation.jsonl": "eligible_only_current_zero_rows",
    "data/research/train_candidates.jsonl_and_validation_candidates.jsonl": "ignored_excluded_game_derived_lexical_rule_exercises",
    "data/external": "en_ja_originals_notices_normalized_JSONL_SQLite",
    "data/processed/report.json": "actual_counts_and_exclusions_not_hardcoded"
  },
  "source_snapshot": {
    "Hecate_CSV_rows": 331,
    "Hecate_unique_forms": 326,
    "Japanese_wordbook_rows": 337,
    "ZpDIC_entries": 363,
    "different_spellings": "not_forced_to_merge",
    "preserve": [
      "case",
      "middle_dot",
      "word_phrase_whitespace"
    ],
    "lookup_aliases": "separate",
    "reading_origin_field": "not_official_meaning_or_etymology_proof",
    "etymology_guess_status": "fan_hypothesis",
    "transcription_conflicts": [
      "Syu_Tain_開廷_vs_閉廷",
      "Commity_大紙_vs_大抵"
    ],
    "unresolved_conflicts": "RAG_with_sources_but_training_excluded"
  },
  "new_parallel_records": {
    "path": "data/raw/parallel.jsonl",
    "required_metadata": [
      "source_id",
      "document_id",
      "status",
      "rights_status"
    ],
    "example_placeholders": "not_training_data",
    "same_headword_both_directions": "same_split",
    "actual_sentences": "group_by_document",
    "lexical_holdout_and_sentence_evaluation": "separate",
    "unobtained_official_parallel": "not_fabricated"
  },
  "models": {
    "Qwen3_4B": "default_chat_context_for_dictionary_etymology_rules_uncertainty",
    "Qwen3_1_7B": "small_comparison",
    "MADLAD_400_3B_MT": "translation_candidate_T5_training_not_supported_by_Qwen_recipe",
    "fix_support_or_superior_translation": "not_established"
  },
  "publication": {
    "GitHub": "source_RAG_preparation_training_evaluation_publication_tools_source_list",
    "Hugging_Face": "old_WordNet_adapter_weights_model_card_evaluation_only",
    "raw_downloads_large_dictionaries_training_outputs_weights": "ignored",
    "new_fixmarge_adapter": "local_only_not_uploaded"
  },
  "validation": [
    "tokenizer_assistant_only_masking_and_length_before_GPU",
    "doctor_and_training_manifest_GPU_VRAM_versions"
  ],
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
python -m pip install -e .
python scripts/prepare_external_lexicons.py
python scripts/prepare_data.py
python -m fixmarge.infer --text "cat" --direction en-to-fix --dry-run
python scripts/train_qlora.py --config configs/train_qwen3_4b.json --dry-run
```

### 02

```powershell
python scripts/doctor.py --json
python scripts/train_qlora.py --config configs/train_qwen3_4b.json --run-training
```

### 03

```bash
python -m pip install -r requirements-demo.txt
python app.py
```

### 04

```bash
# 기본값은 근거·프롬프트만 확인하며 모델을 불러오지 않는다.
python scripts/test_sentence.py --source en --target fix --text "I want to know the truth."
# 이미 캐시된 모델로만 문장 제안을 생성한다. 추가 다운로드는 허용하지 않는다.
python scripts/test_sentence.py --source en --target fix --text "I want to know the truth." --generate
```

### 05

```powershell
python -m unittest discover -s tests -v
python scripts/train_qlora.py --config configs/train_qwen3_4b.json --dry-run
python scripts/train_qlora.py --config configs/train_qwen3_1_7b.json --dry-run
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "--generate",
    "fix-to-ko",
    "ko-to-fix",
    "fix-to-ja",
    "ja-to-fix",
    "fix-to-en",
    "en-to-fix",
    "lexical_contract",
    "generation",
    "generation_raw",
    "grounding",
    "alternatives",
    "translation: null",
    "http://127.0.0.1:7860",
    "python scripts/prepare_space.py --output runs/space-staging-new",
    "scripts/test_sentence.py",
    "ModelRunner",
    "ko",
    "en",
    "ja",
    "fix",
    "not_assessed",
    "data/raw/",
    "data/sources.json",
    "data/curation/",
    "data/processed/lexicon.jsonl",
    "data/processed/rules.jsonl",
    "data/processed/rag_documents.jsonl",
    "rag.sqlite3",
    "data/training/{train,validation}.jsonl",
    "data/research/{train_candidates,validation_candidates}.jsonl",
    "data/external/",
    "data/processed/report.json",
    "ヨミの由来",
    "fan_hypothesis",
    "Syu Tain",
    "Commity",
    "data/raw/parallel.jsonl",
    "source_id",
    "document_id",
    "status",
    "rights_status"
  ]
}
```

## 🔗 · WiD

- [↗ 01](../TODO.md)
- [↗ 02](SOURCES.md)
- [↗ 03](https://manosaba.com/guidelines)
- [↗ 04](https://huggingface.co/uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge)
- [↗ 05](WORDNET_LORA.md)
- [↗ 06](TRAINING.md)
- [↗ 07](VALIDATION.md)
- [↗ 08](../spaces/DEPLOY.cloud.md)
- [↗ 09](EXTERNAL_DICTIONARIES.md)
- [↗ 10](../spaces/DEPLOY.md)
- [↗ 11](../data/parallel.example.jsonl)
- [↗ 12](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [↗ 13](https://huggingface.co/Qwen/Qwen3-1.7B)
- [↗ 14](https://huggingface.co/google/madlad400-3b-mt)
- [↗ 15](../scripts/publish_adapter.py)

## ⚖️

[공식 가이드라인 제6항](https://manosaba.com/guidelines)(2026-10-21 갱신)이 공식 텍스트·음악·시나리오 등 공식 콘텐츠의 생성 AI·기계학습 학습 데이터 사용·제공을 금지한다고 명시합니다.

공개 RAG 사용도 별도 권리 확인 없이 허용됐다고 주장하지 않습니다.

프로젝트의 새 코드는 MIT입니다. 기본 모델은 각각의 Apache-2.0 조건을 유지합니다. [영일 사전의 고지 조건](EXTERNAL_DICTIONARIES.md)은 해당 자료에 적용됩니다.

공식 가이드라인 제6항의 학습 금지 때문에 게임 유래 후보는 학습 대상에서 제외합니다. 별도 허락을 받은 자료가 생기면 그 허락의 적용 범위를 기록해야 합니다. 팬 사전의 공개 접근 자체를 허락으로 간주하지 않습니다. 모델의 Apache-2.0 라이선스와 게임 유래 데이터의 이용 조건은 별개입니다. 공개 RAG를 포함한 팬 앱에는 같은 가이드라인 제9항 등 별도 조건도 적용됩니다.

[🧪 Coword](FIXMARGE_LORA.md)
