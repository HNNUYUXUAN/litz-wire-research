"""Regressions for the actual MCP startup, dependency, and false-success failures."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from litz_research.automation import configure,server_environment,probe_environment,candidate_server
from litz_research.common import project,write
from litz_research.readiness import inspect_server,lock_mismatches,inspect_upstream
from litz_research.tasks import source_manifest

spec=importlib.util.spec_from_file_location('readiness_mcp_client',project()/'automation/mcp/client.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)


class ReadinessTests(unittest.TestCase):
    def test_candidate_json_and_toml_selection_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix='Litz 中文 candidate ') as tmp:
            path=Path(tmp)/'mcp.json'
            write(path,{'mcpServers':{'Ansys':{'command':'candidate-python'}}})
            self.assertEqual(candidate_server(path,'ansys')['command'],'candidate-python')
            with self.assertRaises(ValueError):candidate_server(path,'wolfram')
            path=Path(tmp)/'config.toml'
            path.write_text('[mcp_servers.ansys]\ncommand="candidate-python"\nenabled=false\n',encoding='utf-8')
            with self.assertRaises(ValueError):candidate_server(path,'ansys')
            path.write_text('[mcp_servers.ansys]\ncommand="candidate-python"\n',encoding='utf-8')
            self.assertEqual(candidate_server(path,'ansys')['command'],'candidate-python')

    def test_fixed_vcs_install_uses_installed_commit_not_download_checkout(self):
        runtime={'versions':{'ansys-aedt-mcp':'0.2'},'direct_urls':{'ansys-aedt-mcp':{
            'url':'file:///C:/download','vcs_info':{'commit_id':'locked'}}}}
        with patch('litz_research.readiness.subprocess.run') as run:
            result=inspect_upstream(runtime,{'commit':'locked','version':'0.2'})
        self.assertEqual(result['status'],'passed')
        run.assert_not_called()
        runtime['direct_urls']['ansys-aedt-mcp'].pop('vcs_info')
        self.assertEqual(inspect_upstream(runtime,{'commit':'locked','version':'0.2'})['status'],'failed')

    def test_editable_install_checks_working_tree_commit_and_tracked_changes(self):
        from subprocess import CompletedProcess
        runtime={'versions':{'ansys-aedt-mcp':'0.2'},'direct_urls':{'ansys-aedt-mcp':{
            'url':'file:///C:/source%20tree','dir_info':{'editable':True}}}}
        for commit,dirty,status in [('locked','','passed'),('other','','failed'),('locked',' M src.py','failed')]:
            with self.subTest(commit=commit,dirty=dirty),patch('litz_research.readiness.subprocess.run',side_effect=[
                CompletedProcess([],0,commit),CompletedProcess([],0,dirty)]) as run:
                result=inspect_upstream(runtime,{'commit':'locked','version':'0.2'})
                self.assertEqual(result['status'],status)
                self.assertIn('source tree',run.call_args_list[0].args[0][4])

    def test_clean_probe_does_not_inherit_accidental_terminal_dependencies(self):
        with patch.dict(os.environ,{'PATH':'system tools','ANSYSEMSV_ROOT252':'hidden installation',
                                    'WOLFRAM_USERBASE':'hidden paclets','PYTHONPATH':'hidden packages'},clear=True):
            env=probe_environment(Path('project'),clean=True)
        self.assertEqual(env,{'PATH':'system tools','LITZ_PROJECT':'project'})

    def test_missing_installation_is_not_successful_tool_execution(self):
        call={'name':'check_aedt_installed'}
        for message in ['No AEDT versions found installed on this system.',
                        'Running inside Docker. AEDT gRPC endpoint at host:50051 is NOT reachable.',
                        '']:
            self.assertIsNotNone(client.tool_failure(call,{'isError':False,'content':[{'type':'text','text':message}]}))
        self.assertIsNone(client.tool_failure(call,{'content':[{'type':'text','text':'AEDT is installed on this system.\nVersion: 2025.2SV'}]}))

    def test_protocol_error_flag_and_text_errors_are_preserved(self):
        from mcp.types import CallToolResult,TextContent
        result=CallToolResult(content=[TextContent(type='text',text='plain failure')],isError=True)
        encoded=result.model_dump(mode='json',by_alias=True)
        self.assertIsNotNone(client.tool_failure({'name':'any_tool'},encoded))
        self.assertIsNotNone(client.tool_failure({'name':'run_python_code'},
                            {'content':[{'type':'text','text':'Error executing code: invalid design'}]}))

    def test_wolfram_test_failure_cannot_pass_as_tool_success(self):
        call={'name':'TestReport'}
        for summary in ['| **Overall Result** | Failure |\n| **Total Tests** | 12 |',
                        '| **Overall Result** | Success |\n| **Total Tests** | 0 |']:
            self.assertIsNotNone(client.tool_failure(call,{'isError':False,'content':[{'type':'text','text':summary}]}))
        self.assertIsNone(client.tool_failure(call,{'content':[{'type':'text','text':'| **Overall Result** | Success |\n| **Total Tests** | 12 |'}]}))

    def test_dependency_drift_and_missing_runtime_are_rejected(self):
        errors=lock_mismatches({'pydantic':'2.14.1','pydantic_core':'2.50.1'},
                               'pydantic==2.13.5\npydantic-core==2.46.5\n',('mcp',))
        self.assertEqual(len(errors),3)
        self.assertEqual(lock_mismatches({'pydantic_core':'2.46.5'},'pydantic-core==2.46.5'),[])

    def test_explicit_environment_survives_empty_parent_environment(self):
        with tempfile.TemporaryDirectory(prefix='Litz configured environment ') as tmp:
            root=Path(tmp);install=root/'AEDT Student';install.mkdir();(install/'ansysedtsv.exe').touch()
            write(root/'litz.config.json',{'mcp_servers':{'ansys':{'env':{'ANSYSEMSV_ROOT252':str(install)}}}})
            with patch.dict(os.environ,{},clear=True):env=server_environment(root,'ansys')
            self.assertEqual(env['ANSYSEMSV_ROOT252'],str(install))
            self.assertEqual(env['PYTHONUTF8'],'1')
            self.assertEqual(env['PYTHONIOENCODING'],'utf-8')

    def test_generated_configuration_keeps_verified_root_and_no_unrelated_secret(self):
        with tempfile.TemporaryDirectory(prefix='Litz MCP config ') as tmp:
            root=Path(tmp);install=root/'AEDT';install.mkdir();(install/'ansysedtsv.exe').touch()
            executable=root/'python.exe';executable.touch();executable.chmod(0o755)
            write(root/'litz.config.json',{'tools':{'wolfram_kernel':str(executable)}})
            with patch.dict(os.environ,{'ANSYSEMSV_ROOT252':str(install),'UNRELATED_SECRET':'never copy'},clear=True):
                result=configure(root,root/'config',str(executable))
            self.assertEqual(result['diagnostics'],[])
            parsed=tomllib.loads((root/'config/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(parsed['mcp_servers']['ansys']['env']['ANSYSEMSV_ROOT252'],str(install))
            self.assertNotIn('never copy',(root/'config/config.toml').read_text(encoding='utf-8'))

    def test_executable_presence_does_not_hide_missing_desktop_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);exe=root/'python.exe';exe.touch();launcher=root/'StartMCP.py';launcher.touch()
            result=inspect_server('ansys',{'command':str(exe),'cwd':str(root),'args':[str(launcher)],'env':{}})
            self.assertEqual(result['status'],'failed')
            self.assertTrue(any('UTF-8' in e for e in result['errors']))
            self.assertTrue(any('installation roots' in e for e in result['errors']))

    def test_dependency_lock_is_part_of_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);lock=root/'automation/mcp/environment.lock';lock.parent.mkdir(parents=True)
            lock.write_text('mcp==1.17.0\n')
            before=source_manifest(root)
            lock.write_text('mcp==2.3.0\n')
            self.assertNotEqual(before['automation/mcp/environment.lock'],source_manifest(root)['automation/mcp/environment.lock'])


if __name__=='__main__':unittest.main()
