"""Install the four research skills into an explicitly selected host directory."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('research-scout', 'paper-acquire', 'research-reuse', 'research-handoff')


def install(destination):
    destination = destination.resolve()
    for name in NAMES:
        if (destination/name).exists():
            raise FileExistsError(f'Existing skill preserved: {destination/name}')
    destination.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copytree(ROOT/'automation/skills'/name, destination/name)
    return [str(destination/name) for name in NAMES]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    print('\n'.join(install(parser.parse_args().destination)))
