---
language:
- ko
- ja
- en
license: apache-2.0
base_model: Qwen/Qwen3-4B-Instruct-2507
library_name: peft
pipeline_tag: text-generation
tags:
- lora
- translation
- fixmarge
---
# fiXmArge · ConWas

```json
{
  "template_status": "TODO_not_a_published_training_claim",
  "project": "unofficial_fiXmArge_fan_project",
  "recipe_required": [
    "base_revision",
    "adapter_revision",
    "package_versions",
    "GPU",
    "max_length",
    "steps",
    "precision",
    "LoRA_settings",
    "seed",
    "GitHub_code_revision"
  ],
  "dataset_required": [
    "each_source",
    "exact_source_revision_hash",
    "permission_or_license_basis",
    "transformations",
    "uncertain_entries_excluded",
    "train_validation_group_counts"
  ],
  "task_types": [
    "lexical_QA",
    "reviewed_sentence_pairs",
    "synthetic_rule_examples"
  ],
  "evaluation_required": [
    "lexical_holdout_separate_from_independent_sentence_results",
    "RAG_enabled_disabled_and_access_to_heldout_glossary",
    "human_review_method",
    "unsupported_vocabulary_behavior",
    "known_failures"
  ],
  "unmeasured_quality_or_training_claims": false,
  "usage_required": [
    "exact_base_plus_adapter_command",
    "retrieval_data_version",
    "canonical_case_and_multiword_preservation"
  ],
  "limitations": [
    "invented_vocabulary",
    "reversed_possession",
    "confused_tense_or_negation"
  ],
  "uncertain_unregistered_terms_and_evidence": "must_surface",
  "definitive_official_dictionary": false
}
```

## ⚖️

The official game guidelines (https://manosaba.com/guidelines, section 6, updated 2026-10-21; checked 2026-11-05) prohibit using or providing the listed game assets, including scenario and text, as generative-AI/ML training data.

An Apache-2.0 base model license does not override this restriction. Do not publish an adapter trained from those candidates without an applicable independent permission basis.

Model license metadata does not grant rights to game materials or third-party dictionaries.

TODO: Include a copy of the reviewed Apache-2.0 base/model license and all applicable third-party attribution/NOTICE requirements. Document data conditions separately.

This is an unofficial fan project for fiXmArge in Magical Girl Witch Trials. It is not affiliated with Re,AER, Acacia, or the base model developers.
