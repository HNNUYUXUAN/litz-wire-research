import importlib.util
from pathlib import Path
import tomllib
import unittest

spec=importlib.util.spec_from_file_location('switch_mcp',Path(__file__).resolve().parents[1]/'tools/SwitchMCPConfiguration.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ConfigurationSwitchTests(unittest.TestCase):
    def test_target_merge_preserves_unrelated_settings_and_server_options(self):
        original='''model="configured-model"
[mcp_servers.Wolfram]
command="old"
tool_timeout_sec=120
[mcp_servers.Wolfram.env]
OLD="old"
[mcp_servers.other]
command="keep"
[projects."中文 path"]
trust_level="trusted"
'''
        updated=tomllib.loads(module.merge_client(original,{
            'wolfram':{'command':'new','env':{'NEW':'new'}},'ansys':{'command':'python'}}))
        self.assertEqual(updated['model'],'configured-model')
        self.assertEqual(updated['mcp_servers']['Wolfram'],{'command':'new','env':{'NEW':'new'},'tool_timeout_sec':120})
        self.assertEqual(updated['mcp_servers']['other'],{'command':'keep'})
        self.assertEqual(updated['projects']['中文 path']['trust_level'],'trusted')
