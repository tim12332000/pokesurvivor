"""Publish an already verified static artifact using the existing Pages mechanism."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'tim12332000/pokesurvivor'


def git(*args, env=None, cwd=ROOT, data=None):
    return subprocess.check_output(['git', *args], cwd=cwd, env=env,
                                   input=data, text=True).strip()


def api(method, route, data=None):
    result = subprocess.run(['git', 'credential', 'fill'], cwd=ROOT,
                            input='protocol=https\nhost=github.com\n\n', text=True,
                            capture_output=True, check=True,
                            env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never'))
    credentials = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    request = urllib.request.Request('https://api.github.com' + route,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization': 'Bearer ' + credentials['password'],
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'pokesurvivor-release'},
        method=method)
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read()
        return json.loads(payload) if payload else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact', type=Path)
    parser.add_argument('source')
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    assert artifact.is_relative_to(ROOT), 'Artifact must stay in this repository'
    assert (artifact / '.nojekyll').is_file() and not (artifact / 'CNAME').exists()
    assert (artifact / '.omx/lf2-freeze-combat.js').is_file()
    assert (artifact / 'assets/lf2/freeze/manifest.json').is_file()
    assert git('remote', 'get-url', 'origin') == 'https://github.com/' + REPO + '.git'
    source = git('rev-parse', args.source + '^{commit}')
    pages = api('GET', '/repos/' + REPO + '/pages')
    assert pages['build_type'] == 'legacy', 'Review changed deployment mechanism first'
    parent = git('ls-remote', 'origin', 'refs/heads/' + pages['source']['branch']).split()[0]
    git('fetch', 'origin', pages['source']['branch'])
    branch = 'codex/freeze-classic-pages-' + source[:8]
    index = ROOT / '.omx/state/freeze/pages.index'
    index.parent.mkdir(parents=True, exist_ok=True)
    index.unlink(missing_ok=True)
    env = dict(os.environ, GIT_INDEX_FILE=str(index),
               GIT_DIR=str(ROOT / '.git'), GIT_WORK_TREE=str(artifact))
    git('read-tree', '--empty', env=env)
    # Store the verified artifact bytes verbatim, including generated HTML on
    # Windows; source-checkout newline policy must not alter the public package.
    git('-c', 'core.autocrlf=false', 'add', '-f', '--all', '--', '.', env=env, cwd=artifact)
    tree = git('write-tree', env=env)
    message = ('Make classic Freeze playable from the existing public entry\n\n'
               'Publish the verified static package from source ' + source + '.\n\n'
               'Constraint: Existing GitHub Pages uses a static branch\n'
               'Confidence: high\nScope-risk: narrow\n'
               'Tested: Freeze mechanics, real level-up playthrough, desktop and mobile viewport\n'
               'Not-tested: Physical mobile devices and multiplayer\n')
    commit = git('commit-tree', tree, '-p', parent, data=message)
    git('update-ref', 'refs/heads/' + branch, commit)
    git('push', 'origin', source + ':refs/heads/feat/digimon-sandbox')
    git('push', 'origin', 'refs/heads/' + branch)
    api('PUT', '/repos/' + REPO + '/pages', {'source': {'branch': branch, 'path': '/'}})
    result = api('GET', '/repos/' + REPO + '/pages')
    assert result['source'] == {'branch': branch, 'path': '/'}
    report = {'source': source, 'pages_commit': commit, 'branch': branch,
              'url': result.get('html_url', pages['html_url']), 'previous_source': pages['source']}
    (ROOT / '.omx/state/freeze/release.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
