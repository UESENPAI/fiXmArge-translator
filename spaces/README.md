---
title: fiXmArge · ConWas
emoji: "🧪"
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "5.49.1"
python_version: "3.12"
app_file: app.py
pinned: false
---
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
    "fix_training_performed": false,
    "sentence_translation_improvement": "not_demonstrated",
    "sentence_grammar_verified": false
  },
  "package": {
    "type": "private_code_preview",
    "contains": [
      "code",
      "pinned_direct_dependencies",
      "operator_documents",
      "licenses"
    ],
    "excludes": [
      "raw_dictionaries",
      "research_training_data",
      "model_weights",
      "LoRA",
      "curation",
      "logs",
      "credentials"
    ],
    "dictionary_connected_required": true,
    "Space_creation_upload_model_download_paid_hardware_selection": false
  },
  "model": {
    "base_frozen": true,
    "fix_training": false,
    "sentence_accuracy_or_free_12_direction_roundtrip": "not_validated",
    "load": "first_button_request",
    "default": "existing_host_cache_only",
    "FIXMARGE_ALLOW_MODEL_DOWNLOAD_1": "explicit_operator_model_download_only_no_dictionary_download_or_rights_change"
  },
  "UI": {
    "input_and_output": "first",
    "dictionary_evidence_and_uncertainty": "closed_details",
    "button_default": "model_sentence_proposal"
  },
  "resources": {
    "general_dictionary_languages": [
      "en",
      "ja"
    ],
    "Korean_dictionary": false,
    "data_and_notices_bundled": false,
    "operator_paths": [
      "FIXMARGE_DATA_DIR",
      "FIXMARGE_EXTERNAL_DIR",
      "HF_HOME",
      "FIXMARGE_MODEL"
    ],
    "actual_host_files_required": true,
    "WSL_files_auto_transferred": false,
    "tokens": "Space_Secrets_not_public_Variables_or_source"
  },
  "hosting_plan_price_hardware": "separate_account_review"
}
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "FIXMARGE_ALLOW_MODEL_DOWNLOAD=1",
    "FIXMARGE_DATA_DIR",
    "FIXMARGE_EXTERNAL_DIR",
    "HF_HOME",
    "FIXMARGE_MODEL"
  ]
}
```

## 🔗 · WiD

- [↗ 01](DEPLOY.md)
- [↗ 02](LICENSE)

## ⚖️

이 문서는 가공 언어 전체가 저작권으로 보호된다거나 모든 사용이 허용·금지된다고 결론 내리지 않습니다.

새 코드의 MIT 고지는 [LICENSE](LICENSE)에 있습니다. 이 고지는 별도 데이터나 모델의 이용 조건을 대신하지 않습니다.
