"""Serve the full local lab without rejecting bursts of parallel sprite requests."""
from functools import partial
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class LabServer(ThreadingHTTPServer):
    request_queue_size = 128


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8318)
    args=parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    with LabServer(('127.0.0.1', args.port), handler) as server:
        print(f'Local preview: http://127.0.0.1:{args.port}/.omx/digimon.html?lang=zh-TW', flush=True)
        server.serve_forever()
