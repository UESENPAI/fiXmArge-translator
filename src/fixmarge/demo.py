"""Local/Spaces demo backend: evidence is separate from model proposals."""
from __future__ import annotations
import json
import re
from pathlib import Path
from threading import Lock
from typing import Any

from .infer import ModelRunner, resolve_revision
from .korean_bridge import build_korean_gloss_prompt, inspect_korean_glosses, retrieve_related_gloss_support
from .rag import LexiconRAG
from .retrieval import build_query_prompt, retrieve_rewritten_queries
from .standard_dictionary import gloss_queries, lookup_standard_dictionary
from .sentence_diagnostics import build_sentence_evidence, build_sentence_prompt, inspect_sentence_generation

DEFAULT_MODEL = 'Qwen/Qwen3-4B-Instruct-2507'
WORDNET_TRAINING_SCOPE = 'commercially_reusable_english_japanese_wordnet_lexical_instruction_tuning'
PRODUCT_TARGETS = {'fix': ('ko', 'ja', 'en'), 'ko': ('fix',), 'ja': ('fix',), 'en': ('fix',)}


def target_languages(source: str) -> tuple[str, ...]:
    """Return only the supported product targets; research helpers stay separate."""
    if not isinstance(source, str) or source not in PRODUCT_TARGETS:
        raise ValueError('⚠ Coword → · source_language ∉ {fiXmArge, ko, ja, en}')
    return PRODUCT_TARGETS[source]


def validate_translation_pair(source: str, target: str) -> None:
    targets = target_languages(source)
    if not isinstance(target, str) or target not in PRODUCT_TARGETS:
        raise ValueError('⚠ → MeMe · target_language ∉ {fiXmArge, ko, ja, en}')
    if target not in targets:
        raise ValueError('⚠ ConWas · fiXmArge ↔ {ko, ja, en} · source_language ≠ target_language')


def _adapter_training_status(adapter):
    """Read bounded, typed training metadata; never adopt freeform claims."""
    summary = {'status': 'unknown' if adapter else 'not_configured',
               'optimizer_steps': None, 'data_scope': None, 'train_rows': None, 'sources': [],
               'selected_checkpoint': None, 'selected_optimizer_step': None,
               'initial_adapter_source_optimizer_steps': None}
    if not adapter:
        return summary
    try:
        with (Path(adapter) / 'training_manifest.json').open('rb') as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return summary
        manifest = json.loads(raw)
    except (OSError, ValueError, RecursionError):
        return summary
    if not isinstance(manifest, dict):
        return summary
    configuration = manifest.get('configuration')
    rights = manifest.get('data_rights')
    scope = configuration.get('data_scope') if isinstance(configuration, dict) else None
    sources = rights.get('sources') if isinstance(rights, dict) else None
    for key in ('optimizer_steps', 'train_rows'):
        value = manifest.get(key)
        if type(value) is int and value >= 0:
            summary[key] = value
    selected = manifest.get('selected_checkpoint')
    if (isinstance(selected, str) and 0 < len(selected) <= 1024
            and not any(ord(character) < 32 or ord(character) == 127 for character in selected)):
        name = selected.replace(chr(92), '/').rsplit('/', 1)[-1]
        matched = re.fullmatch(r'checkpoint-([0-9]{1,12})', name)
        if matched:
            summary['selected_checkpoint'] = name
            summary['selected_optimizer_step'] = int(matched.group(1))
    initial_steps = manifest.get('initial_adapter_source_optimizer_steps')
    if type(initial_steps) is int and initial_steps >= 0:
        summary['initial_adapter_source_optimizer_steps'] = initial_steps
    if isinstance(scope, str) and 0 < len(scope) <= 200 and not any(ord(c) < 32 for c in scope):
        summary['data_scope'] = scope
    if (isinstance(sources, list) and 0 < len(sources) <= 32
            and all(isinstance(source, str) and 0 < len(source) <= 160
                    and not any(ord(c) < 32 for c in source) for source in sources)):
        summary['sources'] = list(dict.fromkeys(sources))
    status = manifest.get('training_status')
    complete = (summary['optimizer_steps'] is not None and summary['train_rows'] is not None
                and summary['data_scope'] is not None and bool(summary['sources']))
    if complete and status in ('completed', 'running', 'failed', 'interrupted'):
        if status != 'completed' or (summary['optimizer_steps'] > 0 and summary['train_rows'] > 0):
            summary['status'] = status
    return summary


class DemoService:
    def __init__(self, *, model_name=DEFAULT_MODEL, data_dir=None, external_dir=None,
                 adapter=None, device='auto', allow_download=False, load_in_4bit: bool = False,
                 runner_factory=ModelRunner, rag_factory=LexiconRAG,
                 standard_lookup=lookup_standard_dictionary, dictionary_first: bool = True):
        self.model_name = model_name
        self.data_dir = data_dir
        self.external_dir = external_dir
        self.adapter = str(Path(adapter).resolve()) if adapter else None
        if self.adapter and not (Path(self.adapter) / 'adapter_config.json').is_file():
            raise ValueError('⚠ LoRA · adapter_config.json · ∅')
        self.device = device
        self.allow_download = allow_download
        self.load_in_4bit = load_in_4bit
        self.runner_factory = runner_factory
        self.rag_factory = rag_factory
        self.standard_lookup = standard_lookup
        self.dictionary_first = dictionary_first
        self._runner = None
        self._rag = None
        self._lock = Lock()

    def _load_runner(self):
        if self._runner is None:
            self._runner = self.runner_factory(model_name=self.model_name, adapter=self.adapter,
                revision=resolve_revision(self.model_name, None), device=self.device,
                allow_download=self.allow_download, load_in_4bit=self.load_in_4bit, max_new_tokens=512)
        return self._runner

    def preload(self):
        """Place the model during startup, as required by ZeroGPU CUDA emulation."""
        with self._lock:
            self._load_runner()

    def run(self, text: str, source: str, target: str, generate: bool = False) -> dict[str, Any]:
        validate_translation_pair(source, target)
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Coword · ∅ · ⚠')
        if len(text) > 1000:
            raise ValueError('⚠ Coword · len(text) ≤ 1000')
        with self._lock:
            if self._rag is None:
                try:
                    self._rag = self.rag_factory(data_dir=self.data_dir, external_dir=self.external_dir)
                except FileNotFoundError as exc:
                    raise ValueError('⚠ fiXmArge · Coword · ∅ · FIXMARGE_DATA_DIR') from exc
            lookup = self._rag.lookup(text, f'{source}-to-{target}')
            evidence = build_sentence_evidence(text, source, target, lookup)
            extra_queries = (gloss_queries(entry for segment in evidence['lexical_segments']
                                          for entry in segment['entries']) if source == 'fix' else [])
            standard_directory = (self.external_dir if self.external_dir is not None else
                                  Path(self.data_dir).parent / 'external' if self.data_dir is not None else None)
            standard = self.standard_lookup(text, external_dir=standard_directory,
                                            languages=('en', 'ja'), extra_queries=extra_queries,
                                            include_input=source in ('en', 'ja'))
            evidence['standard_dictionary'] = standard
            result = {'source_text': text, 'source_language': source, 'target_language': target,
                      'source_evidence': evidence, 'standard_dictionary': standard, 'mode': 'generate' if generate else 'lookup',
                      'model': self.model_name, 'base_revision': resolve_revision(self.model_name, None),
                      'runtime': {'device': self.device, 'load_in_4bit': self.load_in_4bit},
                      'adapter_configured': bool(self.adapter), 'adapter_loaded': bool(self.adapter and self._runner),
                      'adapter_training': _adapter_training_status(self.adapter), 'training_performed': False,
                      'sentence_verified': False, 'model_loaded': self._runner is not None,
                      'translation_strategy': 'dictionary_first_rag' if self.dictionary_first else 'model_with_dictionary',
                      'query_rewrite_performed': False, 'korean_bridge_performed': False,
                      'generation_performed': False, 'answer_source': 'lookup'}
            if generate and self.dictionary_first:
                contract = lookup['lexical_contract']
                if contract['expected_translation'] is not None:
                    result['answer_source'] = 'dictionary'
                    result['dictionary_answer'] = {
                        'translation': contract['expected_translation'],
                        'evidence_ids': list(dict.fromkeys(identifier for segment in contract['segments']
                                                          for identifier in segment['entry_ids'])),
                        'scope': 'single_lexical', 'sentence_verified': False,
                        'source_review_verified': False,
                    }
                    return result
                if (source == 'fix' and contract['scope'] == 'single_lexical'
                        and set(contract['abstention_reasons']) == {'source_conflict'}
                        and not any('?' in item['text'] or '？' in item['text']
                                    for item in contract['segments'][0]['candidates'])):
                    segment = contract['segments'][0]
                    result['answer_source'] = 'dictionary_claims'
                    result['answer_kind'] = 'unresolved_dictionary_alternatives'
                    result['dictionary_claims_answer'] = {
                        'translation': contract['candidate_separator'].join(item['text'] for item in segment['candidates']),
                        'evidence_ids': segment['entry_ids'], 'alternatives': segment['candidates'],
                        'source_conflict_entry_ids': segment['conflicting_entry_ids'],
                        'conflicts_resolved': False, 'source_review_verified': False,
                        'sentence_verified': False, 'model_generated': False,
                    }
                    return result
                if not evidence['lexical_segments'] and source == 'ko' and target == 'fix':
                    raw_queries = self._load_runner().generate(build_query_prompt(text))
                    evidence['indirect_dictionary'] = retrieve_rewritten_queries(raw_queries, self._rag)
                    result['query_rewrite_performed'] = True
                    result['generation_performed'] = True
                    result['model_loaded'] = True
                    result['adapter_loaded'] = bool(self.adapter)
                if not evidence['lexical_segments'] and not evidence.get('indirect_dictionary', {}).get('entries'):
                    result['answer_source'] = 'abstained'
                    result['abstention_reason'] = 'no_fiXmArge_dictionary_evidence'
                    return result
                if source == 'fix' and target == 'ko':
                    evidence['korean_related_gloss_support'] = retrieve_related_gloss_support(evidence, self._rag)
                    attempts = []
                    for attempt in range(2):
                        raw_bridge = self._load_runner().generate(build_korean_gloss_prompt(evidence, retry=attempt > 0))
                        bridge = inspect_korean_glosses(raw_bridge, evidence)
                        attempts.append({key: bridge[key] for key in ('raw_output', 'raw_json_valid', 'json_extraction', 'schema_valid', 'unsupported_entry_ids')})
                        if bridge['schema_valid']:
                            break
                    bridge['attempts'] = attempts
                    evidence['korean_lexical_bridge'] = bridge
                    result['korean_bridge_performed'] = True
                    result['generation_performed'] = True
                    result['model_loaded'] = True
                    result['adapter_loaded'] = bool(self.adapter)
                    if not bridge['schema_valid'] or not bridge['glosses']:
                        result['answer_source'] = 'abstained'
                        result['abstention_reason'] = 'korean_gloss_bridge_unavailable'
                        return result
                    supplied = {item['entry_id'] for item in bridge['glosses']}
                    required = {identifier for segment in contract['segments'] for identifier in segment['entry_ids']}
                    words = list(dict.fromkeys(word for item in bridge['glosses'] for word in item['korean']))
                    if (contract['scope'] == 'single_lexical'
                            and set(contract['abstention_reasons']) <= {'missing_target_senses', 'source_conflict'}
                            and ('source_conflict' not in contract['abstention_reasons'] or len(words) > 1)
                            and required <= supplied
                            and not any(item['source_uncertain'] for item in bridge['glosses'])):
                        result['answer_source'] = 'model_with_dictionary'
                        result['answer_kind'] = 'korean_lexical_paraphrase'
                        result['korean_bridge_answer'] = {
                            'translation': '; '.join(words), 'evidence_ids': list(dict.fromkeys(
                                item['entry_id'] for item in bridge['glosses'])),
                            'machine_generated': True, 'gloss_alignment_verified': False,
                            'source_conflict_entry_ids': [item['entry_id'] for item in bridge['glosses'] if item['source_conflict']],
                            'conflicts_resolved': False, 'sentence_verified': False,
                        }
                        return result
            if generate:
                prompt = build_sentence_prompt(evidence, lookup)
                raw = self._load_runner().generate(prompt)
                try:
                    parsed = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    parsed = None
                proposal = parsed.get('tentative_translation') if isinstance(parsed, dict) else None
                output_lookup = self._rag.lookup(proposal, 'fix-to-ja') if target == 'fix' and isinstance(proposal, str) else None
                result['diagnostic'] = inspect_sentence_generation(raw, evidence, lookup, output_lookup)
                result['answer_source'] = 'model_with_dictionary'
                result['generation_performed'] = True
                result['model_loaded'] = True
                result['adapter_loaded'] = bool(self.adapter)
            return result


def source_highlights(evidence):
    text = evidence['source_text']
    if not evidence['dictionary_assessed']:
        return [(text, 'fiXmArge · ∅')]
    marks = []
    for segment in evidence['lexical_segments']:
        label = ('MeMe · ≠' if segment['conflicting_entry_ids'] else
                 'MeMe · ∅' if segment['missing_target_entry_ids'] else
                 'MeMe · 1…n' if segment.get('ambiguous') else 'Coword ↔ MeMe')
        marks.append((segment['start'], segment['end'], label))
    marks.extend((span['start'], span['end'], 'Coword · ?') for span in evidence['unmatched_source_spans'])
    boundaries = sorted({0, len(text), *(i for lo, hi, _ in marks for i in (lo, hi))})
    return [(text[lo:hi], next((label for start, end, label in marks if start <= lo and hi <= end), None))
            for lo, hi in zip(boundaries, boundaries[1:]) if hi > lo]


def present_result(result):
    evidence = result['source_evidence']
    diagnostic = result.get('diagnostic')
    if result.get('dictionary_answer') is not None:
        proposal = result['dictionary_answer']['translation']
    elif result.get('dictionary_claims_answer') is not None:
        proposal = '⚠ ' + result['dictionary_claims_answer']['translation']
    elif result.get('korean_bridge_answer') is not None:
        proposal = result['korean_bridge_answer']['translation']
    elif result.get('answer_source') == 'abstained':
        proposal = 'MeMe · ∅ · ⚠'
    elif diagnostic is None:
        proposal = 'Coword ↔ MeMe'
    elif not diagnostic['schema_valid']:
        proposal = '⚠ MeMe · JSON · ∅ · {}'
    elif (result['target_language'] == 'fix' and diagnostic['unsupported_output_spans']
          and not diagnostic['registered_output_spans']):
        proposal = '⚠ fiXmArge · MeMe · ∅ · {}'
    else:
        proposal = diagnostic['tentative_translation'] or 'MeMe · ∅ · ⚠'
    rows = []
    for segment in evidence['lexical_segments']:
        terms = ' / '.join(candidate['text'] for candidate in segment['candidates']) or 'MeMe · ∅'
        flags = []
        if segment['conflicting_entry_ids']: flags.append('⚠ · ≠')
        if segment['missing_target_entry_ids']: flags.append('MeMe · ∅')
        if segment.get('ambiguous'): flags.append('MeMe · 1…n')
        sources = sorted({source for entry in segment.get('entries', []) for source in entry.get('sources', [])})
        rows.append([segment['text'], terms, ', '.join(flags) or 'Coword ↔ MeMe', ', '.join(sources)])
    rows.extend([span['text'], '—', 'Coword · ?', '—'] for span in evidence['unmatched_source_spans'])
    if not evidence['dictionary_assessed']:
        rows.append(['Coword · ∀', '⚙', 'fiXmArge · ∅', '—'])
    korean_bridge = evidence.get('korean_lexical_bridge', {})
    for item in korean_bridge.get('glosses', []):
        original = ' / '.join(value for values in item['source_senses'].values() for value in values)
        flags = 'MeMe · ⚙ · ?' + (' · ≠' if item['source_conflict'] else '')
        rows.append([original, ' / '.join(item['korean']), flags, item['entry_id']])
    indirect = evidence.get('indirect_dictionary', {})
    for record in indirect.get('entries', []):
        entry = record['entry']
        queries = ' / '.join(dict.fromkeys(match['query'] for match in record['matches']))
        flag = '⚠ · ≠' if entry.get('has_conflict') else 'MeMe · ⚙ · ?'
        rows.append([queries, entry['form'], flag, ', '.join(entry.get('sources', []))])
    standard = result.get('standard_dictionary', {})
    for record in standard.get('entries', []):
        entry = record['entry']
        queries = ' / '.join(dict.fromkeys(match['query'] for match in record.get('matches', [])))
        glosses = ' / '.join(entry.get('glosses', [])[:2]) or ' / '.join(entry.get('synonyms', [])[:5])
        rows.append([queries or entry['lemma'], f"{entry['lemma']}: {glosses}",
                     f"{entry['language']} · {entry['license']}", entry['source']])
    # Technical identifiers and verbatim evidence stay readable without inventing
    # unattested fiXmArge technical vocabulary or sentence grammar.
    status_fields = {
        'model': result['model'],
        'translation_strategy': result.get('translation_strategy'),
        'answer_source': result.get('answer_source'),
        'generation_performed': bool(result.get('generation_performed')),
        'query_rewrite_performed': bool(result.get('query_rewrite_performed')),
        'korean_bridge_performed': bool(result.get('korean_bridge_performed')),
        'korean_bridge_schema_valid': korean_bridge.get('schema_valid'),
        'korean_bridge_raw_json_valid': korean_bridge.get('raw_json_valid'),
        'korean_bridge_json_extraction': korean_bridge.get('json_extraction'),
        'korean_bridge_attempts': len(korean_bridge.get('attempts', [])),
        'korean_gloss_alignment_verified': False,
        'answer_kind': result.get('answer_kind'),
        'indirect_dictionary_entries': len(indirect.get('entries', [])),
        'query_translation_verified': False,
        'adapter_configured': bool(result.get('adapter_configured')),
        'adapter_loaded': bool(result['adapter_loaded']),
        'sentence_verified': False,
        'sentence_grammar_verified': bool(evidence.get('grammar', {}).get('sentence_grammar_verified', False)),
        'output_source_alignment_verified': bool((diagnostic or {}).get('output_source_alignment_verified', False)),
        'dictionary_assessed': bool(evidence['dictionary_assessed']),
        'lexical_segments': len(evidence['lexical_segments']),
        'unmatched_source_spans': len(evidence['unmatched_source_spans']),
        'standard_dictionary': {
            'available': bool(standard.get('available')),
            'languages': ['en', 'ja'],
            'entries': len(standard.get('entries', [])),
            'query_policy': standard.get('query_policy'),
        },
    }
    if result.get('abstention_reason'):
        status_fields['abstention_reason'] = result['abstention_reason']
    if result.get('dictionary_claims_answer'):
        status_fields['dictionary_claims_answer'] = result['dictionary_claims_answer']
    if result.get('korean_bridge_answer'):
        status_fields['korean_bridge_answer'] = result['korean_bridge_answer']
    if result.get('dictionary_answer'):
        status_fields['dictionary_answer'] = result['dictionary_answer']
    if result.get('adapter_configured'):
        training = result.get('adapter_training', {})
        status_fields['adapter_training'] = {
            'status': training.get('status', 'unknown'),
            'optimizer_steps': training.get('optimizer_steps'),
            'data_scope': training.get('data_scope'),
            'selected_checkpoint': training.get('selected_checkpoint'),
            'selected_optimizer_step': training.get('selected_optimizer_step'),
            'initial_adapter_source_optimizer_steps': training.get('initial_adapter_source_optimizer_steps'),
        }
        if training.get('selected_checkpoint') is not None:
            status_fields['adapter_selection'] = 'LoRA · ' + training['selected_checkpoint']
        if training.get('initial_adapter_source_optimizer_steps') is not None:
            status_fields['initial_source_steps'] = training['initial_adapter_source_optimizer_steps']
    if diagnostic:
        status_fields['unsupported_output_spans'] = [span['text'] for span in diagnostic['unsupported_output_spans']]
        status_fields['malformed_gap_placeholders'] = [span['text'] for span in diagnostic['malformed_gap_placeholders']]
        status_fields['model_uncertainties'] = diagnostic['model_uncertainties']
        status_fields['unsupported_evidence_ids'] = diagnostic['unsupported_evidence_ids']
        status_fields['model_indirect_evidence_ids'] = diagnostic.get('model_indirect_evidence_ids', [])
        status_fields['model_related_evidence_ids'] = diagnostic.get('model_related_evidence_ids', [])
    status = json.dumps(status_fields, ensure_ascii=False, indent=2)
    # License credits are reproduced verbatim under the user's license exception.
    for credit in standard.get('attributions', []):
        status += f"\n{credit['credit']} ({credit['license']})"
    return proposal, source_highlights(evidence), rows, status, result
