"""Export only selected project conversations from the desktop's read-only history.

Retains user-visible messages and action evidence. Internal reasoning and account
or session databases are not exported. Run again into a new destination at closure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

def export(database, inventory, destination):
    selected=json.loads(Path(inventory).read_text(encoding='utf-8'))
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    db=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    records=[]
    try:
        db.execute('BEGIN')
        for thread in selected:
            turns=[dict(row) for row in db.execute('SELECT * FROM thread_turns WHERE thread_id=? ORDER BY rollout_ordinal',(thread['id'],))]
            items=[];omitted={}
            for row in db.execute('SELECT * FROM thread_items WHERE thread_id=? ORDER BY rollout_ordinal',(thread['id'],)):
                item=dict(row)
                if 'reason' in item['item_type'].lower():
                    omitted[item['item_type']]=omitted.get(item['item_type'],0)+1;continue
                item['item']=json.loads(item.pop('item_json'));items.append(item)
            value={'thread':thread,'turns':turns,'items':items,'omitted_internal_item_counts':omitted}
            path=destination/(thread['id']+'.json')
            path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
            records.append({'id':thread['id'],'title':thread['title'],'turns':len(turns),'items':len(items),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    finally:db.close()
    manifest={'scope':'Selected project user-visible conversation history; internal reasoning excluded; credentials excluded by subsequent private-backup audit','threads':records}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'threads':len(records),'turns':sum(r['turns'] for r in records),'items':sum(r['items'] for r in records)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--inventory',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();print(json.dumps(export(a.database,a.inventory,a.destination)))
