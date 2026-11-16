"""Source-bound property inspector payload; no inference from display labels."""
from __future__ import annotations
import json
from pathlib import Path


def input_paths(root: Path) -> list[Path]:
    folder = root / 'manual2/data/m1/properties'
    return [folder / name for name in (
        'definitions.json', 'states.json', 'catalog.json', 'coverage.json',
        'source_manifest.json', 'model/prediction.json', 'model/obligations.json')]


def ui_projection(root: Path) -> dict:
    names = ('definitions', 'states', 'catalog', 'coverage', 'sources')
    paths = input_paths(root)
    prediction = json.loads(paths[-2].read_text())
    obligations = json.loads(paths[-1].read_text())
    return {'schema': 'matter1.property-inspector.v1', 'model': {
        'physical_prediction_complete': prediction['physical_prediction_complete'],
        'rows': [{key: row[key] for key in ('entity_id', 'native_observation', 'physical_properties')}
                 for row in prediction['rows']],
        'dependencies': obligations['items']}, **{
        name: json.loads(path.read_text())
        for name, path in zip(names, paths[:5])}}
