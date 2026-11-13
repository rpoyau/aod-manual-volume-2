"""Load the exact current M3 producer without rebinding historical consumers."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
VENDOR = Path('manual2/vendor/aod_m3_producer')
HEAD = '8c3149b9d3d924b80b9385b178da4ba2c39175e8'
TREE = 'b2b55cbcf18354828f7b34418ab3fa26d747a927'
BINDING_SHA256 = 'a7fc7c6bb6fc4332e9ac151ae0afeb0a4211cc9fa18d5769adb3391905cea4ec'
MODULES = {
    'native': 'aod_native_closure_wave', 'mapping': 'aod_mapping_error',
    'cells': 'aod_cell_measures', 'temporal': 'aod_m3_temporal',
    'metrology': 'aod_m3_metrology', 'experimental': 'aod_m3_experimental',
}
_LOADED = {}


def require(value, message):
    if not value:
        raise ValueError('M3 producer: ' + message)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def verify(root=ROOT, upstream_root=None):
    root = Path(root).resolve()
    vendor = root / VENDOR
    raw = (vendor / 'binding.json').read_bytes()
    require(digest(raw) == BINDING_SHA256, 'unreviewed dependency binding')
    binding = json.loads(raw)
    require(binding['upstream_head'] == HEAD and binding['upstream_tree'] == TREE,
            'wrong producer identity')
    receipt = binding['producer_handoff']
    raw = (vendor / receipt['path']).read_bytes()
    require(digest(raw) == receipt['sha256'], 'producer handoff changed')
    handoff = json.loads(raw)
    require(handoff['binding']['successor_commit'] == HEAD
            and handoff['binding']['successor_tree'] == TREE,
            'handoff successor mismatch')
    require(receipt['readiness'] == 'producer_verified_in_scope', 'producer not ready')
    for name, row in binding['files'].items():
        require(digest((vendor / 'current' / name).read_bytes()) == row['sha256'],
                'export changed: ' + name)
    if upstream_root is not None:
        upstream = Path(upstream_root).resolve()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(upstream), *args], text=True).strip()
        require(git('rev-parse', 'HEAD') == HEAD and git('rev-parse', 'HEAD^{tree}') == TREE,
                'actual checkout is not the pinned producer')
        require(not git('diff', '--name-only', 'HEAD'), 'actual producer has tracked modifications')
        for name, row in binding['files'].items():
            require((upstream / row['upstream_path']).read_bytes()
                    == (vendor / 'current' / name).read_bytes(),
                    'export differs from actual producer: ' + name)
    return binding


@contextmanager
def _aliases(loaded):
    previous = {name: sys.modules.get(name) for name in loaded}
    sys.modules.update(loaded)
    try:
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def _load_folder(folder, binding):
    """Isolate module classes while retaining exact upstream file bytes/paths."""
    folder = Path(folder).resolve()
    tag = digest(str(folder).encode())[:16]
    loaded, exports = {}, {}
    with _aliases({name: sys.modules.get(name) for name in MODULES.values()}):
        for key, name in MODULES.items():
            spec = importlib.util.spec_from_file_location('_matter1_producer_' + tag + '_' + name,
                                                         folder / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
            exports[key] = module
            sys.modules[name] = module
    t, m, n, mt, e = (exports[k] for k in ('temporal','mapping','native','metrology','experimental'))
    require(t.n is n and t.m is m and mt.t is t and mt.m is m
            and e.t is t and e.m is m and e.mt is mt, 'mixed producer module identities')
    return SimpleNamespace(**exports, binding=binding, activate=lambda: _aliases(loaded))


def load(root=ROOT):
    binding = verify(root)
    folder = (Path(root) / VENDOR / 'current/manual/scripts').resolve()
    if folder not in _LOADED:
        _LOADED[folder] = _load_folder(folder, binding)
    require(_LOADED[folder].binding == binding, 'cached dependency identity changed')
    return _LOADED[folder]


def load_upstream(root, upstream_root):
    """Require the actual checkout before executing its independent modules."""
    binding = verify(root, upstream_root)
    return _load_folder(Path(upstream_root) / 'manual/scripts', binding)
