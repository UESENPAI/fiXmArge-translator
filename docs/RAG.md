# fiXmArge · Coword · MeMe

```json
{
  "strategy": "dictionary_first_RAG",
  "routes": [
    "fix-to-ko",
    "ko-to-fix",
    "fix-to-ja",
    "ja-to-fix",
    "fix-to-en",
    "en-to-fix"
  ],
  "same_language_and_natural_language_only_routes": "blocked",
  "dictionary": {
    "fiXmArge": [
      "data/processed/lexicon.jsonl",
      "data/processed/rules.jsonl"
    ],
    "canonical_spellings_aliases_source_references": "preserved",
    "conflicting_alternatives": "retained_not_resolved_by_automatic_selection",
    "missing_direct_target_sense": "distinct_from_unknown_source_word",
    "WordNet": "existing_local_English_Japanese_index_only",
    "Korean_dictionary": "no_external_Korean_dictionary_10_unreviewed_Korean_fan_claim_entries_in_expanded_fiXmArge_lexicon",
    "grammar_or_sentence_alignment_verified": false,
    "active_local_expansion": "data/processed/rag-expanded-v1",
    "original_processed_and_raw": "preserved_without_overwrite",
    "source_and_review_rights_ID_group_and_existing_meanings": "preserved"
  },
  "answer_flow": [
    {
      "when": "full_input_single_lexical_span_with_non_null_lexical_contract_expected_translation",
      "answer_source": "dictionary",
      "output": "all_direct_target_alternatives",
      "generation_performed": false,
      "model_load_required": false,
      "sentence_verified": false
    },
    {
      "when": "fiXmArge_source_single_lexical_span_with_direct_target_senses_and_only_source_conflict_abstention",
      "answer_source": "dictionary_claims",
      "answer_kind": "unresolved_dictionary_alternatives",
      "result_field": "dictionary_claims_answer",
      "output": "all_recorded_target_alternatives_with_warning_marker_⚠",
      "case_ambiguity_or_question_mark_in_target_candidates": "excluded",
      "original_lexical_contract_null": "preserved",
      "conflicts_resolved": false,
      "source_review_verified": false,
      "generation_performed": false
    },
    {
      "when": "Korean_to_fiXmArge_with_no_direct_lexical_segments",
      "stage_1": "cached_model_rewrites_Korean_as_Japanese_English_lookup_queries",
      "query_limits": {
        "queries": 8,
        "characters_per_query": 80
      },
      "stage_2": "actual_reverse_lookup_of_each_query_in_existing_fiXmArge_dictionary",
      "generated_fiXmArge_forms_accepted_as_retrieval_evidence": false,
      "evidence_field": "source_evidence.indirect_dictionary",
      "raw_query_output": "preserved",
      "query_rewrite_performed": true,
      "query_translation_verified": false,
      "output_source_alignment_verified": false,
      "original_unmatched_source_spans": "retained_not_counted_as_direct_coverage"
    },
    {
      "when": "no_direct_fiXmArge_segments_and_no_indirect_dictionary_entries_after_optional_Korean_query_bridge",
      "answer_source": "abstained",
      "abstention_reason": "no_fiXmArge_dictionary_evidence",
      "final_translation_generation": "skipped",
      "model_generation_for_query_rewriting": "Korean_bridge_may_have_occurred_recorded_separately",
      "WordNet_only_evidence_authorizes_new_fiXmArge_vocabulary": false
    },
    {
      "when": "fiXmArge_to_Korean_without_direct_Korean_answer_and_with_retrieved_EN_JA_senses",
      "task": "retrieved_Japanese_English_senses_to_Korean_lexical_paraphrases_separate_from_fiXmArge_sentence_verification",
      "evidence_field": "source_evidence.korean_lexical_bridge",
      "source_fields": "original_entry_EN_JA_senses_short_model_ID_alias_conflict_question_flags_and_separate_related_English_hints",
      "response_schema": {
        "glosses": [
          {
            "entry_id": "g0_from_supplied_aliases",
            "korean": [
              "Korean_lexical_equivalent"
            ]
          }
        ]
      },
      "limits": {
        "entries": 32,
        "alternatives_per_entry": 16,
        "characters_per_alternative": 80
      },
      "validation": "known_entry_IDs_unique_entries_exact_response_fields_nonempty_Hangul_containing_strings",
      "original_Korean_dictionary_senses": "unchanged",
      "machine_generated": true,
      "gloss_alignment_verified": false,
      "single_lexical_complete_nonconflicting_not_explicitly_uncertain_answer": {
        "answer_source": "model_with_dictionary",
        "answer_kind": "korean_lexical_paraphrase",
        "result_field": "korean_bridge_answer",
        "second_sentence_generation": "skipped",
        "direct_dictionary_answer": false,
        "lexical_generation": "one_gloss_stage_with_at_most_two_strictly_validated_attempts",
        "source_conflict_alternatives": "also_allowed_when_all_required_IDs_covered_at_least_two_distinct_Korean_options_and_no_explicit_question_or_case_ambiguity_source_conflict_IDs_retained_conflicts_resolved_false",
        "conflicts_resolved": false
      },
      "multiple_segments_conflicts_or_explicit_uncertainty": "Korean_options_supplied_to_separate_tentative_sentence_generation",
      "invalid_or_empty_bridge": {
        "answer_source": "abstained",
        "abstention_reason": "korean_gloss_bridge_unavailable"
      },
      "raw_bridge_output": "preserved_not_fabricated_as_a_sentence_response",
      "source_conflicts_unknown_spans_and_grammar_unverified": "preserved",
      "prompt_language": "Korean_instructions_with_general_水_water_to_물_example_for_language_and_schema",
      "generation_attempts": {
        "maximum": 2,
        "retry_when": "typed_schema_or_Korean_language_validation_fails_after_allowed_complete_object_extraction",
        "valid_empty_glosses": "no_retry_and_abstain",
        "attempts_field": "source_evidence.korean_lexical_bridge.attempts",
        "raw_outputs_and_validation_status": "all_attempts_preserved",
        "accepting_English_copy_as_Korean": false,
        "response_extraction_policy": {
          "complete_JSON": "raw_json_valid_true_json_extraction_complete_json",
          "complete_object_followed_only_by_1_to_3_extra_closing_delimiters_or_quotes": "typed_payload_extracted_without_changing_content",
          "extracted_payload_status": "raw_json_valid_false_json_extraction_complete_object_before_extra_closing_delimiters",
          "trailing_text_second_JSON_unknown_IDs_or_non_Korean_values": "rejected",
          "raw_output": "preserved_verbatim",
          "schema_valid_true_is_valid_raw_JSON_or_verified_semantics": false
        }
      },
      "model_IDs": "short_g0_aliases_mapped_exactly_to_original_IDs_with_model_id_map_unknown_IDs_rejected",
      "related_English_support": {
        "field": "source_evidence.korean_related_gloss_support",
        "relation": "shared_Japanese_gloss_retrieves_other_entry_English_senses",
        "terminal_question_mark_removed_for_lookup": "separate_query_is_hypothesis_true",
        "direct_English_senses_including_empty_arrays": "unchanged",
        "entry_equivalence_or_alignment_verified": false
      }
    },
    {
      "when": "sentence_partial_lookup_conflict_or_language_bridge_with_direct_or_indirect_dictionary_evidence",
      "answer_source": "model_with_dictionary",
      "generation": "cached_frozen_model_with_retrieved_lexical_evidence",
      "unsupported_content": "prompt_requires_unresolved_spans_output_audit_does_not_verify_semantic_alignment",
      "language_bridge": "machine_paraphrase_of_supplied_EN_JA_gloss_not_restored_reference",
      "sentence_verified": false
    }
  ],
  "retrieval_changes": {
    "fiXmArge_raw_input_as_English_Japanese_WordNet_query": false,
    "fiXmArge_gloss_bridges": "all_recorded_EN_JA_senses_with_source_entry_ID_reasons_within_bounded_query_limits",
    "English_exact_spelling": "fiXmArge_gloss_only_query_reasons_prefer_NFC_exact_lemma_or_synonym_spelling_when_available",
    "English_case_only_candidates": "bridge_only_queries_exclude_proven_case_only_matches_if_exact_spelling_available",
    "English_casefold_fallback": "retain_when_no_exact_spelling_candidate",
    "examples": {
      "riEl": "no_raw_fiXmArge_to_Cambodian_currency_query",
      "no": "ordinary_lowercase_candidates_before_capitalized_No_chemical_candidates",
      "No": "natural_input_retains_casefold_alternatives_including_negation_and_chemical_senses_not_automatic_chemical_selection",
      "CAT_and_STRASSE": "casefold_fallback_retained"
    },
    "synonym_and_indexed_alias_matches": "retained",
    "WordNet_meanings_prove_fiXmArge_equivalence": false,
    "etymology_hints_in_lexical_research_lookup": "separate_hypotheses_not_sentence_translation_evidence",
    "natural_English_input": "retain_normal_casefold_candidates_capitalized_No_may_be_sentence_initial_negation"
  },
  "presentation": {
    "primary": "input_and_result_side_by_side",
    "details": "closed_accordion",
    "details_include": [
      "answer_source",
      "generation_performed",
      "dictionary_candidates_and_sources",
      "source_conflicts",
      "unmatched_source_spans",
      "missing_target_senses",
      "grammar_unverified",
      "model_uncertainties",
      "raw_model_output_when_generated",
      "query_rewrite_performed",
      "indirect_dictionary_entries",
      "raw_query_output_when_rewritten",
      "model_indirect_evidence_ids",
      "korean_bridge_performed",
      "korean_bridge_schema_valid",
      "korean_bridge_answer_when_single_lexical",
      "raw_Korean_bridge_output",
      "original_EN_JA_glosses_and_machine_Korean_alternatives",
      "korean_bridge_attempts_and_raw_outputs",
      "dictionary_claims_answer_and_unresolved_source_alternatives",
      "raw_json_valid_and_json_extraction",
      "model_id_map",
      "korean_related_gloss_support"
    ],
    "direct_dictionary_answer_is_verified_sentence_translation": false,
    "registered_output_spelling_proves_source_alignment": false
  },
  "model": {
    "base_model": "Qwen/Qwen3-4B-Instruct-2507",
    "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
    "default_adapter": null,
    "runtime_profile": "local_original_base_RAG",
    "cloud_bootstrap": "historical_pinned_WordNet_adapter_profile_not_deployed",
    "optional_adapter_selection": "explicit_FIXMARGE_ADAPTER_PATH",
    "original_base_and_existing_LoRA_artifacts": "preserved_not_merged",
    "new_training_performed": false,
    "additional_model_download": false,
    "dictionary_first_default": true,
    "research_opt_out": "DemoService(dictionary_first=False)_explicit_model_diagnostic",
    "research_sentence_CLI": "scripts/test_sentence.py_retains_explicit_generation_diagnostics",
    "current_validation_precision": "BF16",
    "previous_smoke_precision": "NF4_4bit",
    "precision_change": "same_cached_backbone_revision_and_weight_files_different_runtime_precision_no_LoRA_no_training_no_model_download",
    "quality_gain_from_code_alone": "not_established_precision_and_dictionary_changed"
  },
  "validation": {
    "latest_report": "../reports/forward-rag-dictionary-update.json",
    "latest_runtime_cases": 10,
    "latest_Gradio_API_cases": 5,
    "protected_original_files_SHA256_unchanged": 48,
    "status": "completed_forward_RAG_smoke_remaining_translation_errors_recorded",
    "new_regression_suites": [
      "tests/test_dictionary_first_rag.py",
      "tests/test_korean_retrieval.py",
      "tests/test_korean_gloss_bridge.py",
      "tests/test_dictionary_import.py"
    ],
    "previous_smoke": {
      "tests_passed": 266,
      "Gradio_API_cases_passed": 3,
      "local_demo": "http://127.0.0.1:7860/",
      "details_accordion_closed": true,
      "protected_files_sha256_unchanged": 48,
      "model_HTTP_attempts": [],
      "report": "../reports/dictionary-rag-smoke.json",
      "sentence_translation_accuracy": "not_established",
      "unmatched_spans_empty_means_complete_grammar_or_semantics": false
    },
    "sentence_translation_accuracy": "not_established",
    "unmatched_spans_empty_means_complete_grammar_or_semantics": false,
    "latest_unit_tests_passed": 295,
    "observed_Korean_quality_limits": [
      "sister_can_be_paraphrased_as_형",
      "older_sister_can_be_copied_in_English_and_rejected_by_language_validation"
    ]
  },
  "current_change_scope": {
    "directions": [
      "fix-to-ko",
      "fix-to-ja",
      "fix-to-en"
    ],
    "reverse_direction_changes": "excluded_existing_HEAD_behavior_retained",
    "new_source_dictionary_entries": "10_added_forms_and_10_existing_form_Korean_source_claim_entries_in_separate_local_output_not_verified_new_translation_facts"
  },
  "ingestion": {
    "registry": "configs/rag-dictionary-imports.json",
    "CLI": "scripts/import_rag_dictionaries.py",
    "formats": [
      "csv",
      "claims_json"
    ],
    "inputs": "existing_local_source_snapshots_with_pinned_SHA256",
    "output": "new_exclusive_standalone_lexicon_and_rules_directory_existing_output_rejected",
    "network_or_model_or_training_used": false,
    "snapshot_counts": {
      "base_entries": 387,
      "expanded_entries": 397,
      "new_canonical_forms": 10,
      "Korean_claim_entries_before": 0,
      "Korean_claim_entries_after": 10,
      "Asankilp_csv_records": 264,
      "Asankilp_skipped_section_labels": 1,
      "Asankilp_lexical_rows": 263,
      "Asankilp_distinct_forms": 262,
      "English_source_claim_set_differences": 151,
      "unresolved_conflict_or_claim_difference_entries_before": 111,
      "unresolved_conflict_or_claim_difference_entries_after": 189
    },
    "source_claim_differences": "unresolved_differences_between_source_sense_sets_not_counts_of_new_correct_meanings_or_verified_contradictions",
    "source_review_or_publication_clearance_granted": false,
    "manifest": "data/processed/rag-expanded-v1/import_manifest.json",
    "selection": {
      "FIXMARGE_DATA_DIR": "absolute_path_to_data/processed/rag-expanded-v1",
      "FIXMARGE_EXTERNAL_DIR": "absolute_path_to_data/external",
      "external_directory": "set_explicitly_nested_output_parent_inference_does_not_locate_existing_WordNet_index"
    }
  }
}
```

## ⚙ · ConWas

```bash
.venv/bin/python scripts/import_rag_dictionaries.py --registry configs/rag-dictionary-imports.json --output data/processed/rag-expanded-rebuild-v1

FIXMARGE_DATA_DIR="$PWD/data/processed/rag-expanded-rebuild-v1" \
FIXMARGE_EXTERNAL_DIR="$PWD/data/external" \
FIXMARGE_ADAPTER_PATH= FIXMARGE_CLOUD=0 FIXMARGE_DEVICE=cuda \
FIXMARGE_LOAD_IN_4BIT=0 FIXMARGE_ALLOW_MODEL_DOWNLOAD=0 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
.venv/bin/python app.py
```

## 🔗 · WiD

- [📖 MeMe](README.ko.md)
- [🔎 Coword](EXTERNAL_DICTIONARIES.md)
- [🧪 Coword](FIXMARGE_LORA.md)
- [⚖️ LICENSE](../LICENSE)
