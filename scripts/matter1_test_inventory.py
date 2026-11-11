#!/usr/bin/env python3
"""Shared optimized-suite inventory for execution and acceptance recording.

The campaign suite retains its separate complete replay/test receipt. Adding an
optimized validation module here updates both the runner and recorder together.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import unittest

OPTIMIZED_MODULES = frozenset({
    'test_matter1_acceptance_inventory',
    'test_matter1_application', 'test_matter1_data', 'test_matter1_folding',
    'test_matter1_temporal', 'test_matter1_hyperfine', 'test_matter1_stateful',
    'test_matter1_metrology', 'test_matter1_atomic', 'test_matter1_bipm',
    'test_matter1_v2_application', 'test_matter1_m3', 'test_matter1_m3_evidence',
    'test_matter1_bipm_precision', 'test_matter1_isotopes', 'test_matter1_survival',
    'test_matter1_isotope_integration', 'test_matter1_constructed_coupling',
    'test_matter1_witnessed_retention', 'test_matter1_retention_adapter',
    'test_matter1_m3_observation', 'test_matter1_m3_metrology',
    'test_matter1_data_classes', 'test_matter1_external_transitions',
    'test_matter1_properties', 'test_matter1_property_model',
    'test_matter1_coupled_preparations', 'test_matter1_preparation_workflow',
    'test_matter1_m3_producer',
})


def optimized_module_names():
    return ['manual2.tests.' + name for name in sorted(OPTIMIZED_MODULES)]


def load_optimized_suite():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(optimized_module_names())
    if loader.errors:
        raise RuntimeError('Cannot load the complete optimized inventory:\n' + '\n'.join(loader.errors))
    return suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--run-optimized', action='store_true')
    actions.add_argument('--list-optimized', action='store_true')
    args = parser.parse_args()
    if args.list_optimized:
        print('\n'.join(optimized_module_names()))
        return 0
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    result = unittest.TextTestRunner(verbosity=2).run(load_optimized_suite())
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
