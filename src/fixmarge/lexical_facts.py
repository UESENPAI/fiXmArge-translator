"""Bounded local lexical-fact records; no claim of source permission or grammar."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import re
import unicodedata

LOCAL_FACT_RIGHTS = 'lexical_facts_local_experiment'
LOCAL_FACT_TASK = 'fix_lexical_correspondence'
SOURCE_RIGHTS = 'game_derived_not_eligible'
SOURCE_IDS = frozenset({'hecate-csv', 'japanese-wordbook'})
DIRECTIONS = ('fix-to-ja', 'ja-to-fix', 'fix-to-en', 'en-to-fix')
MAX_FORM_CHARS = 80
MAX_GLOSS_CHARS = {'ja': 40, 'en': 80}
MAX_WORDS = 8
MAX_ALTERNATIVES = 16
CONTROL_TOKENS = ('<|', '|>', '<think>', '</think>', '[INST]', '[/INST]')
PUNCT = str.maketrans({'•':'·', '・':'·', '’':"'", '‘':"'", 'ʼ':"'", '‐':'-', '‑':'-'})
FACT_FIELDS = frozenset({'language', 'forms', 'glosses'})
META_FIELDS = frozenset({'group_id', 'source', 'source_ids', 'source_entries', 'status', 'task',
    'direction', 'source_language', 'target_language', 'rights_status', 'source_rights_status',
    'local_experiment_only', 'publication_cleared', 'sentence_supervision', 'extraction_version', 'fact'})


def bounded_text(value, *, language=None):
    """Reject free-form/uncertain or overlong terms without rewriting spellings."""
    limit = MAX_FORM_CHARS if language is None else MAX_GLOSS_CHARS.get(language)
    if limit is None or not isinstance(value, str) or not value or value != value.strip():
        raise ValueError('Expected an exact nonempty bounded lexical string')
    if len(value) > limit or len(value.split()) > MAX_WORDS:
        raise ValueError('Lexical string exceeds the character/word bound')
    if any(unicodedata.category(c).startswith('C') or unicodedata.category(c) in ('Zl', 'Zp') for c in value):
        raise ValueError('Control characters and line breaks are excluded')
    if any(token in value for token in CONTROL_TOKENS):
        raise ValueError('Chat control markers are excluded')
    if '?' in value or '？' in value:
        raise ValueError('Explicitly uncertain lexical strings are excluded')
    return value


def variant_key(value):
    return ' '.join(unicodedata.normalize('NFC', value).translate(PUNCT).casefold().split())


def entry_id(form):
    canonical = ' '.join(form.translate(PUNCT).split())
    return 'fx-' + hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _validate_fact(fact, direction):
    if not isinstance(fact, dict) or set(fact) != FACT_FIELDS or direction not in DIRECTIONS:
        raise ValueError('Expected the bounded fact schema and one supported lexical direction')
    language = fact['language']
    if language not in ('ja', 'en') or language not in direction.split('-to-'):
        raise ValueError('Fact language and direction disagree')
    for field in ('forms', 'glosses'):
        terms = fact[field]
        if not isinstance(terms, list) or not 1 <= len(terms) <= MAX_ALTERNATIVES:
            raise ValueError('Expected a bounded complete alternatives list')
        if any(not isinstance(term, str) for term in terms) or len(terms) != len(set(terms)):
            raise ValueError('Alternatives must be unique strings')
        for term in terms:
            bounded_text(term, language=language if field == 'glosses' else None)
    if direction.startswith('fix-to-') and len(fact['forms']) != 1:
        raise ValueError('A forward lexical prompt has exactly one canonical headword')
    if direction.endswith('-to-fix') and len(fact['glosses']) != 1:
        raise ValueError('A reverse lexical prompt has exactly one recorded gloss')


def render_fact_messages(fact, direction):
    """Reconstruct the only permitted local-fact training wrapper exactly."""
    _validate_fact(fact, direction)
    if direction.startswith('fix-to-'):
        prompt = (f"Translate this recorded fiXmArge dictionary headword into {fact['language']}. "
                  "Return ALL recorded short lexical equivalents, separated by ' / '; preserve spelling. "
                  "This is lexical correspondence practice, not sentence-grammar supervision.\n"
                  f"Headword: {fact['forms'][0]}")
        answer = ' / '.join(fact['glosses'])
    else:
        prompt = (f"Return ALL recorded canonical fiXmArge headwords for this {fact['language']} dictionary gloss, "
                  "separated by ' / '; preserve letter case, spaces and punctuation. "
                  "This is lexical correspondence practice, not sentence-grammar supervision.\n"
                  f"Gloss: {fact['glosses'][0]}")
        answer = ' / '.join(fact['forms'])
    return [{'role':'user', 'content':prompt}, {'role':'assistant', 'content':answer}]


def make_fact_record(fact, direction, *, group_id=None, source_ids=None):
    _validate_fact(fact, direction)
    ids = sorted(entry_id(form) for form in fact['forms'])
    source, target = direction.split('-to-')
    metadata = {
        'group_id': group_id or 'fixfact-' + min(ids),
        'source': 'fiXmArge_lexical_facts', 'source_ids': sorted(set(source_ids or ['hecate-csv'])),
        'source_entries': ids, 'status': 'unreviewed_bounded_lexical_mapping',
        'task': LOCAL_FACT_TASK, 'direction': direction,
        'source_language': source, 'target_language': target,
        'rights_status': LOCAL_FACT_RIGHTS, 'source_rights_status': SOURCE_RIGHTS,
        'local_experiment_only': True, 'publication_cleared': False,
        'sentence_supervision': False, 'extraction_version': 1, 'fact': deepcopy(fact),
    }
    row = {'messages': render_fact_messages(fact, direction), 'metadata': metadata}
    validate_local_fact_record(row)
    return row


def validate_local_fact_record(row):
    """Accept only reconstructed bounded local experiments, never legal clearance."""
    if not isinstance(row, dict) or set(row) != {'messages', 'metadata'}:
        raise ValueError('Local fact record has unexpected top-level fields')
    meta = row['metadata']
    if not isinstance(meta, dict) or set(meta) != META_FIELDS:
        raise ValueError('Local fact metadata has unexpected or missing fields')
    fixed = {'source':'fiXmArge_lexical_facts', 'status':'unreviewed_bounded_lexical_mapping',
             'task':LOCAL_FACT_TASK, 'rights_status':LOCAL_FACT_RIGHTS, 'source_rights_status':SOURCE_RIGHTS}
    if any(meta.get(key) != value for key, value in fixed.items()):
        raise ValueError('Local experiment/source status must remain explicit and unchanged')
    for key, value in (('local_experiment_only', True), ('publication_cleared', False), ('sentence_supervision', False)):
        if type(meta[key]) is not bool or meta[key] is not value:
            raise ValueError('Local-only and non-clearance flags must be strict booleans')
    if type(meta['extraction_version']) is not int or meta['extraction_version'] != 1:
        raise ValueError('Unsupported extraction schema version')
    if not isinstance(meta['group_id'], str) or re.fullmatch(r'fixfact-fx-[0-9a-f]{16}', meta['group_id']) is None:
        raise ValueError('Invalid lexical family identifier')
    ids = meta['source_ids']
    if (not isinstance(ids, list) or not ids or any(not isinstance(value, str) or value not in SOURCE_IDS for value in ids)
            or ids != sorted(set(ids))):
        raise ValueError('Expected only the recorded source identifiers')
    direction = meta['direction']
    fact = meta['fact']
    _validate_fact(fact, direction)
    if [meta['source_language'], meta['target_language']] != direction.split('-to-'):
        raise ValueError('Language metadata does not match direction')
    if meta['source_entries'] != sorted(entry_id(form) for form in fact['forms']):
        raise ValueError('Source entry IDs do not match canonical forms')
    if row['messages'] != render_fact_messages(fact, direction):
        raise ValueError('Messages must exactly reconstruct the bounded lexical wrapper')
    return True
