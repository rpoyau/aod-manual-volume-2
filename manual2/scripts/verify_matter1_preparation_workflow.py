#!/usr/bin/env python3
"""Read-only original-input replay of the new preparation and uncertainty products."""
import argparse
from pathlib import Path
import json
import matter1_preparation_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=workflow.ROOT)
    args = parser.parse_args()
    try:
        result = workflow.verify(args.root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'FAIL_PAIRED_PREPARATION_REPLAY', 'error': str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
