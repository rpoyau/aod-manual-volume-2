#!/usr/bin/env python3
"""Read-only source/PDF binding, semantic Main-link and final print checks."""
import argparse
import json
from pathlib import Path
from publication_support import verify_publication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify_publication(args.root.resolve())
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status':'FAIL_PUBLICATION','error':str(exc)},indent=2))
        return 1
    print(json.dumps(result,indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
