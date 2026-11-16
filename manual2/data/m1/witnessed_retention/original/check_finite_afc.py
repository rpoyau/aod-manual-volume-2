#!/usr/bin/env python3
"""Exact checks of a declared finite AFC model; no physical interpretation."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError('Use integers or exact rational strings, not floats/booleans.')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError('Invalid exact rational input.') from exc


def check(data):
    if not isinstance(data, dict) or set(data) - {'p', 'P', 'permutation'}:
        raise ValueError('Expected only p, P and optional permutation.')
    if not isinstance(data.get('p'), list) or not isinstance(data.get('P'), list):
        raise ValueError('p and P must be lists.')
    p = [rational(x) for x in data['p']]
    n = len(p)
    if not 1 <= n <= 10:
        raise ValueError('Exhaustive region checking supports 1 to 10 states.')
    if len(data['P']) != n or any(not isinstance(row, list) or len(row) != n for row in data['P']):
        raise ValueError('P must be square with the same dimension as p.')
    P = [[rational(x) for x in row] for row in data['P']]
    if any(x < 0 for x in p) or sum(p) != 1:
        raise ValueError('Memory must be nonnegative and normalized.')
    if any(x < 0 for row in P for x in row) or any(sum(row) != 1 for row in P):
        raise ValueError('Kernel must be nonnegative and row-stochastic.')
    updated = [sum(p[i] * P[i][j] for i in range(n)) for j in range(n)]
    phi = [[p[i] * P[i][j] - p[j] * P[j][i] for j in range(n)] for i in range(n)]
    divergence = [sum(row) for row in phi]
    if sum(updated) != 1 or any(x < 0 for x in updated):
        raise ValueError('Updated memory normalization failed.')
    if any(phi[i][j] != -phi[j][i] or abs(phi[i][j]) > 1 for i in range(n) for j in range(n)):
        raise ValueError('Normalized flux antisymmetry/bound failed.')
    for mask in range(1 << n):
        region = {i for i in range(n) if mask & (1 << i)}
        interior = sum(divergence[i] for i in region)
        boundary = sum(phi[i][j] for i in region for j in range(n) if j not in region)
        if interior != boundary:
            raise ValueError('Finite Stokes failed for region ' + str(sorted(region)))
    result = {
        'scope': 'declared_exact_finite_AFC_fixture',
        'status': 'PASS', 'states': n, 'regions_checked': 1 << n,
        'updated_memory': [str(x) for x in updated],
        'flux': [[str(x) for x in row] for row in phi],
        'divergence': [str(x) for x in divergence],
        'physical_prediction': False,
    }
    if 'permutation' in data:
        perm = data['permutation']
        if (not isinstance(perm, list) or len(perm) != n
                or any(type(x) is not int for x in perm) or sorted(perm) != list(range(n))):
            raise ValueError('permutation must contain every state index exactly once.')
        p_invariant = all(p[i] == p[perm[i]] for i in range(n))
        P_invariant = all(P[i][j] == P[perm[i]][perm[j]] for i in range(n) for j in range(n))
        phi_invariant = all(phi[i][j] == phi[perm[i]][perm[j]] for i in range(n) for j in range(n))
        result['permutation_check'] = {
            'memory_invariant': p_invariant,
            'kernel_invariant': P_invariant,
            'flux_invariant': phi_invariant,
            'joint_sufficient_hypotheses_met': p_invariant and P_invariant,
        }
        if p_invariant and P_invariant and not phi_invariant:
            raise ValueError('Joint-invariance implication failed.')
    return result


def examples():
    kernel = [['1/2', '1/2'], ['1/2', '1/2']]
    negative = check({'p': [1, 0], 'P': kernel, 'permutation': [1, 0]})
    positive = check({'p': ['1/2', '1/2'], 'P': kernel, 'permutation': [1, 0]})
    if negative['permutation_check']['flux_invariant'] or not positive['permutation_check']['flux_invariant']:
        raise ValueError('Isotropy controls did not discriminate.')
    return {'kernel_only_counterexample': negative, 'joint_invariance_control': positive}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    args = parser.parse_args()
    try:
        result = check(json.loads(args.input.read_text())) if args.input else examples()
    except (ValueError, OSError) as exc:
        print(json.dumps({'status': 'INVALID_OR_FAILED', 'message': str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
