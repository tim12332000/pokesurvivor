"""Read current Pages configuration without exposing Git credentials."""
import json
import os
import subprocess
import urllib.request


def api(route):
    result = subprocess.run(
        ['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
        text=True, capture_output=True, check=True,
        env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never'))
    credentials = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    request = urllib.request.Request('https://api.github.com' + route, headers={
        'Authorization': 'Bearer ' + credentials['password'],
        'Accept': 'application/vnd.github+json', 'User-Agent': 'pokesurvivor-release'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


if __name__ == '__main__':
    pages = api('/repos/tim12332000/pokesurvivor/pages')
    print(json.dumps({key: pages.get(key) for key in
                     ('html_url', 'status', 'build_type', 'source', 'cname', 'https_enforced')}))
