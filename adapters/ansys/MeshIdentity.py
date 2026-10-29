"""Exact native 2D mesh identity modulo node and element numbering only."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def canonical(folder):
    folder = Path(folder)
    with (folder / 'mesh_nodes_SI.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    nodes = {(r['mesh_file'], r['node_id']): tuple(str(Decimal(r[k]).normalize()) for k in ['x_m','y_m','z_m']) for r in rows}
    if len(nodes) != len(rows): raise ValueError('Duplicate native node identity')
    elements = []
    with (folder / 'mesh_records.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            values = [x.strip() for x in row['native_values'].split(',')]
            if row['record_kind'] != 't' or row['declared_arity'] != '6' or len(values) != 6:
                raise ValueError('Unrecognized native mesh record; exact comparison cannot certify it')
            coords = sorted(nodes[(row['mesh_file'], n)] for n in values[1:4])
            # Keep both trailing native markers without assigning undocumented semantics.
            elements.append([coords, values[4:]])
    payload = {'coordinates': sorted(nodes.values()), 'elements': sorted(elements)}
    return {'sha256': hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),
            'nodes': len(nodes), 'records': len(elements),
            'normalization': 'Exact decimal coordinates, sorted node/element identity; all trailing markers retained; no coordinate tolerance'}
