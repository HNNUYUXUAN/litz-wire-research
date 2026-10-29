"""Project mixed-repository manifests onto one explicitly identified API snapshot."""
import re

def for_repository(catalog,publications,supplemental,repository):
    parent=catalog['repository']
    manifests=[publications]+([supplemental] if supplemental is not None else [])
    allowed={parent,*[d.get('repository',parent) for d in catalog['datasets'].values()],
             *[m.get('repository',parent) for m in manifests]}
    for value in allowed:
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value) or any(p in {'.','..'} for p in value.split('/')):
            raise ValueError('Invalid release repository identity')
    if repository not in allowed:return catalog,publications,supplemental
    selected=dict(catalog,repository=repository,datasets={name:d for name,d in catalog['datasets'].items() if d.get('repository',parent)==repository})
    projected=[dict(m,artifacts=m['artifacts'] if m.get('repository',parent)==repository else []) for m in manifests]
    return selected,projected[0],projected[1] if supplemental is not None else None
