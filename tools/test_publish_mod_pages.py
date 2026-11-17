"""Temporary-repository integration checks; never access the real Git remote."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import publish_mod_pages as publisher


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mod-pages-test-')
        self.root = Path(self.temp.name)
        self.repo = self.root/'source'
        self.remote = self.root/'remote.git'
        self.repo.mkdir()
        self.run_git('init', '-b', 'mod-main')
        self.run_git('config', 'user.name', 'Publisher Test')
        self.run_git('config', 'user.email', 'publisher@example.invalid')
        self.files = {
            '.gitignore': b'dist-digimon/\n', 'README.md': b'committed source\n',
            'index.html': b'original source index\n', '.nojekyll': b'', 'LICENSE': b'license\nline two\n',
            '.omx/digimon.html': b'<script src="js/main.js?v=old"></script><link rel="stylesheet" href="css/game.css?v=old"><script src=".omx/lf2-art.js"></script><script src=".omx/lf2-boss-art.js"></script><script src="art-review/madara/runtime.js"></script>',
            '.omx/portrait.html': b'portrait\n', 'js/main.js': b'const runtime=1;\n',
            'css/game.css': b'body { color: green; }\n', '.omx/lf2-art.js': b'freeze\n',
            '.omx/lf2-boss-art.js': b'bosses\n', 'art-review/madara/runtime.js': b'madara\n',
            'art-review/madara/frames.json': b'{"frames":1}\n',
            'assets/lf2/freeze/manifest.json': b'{"freeze":1}\n',
            'assets/lf2/firzen/manifest.json': b'{"firzen":1}\n',
            'assets/lf2/julian/manifest.json': b'{"julian":1}\n',
            'assets/lf2/firen/manifest.json': b'{"firen":1}\n'}
        for name, data in self.files.items():
            self.write(self.repo/name, data)
        self.run_git('add', '.')
        self.run_git('commit', '-m', 'source fixture')
        self.source = self.run_git('rev-parse', 'HEAD').strip().decode()
        env = dict(os.environ, GIT_INDEX_FILE=str(self.root/'old.index'))
        self.run_git('read-tree', '--empty', env=env)
        old_files = {'.nojekyll': b'', 'index.html': b'old site\n',
                     '.omx/digimon.html': b'old entry\n', 'LICENSE': b'license\r\nline two\r\n',
                     'js/main.js': b'const runtime=1;\r\n', 'assets/old.png': b'old public asset'}
        for name, data in old_files.items():
            blob = self.run_git('hash-object', '-w', '--stdin', data=data).strip().decode()
            self.run_git('update-index', '--add', '--cacheinfo', '100644,'+blob+','+name, env=env)
        tree = self.run_git('write-tree', env=env).strip().decode()
        self.parent = self.run_git('commit-tree', tree, '-m', 'old static fixture').strip().decode()
        self.run_git('update-ref', 'refs/heads/gh-pages', self.parent)
        subprocess.run(['git', 'init', '--bare', str(self.remote)], capture_output=True, check=True)
        self.run_git('config', 'user.name', 'Remote Publisher Test', repo=self.remote)
        self.run_git('config', 'user.email', 'remote@example.invalid', repo=self.remote)
        self.run_git('remote', 'add', 'origin', str(self.remote))
        self.run_git('push', 'origin', 'mod-main', 'gh-pages')
        self.artifact = self.repo/'dist-digimon'
        for name, data in self.files.items():
            if name not in ('.gitignore', 'README.md'):
                self.write(self.artifact/name, data)
        self.write(self.artifact/'index.html', b'generated public redirect\n')

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def run_git(self, *args, data=None, env=None, repo=None):
        return subprocess.run(['git', '-c', 'core.autocrlf=false', *args], cwd=repo or self.repo,
                              input=data, env=env, capture_output=True, check=True).stdout

    def snapshot(self):
        return (self.run_git('show-ref'), (self.repo/'.git/index').read_bytes(),
                {p.relative_to(self.artifact).as_posix(): p.read_bytes() for p in self.artifact.rglob('*') if p.is_file()})

    def prepare(self, **kwargs):
        return publisher.prepare(self.repo, self.artifact, self.source, self.parent, tag='releases/test', **kwargs)

    def blob(self, ref, path):
        return self.run_git('show', ref+':'+path)

    def advance_remote(self, branch, parent):
        tree = self.run_git('rev-parse', parent+'^{tree}', repo=self.remote).strip().decode()
        commit = self.run_git('commit-tree', tree, '-p', parent, '-m', 'concurrent update', repo=self.remote).strip().decode()
        self.run_git('update-ref', 'refs/heads/'+branch, commit, parent, repo=self.remote)
        return commit

    def test_dry_run_preserves_refs_index_source_and_artifact(self):
        self.write(self.artifact/'assets/old.png', b'uncommitted change to a retired asset')
        before = self.snapshot()
        record = self.prepare(dry_run=True)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.run_git('diff', '--name-only'), b'')
        self.assertEqual(self.blob(record['tree'], 'LICENSE'), b'license\r\nline two\r\n')
        self.assertEqual(self.blob(record['tree'], 'assets/old.png'), b'old public asset')
        runtime = self.blob(record['tree'], 'js/main.js')
        self.assertEqual(runtime, b'const runtime=1;\r\n')
        html = self.blob(record['tree'], '.omx/digimon.html').decode()
        self.assertIn('js/main.js?v='+hashlib.sha256(runtime).hexdigest()[:12], html)
        freeze_hash = hashlib.sha256(self.files['assets/lf2/freeze/manifest.json']).hexdigest()[:12]
        self.assertIn('&amp;data='+freeze_hash, html)
        manifest = json.loads(self.blob(record['tree'], 'release.json'))
        self.assertEqual(manifest['sourceCommit'], self.source)
        self.assertEqual(manifest['sourceBranch'], 'mod-main')
        self.assertEqual(manifest['sha256']['js/main.js'], hashlib.sha256(runtime).hexdigest())

    def test_rejects_private_and_raw_files_before_refs_change(self):
        for name in ['C:/private-release.json', 'assets\\..\\private.json', '.omx/STATE/token.json']:
            with self.assertRaises(ValueError): publisher.public_path(name)
        for name in ['CNAME', '.git/config', '.omx/state/token.json', '.omx/worktrees/draft.json', 'assets/raw.webm']:
            with self.subTest(name=name):
                self.write(self.artifact/name, b'private')
                before = self.run_git('show-ref')
                with self.assertRaises(ValueError): self.prepare(dry_run=True)
                self.assertEqual(before, self.run_git('show-ref'))
                (self.artifact/name).unlink()

    def test_cli_dry_run_uses_tracking_refs_without_writing_refs(self):
        before = self.snapshot()
        result = subprocess.run([sys.executable, publisher.__file__, '--repo', str(self.repo),
                                 '--dry-run', '--tag', 'releases/cli'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['dryRun'])
        self.assertEqual(before, self.snapshot())

    def test_clean_crlf_checkout_uses_repository_normalization(self):
        self.run_git('config', 'core.autocrlf', 'true')
        for name in self.files: (self.repo/name).unlink()
        subprocess.run(['git', 'checkout', '--force', 'HEAD', '--', '.'], cwd=self.repo,
                       capture_output=True, check=True)
        self.assertIn(b'\r\n', (self.repo/'js/main.js').read_bytes())
        clean = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'],
                               cwd=self.repo, capture_output=True, check=True).stdout
        self.assertEqual(clean, b'')
        self.assertTrue(self.prepare(dry_run=True)['dryRun'])
        self.write(self.repo/'README.md', b'committed source \r\n')
        with self.assertRaisesRegex(RuntimeError, 'tracked modifications'):
            self.prepare(dry_run=True)

    def test_local_independent_release_is_not_overwritten(self):
        tree = self.run_git('rev-parse', self.parent+'^{tree}').strip().decode()
        other = self.run_git('commit-tree', tree, '-p', self.parent, '-m', 'other local release').strip().decode()
        self.run_git('update-ref', 'refs/heads/gh-pages', other, self.parent)
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, 'Local gh-pages'): self.prepare()
        self.assertEqual(before, self.snapshot())

    def test_rejects_uncommitted_or_stale_artifact(self):
        self.write(self.artifact/'assets/private.json', b'not committed')
        with self.assertRaisesRegex(ValueError, 'Uncommitted'): self.prepare(dry_run=True)
        (self.artifact/'assets/private.json').unlink()
        self.write(self.artifact/'js/main.js', b'stale or uncommitted runtime')
        with self.assertRaisesRegex(ValueError, 'committed source'): self.prepare(dry_run=True)

    def test_rejects_stale_remote_heads(self):
        for branch, old in [('mod-main', self.source), ('gh-pages', self.parent)]:
            with self.subTest(branch=branch):
                before = self.snapshot()
                self.advance_remote(branch, old)
                with self.assertRaisesRegex(RuntimeError, 'changed'): self.prepare(dry_run=True)
                self.assertEqual(before, self.snapshot())
                self.run_git('push', '--force-with-lease=refs/heads/'+branch+':'+self.run_git('ls-remote','origin','refs/heads/'+branch).decode().split()[0], 'origin', old+':refs/heads/'+branch)

    def test_push_is_fast_forward_and_tag_points_at_static_commit(self):
        record = self.prepare(push=True)
        static = record['staticCommit']
        self.assertEqual(self.run_git('rev-parse', 'gh-pages').strip().decode(), static)
        self.assertEqual(self.run_git('rev-parse', 'releases/test').strip().decode(), static)
        self.assertEqual(self.run_git('rev-parse', static+'^').strip().decode(), self.parent)
        self.assertEqual(publisher.remote_heads(self.repo, 'origin'), {'mod-main':self.source,'gh-pages':static})
        self.assertEqual(self.run_git('ls-remote', 'origin', 'refs/tags/releases/test').decode().split()[0], static)

    def test_racing_source_update_cannot_publish_or_rewind_remote(self):
        original = publisher.require_heads
        calls = 0
        def race(*args):
            nonlocal calls
            original(*args)
            calls += 1
            if calls == 2: self.advance_remote('mod-main', self.source)
        before = self.snapshot()
        with patch.object(publisher, 'require_heads', race):
            with self.assertRaisesRegex(RuntimeError, 'push'): self.prepare(push=True)
        self.assertEqual(before, self.snapshot())
        heads = publisher.remote_heads(self.repo, 'origin')
        self.assertNotEqual(heads['mod-main'], self.source)
        self.assertEqual(heads['gh-pages'], self.parent)
        self.assertFalse(self.run_git('ls-remote','origin','refs/tags/releases/test'))

    def test_source_change_after_push_advertisement_is_detected(self):
        tree = self.run_git('rev-parse', self.source+'^{tree}', repo=self.remote).strip().decode()
        newer = self.run_git('commit-tree', tree, '-p', self.source, '-m', 'source race in hook', repo=self.remote).strip().decode()
        hook = self.remote/'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nunset GIT_QUARANTINE_PATH\ngit update-ref refs/heads/mod-main '+newer+' '+self.source+' || exit 1\nexit 0\n', encoding='utf-8', newline='\n')
        hook.chmod(0o755)
        local_refs = self.run_git('for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads', 'refs/tags')
        index = (self.repo/'.git/index').read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'changed during push'): self.prepare(push=True)
        self.assertEqual(local_refs, self.run_git('for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads', 'refs/tags'))
        self.assertEqual(index, (self.repo/'.git/index').read_bytes())
        heads = publisher.remote_heads(self.repo, 'origin')
        self.assertEqual(heads['mod-main'], newer)
        self.assertNotEqual(heads['gh-pages'], self.parent)  # No-op source leases cannot undo a completed push.


if __name__ == '__main__':
    unittest.main()
