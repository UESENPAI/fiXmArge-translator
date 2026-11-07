"""Pinned adapter bootstrap for the separately enabled Hugging Face Space."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ADAPTER_REPO = 'uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge'
ADAPTER_REVISION = 'c17943bf523779fb2dd75078148a50816dd52ed7'
BASE_MODEL = 'Qwen/Qwen3-4B-Instruct-2507'
BASE_REVISION = 'cdbee75f17c01a7cc42f958dc650907174af0554'
ADAPTER_FILES = ['adapter_config.json', 'adapter_model.safetensors', 'training_manifest.json',
                 'README.md', 'LICENSE', 'NOTICE']


def prepare_cloud_adapter(*, snapshot_loader=None) -> Path:
    """Fetch only the pinned adapter; Hub authentication comes from Space Secrets."""
    if snapshot_loader is None:
        from huggingface_hub import snapshot_download
        snapshot_loader = snapshot_download
    try:
        directory = Path(snapshot_loader(repo_id=ADAPTER_REPO, revision=ADAPTER_REVISION,
                                          allow_patterns=ADAPTER_FILES))
    except Exception as exc:
        raise ValueError('The pinned cloud adapter could not be fetched.') from exc
    try:
        config = json.loads((directory / 'adapter_config.json').read_text(encoding='utf-8'))
        manifest = json.loads((directory / 'training_manifest.json').read_text(encoding='utf-8'))
        valid = (config.get('peft_type') == 'LORA' and config.get('base_model_name_or_path') == BASE_MODEL
                 and config.get('revision') == BASE_REVISION
                 and manifest.get('training_status') == 'completed'
                 and manifest.get('optimizer_steps') == 256
                 and manifest.get('base_frozen') is True and manifest.get('adapter_only') is True
                 and manifest.get('merge_performed') is False)
        if not valid:
            raise ValueError('The cloud adapter does not match the reviewed training release.')
        digest = hashlib.sha256()
        with (directory / 'adapter_model.safetensors').open('rb') as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != manifest.get('adapter_sha256'):
            raise ValueError('The cloud adapter weight hash differs from its training manifest.')
    except (OSError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError('The pinned cloud adapter is incomplete or invalid.') from exc
    return directory
