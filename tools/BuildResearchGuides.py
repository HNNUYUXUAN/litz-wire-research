"""Generate bilingual text/CLI tutorials from the maintained model registrations."""
import argparse
import hashlib
import json
from pathlib import Path

from litz_research.tasks import DEFAULTS

ROOT = Path(__file__).resolve().parents[1]


def generate(root=ROOT):
    outputs = {}
    entries = []
    registrations = sorted((root / 'models').glob('*/model.json')) + sorted((root / 'adapters').glob('*/model.json'))
    for path in registrations:
        model = json.loads(path.read_text(encoding='utf-8'))
        route, identifier = model['route'], model['model_id']
        directory = path.parent.relative_to(root).as_posix()
        inputs = directory + '/examples/tutorial.json'
        case = 'diagnostic' if identifier == 'aphi' else 'preflight' if identifier == 'ansys' else 'tutorial'
        if model['parameters'] != DEFAULTS[identifier]:
            raise ValueError('Registered parameters differ from executable defaults: ' + identifier)
        for language in ('en', 'zh-CN'):
            zh = language == 'zh-CN'
            target = directory + ('/README.zh-CN.md' if zh else '/README.md')
            run_id = route + '_example_01'
            common = identifier + ' --case ' + case + ' --parameters ' + inputs + ' --run-id ' + run_id
            commands = {'inspect': 'litz-research models ' + identifier,
                        'preflight': 'litz-research run ' + common + ' --dry-run',
                        'run': 'litz-research run ' + common,
                        'submit': 'litz-research jobs submit ' + common,
                        'status': 'litz-research jobs status ' + run_id,
                        'cancel': 'litz-research jobs cancel ' + run_id}
            lines = ['# ' + model['titles'][language], '',
                     '缪雨轩 · 淮南师范学院' if zh else 'Miao Yuxuan · Huainan Normal University', '',
                     '## 模型与假设' if zh else '## Model and assumptions', '',
                     model['equation'], '', model['fixed_conventions'], '', model['tutorial_instructions'][language], '',
                     '## 保存输入并执行' if zh else '## Save inputs and execute', '',
                     ('在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。'
                      if zh else 'Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.'), '',
                     f'[{"参数文件" if zh else "Parameter file"}](examples/tutorial.json)', '', '```bash',
                     commands['inspect'], commands['preflight'], commands['run'], '```', '',
                     ('已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。'
                      if zh else 'Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.'), '',
                     '## 异步任务与恢复' if zh else '## Asynchronous jobs and recovery', '',
                     '```bash', commands['submit'], commands['status'], '```', '',
                     ('同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `' + commands['cancel'] + '`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。'
                      if zh else 'The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `' + commands['cancel'] + '`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.'), '',
                     '## 结果与验收' if zh else '## Results and acceptance', '',
                     ('检查 `outputs/' + run_id + '/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。'
                      if zh else 'Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/' + run_id + '/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.'), '',
                     ('任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。'
                      if zh else 'Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.'), '',
                     '## 推导与结果解释' if zh else '## Derivation and interpretation', '']
            lines += model['derivation'][language]
            lines += ['', '## 接续研究' if zh else '## Continue the research', '',
                      ('每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。'
                       if zh else 'Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.'), '',
                      '[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)', '',
                      '## 历史证据与来源' if zh else '## Historical evidence and sources', '', model['history'], '',
                      ', '.join('[' + key + '](../../references/README.md)' for key in model['references']), '']
            outputs[target] = '\n'.join(lines)
            entries.append({'route': route, 'model_id': identifier, 'language': language,
                            'title': model['titles'][language], 'titles': model['titles'],
                            'path': target, 'parameters_path': inputs, 'parameters': model['parameters'],
                            'case': case, 'usage': model['tutorial_instructions'][language],
                            'references': model['references'], 'fixed_conventions': model['fixed_conventions'],
                            'evidence_dataset': model['evidence_dataset'], 'commands': commands})
    if len(entries) != 20:
        raise ValueError('Expected ten routes with twenty bilingual text entries')
    outputs['configs/research_entries.json'] = json.dumps(entries, ensure_ascii=False, indent=2) + '\n'
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    changed = []
    for path, text in generate().items():
        target = ROOT / path
        if not target.exists() or target.read_text(encoding='utf-8') != text:
            changed.append(path)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding='utf-8')
    if args.check and changed:
        raise SystemExit('Research guides differ: ' + ', '.join(changed))
    print('Twenty text/CLI entries verified' if args.check else 'Twenty text/CLI entries written')


if __name__ == '__main__':
    main()
