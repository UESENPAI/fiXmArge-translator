# fiXmArge · sinruits

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
    "fix_training_performed": false,
    "sentence_translation_improvement": "not_demonstrated",
    "sentence_grammar_verified": false
  },
  "lexical_evaluation": {
    "script": "scripts/evaluate.py",
    "training_import": false,
    "optimizer_created": false,
    "backward_called": false,
    "weights_changed": false,
    "default": "dry_run_without_model_dependencies_or_weight_download",
    "default_dataset": "data/research/validation_candidates.jsonl",
    "override": "--dataset_PATH",
    "plain_and_RAG_selection": "same_first_valid_lexical_candidates",
    "rule_explanations_and_invalid_records": "reported_separately",
    "reports": "ignored_local_runs",
    "report_fields": [
      "prompts",
      "draft_references",
      "RAG_evidence",
      "rights_metadata",
      "generated_outputs"
    ],
    "per_direction_empty_selection": "zero_examples",
    "all_directions_one_model_process": "omit_--direction_and_raise_--limit",
    "model_loads_per_process": 1
  },
  "generation": {
    "explicit": "--generate",
    "downloads_default": false,
    "download_opt_in": "--allow-download",
    "known_model_revision": "configs_pinned_unless_--revision_override",
    "adapter": "optional_local_--adapter_PATH",
    "CPU": "--device_cpu_without_--load-in-4bit",
    "dependencies": "requirements-train.txt",
    "reverse_phrase_lookup": "snapshot_and_gloss_spelling_dependent"
  },
  "outputs": {
    "RAG_raw_output": "unchanged_model_text",
    "RAG_output": "dictionary_grounded_JSON",
    "plain_output": "unchanged_model_text",
    "output_source": {
      "generated_RAG": "dictionary_grounded",
      "generated_plain": "model",
      "dry_run": "none"
    },
    "raw_exact_reference_rate": "raw_model_response_metric",
    "exact_reference_rate": "displayed_output_metric_RAG_dictionary_consistency",
    "improved_grounded_metric_implies_model_translation_ability": false
  },
  "lexical_contract": {
    "translation": "one_lookup_span_covers_whole_input_except_outer_whitespace",
    "forward_sense_separator": "; ",
    "reverse_alternative_separator": " / ",
    "null_cases": [
      "source_conflict",
      "ambiguous_case_fallback",
      "missing_target_sense",
      "partial_input"
    ],
    "null_retains": "candidates_grouped_by_source_span",
    "external_WordNet_can_create_fix_candidate": false,
    "candidate_coverage": [
      "expected_alternatives",
      "raw_returned_alternatives",
      "missing_alternatives",
      "final_retained_alternatives"
    ],
    "legacy_exact_match": "accepts_individual_attested_reverse_alternative_cannot_detect_other_omissions",
    "model_analysis": "raw_unverified_claim",
    "legacy_exit_semicolon_go_out": "may_be_partial_lexical_input_format_limitation",
    "inference_raw_field": "generation_raw",
    "inference_grounded_field": "generation",
    "ModelRunner.generate": "raw_text",
    "ground_generation": "explicit_shared_grounding"
  },
  "metrics": {
    "references": "draft_dictionary_exercises_not_verified_sentence_translations",
    "plain_exact_draft_reference": "reference_excluded_from_prompt",
    "rag_exact_draft_reference": "retrieval_can_expose_reference_grounded_dictionary_consistency_only",
    "normalization": "case_and_punctuation_preserved_whitespace_trim_and_collapse",
    "punctuation_aliases": "explicit_opt_in_declared_apostrophe_middle_dot_equivalents",
    "reverse_references": "metadata.alternatives_or_full_recorded_answer",
    "BLEU": false,
    "sentence_quality_claim": false,
    "generalization_claim": false,
    "manual_review": [
      "draft_Korean_glosses",
      "conflicting_senses",
      "source_hypotheses"
    ]
  },
  "research_sentence_CLI": {
    "script": "scripts/test_sentence.py",
    "language_codes": [
      "ko",
      "en",
      "ja",
      "fix"
    ],
    "different_code_pairs": 12,
    "product_pairs": 6,
    "same_lexical_contract": false,
    "default": "dry_run",
    "generate": "cached_model_only_forced_offline_allow_download_False",
    "trains": false,
    "loads_LoRA": false,
    "proposal": "tentative",
    "source_evidence": "direct_lookup_not_model_claim",
    "reported_separately": [
      "dictionary_segments",
      "unmatched_spans",
      "missing_target_senses",
      "conflicts",
      "ambiguity"
    ],
    "unmatched": "no_direct_match_not_word_nonexistence",
    "grammar_word_order_negation_tense_alignment": "unverified_even_with_known_words",
    "natural_language_control_domain_status": "not_assessed",
    "fix_output_categories": [
      "direct_spelling_matches",
      "unsupported_output_runs",
      "explicit_UNRESOLVED_placeholders"
    ],
    "registered_output_form": "not_proof_of_source_translation",
    "raw_outputs_and_invented_evidence_IDs": "unverified_model_claims",
    "prompt_fields": "lexical_fields_and_row_references_only",
    "full_sentence_fan_notes": "excluded_from_prompt",
    "local_quoted_fix_sentence": "secondary_fan_provenance_not_official_verified_parallel",
    "sentence_accuracy_score": false,
    "base_weights_changed": false
  },
  "demo": {
    "layout": "input_result_side_by_side",
    "default_action": "generation",
    "details": "closed",
    "model_load": "first_request_then_reuse",
    "cache_only_default": true,
    "training_or_weight_changes": false,
    "standard_dictionary_helper": "standalone_existing_en_ja_WordNet_index",
    "prompt_field": "evidence.standard_dictionary",
    "prompt_content": [
      "definitions",
      "synonyms",
      "source_IDs",
      "license_labels"
    ],
    "empty_lookup": "explicit_empty_result",
    "fix_bridge_queries": "recorded_en_ja_glosses",
    "bridge_attests_fix_equivalence_etymology_grammar": false,
    "evidence_ID_fields": [
      "diagnostic.model_domain_evidence_ids",
      "diagnostic.model_standard_evidence_ids",
      "unsupported_evidence_ids"
    ],
    "known_ID": "provenance_check_not_sense_usage_verification",
    "Korean_dictionary": false,
    "Korean_output": "base_model_with_relevant_en_ja_context",
    "new_sentence_accuracy_claim": false,
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
    }
  }
}
```

## ⚙️ · ConWas

### 01

```powershell
python scripts/evaluate.py --dry-run --mode plain --limit 10
python scripts/evaluate.py --dry-run --mode rag --limit 10
```

### 02

```powershell
foreach ($direction in @('fix-to-ko','ko-to-fix','fix-to-ja','ja-to-fix','fix-to-en','en-to-fix')) {
    python scripts/evaluate.py --dry-run --mode plain --direction $direction --limit 10
    python scripts/evaluate.py --dry-run --mode rag --direction $direction --limit 10
}
```

### 03

```powershell
python scripts/evaluate.py --generate --mode plain --model Qwen/Qwen3-4B-Instruct-2507 --device auto --load-in-4bit --limit 10
python scripts/evaluate.py --generate --mode rag --model Qwen/Qwen3-4B-Instruct-2507 --device auto --load-in-4bit --limit 10
```

### 04

```powershell
python -m fixmarge.infer --text LaVI --direction fix-to-ko
python -m fixmarge.infer --text "법의 악마" --direction ko-to-fix
python -m fixmarge.infer --text LaVI --direction fix-to-ja
python -m fixmarge.infer --text "法の悪魔" --direction ja-to-fix
python -m fixmarge.infer --text LaVI --direction fix-to-en
python -m fixmarge.infer --text "demon of the law" --direction en-to-fix
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "scripts/evaluate.py",
    "data/research/validation_candidates.jsonl",
    "--dataset PATH",
    "runs/",
    "--direction",
    "--limit",
    "--allow-download",
    "configs/",
    "--revision",
    "--adapter PATH",
    "--device cpu",
    "--load-in-4bit",
    "requirements-train.txt",
    "--generate --model ...",
    "raw_output",
    "output",
    "output_source",
    "dictionary_grounded",
    "model",
    "none",
    "raw_exact_reference_rate",
    "raw_exact_reference",
    "exact_reference_rate",
    "exact_reference",
    "; ",
    " / ",
    "record.grounding.candidate_coverage",
    "exit; go out",
    "partial_lexical",
    "generation_raw",
    "generation",
    "ModelRunner.generate()",
    "ground_generation(lookup, raw_output)",
    "plain_exact_draft_reference",
    "rag_exact_draft_reference",
    "--punctuation-aliases",
    "metadata.alternatives",
    "scripts/test_sentence.py --source LANG --target LANG --text TEXT",
    "ko",
    "en",
    "ja",
    "fix",
    "--generate",
    "allow_download=False",
    "not_assessed",
    "[UNRESOLVED: ...]",
    "python app.py",
    "requirements-demo.txt",
    "standard_dictionary",
    "evidence.standard_dictionary",
    "diagnostic.model_domain_evidence_ids",
    "diagnostic.model_standard_evidence_ids",
    "wnja:",
    "oewn:",
    "unsupported_evidence_ids",
    "lexicon.jsonl",
    "rules.jsonl"
  ]
}
```

## 🔗 · WiD

- [↗ 01](EXTERNAL_DICTIONARIES.md)

## ⚖️

Source availability and recorded rights metadata are not permission for training or public redistribution.
