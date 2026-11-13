"""Read-only whole-report replay from the separately retained R03 inputs."""
import argparse
import json
from pathlib import Path
from matter1_m3_observation import ROOT, verify

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check-data', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'M3 observation verification failed: {exc}\n')
