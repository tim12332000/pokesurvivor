"""Prepare a fixed gh-pages release from a clean mod-main checkout.

Build dist-digimon first. Default prepares local refs only; --dry-run changes no
refs or worktree files, and --push explicitly publishes with remote-head leases.
The source is checked again after push; if it moved concurrently, fetch/rebuild
before requesting a Pages build. A source no-op is not an atomic server lock.
This tool never changes Pages configuration or requests a Pages build. With
Actions disabled, run locally and request/verify the existing legacy build.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import threading

SOURCE_BRANCH, PAGES_BRANCH = 'mod-main', 'gh-pages'
TEXT = {'.js', '.json', '.html', '.css', '.md', '.txt', '.svg', '.xml', '.yml', '.yaml', '.webmanifest'}


def git(repo, *args, data=None, env=None):
    result = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', *args],
                            cwd=repo, input=data, env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError('Git command failed: ' + args[0])
    return result.stdout


def text(repo, *args, **kwargs):
    return git(repo, *args, **kwargs).decode('utf-8').strip()


def public_path(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or not name:
        raise ValueError('Invalid public path: ' + name)
    folded = name.casefold()
    if {'cname', '.git'} & {part.casefold() for part in p.parts} or any(folded == x or folded.startswith(x + '/') for x in ('.omx/state', '.omx/worktrees')):
        raise ValueError('Excluded public path: ' + name)
    if p.suffix.lower() in {'.webm', '.mp4', '.mov'} and not name.startswith('assets/previews/'):
        raise ValueError('Raw media is not a public runtime asset: ' + name)
    roots = {'.omx', 'assets', 'css', 'js', 'art-review'}
    files = {'.nojekyll', 'index.html', 'sw.js', 'manifest.webmanifest', 'version.json', 'LICENSE', 'LICENSE-NONCOMMERCIAL.md', 'release.json'}
    if p.parts[0] not in roots and name not in files and not name.endswith('-release.json'):
        raise ValueError('Unexpected artifact file: ' + name)
    return name


def equivalent(name, a, b):
    if Path(name).suffix.lower() in TEXT or name == 'LICENSE':
        return a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n')
    return a == b


def blobs(repo, revision):
    entries = []
    for item in git(repo, 'ls-tree', '-r', '-z', revision).split(b'\0'):
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        mode, kind, oid = metadata.split()
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise ValueError('Non-file in public tree: ' + name.decode())
        entries.append((name.decode('utf-8'), oid))
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=repo, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    errors = []
    def feed():
        try:
            for _, oid in entries:
                process.stdin.write(oid + b'\n')
        except OSError as error:
            errors.append(error)
        finally:
            process.stdin.close()
    writer = threading.Thread(target=feed, daemon=True)
    writer.start()
    try:
        for name, oid in entries:
            header = process.stdout.readline().split()
            if len(header) != 3 or header[:2] != [oid, b'blob']:
                raise RuntimeError('Invalid Git blob response')
            data = process.stdout.read(int(header[2]))
            if len(data) != int(header[2]) or process.stdout.read(1) != b'\n':
                raise RuntimeError('Truncated Git blob')
            yield name, data
        writer.join()
        if process.wait() or errors:
            raise RuntimeError('Git blob reader failed')
    finally:
        if process.poll() is None:
            process.terminate()
        writer.join()
        process.wait()
        process.stdout.close()


def remote_heads(repo, remote):
    raw = text(repo, 'ls-remote', '--heads', remote, 'refs/heads/' + SOURCE_BRANCH, 'refs/heads/' + PAGES_BRANCH)
    return {line.split()[1].removeprefix('refs/heads/'): line.split()[0] for line in raw.splitlines()}


def require_heads(repo, remote, source, parent):
    if remote_heads(repo, remote) != {SOURCE_BRANCH: source, PAGES_BRANCH: parent}:
        raise RuntimeError('Remote mod-main or gh-pages changed; fetch and rebuild before publishing')


def prepare(repo, artifact, expected_source, expected_pages, remote='origin', dry_run=False, push=False, tag=None):
    repo, artifact = Path(repo).resolve(), Path(artifact).resolve()
    if not re.fullmatch(r'[\w.-]+', remote):
        raise ValueError('Use a configured Git remote name')
    source = text(repo, 'rev-parse', 'HEAD')
    if source != expected_source or text(repo, 'rev-parse', SOURCE_BRANCH) != source:
        raise RuntimeError('Use the expected mod-main source checkout')
    git(repo, 'diff', '--quiet', 'HEAD')
    git(repo, 'diff', '--cached', '--quiet')
    if 'branch refs/heads/' + PAGES_BRANCH in text(repo, 'worktree', 'list', '--porcelain').splitlines():
        raise RuntimeError('Detach the gh-pages worktree before publishing')
    git(repo, 'cat-file', '-e', expected_pages + '^{commit}')
    require_heads(repo, remote, source, expected_pages)
    if not (artifact/'.nojekyll').is_file() or not (artifact/'.omx/digimon.html').is_file():
        raise ValueError('Build dist-digimon with .nojekyll before publishing')
    for path in artifact.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in artifact')
        if path.is_file():
            public_path(path.relative_to(artifact).as_posix())
    tag = tag or 'releases/' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + source[:8]
    if not tag.startswith('releases/'):
        raise ValueError('Release tags must use releases/')
    git(repo, 'check-ref-format', 'refs/tags/' + tag)
    with tempfile.TemporaryDirectory(prefix='mod-pages-') as directory:
        temp = Path(directory)
        site = temp/'site'
        shutil.copytree(artifact, site)
        source_names = set(git(repo, 'ls-tree', '-r', '--name-only', '-z', source).decode('utf-8').rstrip('\0').split('\0'))
        generated = {'index.html', '.omx/digimon.html', '.nojekyll', 'release.json'}
        previous_names = set()
        for name, previous in blobs(repo, expected_pages):
            previous_names.add(name)
            target = site/public_path(name)
            if name not in source_names | generated or not target.exists() or equivalent(name, target.read_bytes(), previous):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(previous)
        for name, data in blobs(repo, source):
            target = site/name
            if target.is_file() and name not in generated and not equivalent(name, target.read_bytes(), data):
                raise ValueError('Artifact differs from committed source: ' + name)
        for path in site.rglob('*'):
            if path.is_file() and path.relative_to(site).as_posix() not in source_names | previous_names | generated:
                raise ValueError('Uncommitted artifact file: ' + path.relative_to(site).as_posix())
        html_path = site/'.omx/digimon.html'
        html = html_path.read_text(encoding='utf-8')
        digest = lambda name: hashlib.sha256((site/public_path(name)).read_bytes()).hexdigest()
        def version(match):
            name = public_path(match[2])
            query = '?v=' + digest(name)[:12]
            if name == 'art-review/madara/runtime.js':
                query += '&amp;data=' + digest('art-review/madara/frames.json')[:12]
            if name == '.omx/lf2-art.js':
                query += '&amp;data=' + digest('assets/lf2/freeze/manifest.json')[:12]
            if name == '.omx/lf2-boss-art.js':
                data = b''.join((site/'assets/lf2'/hero/'manifest.json').read_bytes() for hero in ['firzen', 'julian', 'firen'])
                query += '&amp;data=' + hashlib.sha256(data).hexdigest()[:12]
            return match[1] + name + query + match[3]
        html = re.sub(r'(<script\b[^>]*\bsrc=")(?!https?://)([^"?]+)(?:\?[^"\s]*)?(")', version, html)
        html = re.sub(r'(<link\b(?=[^>]*\brel="stylesheet")[^>]*\bhref=")(?!https?://)([^"?]+)(?:\?[^"\s]*)?(")', version, html)
        html_path.write_text(html, encoding='utf-8', newline='\n')
        paths = {'index.html', '.omx/digimon.html', '.omx/portrait.html'}
        paths.update(re.findall(r'<(?:script|link)\b[^>]*(?:src|href)="((?!https?://)[^"?]+)', html))
        manifest = {'sourceCommit': source, 'sourceBranch': SOURCE_BRANCH, 'previousStaticCommit': expected_pages,
                    'sha256': {name: digest(name) for name in sorted(paths) if (site/name).is_file()}}
        (site/'release.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        env = dict(os.environ, GIT_INDEX_FILE=str(temp/'index'))
        git_dir = text(repo, 'rev-parse', '--absolute-git-dir')
        base = ['--git-dir=' + git_dir, '--work-tree=' + str(site)]
        git(repo, *base, 'read-tree', '--empty', env=env)
        git(repo, *base, 'add', '--force', '--all', '--', '.', env=env)
        tree = text(repo, *base, 'write-tree', env=env)
        record = {'source': source, 'parent': expected_pages, 'tree': tree, 'branch': PAGES_BRANCH, 'tag': tag,
                  'changedFiles': text(repo, 'diff-tree', '-r', '--name-only', expected_pages, tree).splitlines(),
                  'manifest': manifest, 'dryRun': dry_run}
        if dry_run:
            return record
        current = subprocess.run(['git', 'rev-parse', '--verify', 'refs/heads/' + PAGES_BRANCH], cwd=repo, capture_output=True)
        local = current.stdout.decode().strip() if current.returncode == 0 else '0'*40
        if local not in ('0'*40, expected_pages):
            raise RuntimeError('Local gh-pages differs from expected parent')
        existing = subprocess.run(['git', 'show-ref', '--verify', '--quiet', 'refs/tags/' + tag], cwd=repo)
        if existing.returncode == 0:
            raise RuntimeError('Release tag already exists')
        message = f'''Keep the verified modification source available at the existing public URL

Publish the canonical artifact from {source} to the fixed gh-pages branch.

Constraint: Preserve existing public assets, URL and Pages settings
Confidence: high
Scope-risk: moderate
Tested: Source and deployment leases, artifact path validation, entry hashes and parent preservation
Not-tested: Public availability must be verified after the Pages build
Related: {source}
'''
        commit = text(repo, 'commit-tree', tree, '-p', expected_pages, data=message.encode('utf-8'))
        git(repo, 'merge-base', '--is-ancestor', expected_pages, commit)
        require_heads(repo, remote, source, expected_pages)
        if push:
            git(repo, 'push', '--atomic', '--force-with-lease=refs/heads/' + PAGES_BRANCH + ':' + expected_pages,
                '--force-with-lease=refs/heads/' + SOURCE_BRANCH + ':' + source, remote,
                commit + ':refs/heads/' + PAGES_BRANCH, source + ':refs/heads/' + SOURCE_BRANCH, commit + ':refs/tags/' + tag)
            if remote_heads(repo, remote) != {SOURCE_BRANCH: source, PAGES_BRANCH: commit}:
                raise RuntimeError('Remote source changed during push; fetch and rebuild before requesting a Pages build')
        # One local transaction prevents a tag-only partial preparation.
        transaction = f'start\ncreate refs/tags/{tag} {commit}\nupdate refs/heads/{PAGES_BRANCH} {commit} {local}\nprepare\ncommit\n'
        git(repo, 'update-ref', '--stdin', data=transaction.encode())
        return {**record, 'staticCommit': commit, 'pushed': push}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--artifact', type=Path)
    parser.add_argument('--remote', default='origin')
    parser.add_argument('--expected-source')
    parser.add_argument('--expected-pages')
    parser.add_argument('--tag')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--push', action='store_true')
    args = parser.parse_args()
    source = args.expected_source or text(args.repo, 'rev-parse', 'refs/remotes/' + args.remote + '/' + SOURCE_BRANCH)
    parent = args.expected_pages or text(args.repo, 'rev-parse', 'refs/remotes/' + args.remote + '/' + PAGES_BRANCH)
    record = prepare(args.repo, args.artifact or args.repo/'dist-digimon', source, parent, args.remote, args.dry_run, args.push, args.tag)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
