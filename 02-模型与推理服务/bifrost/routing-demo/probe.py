#!/usr/bin/env python3
"""Send a bounded set of requests to the tutorial gateway and summarize results."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import time
import urllib.error
import urllib.request

p = argparse.ArgumentParser()
p.add_argument('--policy', choices=['default', 'cost', 'stable', 'throughput'], default='default')
p.add_argument('--count', type=int, default=20)
p.add_argument('--concurrency', type=int, default=1)
a = p.parse_args()
if not 1 <= a.count <= 500 or not 1 <= a.concurrency <= 100:
    p.error('count must be 1..500 and concurrency 1..100')
key = os.environ.get('BF_VK')
if not key:
    p.error('Set BF_VK to the tutorial Virtual Key secret')
base = os.environ.get('BASE_URL', 'http://127.0.0.1:8081').rstrip('/')


def call(_):
    data = json.dumps({'model': 'demo-model', 'messages': [
        {'role': 'user', 'content': '请回答测试成功'}], 'stream': False}).encode()
    headers = {'x-bf-vk': key, 'Content-Type': 'application/json'}
    if a.policy != 'default':
        headers['x-demo-policy'] = a.policy
    req = urllib.request.Request(base + '/v1/chat/completions', data=data, headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
            content = result['choices'][0]['message']['content']
            source = re.search(r'source-[abcd]', content)
            return r.status, source.group() if source else 'unknown', time.monotonic() - start
    except urllib.error.HTTPError as e:
        e.read()
        return e.code, 'failed', time.monotonic() - start
    except Exception as e:
        return type(e).__name__, 'failed', time.monotonic() - start

with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
    results = list(pool.map(call, range(a.count)))
durations = sorted(r[2] for r in results)
print(json.dumps({
    'policy': a.policy, 'requests': a.count, 'concurrency': a.concurrency,
    'statuses': dict(Counter(str(r[0]) for r in results)),
    'final_sources': dict(Counter(r[1] for r in results)),
    'mean_seconds': round(sum(durations) / len(durations), 3),
    'p95_seconds': round(durations[min(len(durations)-1, int(len(durations)*0.95))], 3),
    'note': 'Final source counts include fallback effects; inspect routing logs for initial targets.'
}, ensure_ascii=False, indent=2))
