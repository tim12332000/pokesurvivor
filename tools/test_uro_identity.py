"""Uro's close palm, remote shatter and projectile reaction stay distinct."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('HERO_IDENTITY_OUT', str(ROOT / '.omx/state/hero-identity/uro')))

# The former single-hit / thin-refresh assertions are intentionally superseded
# by the shared production fracture identity contract (all ranks and lifecycles).
from test_uro_fracture import CHECK


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_args):
        pass

    def do_GET(self):
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    report = {}
    server = None
    if not os.environ.get('JUJUTSU_URL'):
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        base.URL = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1100, 'height': 850},
                                              is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                frame = base.boot(page, 30015, label)
                report[label] = frame.evaluate(CHECK)
                assert not errors, errors
                report[label]['errors'] = errors
                context.close()
            browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'viewports': list(report), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
