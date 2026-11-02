"""A previously cached game URL must receive new HTML while online."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

WORKER = (Path(__file__).resolve().parents[1] / 'sw.js').read_bytes()


class Handler(BaseHTTPRequestHandler):
    version = 1

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == '/sw.js':
            body, kind = WORKER, 'application/javascript'
        elif self.path.startswith('/assets/icons/'):
            body, kind = str(self.version).encode(), 'text/plain'
        else:
            body = (f'<body>release-{self.version}<script>'
                    "navigator.serviceWorker.register('/sw.js')"
                    '</script></body>').encode()
            kind = 'text/html'
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}'
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(base + '/index.html')
            page.wait_for_function('!!navigator.serviceWorker.controller')
            assert 'release-1' in page.locator('body').inner_text()
            assert page.evaluate("fetch('/assets/icons/test').then(r=>r.text())") == '1'
            Handler.version = 2
            page.goto(base + '/other.html')
            page.goto(base + '/index.html')
            assert 'release-2' in page.locator('body').inner_text(), 'old URL reused stale HTTP-cached HTML'
            assert page.evaluate("fetch('/assets/icons/test').then(r=>r.text())") == '1', 'art cache no longer reused'
            # Let Cache Storage writes settle before losing network access.
            page.wait_for_function("caches.match('/index.html').then(r=>r && r.text()).then(s=>s.includes('release-2'))")
            context.set_offline(True)
            page.reload()
            assert 'release-2' in page.locator('body').inner_text(), 'offline fallback lost latest HTML'
            browser.close()
        server.shutdown()
    print('Old URL refreshes online; latest HTML works offline; art remains cached.')
