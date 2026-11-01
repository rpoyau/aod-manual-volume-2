"""Persisted full-execution regressions for the checked M3 evidence dependency.

These are declared rational map fixtures, not physical uncertainty estimates.
Every hostile evidence payload is deliberately resealed and independently
trusted so that stale hashes cannot substitute for the numeric-type guard.
"""
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'manual2/scripts'))
from matter1_m3 import mapping

_SAME_VALUE = object()


class M3EvidenceExecutionTests(unittest.TestCase):
    def setUp(self):
        self.m = mapping(ROOT)

    def fixture(self, kind, claim, evidence_value=_SAME_VALUE, law=None):
        """Bind the evidence to the complete map using its public constructors."""
        m = self.m
        record = m.example_map()
        model = record['sources'][0]
        output = record['codomain'][0]
        payload = {
            'model_sha256': m.model_sha256(record),
            'output': output['name'], 'component': 'window', 'kind': kind,
            'unit': output['unit'], 'included_sources': {},
            'value': claim if evidence_value is _SAME_VALUE else evidence_value,
        }
        if kind == 'standard_uncertainty':
            amount = Fraction(claim)
            payload['joint_law'] = law if law is not None else [
                ['1/2', {'error': str(-amount)}],
                ['1/2', {'error': str(amount)}],
            ]
        evidence = m.source('evidence:window', 'model', {'result': payload})
        record['sources'].append(evidence)
        record['error']['y']['window'] = {
            'kind': kind, 'value': claim, 'unit': output['unit'],
            'reason': 'declared finite output-error fixture',
            'included_sources': {},
            'evidence': {'source_id': evidence['id'], 'payload_key': 'result',
                         'sha256': evidence['sha256']},
        }
        record = m.seal(record)
        values = {'x': m.value(record['domain'][0], '3',
            {model['id']: model['sha256']},
            {'kind': 'source', 'source_id': model['id'], 'payload_key': 'input'})}
        return {'record': record, 'values': values,
                'trusted': {item['id']: item for item in record['sources']}}

    def execute_persisted(self, fixture):
        """Round-trip actual JSON bytes and call the verified vendor's run_map."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'evidence-execution.json'
            path.write_text(json.dumps(fixture, sort_keys=True) + '\n')
            before = path.read_bytes()
            stored = json.loads(before)
            record, trusted = stored['record'], stored['trusted']
            evidence = trusted['evidence:window']
            payload = evidence['payload']['result']
            original = fixture['trusted']['evidence:window']['payload']['result']
            self.assertIs(type(payload['value']), type(original['value']))
            self.assertEqual(evidence['sha256'], self.m.digest(evidence['payload']))
            self.assertEqual(record['error']['y']['window']['evidence']['sha256'],
                             evidence['sha256'])
            self.assertEqual(payload['model_sha256'], self.m.model_sha256(record))
            self.assertEqual(record['spec_sha256'], self.m.digest(
                {key: value for key, value in record.items() if key != 'spec_sha256'}))
            self.m.validate_sources(record['sources'], trusted)
            try:
                return self.m.run_map(record, stored['values'], trusted)
            finally:
                self.assertEqual(path.read_bytes(), before)

    def test_matching_exact_integer_and_rational_controls_execute(self):
        for kind in ('bound', 'standard_uncertainty'):
            for amount in (0, 1, '0', '1/2'):
                with self.subTest(kind=kind, amount=repr(amount)):
                    result = self.execute_persisted(self.fixture(kind, amount))
                    self.assertEqual(result['outputs']['y']['value'], '6')
                    self.assertIn('evidence:window', result['provenance'])
                    self.assertEqual(set(result['operand_sources']['y']), {'model:scale'})

    def test_rehashed_boolean_and_float_evidence_is_rejected(self):
        for kind in ('bound', 'standard_uncertainty'):
            for payload_value, claim in ((False, 0), (True, 1), (0.0, 0), (1.0, 1)):
                with self.subTest(kind=kind, payload=repr(payload_value)):
                    with self.assertRaisesRegex(self.m.ContractError,
                            'exact rational required; floats and booleans are forbidden'):
                        self.execute_persisted(self.fixture(kind, claim, payload_value))

    def test_negative_evidence_is_rejected_as_nonnegative_error(self):
        for kind in ('bound', 'standard_uncertainty'):
            for payload_value in (-1, '-1/2'):
                with self.subTest(kind=kind, payload=payload_value):
                    with self.assertRaisesRegex(self.m.ContractError, 'nonnegative'):
                        self.execute_persisted(self.fixture(kind, 1, payload_value))

    def test_malformed_rational_evidence_is_rejected(self):
        for kind in ('bound', 'standard_uncertainty'):
            for payload_value in ('not-a-rational', '1/0'):
                with self.subTest(kind=kind, payload=payload_value):
                    with self.assertRaisesRegex(self.m.ContractError, 'invalid rational'):
                        self.execute_persisted(self.fixture(kind, 1, payload_value))

    def test_equivalent_rational_representations_must_still_match(self):
        for kind in ('bound', 'standard_uncertainty'):
            for claim, payload_value in ((1, '1'), ('1', 1), (0, '0'),
                                         ('1/2', '2/4')):
                with self.subTest(kind=kind, claim=repr(claim), payload=repr(payload_value)):
                    with self.assertRaisesRegex(self.m.ContractError, 'evidence disagrees'):
                        self.execute_persisted(self.fixture(kind, claim, payload_value))

    def test_changed_exact_value_cannot_match_claim(self):
        for kind in ('bound', 'standard_uncertainty'):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(self.m.ContractError, 'evidence disagrees'):
                    self.execute_persisted(self.fixture(kind, 1, 2))

    def test_matching_standard_uncertainty_still_requires_its_variance(self):
        law = [['1/2', {'error': '-2'}], ['1/2', {'error': '2'}]]
        with self.assertRaisesRegex(self.m.ContractError,
                'standard uncertainty disagrees with supplied law'):
            self.execute_persisted(self.fixture('standard_uncertainty', 1, law=law))


if __name__ == '__main__':
    unittest.main()
