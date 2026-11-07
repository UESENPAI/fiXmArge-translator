# fiXmArge · ConWas

```json
{
  "checked": "2026-11-05",
  "eligible_fix_training_rows": 0,
  "sources": {
    "ZpDIC": {
      "entries": 363,
      "examples": 1,
      "lookup_scope": "introduction_some_lexemes_function_words_not_full_dump",
      "source_chain": "fan_wordbook_plus_official_setting_book",
      "attribution": "Re,AER_Acacia"
    },
    "Japanese_wordbook": {
      "rows": 337,
      "readme_available": true,
      "meaning_method": "OST_fix_ja_lyrics_and_word_order_inference",
      "etymology": "personal_hypothesis",
      "reading_origin": [
        "official_spelling",
        "heard_transcription",
        "spelling_guess"
      ]
    },
    "research_notebook_edition_2": {
      "bibliography_verified": true,
      "purchased_contents_obtained": false
    },
    "early_fan_wiki": {
      "word_construction": [
        "en_en",
        "ja_en",
        "en_ja"
      ],
      "imperative_Lee": "question_marked_early_hypothesis_not_confirmed_rule"
    },
    "Hecate2": {
      "CSV_columns": 7,
      "rows": 331,
      "forms": 326,
      "fields": [
        "ja",
        "zh",
        "en",
        "reading"
      ],
      "transcription_conflicts": true
    },
    "Bilibili_3_language_OST_subtitles": {
      "claimed_fix_ja_source": "official_OST_booklet",
      "subtitle_files_obtained": false,
      "parallel_candidates": "recorded_only"
    },
    "new_standard_witch_language": {
      "topic": [
        "nouns",
        "numbers",
        "pronouns"
      ],
      "status": "fan_vocabulary_etymology_hypotheses_not_official_grammar"
    },
    "TNOT_cover": {
      "Qwen3_use": "meaning_expansion_error_correction_punctuation_assistance",
      "published_trained_translation_model": false
    },
    "English_Reddit": "Japanese_parallel_and_ZpDIC_shared",
    "Chinese_translator_search": {
      "titles_found": true,
      "original_video_binary_code_verified": false
    },
    "official_OST": "fix_vocals_and_booklet_confirmed",
    "official_lyric_video_links": {
      "notice_found": true,
      "parallel_transcription_obtained": false
    },
    "downloadable_fix_translation_model_or_LoRA": "not_verified_in_searched_scope_not_global_absence_claim"
  },
  "fan_function_word_descriptions": {
    "Bah": "previous_word_emphasis",
    "oRei": "previous_word_imperative",
    "Iz'u": "copula",
    "oF_and_N'o": "possession_or_relation",
    "Nii": "multiple_negation_related_senses",
    "official_complete_grammar": false
  },
  "evaluation": {
    "real_parallel_samples": "data_processed_report_actual_value",
    "lexical_SFT_examples": "dictionary_derived_exercises",
    "actual_sentence_syntax_polysemy_omission_restoration": "additional_parallel_validation_required"
  },
  "source_rights_records": {
    "ZpDIC": "credits_original_rights_Re,AER_Acacia",
    "Hecate2": "separate_LICENSE_not_found",
    "Bilibili_3_language_OST_subtitles": "reuse_permission_not_obtained"
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
  },
  "eligible_fix_training_rows_scope": "unchanged_default_licensed_or_permission_gate_not_the_explicit_local_fact_experiment"
}
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "-Lee",
    "Bah",
    "oRei",
    "Iz'u",
    "oF",
    "N'o",
    "Nii",
    "real_parallel_samples"
  ]
}
```

## 🔗 · WiD

- [↗ 01](https://manosaba.com/guidelines)
- [↗ 02](https://zpdic.ziphil.com/dictionary/5729)
- [↗ 03](https://docs.google.com/spreadsheets/d/1ytGU7wmmOpmEegbIkkoFhcjkxeAKvC31B597HVFE9HI/edit)
- [↗ 04](https://isdn.jp/2784874501013)
- [↗ 05](https://w.atwiki.jp/manosaba/pages/21.html)
- [↗ 06](https://github.com/Hecate2/fiXmArge-dictionary)
- [↗ 07](https://www.bilibili.com/video/BV1CjshzuEBi/)
- [↗ 08](https://www.bilibili.com/opus/1142918534408437762)
- [↗ 09](https://www.bilibili.com/video/BV1NgW1z2Ehg/)
- [↗ 10](https://www.reddit.com/r/manosaba/comments/1uy3fei/fixmarge_translations/)
- [↗ 11](https://www.fwinc.co.jp/manosaba_CD/archives/983)
- [↗ 12](https://acacia-matome.com/news/2026-11-02-news)

## ⚖️

최종 갱신일은 2026-10-21이며 제6항은 공식 텍스트·음악·시나리오 등 공식 콘텐츠를 생성 AI·기계학습 학습 데이터로 사용하거나 제공하는 것을 금지한다고 명시한다. 제9항은 팬 게임·앱의 무료 제공, 비수익, 적법하게 처리한 자체/제3자 소재 등 조건도 둔다.

[🧪 Coword](FIXMARGE_LORA.md)
