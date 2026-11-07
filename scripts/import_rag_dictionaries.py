"""Build a new local RAG dictionary from pinned, additive source registrations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fixmarge.dictionary_import import import_dictionaries


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--registry', type=Path, default=Path('configs/rag-dictionary-imports.json'))
    parser.add_argument('--output', type=Path, required=True, help='A new directory inside the project; existing outputs are rejected')
    args = parser.parse_args(argv)
    try:
        report = import_dictionaries(root=args.root, registry=args.registry, output=args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps({'status': report['status'], 'output': report['output'],
                      'base_entries': report['base_entries'], 'merged_entries': report['merged_entries'],
                      'new_entries': report['new_entries'], 'merged_Korean_entries': report['merged_Korean_entries'],
                      'source_claim_differences': {source['id']: source['source_claim_differences'] for source in report['sources']},
                      'training_performed': False, 'network_access': False}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
