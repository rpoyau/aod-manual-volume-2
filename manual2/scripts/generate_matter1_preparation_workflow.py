#!/usr/bin/env python3
"""Explicitly generate the paired preparation products, or one selected reference."""
import argparse
from pathlib import Path
import json
import matter1_preparation_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=workflow.ROOT)
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--execute-reference', type=int)
    parser.add_argument('--preparation', choices=('bare', 'neutral'))
    args = parser.parse_args()
    if args.execute_reference is not None:
        if args.preparation is None or args.output_root is None:
            parser.error('A selected reference needs --preparation and --output-root')
        row, result = workflow.execute_reference(args.execute_reference, args.preparation, args.root)
        path = args.output_root/'reference-runs'/(row['id']+'.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(workflow.canonical({'preparation': row, 'execution': result}))
        print(json.dumps({'status': 'EXECUTED_CONDITIONAL_REFERENCE', 'path': str(path),
                          'physical_prediction': None}))
    else:
        if args.preparation is not None:
            parser.error('--preparation requires --execute-reference')
        print(json.dumps(workflow.generate(args.root, args.output_root), indent=2))


if __name__ == '__main__':
    main()
