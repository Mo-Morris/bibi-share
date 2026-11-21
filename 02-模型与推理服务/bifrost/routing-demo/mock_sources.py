#!/usr/bin/env python3
"""Four local OpenAI-compatible, non-streaming tutorial sources. No upstream calls."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = 'demo-model'
PROFILES = [
    ('source-a', 18081, 1, 2, 5, 10),
    ('source-b', 18082, 2, 4, 20, 50),
    ('source-c', 18083, 3, 6, 100, 25),
    ('source-d', 18084, 5, 10, 40, 1000),
]


def handler_for(name, port, input_price, output_price, capacity, fail_every):
    state = dict(source=name, model=MODEL, port=port, input_price=input_price,
                 output_price=output_price, capacity=capacity, fail_every=fail_every,
                 delay=2.0, always_fail=False, attempts=0, admitted=0, active=0,
                 succeeded=0, failed_503=0, rejected_429=0)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, status, body):
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if path == '/v1/models':
                self.respond(200, {'object': 'list', 'data': [
                    {'id': MODEL, 'object': 'model', 'created': 0, 'owned_by': 'tutorial'}]})
            elif path == '/demo/stats':
                with lock:
                    snapshot = dict(state)
                self.respond(200, snapshot)
            else:
                self.respond(404, {'error': {'message': 'Unknown route'}})

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
                if not isinstance(body, dict):
                    raise ValueError('Expected an object')
            except (ValueError, json.JSONDecodeError):
                self.respond(400, {'error': {'message': 'Expected a JSON object'}})
                return
            path = self.path.split('?', 1)[0]
            if path == '/demo/control':
                allowed = {'always_fail', 'fail_every', 'delay'}
                if set(body) - allowed:
                    self.respond(400, {'error': {'message': 'Allowed: always_fail, fail_every, delay'}})
                    return
                if ('always_fail' in body and not isinstance(body['always_fail'], bool)) or \
                   ('fail_every' in body and (type(body['fail_every']) is not int or body['fail_every'] < 0)) or \
                   ('delay' in body and (type(body['delay']) not in (float, int) or not 0 <= body['delay'] <= 30)):
                    self.respond(400, {'error': {'message': 'Invalid control value'}})
                    return
                with lock:
                    state.update(body)
                    snapshot = dict(state)
                self.respond(200, snapshot)
                return
            if path != '/v1/chat/completions':
                self.respond(404, {'error': {'message': 'Unknown route'}})
                return
            if body.get('model') != MODEL or body.get('stream', False):
                self.respond(400, {'error': {'message': 'Use model=demo-model and stream=false'}})
                return
            with lock:
                state['attempts'] += 1
                overloaded = state['active'] >= capacity
                if overloaded:
                    state['rejected_429'] += 1
                else:
                    state['active'] += 1
                    state['admitted'] += 1
                    attempt = state['admitted']
                    failure = state['always_fail'] or (state['fail_every'] > 0 and attempt % state['fail_every'] == 0)
                    delay = state['delay']
            if overloaded:
                self.respond(429, {'error': {'message': 'Source concurrency limit reached', 'type': 'rate_limit_error'}})
                return
            try:
                time.sleep(delay)
                if failure:
                    with lock:
                        state['failed_503'] += 1
                    self.respond(503, {'error': {'message': 'Simulated source failure', 'type': 'server_error'}})
                else:
                    with lock:
                        state['succeeded'] += 1
                    self.respond(200, {
                        'id': f'chatcmpl-{name}-{attempt}', 'object': 'chat.completion',
                        'created': int(time.time()), 'model': MODEL,
                        'choices': [{'index': 0, 'message': {'role': 'assistant',
                            'content': f'模拟回答：请求处理成功。实际来源：{name}。'}, 'finish_reason': 'stop'}],
                        'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30},
                    })
            finally:
                with lock:
                    state['active'] -= 1
    return Handler


class DemoServer(ThreadingHTTPServer):
    request_queue_size = 256


def main():
    servers = []
    try:
        for profile in PROFILES:
            server = DemoServer(('127.0.0.1', profile[1]), handler_for(*profile))
            server.daemon_threads = True
            servers.append(server)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            print(f'{profile[0]} http://127.0.0.1:{profile[1]}/v1 capacity={profile[4]} fail_every={profile[5]}', flush=True)
        print('Ctrl+C stops all four sources. Prices and token usage are fictional.', flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
