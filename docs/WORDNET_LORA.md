# fiXmArge · ConWas

```json
{
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
  "training": {
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
  "corpus": {
    "input": "existing_data/external_only",
    "output": "data/training/wordnet-en-ja-v1",
    "excluded": [
      "fiXmArge",
      "Korean",
      "lyrics",
      "model_generated_targets"
    ],
    "tasks": {
      "JWN_1_1_en_to_ja": [
        1024,
        64,
        64
      ],
      "JWN_1_1_ja_to_en": [
        1024,
        64,
        64
      ],
      "JWN_1_1_ja_definition": [
        1024,
        64,
        64
      ],
      "OEWN_2025_en_definition": [
        1024,
        64,
        64
      ]
    },
    "JWN_alignment": "same_original_PWN3_synset_only",
    "JWN_context": [
      "POS",
      "definition"
    ],
    "target_alternatives": "all_retained",
    "overlong_definitions_or_candidate_sets": "excluded_with_manifest_reasons",
    "reverse_and_ja_definition": "same_synset_group_same_split",
    "OEWN_group": "exact_signature_original_definition_POS_full_synonym_set",
    "OEWN_group_is_recovered_synset_ID": false,
    "cross_version_JWN_OEWN_synset_alignment": false,
    "group_overlap_across_splits": 0,
    "identical_chat_overlap_across_splits": 0,
    "lemma_overlap_and_homonyms_across_other_synsets_or_sources": "possible",
    "lemma_disjoint_evaluation": false
  },
  "adapter_safety": {
    "trainable": "lora_*_only",
    "output_cache_overlap": "reject",
    "save": "PEFT_adapter_only",
    "merge_into_base": false
  },
  "offline_reproduction": {
    "requires": [
      "existing_project_environment",
      "existing_model_cache",
      "prepared_WordNet_originals"
    ],
    "new_output_paths": "do_not_overwrite_existing_artifacts"
  },
  "artifact_files": [
    "training_manifest.json",
    "evaluation.json",
    "adapter_model.safetensors",
    "adapter_config.json"
  ],
  "observed_generation": {
    "record": "runs/wordnet-lora-2026-11-06/adapter-comparison.json",
    "general_self_authored_sentence_cases": 4,
    "base_vs_adapter_raw_outputs_equal": 4,
    "general_translation_quality_guaranteed": false,
    "rare_word_and_definition_errors": "persist",
    "x-ray_machine": {
      "reference_candidate": "レントゲン撮影機",
      "reference_present": true,
      "extra_candidate_repetition": true,
      "truncated_at_new_tokens": 96
    },
    "validation_loss_reduction_implies_sentence_improvement": false
  },
  "inference_adapter_selection": [
    "FIXMARGE_ADAPTER_PATH",
    "--adapter"
  ],
  "return_to_base": [
    "unset_FIXMARGE_ADAPTER_PATH_and_restart_demo",
    "omit_--adapter_from_CLI"
  ],
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
  }
}
```

## ⚙️ · ConWas

### 01

```bash
source .venv/bin/activate
export HF_HOME=/home/user/.cache/codex-dev/huggingface
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
python scripts/prepare_wordnet_training.py --output data/training/wordnet-en-ja-v1-repro
python scripts/train_qlora.py --config configs/train_qwen3_4b_wordnet_lora.json \
  --train data/training/wordnet-en-ja-v1-repro/train.jsonl \
  --validation data/training/wordnet-en-ja-v1-repro/validation.jsonl \
  --output artifacts/qwen3-4b-wordnet-en-ja-lora-repro --run-training
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "data/external",
    "data/training/wordnet-en-ja-v1",
    "manifest.json",
    "lora_*",
    "NOTICE.txt",
    "licenses/",
    "2e-5",
    "checkpoint-256",
    "artifacts/qwen3-4b-wordnet-en-ja-lora-v1/training_manifest.json",
    "evaluation.json",
    "adapter_model.safetensors",
    "adapter_config.json",
    "c17943bf523779fb2dd75078148a50816dd52ed7",
    "runs/wordnet-lora-2026-11-06/adapter-comparison.json",
    "x-ray_machine",
    "レントゲン撮影機",
    "FIXMARGE_ADAPTER_PATH",
    "--adapter",
    "unset FIXMARGE_ADAPTER_PATH"
  ]
}
```

## 🔗 · WiD

- [↗ 01](../scripts/prepare_wordnet_training.py)
- [↗ 02](EXTERNAL_DICTIONARIES.md)
- [↗ 03](https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/LICENSE.md)
- [↗ 04](../configs/train_qwen3_4b_wordnet_lora.json)
- [↗ 05](https://huggingface.co/uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge)
- [↗ 06](https://huggingface.co/uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge/commit/c17943bf523779fb2dd75078148a50816dd52ed7)

## ⚖️

기본 Qwen은 **Apache-2.0**입니다. 원자료는 [Japanese WordNet 자체 고지와 Princeton WordNet](EXTERNAL_DICTIONARIES.md), [OEWN CC BY 4.0과 기반 WordNet](https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/LICENSE.md) 조건을 각각 유지합니다. 모델·어댑터의 배포 조건과 데이터의 출처 표시·고지 조건을 함께 확인합니다. 코퍼스의 `NOTICE.txt`, `licenses/` 네 고지문, 사전 원본·정규화 파일의 전체 해시와 변환 설명을 보존합니다.

## 🧪 · sinruits

```bash
python scripts/compare_fixmarge_sentences.py --generate --output runs/fixmarge-sentence-comparison-2026-11-07/results.json
```

[🧪 MeMe](../reports/fixmarge-sentence-comparison.md)
