"""Build requests for an explicitly owned AEDT session and a new Maxwell run."""
from pathlib import Path
import argparse,json

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',required=True);p.add_argument('--run-id',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=next(x for x in Path(__file__).resolve().parents if (x/'pyproject.toml').exists());port=json.loads(Path(a.session).read_text())['port']
    code='import sys;sys.path.insert(0,'+repr(str(root/'adapters/ansys'))+');from MCPMaxwellCase import execute;result=execute('+repr(str(root))+','+repr(str(root/'outputs'/a.run_id))+','+str(port)+');print(result["execution_status"])'
    calls=[{'name':'check_aedt_installed','arguments':{}},{'name':'connect_to_aedt','arguments':{'port':port,'version':'2025.2','non_graphical':True}},{'name':'run_python_code','arguments':{'code':code}},{'name':'get_model_info','arguments':{}}]
    Path(a.output).write_text(json.dumps(calls,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
