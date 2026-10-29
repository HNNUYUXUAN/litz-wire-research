"""Discover the installed TeX runtime with bounded library thread settings."""
import os


def environment():
    env = dict(os.environ, OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
               OPENBLAS_NUM_THREADS='8', PYTHONIOENCODING='utf-8', LANG='C', LC_ALL='C')
    if os.name != 'nt':
        return env
    import winreg
    paths = [env.get('PATH', '')]
    for hive, key in [(winreg.HKEY_CURRENT_USER, 'Environment'),
                      (winreg.HKEY_LOCAL_MACHINE,
                       r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')]:
        with winreg.OpenKey(hive, key) as handle:
            paths.append(os.path.expandvars(winreg.QueryValueEx(handle, 'Path')[0]))
    env['PATH'] = ';'.join(paths)
    return env
