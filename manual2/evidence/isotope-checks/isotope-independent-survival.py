#!/usr/bin/env python3
"""Independent exact state-aggregated check of the full-history survival output.

This review probe is intentionally a different representation from the production
executor: it combines mass by memory for arithmetic only. It neither verifies
native admission nor endorses erasure of the production history/lineage records.
"""
import argparse
from collections import defaultdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path


def check(root):
    source = Path(root) / 'manual2/data/m1/survival/prediction.json'
    blob = source.read_bytes()
    prediction = json.loads(blob)
    checks = {}
    for name, run in prediction['runs'].items():
        parameters = run['parameters']
        capacity, gain = Q(parameters['capacity']), Q(parameters['loss_gain'])
        states = {Q(0): Q(1)}
        survival = [Q(1)]
        lost = Q(0)
        for count in range(1, 9):
            following = defaultdict(Q)
            for memory, mass in states.items():
                exit_weight = gain * max(Q(0), abs(memory) - capacity)
                normalization = 2 + exit_weight
                lost += mass * exit_weight / normalization
                for sign in (-1, 1):
                    disabled_from = parameters['disable_feedback_from_count']
                    response = sign if disabled_from is None or count < disabled_from else 0
                    following[memory + response] += mass / normalization
            states = following
            survival.append(sum(states.values()))
            if sum(states.values()) + lost != 1:
                raise ValueError(f'{name}: independent probability mass check failed at {count}')
        expected = [Q(row['survival']) for row in run['rows']]
        if survival != expected:
            raise ValueError(f'{name}: independent recurrence differs from history enumeration')
        checks[name] = {'all_nine_survival_values_match': True,
                        'survival': [str(x) for x in survival],
                        'end_survival': str(survival[-1]),
                        'final_aggregated_memory_states': len(states),
                        'mass_conserved_at_each_step': True}
    if set(checks) != {'baseline', 'loss_gain_2', 'feedback_off', 'capacity_0'}:
        raise ValueError('Unexpected variant inventory')
    return {'status': 'PASS_INDEPENDENT_SURVIVAL_ARITHMETIC',
            'input_sha256': hashlib.sha256(blob).hexdigest(),
            'scope': 'Independent exact state-aggregated recurrence checks enumeration arithmetic only; no native isotope admission or physical half-life claim.',
            'variants': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.root), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
