"""Manual I data-card overlay. This checker classifies bound records, not physics.

No model is executed or repaired. D0 and O0 describe selected support, while
record form, claim class, source outcome and decimal scope remain independent.
The immutable source lock binds this version of the overlay to existing bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'manual2/data/m1/'
REGISTRY = BASE + 'classification/data_cards.json'
LOCK = 'manual2/evidence/data-classes/source-bindings.json'
LOCK_SHA256 = 'c7cb00b17666e3b23fbc6e56165de81d5c0e6cc310d646925e2da6ac52ccba52'
AUTHORITY_COMMIT = '71cbcf7e637ababcde3b2e073fb4ceec4b1681b9'
AUTHORITY_TREE = '3ab04df3793beda481b4fb7ed0d628ba6765da70'
SUPPORT = {'D0': 'exact internal fixture', 'O0': 'observable-map fixture'}
CLAIMS = ('native exact fixture', 'declared model/simulation', 'metrology record', 'empirical comparison')
FORMS = ('AΩ field record', 'Measured target record', 'External comparison record', 'Observable-map record', 'Exact fixture', 'Benchmark manifest', 'Calibration anchor')
DISPLAY = ('internal', 'external', 'measured', 'derived external', 'value map', 'demonstration')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field: ' + key)
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + value)))


def safe_path(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'relative source path required')
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'source path escaped repository')
    require(path.is_file(), 'missing bound source: ' + relative)
    return path


def select(document, pointer):
    require(isinstance(pointer, str) and (pointer == '' or pointer.startswith('/')), 'invalid JSON pointer')
    result = document
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(result, list):
            require(token.isdigit() and str(int(token)) == token, 'noncanonical list index')
            result = result[int(token)]
        else:
            require(isinstance(result, dict) and token in result, 'missing selector: ' + pointer)
            result = result[token]
    return result


def _spec(id_, path, selectors, support, form, claim, scopes, inputs, model, coordinate, uncertainty, residual, limits, statuses=()):
    return dict(id=id_, path=BASE + path, selectors=list(selectors), support=support,
                form=form, claim=claim, scopes=list(scopes), inputs=inputs, model=model,
                coordinate=coordinate, uncertainty=uncertainty, residual=residual,
                limits=limits, statuses=list(statuses))


def specifications():
    """Versioned dispatch contract; IDs name artifact components, not new classes."""
    return [
        _spec('static-reference', 'matter1_audit_report.json', ['/executed_checks','/native_evidence_lanes','/interpretation'], None, 'Benchmark manifest', CLAIMS[1], ['internal'],
              '118 reference-A selections and 126 placement slots; source selection provenance remains unresolved', 'Exact declared grouping and conditional support arithmetic', 'slot/count and exact conditional support sum', 'Exact arithmetic of declared inputs; no physical uncertainty inferred', None,
              'Static arithmetic is not a returned-current gate/comparator fixture.', ['/profile','/status','/interpretation']),
        _spec('folding-current-comparator', 'folding/temporal_report.json', ['/comparison_rows','/response_rows','/statuses','/certificates'], 'D0', 'Exact fixture', CLAIMS[1], ['internal'],
              'Finite declared H1 return/contact histories', 'Committed comparator and signed current-pair response', 'exact recurrence ratio, lag and signed pair residual', 'Exact finite model operands', 'signed pair cancellation; scoped comparator residual',
              'D0 covers this internal comparator audit only; finite witnesses are not complete motif admission.', ['/finite_model_execution','/statuses','/certificates']),
        _spec('campaign-current-audit', 'campaign/cases/Z001-A001.json', ['/result/execution','/result/observation','/result/trajectory/contacts','/result/physical'], 'D0', 'Exact fixture', CLAIMS[0], ['internal'],
              'H-1 generic neutral fixture; distinct p/e constituents and committed native return pairs', 'Current-native compare and exact directed-contact audit within declared pacing', 'native current-pair RCD, recurrence count and lag', 'Exact fixture operands; no SI unit supplied', 'internal pair/comparator consistency, not a spectral residual',
              'Native exact fixture identifies selected typed comparisons only, not hydrogen atomic admission or the whole campaign model.', ['/result/execution/status','/result/execution/native_inner_and_outer_returns_admitted','/result/physical']),
        _spec('campaign-declared-dynamics', 'campaign/prediction.json', ['/configuration_count','/native_comparisons','/unresolved_dependencies','/physical_atomic_prediction','/physical_half_life_prediction'], None, 'Benchmark manifest', CLAIMS[1], ['internal'],
              '135 distinct (Z,A) neutral generic preparations; all source state records retained separately', 'Versioned finite state-dependent recurrence law and independent 3:3:6 reference', 'bounded returns/lag in configuration-specific scheduler windows', 'Exact sampled finite history; no atomic preparation/map uncertainty supplied', None,
              'A declared campaign is not automatically a D0 fixture or O0 atomic-frequency comparison.', ['/configuration_count','/physical_atomic_prediction','/physical_half_life_prediction','/target_access']),
        _spec('hydrogen-measured-transition', 'hyperfine/target_inventory.json', ['/transitions/0','/sources'], None, 'Measured target record', CLAIMS[2], ['measured'],
              'Historical H-1 ground-state hyperfine interval; known target exposure', 'Source transcription, with published combined uncertainty retained', 'transition frequency Hz', 'Published one-sigma 0.002 Hz; shared-reference covariance not independently reconstructed', None,
              'A raw measured target does not instantiate an O0 map or a native prediction.', ['/transitions/0/role','/transitions/0/native_mapping_status','/transitions/0/uncertainty_kind']),
        _spec('cesium-defining-anchor', 'hyperfine/target_inventory.json', ['/transitions/1','/sources'], None, 'Calibration anchor', CLAIMS[2], ['external'],
              'Cs-133 SI defining unperturbed transition', 'Convention anchor; realized oscillator uncertainty is separate', 'exact defining frequency Hz', 'Definition uncertainty zero; realization uncertainty is not zero by definition', 'convention identity only',
              'A defining anchor is not an independent prediction or measured realization.', ['/transitions/1/role','/transitions/1/uncertainty_kind','/transitions/1/realization_uncertainty_hz']),
        _spec('isotope-finite-targets', 'isotopes/catalog.json', ['/isotopes/'+str(i) for i in [*range(5,16),*range(17,24),25]] + ['/sources'], None, 'Measured target record', CLAIMS[2], ['measured'],
              'Finite selected evaluated half-life records; original nuclear-state and tentative-isomer assignments retained', 'Selected source transcription and decimal SI-prefix conversion; no averaging', 'total half-life seconds; partial channels and individual delays remain distinct', 'Source asymmetric uncertainties and confidence qualifications; no distribution invented', None,
              'Selected finite target rows only. Neither evaluation nor tentative state assignment establishes native isotope identity.'),
        _spec('isotope-nonpoint-inventory', 'isotopes/catalog.json', ['/isotopes/'+str(i) for i in [0,1,2,3,4,16,24,26]] + ['/coverage'], None, 'Benchmark manifest', CLAIMS[2], ['external'],
              'Observational stability, unknown/tentative records, Fl-298 unobserved declaration and rejected Og-295 candidate', 'Source inventory with original qualifications; no point target assigned', 'qualified record or unknown, not zero/infinite half-life', 'Null value and unknown uncertainty remain null; no measured point inferred', None,
              'Not every catalog row is measured. Model-target declarations remain declarations, and source crosschecks are not promoted.'),
        _spec('atomic-observation-declaration', 'hyperfine/observation_map.json', [''], 'O0', 'Observable-map record', CLAIMS[1], ['value map'],
              'Specified atomic transition endpoints and required construction/comparison stages', 'Declared observation-map contract; map and atomic configuration operands absent', 'intended frequency ratio and phase lag', 'Not supplied for a completed physical map', 'intended target residual; not evaluated',
              'O0 identifies intended observable-map support only. Declaration has no completed map value or empirical score.', ['/map_status','/native_admission_status','/native_execution_status','/empirical_status','/predicted_frequency_ratio','/empirical_score']),
        _spec('atomic-countermodel-residuals', 'atomic/comparison.json', ['/rows','/classification','/selection_policy','/covariance_status'], 'O0', 'External comparison record', CLAIMS[1], ['value map'],
              'Unselected conditional observation maps and the exposed H-1 target', 'Retrospective underdetermination diagnostics; no map selected or fitted', 'conditional frequency residual Hz and relative residual', 'Atomic-map uncertainty/joint covariance incomplete; standardized residual null', 'conditional diagnostic residual, not an empirical AOD score',
              'Computed diagnostic residuals do not establish an atomic prediction or empirical agreement.', ['/atomic_empirical_score','/atomic_prediction_test_status','/classification']),
        _spec('conventional-hyperfine-benchmark', 'atomic/benchmark.json', ['/rows','/approximation','/input_uncertainties'], None, 'Benchmark manifest', CLAIMS[1], ['demonstration'],
              'Conventional spin-only Hamiltonian with measured/defining zero-field inputs', 'External calibrated benchmark, including its stated approximations', 'frequency and field-shift Hz', 'Partial benchmark uncertainty; no precision-spectroscopy claim', None,
              'A conventional calibrated calculation is not native AOD output; zero-field agreement is calibration.', ['/classification','/native_atomic_prediction','/uncertainty_status','/zero_field_agreement_role']),
        _spec('source-metrology-reductions', 'm3_metrology/metrology_report.json', ['/hydrogen','/cesium','/isotope_applications/livermorium'], None, 'Benchmark manifest', CLAIMS[2], ['derived external'],
              'Published H Table IV/VI and Cs realization records; selected Lv event delays', 'Source-bound metrological reductions with acquisition protocols', 'source frequency/correction Hz and individual event delay seconds', 'Published uncertainty retained; full model/realization covariance not silently supplied', None,
              'Source reductions are distinct from atomic prediction and half-life estimates from individual delays.', ['/independent_physical_prediction','/physical_calibration','/complete_physical_uncertainty']),
        _spec('finite-survival-internal-audit', 'survival/survival_report.json', ['/exact_assertions','/causal_control','/statuses','/native_medians'], 'D0', 'Exact fixture', CLAIMS[1], ['internal'],
              'Declared finite Q4 histories, exact gates and competing outcomes', 'Exact finite kernel, probability conservation and antisymmetric-response controls', 'survival and first-discrete-crossing reference-return count', 'Exact finite distribution; no physical loss/time map uncertainty supplied', 'probability-mass and internal pair residuals',
              'D0 covers exact internal checks in the declared survival model, not physical isotope admission or seconds.', ['/statuses','/physical_prediction_executed','/geometry_or_test_success_is_native_admission']),
        _spec('deuterium-tritium-target-supplement', 'external_transitions/catalog.json', ['/records','/source_rows','/warnings'], None, 'Measured target record', CLAIMS[2], ['derived external','external'],
              'D/H and T/H maser comparisons; H-conditioned reported frequencies and separately untranscribed original T value', 'Source acquisition and evaluated reference rescaling; not native simulation', 'ground-state hyperfine Hz with source reference dependence retained', 'Evaluated T standard uncertainty 0.007 Hz with legacy-source caveat; primary D abstract qualification separate; distribution, coverage probability and joint covariance remain unknown', None,
              'Metrology record names the source-acquisition role only. Original row scientific_claim_class remains null; no map or empirical score is added.', ['/scope','/missing_dependencies_unchanged','/records/0/scientific_claim_class','/records/1/value_hz','/records/2/scientific_claim_class']),
    ]


def expected_registry(root, lock):
    cards = []
    for spec in specifications():
        path = spec['path']
        require(path in lock['artifacts'], 'artifact absent from classification source lock: ' + path)
        source = read(safe_path(root, path))
        selectors = spec['selectors']
        selected = [select(source, pointer) for pointer in selectors]
        code = spec['support']
        cards.append({
            'id': spec['id'],
            'support_class': {'code': code, 'name': SUPPORT.get(code), 'scope': spec['limits']},
            'record_form': spec['form'], 'claim_class': spec['claim'],
            'data_card': {'D': spec['inputs'], 'C_support': code, 'M_AOmega': spec['model'],
                          'Pi_report': spec['coordinate'], 'sigma_input': spec['uncertainty'],
                          'epsilon_report': spec['residual'], 'src': [path]},
            'decimal_display': {'scopes': spec['scopes'], 'policy': 'Preserve source value, unit, uncertainty, rounding and qualification. Exact decimal transcription does not imply exact physical measurement.'},
            'execution_outcome': {'source_fields': {p: select(source, p) for p in spec['statuses']},
                                  'classifier_executes_model': False, 'classifier_confers_native_admission': False,
                                  'classifier_confers_physical_prediction': False, 'classifier_confers_empirical_agreement': False},
            'bindings': [{'path': path, 'sha256': lock['artifacts'][path], 'json_pointers': selectors,
                          'selected_sha256': digest_bytes(canonical(selected).encode())}],
        })
    return {'schema': 'matter1.manual-i-data-cards.v1', 'authority_commit': AUTHORITY_COMMIT,
            'source_lock': {'path': LOCK, 'sha256': LOCK_SHA256},
            'scope': 'Classification overlay for selected existing artifact families/components; not scientific replay, native admission, physical prediction or empirical scoring.',
            'null_support_semantics': 'No applicable instantiated Manual I support class for this component; null is metadata, not a new support class.',
            'cards': cards}


def verify(root=ROOT):
    root = Path(root)
    lock_path = safe_path(root, LOCK)
    require(digest_bytes(lock_path.read_bytes()) == LOCK_SHA256, 'classification source lock changed')
    lock = read(lock_path)
    require(lock['authority']['commit'] == AUTHORITY_COMMIT and lock['authority']['tree'] == AUTHORITY_TREE, 'wrong Manual I authority')
    for path, sha in {**lock['artifacts'], **lock['authority']['files']}.items():
        require(digest_bytes(safe_path(root, path).read_bytes()) == sha, 'bound source changed: ' + path)
    observed = read(safe_path(root, REGISTRY))
    expected = expected_registry(root, lock)
    require(canonical(observed) == canonical(expected), 'classification dispatch/card mismatch: class, binding, scope or source outcome changed')
    # These checks document independent axes even if the versioned dispatch is changed.
    for card in observed['cards']:
        code = card['support_class']['code']
        require(code in (None, 'D0', 'O0'), 'unknown support class')
        require(card['record_form'] in FORMS and card['claim_class'] in CLAIMS, 'unknown record/claim class')
        require(all(scope in DISPLAY for scope in card['decimal_display']['scopes']), 'unknown decimal scope')
        if card['record_form'] in ('Measured target record', 'Calibration anchor'):
            require(code is None and card['claim_class'] == 'metrology record', 'raw external data promoted to native/map output')
        if code == 'D0':
            require(card['record_form'] == 'Exact fixture' and card['decimal_display']['scopes'] == ['internal'], 'D0 applied outside selected internal fixture')
        if code == 'O0':
            require(card['record_form'] in ('Observable-map record', 'External comparison record'), 'O0 requires a scoped map/comparison record')
    return {'status': 'PASS_CLASSIFICATION_BINDINGS_ONLY', 'schema': 'matter1.manual-i-classification-check.v1',
            'cards': len(observed['cards']), 'source_artifacts': len(lock['artifacts']),
            'support_codes': {code: sum(card['support_class']['code'] == code for card in observed['cards']) for code in SUPPORT},
            'authority_commit': AUTHORITY_COMMIT, 'registry_sha256': digest_bytes(safe_path(root, REGISTRY).read_bytes()),
            'scope': observed['scope'], 'executed_models': 0, 'replayed_campaign_cases': 0,
            'native_admission_verified': False, 'physical_predictions_verified': False, 'empirical_agreement_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2, sort_keys=True))
    except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'FAIL_CLASSIFICATION_BINDINGS', 'error': str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
