#!/usr/bin/env python3
"""Validate a fiXmArge corpus, then optionally train a local QLoRA adapter.

The default path is offline and imports only the Python standard library.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fixmarge.lexical_facts import LOCAL_FACT_RIGHTS, validate_local_fact_record

LOCAL_FACT_SCOPE = "local_fixmarge_lexical_facts_and_licensed_en_ja_wordnet"
WORDNET_SOURCES = {"wnja:1.1", "oewn:2025"}
WORDNET_TASKS = {"wordnet_translation", "wordnet_definition"}
LORA_TARGETS = {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
ALLOWED_MODELS = {"Qwen/Qwen3-4B-Instruct-2507", "Qwen/Qwen3-1.7B"}
CONTROL_TOKENS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>", "<think>", "</think>")


APPROVED_RIGHTS = {"self_authored", "open_license", "permission_granted"}


def load_jsonl(path: Path, allow_empty: bool = False) -> list[dict]:
    records = []
    with path.open(encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                validate_record(record)
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
            records.append(record)
    if not records and not allow_empty:
        raise ValueError(f"Empty dataset: {path}")
    return records


def validate_record(record: dict) -> None:
    if not isinstance(record, dict):
        raise ValueError("Each row must be an object")
    messages = record.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    roles = [m.get("role") if isinstance(m, dict) else None for m in messages]
    if roles not in (["user", "assistant"], ["system", "user", "assistant"]):
        raise ValueError("Supported roles: optional system, user, final assistant (single turn)")
    for message in messages:
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Every message requires non-empty string content")
        if any(token in content for token in CONTROL_TOKENS):
            raise ValueError("Raw chat control tokens are not allowed inside content")
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("metadata is required")
    for key in ("group_id", "source", "status", "task"):
        if not metadata.get(key):
            raise ValueError(f"metadata.{key} is required")
    if not isinstance(metadata["group_id"], str):
        raise ValueError("metadata.group_id must be a string")


def validate_split(train: list[dict], validation: list[dict]) -> dict:
    train_groups = {r["metadata"]["group_id"] for r in train}
    val_groups = {r["metadata"]["group_id"] for r in validation}
    leaked = train_groups & val_groups
    if leaked:
        raise ValueError(f"Group leakage between train/validation: {sorted(leaked)[:10]}")
    def fingerprints(records):
        return {json.dumps(r["messages"], ensure_ascii=False, sort_keys=True) for r in records}
    if fingerprints(train) & fingerprints(validation):
        raise ValueError("Identical chat records occur in both splits")
    return {
        "train_rows": len(train), "validation_rows": len(validation),
        "train_groups": len(train_groups), "validation_groups": len(val_groups),
        "train_tasks": dict(collections.Counter(r["metadata"]["task"] for r in train)),
        "train_statuses": dict(collections.Counter(r["metadata"]["status"] for r in train)),
        "evaluation_scope": "Held-out lexical groups; not a validated sentence-translation benchmark.",
    }


def assistant_token_labels(input_ids, offsets, boundary: int) -> list[int]:
    """Mask prompt and boundary-straddling tokens; keep assistant + end markers."""
    labels = [token if start >= boundary and end > start else -100
              for token, (start, end) in zip(input_ids, offsets)]
    if not any(label != -100 for label in labels):
        raise ValueError("No supervised assistant tokens remain")
    return labels


def encode_record(tokenizer, record: dict, max_length: int) -> dict:
    messages = record["messages"]
    kwargs = {"tokenize": False, "enable_thinking": False}
    prompt = tokenizer.apply_chat_template(messages[:-1], add_generation_prompt=True, **kwargs)
    rendered = tokenizer.apply_chat_template(messages, add_generation_prompt=False, **kwargs)
    if not rendered.startswith(prompt):
        raise ValueError("Chat template changed the prompt prefix; refusing unsafe loss masking")
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    if len(encoded["input_ids"]) > max_length:
        raise ValueError(f"Record {record['metadata']['group_id']} has {len(encoded['input_ids'])} tokens "
                         f"> max_length={max_length}; shorten evidence or raise the limit")
    labels = assistant_token_labels(encoded["input_ids"], encoded.pop("offset_mapping"), len(prompt))
    return {"input_ids": encoded["input_ids"], "attention_mask": encoded["attention_mask"], "labels": labels}


def validate_config(config: dict) -> None:
    if config.get("model_name") not in ALLOWED_MODELS:
        raise ValueError("This recipe supports only the two reviewed Apache-2.0 Qwen models")
    for key in ("max_length", "batch_size", "gradient_accumulation_steps", "lora_r", "lora_alpha", "eval_steps"):
        if not isinstance(config.get(key), int) or config[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if config.get("max_steps", 0) <= 0 or config.get("learning_rate", 0) <= 0:
        raise ValueError("max_steps and learning_rate must be positive")
    if config.get("push_to_hub"):
        raise ValueError("Training never uploads; use the separate publication command")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rights_readiness(train, validation, *, local_lexical_experiment=False):
    if not train or not validation:
        return {"status": "blocked_no_eligible_corpus", "reason": "Both train and validation require eligible records. Game-derived candidate data is excluded under the official AI/ML training prohibition."}
    bad, invalid_facts = [], []
    counts = {split: {"fix": 0, "wordnet": 0} for split in ("train", "validation")}
    for split, records in (("train", train), ("validation", validation)):
        for row in records:
            metadata = row["metadata"]
            status = metadata.get("rights_status")
            if local_lexical_experiment and status == LOCAL_FACT_RIGHTS:
                try:
                    validate_local_fact_record(row)
                except ValueError:
                    invalid_facts.append(metadata["group_id"])
                else:
                    counts[split]["fix"] += 1
            elif status in APPROVED_RIGHTS:
                if local_lexical_experiment:
                    if metadata.get("source") not in WORDNET_SOURCES or metadata.get("task") not in WORDNET_TASKS:
                        bad.append(metadata["group_id"])
                    else:
                        counts[split]["wordnet"] += 1
            else:
                bad.append(metadata["group_id"])
    if bad or invalid_facts:
        return {"status": "blocked_source_rights",
                "reason": "Every record requires its recorded eligible basis, or an intact bounded lexical-fact record in the explicitly selected local experiment.",
                "ineligible_groups": sorted(set(bad)), "invalid_local_fact_groups": sorted(set(invalid_facts))}
    if local_lexical_experiment:
        if any(not value["fix"] or not value["wordnet"] for value in counts.values()):
            return {"status": "blocked_local_experiment_mixture",
                    "reason": "The declared experiment requires both bounded fiXmArge facts and eligible WordNet records in train and validation.",
                    "row_counts": counts}
        return {"status": "local_lexical_experiment_ready", "row_counts": counts,
                "reason": "Bounded factual correspondences validated for the explicitly selected local experiment; original source-rights metadata remains unchanged.",
                "source_rights_cleared": False, "publication_cleared": False}
    return {"status": "corpus_eligible", "reason": "Recorded source rights are eligible; GPU training and translation quality remain unverified."}


def ensure_training_rights(train, validation, *, local_lexical_experiment=False):
    readiness = rights_readiness(train, validation, local_lexical_experiment=local_lexical_experiment)
    allowed = {"corpus_eligible"}
    if local_lexical_experiment:
        allowed.add("local_lexical_experiment_ready")
    if readiness["status"] not in allowed:
        raise ValueError(readiness["status"] + ": " + readiness["reason"])


def validate_local_experiment_options(config, output: Path, *, local_lexical_experiment=False,
                                      resume=None, allow_download=False, init_adapter=None):
    """An explicit bounded local experiment cannot become resume/upload/general text training."""
    if not local_lexical_experiment:
        if init_adapter is not None:
            raise ValueError("--init-adapter requires explicit --local-lexical-experiment")
        if config.get("local_lexical_experiment"):
            raise ValueError("This configuration requires explicit --local-lexical-experiment")
        return
    requirements = {"local_lexical_experiment": True, "local_only": True,
                    "publication_allowed": False, "push_to_hub": False}
    for key, value in requirements.items():
        if config.get(key) is not value:
            raise ValueError(f"Local lexical experiment requires {key}={value}")
    if config.get("data_scope") != LOCAL_FACT_SCOPE:
        raise ValueError("Local lexical experiment requires its exact bounded lexical-fact data_scope")
    if config.get("model_name") != "Qwen/Qwen3-4B-Instruct-2507" or config.get("revision") != "cdbee75f17c01a7cc42f958dc650907174af0554":
        raise ValueError("Local lexical experiment requires the pinned original Qwen3-4B backbone")
    if resume is not None:
        raise ValueError("Local lexical experiment starts a new adapter; --resume is not allowed")
    if allow_download:
        raise ValueError("Local lexical experiment uses cached model/tokenizer files only")
    if (config.get("initial_adapter_path") or config.get("initial_adapter_sha256")) and init_adapter is None:
        raise ValueError("This configuration requires explicit --init-adapter with the pinned local weights")
    candidate = Path(output).expanduser()
    if candidate.exists() or candidate.is_symlink():
        raise ValueError("Local lexical experiment requires a new nonexistent adapter output directory")



def _bounded_json_file(path: Path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Initial adapter requires regular bounded local JSON metadata files")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Initial adapter JSON metadata must be an object")
    return value


def _adapter_safetensor_header(path: Path, rank: int):
    """Validate safe LoRA tensor headers using only the standard library."""
    if not path.is_file() or path.is_symlink() or not 8 < path.stat().st_size <= 256 * 1024 * 1024:
        raise ValueError("Initial adapter requires bounded regular adapter_model.safetensors weights")
    with path.open("rb") as stream:
        length = int.from_bytes(stream.read(8), "little")
        if not 0 < length <= 1024 * 1024 or length + 8 >= path.stat().st_size:
            raise ValueError("Initial adapter safetensors header is invalid")
        tensors = json.loads(stream.read(length))
    if not isinstance(tensors, dict):
        raise ValueError("Initial adapter safetensors header must be an object")
    intervals, pairs, parameters = [], {}, 0
    for name, tensor in tensors.items():
        if name == "__metadata__":
            continue
        if not isinstance(tensor, dict) or not name.endswith((".lora_A.weight", ".lora_B.weight")):
            raise ValueError("Initial adapter must contain only LoRA A/B weights")
        prefix, suffix = name.rsplit(".lora_", 1)
        if prefix.split(".")[-1] not in LORA_TARGETS:
            raise ValueError("Initial adapter tensor targets an unsupported module")
        shape, offsets = tensor.get("shape"), tensor.get("data_offsets")
        dtype = tensor.get("dtype")
        width = {"F32": 4, "BF16": 2, "F16": 2}.get(dtype) if isinstance(dtype, str) else None
        if (width is None or not isinstance(shape, list) or len(shape) != 2
                or any(type(value) is not int or value <= 0 for value in shape)
                or shape[0 if suffix == "A.weight" else 1] != rank
                or not isinstance(offsets, list) or len(offsets) != 2
                or any(type(value) is not int or value < 0 for value in offsets)
                or offsets[1] - offsets[0] != shape[0] * shape[1] * width):
            raise ValueError("Initial adapter tensor shape or offsets are invalid")
        intervals.append(tuple(offsets))
        pairs.setdefault(prefix, set()).add(suffix)
        parameters += shape[0] * shape[1]
    if not intervals or any(values != {"A.weight", "B.weight"} for values in pairs.values()):
        raise ValueError("Initial adapter requires complete LoRA A/B pairs")
    cursor = 0
    for start, end in sorted(intervals):
        if start != cursor or end <= start:
            raise ValueError("Initial adapter safetensors data must be complete and nonoverlapping")
        cursor = end
    if length + 8 + cursor != path.stat().st_size:
        raise ValueError("Initial adapter safetensors byte length is invalid")
    return {"tensor_count": len(intervals), "parameter_count": parameters}


def validate_initial_adapter(config, initial_adapter: Path, output: Path):
    """Pin a completed local adapter's weights, never its optimizer or scheduler."""
    source = Path(initial_adapter).expanduser()
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Initial adapter must be a regular existing local directory")
    source = validate_adapter_output(source)
    destination = Path(output).expanduser().resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Initial adapter and new output must not overlap")
    configured_source = config.get("initial_adapter_path")
    if configured_source:
        configured_source = Path(configured_source).expanduser()
        if not configured_source.is_absolute():
            configured_source = ROOT / configured_source
        if configured_source.resolve() != source:
            raise ValueError("Initial adapter path does not match the pinned local configuration")
    expected_hash = config.get("initial_adapter_sha256")
    if (not isinstance(expected_hash, str) or len(expected_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_hash)):
        raise ValueError("Initial adapter requires a pinned SHA256 in its configuration")
    adapter = _bounded_json_file(source / "adapter_config.json")
    manifest = _bounded_json_file(source / "training_manifest.json")
    if (adapter.get("base_model_name_or_path") != config["model_name"]
            or adapter.get("revision") != config["revision"] or adapter.get("peft_type") != "LORA"
            or adapter.get("task_type") != "CAUSAL_LM" or adapter.get("bias") != "none"
            or adapter.get("r") != config["lora_r"] or adapter.get("lora_alpha") != config["lora_alpha"]
            or not isinstance(adapter.get("target_modules"), list)
            or any(not isinstance(module, str) for module in adapter["target_modules"])
            or set(adapter["target_modules"]) != LORA_TARGETS
            or adapter.get("rank_pattern") or adapter.get("alpha_pattern")
            or any(adapter.get(field) for field in ("modules_to_save", "trainable_token_indices",
                "target_parameters", "use_dora", "use_rslora", "use_qalora", "lora_bias"))):
        raise ValueError("Initial adapter must match the pinned base and plain supported LoRA configuration")
    initial_config = manifest.get("configuration")
    if (manifest.get("training_status") != "completed" or manifest.get("training_performed") is not True
            or type(manifest.get("optimizer_steps")) is not int or manifest["optimizer_steps"] < 1
            or manifest.get("base_frozen") is not True or manifest.get("adapter_only") is not True
            or manifest.get("merge_performed") is not False or manifest.get("local_lexical_experiment") is not True
            or not isinstance(initial_config, dict)
            or initial_config.get("model_name") != config["model_name"]
            or initial_config.get("revision") != config["revision"]
            or initial_config.get("lora_r") != config["lora_r"]
            or initial_config.get("lora_alpha") != config["lora_alpha"]
            or initial_config.get("local_only") is not True or initial_config.get("publication_allowed") is not False
            or initial_config.get("push_to_hub") is not False):
        raise ValueError("Initial adapter requires its completed frozen-base local training manifest")
    header = _adapter_safetensor_header(source / "adapter_model.safetensors", config["lora_r"])
    if (manifest.get("trainable_tensor_count") != header["tensor_count"]
            or manifest.get("trainable_parameter_count") != header["parameter_count"]):
        raise ValueError("Initial adapter tensor counts disagree with its training manifest")
    names = ("adapter_model.safetensors", "adapter_config.json", "training_manifest.json")
    hashes = {name: sha256(source / name) for name in names}
    if hashes["adapter_model.safetensors"] != expected_hash:
        raise ValueError("Initial adapter weight SHA256 does not match the pinned configuration")
    return {"path": str(source), "weight_sha256": hashes["adapter_model.safetensors"],
            "files_sha256": hashes, "source_optimizer_steps": manifest["optimizer_steps"], **header}


def verify_initial_adapter_unchanged(initial):
    for name, expected in initial["files_sha256"].items():
        if sha256(Path(initial["path"]) / name) != expected:
            raise RuntimeError("Initial adapter source files changed during the isolated training run")


def local_initialization_report(initial=None):
    return {"initial_adapter_path": initial["path"] if initial else None,
            "initial_adapter_sha256": initial["weight_sha256"] if initial else None,
            "initial_adapter_source_optimizer_steps": initial["source_optimizer_steps"] if initial else None,
            "initial_global_step": 0, "optimizer_state_reused": False, "scheduler_state_reused": False,
            "baseline_model": "original_base_plus_initial_adapter" if initial else "original_base"}


def data_rights_report(train, validation, config, *, local_lexical_experiment=False):
    rows = train + validation
    statuses = {row["metadata"].get("rights_status", "missing") for row in rows}
    source_statuses = {row["metadata"].get("source_rights_status", row["metadata"].get("rights_status", "missing"))
                       for row in rows}
    facts = [row for row in rows if row["metadata"].get("rights_status") == LOCAL_FACT_RIGHTS]
    return {"recorded_statuses": sorted(statuses), "source_rights_statuses": sorted(source_statuses),
            "sources": sorted({str(row["metadata"]["source"]) for row in rows}),
            "scope": config.get("data_scope", "Provided eligible corpus only"),
            "game_derived_candidates_included": "game_derived_not_eligible" in statuses | source_statuses,
            "bounded_local_lexical_fact_rows": len(facts),
            "local_lexical_experiment": bool(local_lexical_experiment),
            "source_rights_relabeling_performed": False,
            "source_rights_cleared_by_local_experiment": False,
            "publication_approved_by_this_run": False}


def component_validation_sets(validation, encoded):
    if len(validation) != len(encoded):
        raise ValueError("Validation metadata and encoded records differ in length")
    partitions = {"fix": [], "wordnet": []}
    for row, value in zip(validation, encoded):
        key = "fix" if row["metadata"]["task"] == "fix_lexical_correspondence" else "wordnet"
        partitions[key].append(value)
    if not all(partitions.values()):
        raise ValueError("Both fiXmArge and WordNet component validation sets must be nonempty")
    return partitions


def model_cache_roots(environ=None) -> list[Path]:
    """Resolve every configured/default Hub cache location without importing ML."""
    environment = os.environ if environ is None else environ
    default_cache = Path.home() / ".cache" / "huggingface"
    xdg_cache = Path(environment.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "huggingface"
    hf_home = Path(environment.get("HF_HOME") or xdg_cache)
    roots = [default_cache, xdg_cache, hf_home, hf_home / "hub"]
    for key in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE",
                "PYTORCH_TRANSFORMERS_CACHE", "PYTORCH_PRETRAINED_BERT_CACHE"):
        if environment.get(key):
            roots.append(Path(environment[key]))
    return list(dict.fromkeys(path.expanduser().resolve() for path in roots))


def validate_adapter_output(output: Path, *, cache_roots=None) -> Path:
    """Prevent writes to base caches, their descendants, or their ancestors."""
    destination = output.expanduser().resolve()
    protected = [Path(root).expanduser().resolve() for root in
                 (model_cache_roots() if cache_roots is None else cache_roots)]
    for root in protected:
        root = Path(root).expanduser().resolve()
        if destination == root or root in destination.parents or destination in root.parents:
            raise ValueError(f"Adapter output overlaps a protected base-model cache: {destination}")
    if destination.is_dir():
        for child in destination.rglob("*"):
            if child.is_symlink():
                resolved = child.resolve()
                if any(resolved == root or root in resolved.parents or resolved in root.parents for root in protected):
                    raise ValueError(f"Adapter output links into a protected base-model cache: {child}")
    # Refuse an existing full-model directory even when it is outside the Hub cache.
    for pattern in ("model*.safetensors", "pytorch_model*.bin", "model.safetensors.index.json",
                    "pytorch_model.bin.index.json"):
        if any(destination.glob(pattern)):
            raise ValueError(f"Adapter output contains full-model weights: {destination}")
    return destination


def inspect_adapter_parameters(model) -> dict:
    """Fail before Trainer construction if anything except LoRA is trainable."""
    trainable = []
    unexpected = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if not any(part.startswith("lora_") for part in name.split(".")):
            unexpected.append(name)
        trainable.append({"name": name, "numel": int(parameter.numel())})
    if unexpected:
        raise ValueError("Non-LoRA parameters are trainable: " + ", ".join(unexpected))
    if not trainable or not sum(item["numel"] for item in trainable):
        raise ValueError("No trainable LoRA parameters were found")
    return {"base_frozen": True, "adapter_only": True, "merge_performed": False,
            "trainable_parameter_names": [item["name"] for item in trainable],
            "trainable_parameter_count": sum(item["numel"] for item in trainable),
            "trainable_tensor_count": len(trainable), "trainable_parameters": trainable}


def configure_adapter_saving(model) -> None:
    """Keep Trainer checkpoints adapter-only and avoid PEFT's Hub embedding probe."""
    original_save = model.save_pretrained

    def save_adapter(*args, **kwargs):
        kwargs.update(safe_serialization=True, save_embedding_layers=False)
        return original_save(*args, **kwargs)

    model.save_pretrained = save_adapter


def run_training(config, train, validation, report, output: Path, resume=None, *, allow_download=False,
                 local_lexical_experiment=False, init_adapter=None):
    ensure_training_rights(train, validation, local_lexical_experiment=local_lexical_experiment)
    if local_lexical_experiment:
        validate_split(train, validation)
    validate_local_experiment_options(config, output, local_lexical_experiment=local_lexical_experiment,
                                      resume=resume, allow_download=allow_download, init_adapter=init_adapter)
    output = validate_adapter_output(output)
    initial = validate_initial_adapter(config, init_adapter, output) if init_adapter is not None else None
    try:
        import torch
        from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                                  Trainer, TrainingArguments, set_seed)
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    except ImportError as exc:
        raise RuntimeError("Install requirements-train.txt in the training environment first") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("This QLoRA recipe requires an NVIDIA CUDA GPU. Offline validation remains available.")
    set_seed(config["seed"])
    precision = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"], revision=config["revision"],
                                             use_fast=True, trust_remote_code=False,
                                             local_files_only=not allow_download)
    if not tokenizer.is_fast:
        raise RuntimeError("Fast tokenizer offsets are required for assistant-only loss")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    train_encoded = [encode_record(tokenizer, row, config["max_length"]) for row in train]
    eval_encoded = [encode_record(tokenizer, row, config["max_length"]) for row in validation]
    component_sets = component_validation_sets(validation, eval_encoded) if local_lexical_experiment else None
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=precision)
    model = AutoModelForCausalLM.from_pretrained(config["model_name"], revision=config["revision"],
        quantization_config=quantization, torch_dtype=precision, trust_remote_code=False,
        local_files_only=not allow_download, use_safetensors=True,
        device_map={"": torch.cuda.current_device()}, attn_implementation="sdpa")
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    if initial is not None:
        from peft import PeftModel
        verify_initial_adapter_unchanged(initial)
        model = PeftModel.from_pretrained(model, initial["path"], is_trainable=True, local_files_only=True)
    else:
        model = get_peft_model(model, LoraConfig(r=config["lora_r"], lora_alpha=config["lora_alpha"],
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=config["lora_dropout"], bias="none", task_type="CAUSAL_LM"), revision=config["revision"])
    adapter_parameters = inspect_adapter_parameters(model)
    configure_adapter_saving(model)

    def collate(features):
        inputs = tokenizer.pad([{k: v for k, v in f.items() if k != "labels"} for f in features],
                               padding=True, return_tensors="pt")
        width = inputs["input_ids"].shape[1]
        inputs["labels"] = torch.tensor([f["labels"] + [-100] * (width - len(f["labels"]))
                                         for f in features], dtype=torch.long)
        return inputs

    output.mkdir(parents=True, exist_ok=not local_lexical_experiment)
    report["data_rights"] = data_rights_report(train, validation, config, local_lexical_experiment=local_lexical_experiment)
    report["local_lexical_experiment"] = bool(local_lexical_experiment)
    if local_lexical_experiment:
        report.update(local_initialization_report(initial))
    report.update(adapter_parameters)
    report.update({"allow_download": bool(allow_download), "base_model_files_overwritten": False,
        "model_save_format": "peft_adapter_safetensors",
        "gpu": torch.cuda.get_device_name(0),
        "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        "base_model_revision": (getattr(model.config, "_commit_hash", None) or config["revision"]),
        "precision": str(precision), "configuration": config,
        "tokenizer_masking": "Assistant-only token offsets verified for every train/eval row.",
        "assistant_supervised_tokens": sum(sum(x != -100 for x in r["labels"]) for r in train_encoded)})
    (output / "training_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    arguments = TrainingArguments(output_dir=str(output), max_steps=config["max_steps"],
        per_device_train_batch_size=config["batch_size"], per_device_eval_batch_size=config.get("eval_batch_size", 1),
        gradient_accumulation_steps=config["gradient_accumulation_steps"], learning_rate=config["learning_rate"],
        warmup_ratio=0.05, lr_scheduler_type="cosine", logging_steps=5,
        eval_strategy="steps", eval_steps=config["eval_steps"], save_strategy="steps",
        save_steps=config["eval_steps"], save_total_limit=2, save_safetensors=True,
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        bf16=precision == torch.bfloat16, fp16=precision == torch.float16,
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="adamw_torch", report_to="none", push_to_hub=False, seed=config["seed"],
        dataloader_num_workers=0, remove_unused_columns=False, label_names=["labels"])
    trainer = Trainer(model=model, args=arguments, train_dataset=train_encoded,
        eval_dataset=eval_encoded, data_collator=collate, processing_class=tokenizer)
    if initial is not None and trainer.state.global_step != 0:
        raise ValueError("Weights-only initialization requires a fresh Trainer global_step of zero")
    baseline = trainer.evaluate(metric_key_prefix="base_eval")
    if component_sets is not None:
        report["component_evaluations"] = {"baseline": {
            key: trainer.evaluate(eval_dataset=values, metric_key_prefix=f"base_{key}_eval")
            for key, values in component_sets.items()}, "final": {}}
    report.update({"training_status": "running", "training_performed": False,
                   "baseline_evaluation": baseline})
    (output / "training_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    train_result = trainer.train(resume_from_checkpoint=resume)
    model.save_pretrained(str(output), safe_serialization=True)
    tokenizer.save_pretrained(str(output))
    metrics = trainer.evaluate()
    if component_sets is not None:
        report["component_evaluations"]["final"] = {
            key: trainer.evaluate(eval_dataset=values, metric_key_prefix=f"{key}_eval")
            for key, values in component_sets.items()}
        metrics["component_evaluations"] = report["component_evaluations"]
    metrics["evaluation_scope"] = report["evaluation_scope"]
    metrics["baseline_evaluation"] = baseline
    if "base_eval_loss" in baseline and "eval_loss" in metrics:
        metrics["eval_loss_change"] = metrics["eval_loss"] - baseline["base_eval_loss"]
    if initial is not None:
        verify_initial_adapter_unchanged(initial)
        report["initial_adapter_files_sha256_unchanged"] = True
        report["initial_adapter_files_sha256"] = initial["files_sha256"]
    report.update({"training_status": "completed", "training_performed": True,
                   "optimizer_steps": int(trainer.state.global_step),
                   "training_metrics": train_result.metrics,
                   "selected_checkpoint": trainer.state.best_model_checkpoint,
                   "best_validation_loss": trainer.state.best_metric,
                   "final_evaluation": metrics,
                   "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                   "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved())})
    (output / "training_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {"mode": "trained_local_adapter", "output": str(output), "metrics": metrics}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/train_qwen3_4b.json")
    parser.add_argument("--train", type=Path, default=ROOT / "data/training/train.jsonl")
    parser.add_argument("--validation", type=Path, default=ROOT / "data/training/validation.jsonl")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--max-length", type=int)
    parser.add_argument("--resume", help="Local checkpoint directory")
    parser.add_argument("--init-adapter", type=Path,
                        help="Explicit local weights-only initialization from a pinned completed adapter; optimizer/scheduler and steps start fresh")
    parser.add_argument("--local-lexical-experiment", action="store_true",
                        help="Explicit isolated local experiment on strictly validated lexical-fact records plus licensed WordNet; no source-prose permission or publication approval")
    parser.add_argument("--allow-download", action="store_true",
                        help="Explicitly allow base model/tokenizer downloads; cached files only by default")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--dry-run", action="store_true", help="Offline corpus/config validation (default)")
    actions.add_argument("--run-training", action="store_true", help="Train a local CUDA adapter after corpus approval; cached base files only by default")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    for arg, key in ((args.max_steps, "max_steps"), (args.max_length, "max_length")):
        if arg is not None:
            config[key] = arg
    validate_config(config)
    if args.local_lexical_experiment or args.init_adapter is not None or config.get("initial_adapter_sha256"):
        validate_local_experiment_options(config, args.output or ROOT / config["output_dir"],
            local_lexical_experiment=args.local_lexical_experiment, resume=args.resume,
            allow_download=args.allow_download, init_adapter=args.init_adapter)
    initial = (validate_initial_adapter(config, args.init_adapter, args.output or ROOT / config["output_dir"])
               if args.init_adapter is not None else None)
    train, validation = load_jsonl(args.train, allow_empty=True), load_jsonl(args.validation, allow_empty=True)
    report = validate_split(train, validation)
    report["readiness"] = rights_readiness(train, validation, local_lexical_experiment=args.local_lexical_experiment)
    report["evaluation_scope"] = config.get("evaluation_scope", report["evaluation_scope"])
    report.update({"mode": "offline_validation", "allow_download": args.allow_download,
        "model": config["model_name"],
        "revision": config["revision"], "model_license": "Apache-2.0", "configuration": config,
        "train_sha256": sha256(args.train), "validation_sha256": sha256(args.validation),
        "tokenizer_masking": "Validated only when tokenizer is available during actual training.",
        "data_rights": data_rights_report(train, validation, config,
                                           local_lexical_experiment=args.local_lexical_experiment),
        "local_lexical_experiment": args.local_lexical_experiment,
        "rights_checked_at": "2026-11-07" if args.local_lexical_experiment else "2026-11-06"})
    if args.local_lexical_experiment:
        report.update(local_initialization_report(initial))
    if args.run_training:
        report = run_training(config, train, validation, report, args.output or ROOT / config["output_dir"],
                              args.resume, allow_download=args.allow_download,
                              local_lexical_experiment=args.local_lexical_experiment, init_adapter=args.init_adapter)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
