# fiXmArge · Coword · MeMe

## 🧪 · sinruits

| ⚑ | Qwen3-4B | LoRA v1 | LoRA v2 |
| :--- | :--- | :--- | :--- |
| `source_candidate_set_equal · train_seen` | `0/4` | `0/4` | `3/4` |
| `source_candidate_set_equal · heldout_test` | `0/8` | `0/8` | `0/8` |

```json
{
  "metric": "source_dictionary_candidate_set_equal",
  "translation_accuracy": null,
  "train_seen_is_unseen_generalization": false,
  "heldout_directional_probes": 8,
  "heldout_unique_families": 7,
  "source_dictionary_is_official_gold": false,
  "new_adapter_HF_upload": false
}
```

## Coword ↔ MeMe

| Coword | → | MeMe | Qwen3-4B | LoRA v1 | LoRA v2 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `niNeEr` | `fix-to-ja` | `兄` | `niNeEr` | `九` | `兄` |
| `笑う` | `ja-to-fix` | `LaLau` | `笑う / smile, to laugh` | `hAa` | `LaLau` |
| `tone wachi` | `fix-to-en` | `eleven` | `tone wachi / tone-wachi` | `tone` | `twelve` |
| `wait a moment` | `en-to-fix` | `wE-MitTa` | `wait a moment` | `WaiT` | `wE-MitTa` |

## ⚙️ · ⚠

```json
{
  "executed_optimizer_steps": {
    "v1": 128,
    "v2": 192
  },
  "selected_weight_lineage": [
    {
      "phase": "v1",
      "selected_checkpoint_step": 128
    },
    {
      "phase": "v2",
      "selected_checkpoint_step": 96
    }
  ],
  "selected_lineage_update_count": 224,
  "validation_losses": {
    "original_base": {
      "fix": 11.098934173583984,
      "wordnet": 5.309939384460449
    },
    "v1_selected": {
      "fix": 3.254272699356079,
      "wordnet": 1.9898017644882202
    },
    "v2_selected": {
      "fix": 4.049633026123047,
      "wordnet": 2.123688220977783
    }
  },
  "tradeoff": {
    "train_seen_source_agreement_improved": true,
    "heldout_source_agreement_improved": false,
    "v2_selected_fix_validation_loss_worse_than_v1": true,
    "v2_selected_WordNet_validation_loss_worse_than_v1": true,
    "interpretation": "better_seen_mapping_fit_with_worse_validation_loss_consistent_with_overfitting",
    "blanket_quality_improvement_established": false
  },
  "protected_files_sha256_unchanged": {
    "original_base": 12,
    "wordnet_adapter": 15,
    "phase1_fix_adapter": 16
  },
  "merge_performed": false
}
```

## ConWas · MeMe

| Coword | → | Qwen3-4B | LoRA v1 | LoRA v2 |
| :--- | :--- | :--- | :--- | :--- |
| `The cat is sleeping.` | `en-to-ja` | `猫は寝ています。` | `猫は寝ています` | `猫が寝ている` |
| `I have two books.` | `en-to-ja` | `私は2冊の本を持っています。` | `私は2冊の本を持っています` | `私は2冊の本を持っている` |
| `これは本です。` | `ja-to-en` | `This is a book.` | `This is a book.` | `This is a book.` |
| `猫が寝ています。` | `ja-to-en` | `The cat is sleeping.` | `The cat is sleeping.` | `The cat is sleeping.` |

```json
{
  "reviewed_general_controls": 4,
  "observed_meaning_loss_in_these_controls": 0,
  "Japanese_register_and_style_drift": true,
  "global_quality_preservation_established": false,
  "reference_string_mismatch_is_not_semantic_regression": true,
  "sentence_comparison": {
    "status": "completed",
    "independent_sentences": 1,
    "target_directions": 3,
    "official_parallel_reference": false,
    "source": "secondary_fan_wordbook_quote",
    "full_sentence_supervised": false,
    "trained_source_token": "riEl",
    "excluded_source_tokens": [
      "sINeEy",
      "Iz'u",
      "Nii"
    ],
    "riEl_direct_JA_senses": [
      "帰る"
    ],
    "riEl_direct_EN_senses": [],
    "base_schema_valid_cases": "3/3",
    "v2_schema_valid_cases": "1/3",
    "raw_unparsed_outputs_are_not_valid_translations_under_the_JSON_contract": true,
    "sentence_translation_improvement_demonstrated": false,
    "local_demo_adapter": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "v2_default_enabled": false,
    "v2_HF_upload": false
  }
}
```

[{} · MeMe](fixmarge-lora-training.json) · [⚙️ ConWas](../scripts/evaluate_fixmarge_adapter.py)

## 🧪 · ConWas · ⚠

> sINeEy Iz'u Nii riEl

| → | Qwen3-4B · MeMe | JSON | LoRA v2 · MeMe/raw | JSON |
| :--- | :--- | :--- | :--- | :--- |
| `fix-to-ja` | `姉は違う` | `true` | `raw_unparsed_text · 姉は帰る` | `false` |
| `fix-to-en` | `Sister is not different` | `true` | `tentative_translation_field · is not sister` | `true` |
| `fix-to-ko` | `null` | `true` | `raw_unparsed_text · 다른가` | `false` |

```json
{
  "sentence_observations": {
    "japanese_raw_return_sense_expressed": true,
    "japanese_raw_negation_expressed": false,
    "japanese_raw_is_valid_JSON_contract": false,
    "Korean_raw_is_valid_JSON_contract": false,
    "English_and_Korean_sentence_reliability_established": false,
    "sentence_grammar_verified": false,
    "source_to_output_alignment_verified": false,
    "sentence_translation_improvement_demonstrated": false,
    "JSON_contract_regression_observed": true
  },
  "source_provenance": {
    "source": "secondary_fan_wordbook",
    "file": "data/raw/japanese_wordbook.xlsx",
    "sha256": "2b29b1cf34e13da278f5c563c5fdcd6ef12fbd8c69252df24d1c1391cd646605",
    "sheet": "単語帳",
    "cell": "G273",
    "linked_primary_url": "https://www.youtube.com/watch?v=AIeAZ_qtdJ4",
    "primary_snapshot_present": false,
    "official_parallel_translation_present": false,
    "fan_interpretation_in_prompt": false
  },
  "deployment_decision": {
    "local_demo_adapter": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "retained_existing_WordNet_demo_adapter": true,
    "new_trained_v2_saved_locally": true,
    "new_trained_v2_enabled_by_default": false,
    "new_trained_HF_upload_performed": false,
    "basis": [
      "sentence_JSON_contract_regression",
      "sentence_gain_not_demonstrated"
    ],
    "base_model_files_or_existing_adapters_overwritten": false
  }
}
```

## ⚙️ · ConWas

```bash
export HF_HOME=/home/user/.cache/codex-dev/huggingface
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
.venv/bin/python scripts/evaluate_fixmarge_adapter.py \
  --train data/training/fixmarge-wordnet-v2/train.jsonl \
  --test data/training/fixmarge-wordnet-v2/test.jsonl \
  --adapter artifacts/qwen3-4b-fixmarge-wordnet-lora-v2 \
  --generate --max-new-tokens 32 \
  --output runs/fixmarge-wordnet-lora-2026-11-07/lexical-comparison-v2-repro.json
.venv/bin/python scripts/compare_fixmarge_sentences.py \
  --adapter artifacts/qwen3-4b-fixmarge-wordnet-lora-v2 \
  --generate --max-new-tokens 384 \
  --output runs/fixmarge-wordnet-lora-2026-11-07/sentence-comparison-v2-repro.json
```
