#!/usr/bin/env python3
"""Minimal Pascal MCP stdio driver.

Spawns `pascal mcp connect`, performs the MCP handshake, then executes a
sequence of calls from a JSON file. Each entry in the calls file is either:

    {"tool": "<tool_name>", "args": {...}}          -> tools/call
    {"method": "<rpc_method>", "params": {...}}     -> raw JSON-RPC

Responses are written to an output file (default rpc_results.json next to
the calls file). Every line is also echoed to stdout so progress is visible.

Usage:
    python3 pascal_mcp_rpc.py calls.json [results.json]
"""
import json
import queue
import subprocess
import sys
import threading
import time

READ_TIMEOUT = 60  # seconds per response


def main():
    calls_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else calls_path + '.results.json'
    calls = json.load(open(calls_path))

    proc = subprocess.Popen(
        ['pascal', 'mcp', 'connect'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    q = queue.Queue()
    threading.Thread(
        target=lambda: [q.put(l) for l in proc.stdout] or q.put(None),
        daemon=True).start()

    def send(msg):
        proc.stdin.write(json.dumps(msg, ensure_ascii=False) + '\n')
        proc.stdin.flush()

    def recv(want_id):
        deadline = time.time() + READ_TIMEOUT
        while time.time() < deadline:
            try:
                line = q.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if line is None:
                raise RuntimeError('connector stdout closed')
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get('id') == want_id:
                return msg
        raise TimeoutError(f'no response for id {want_id}')

    send({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "devin-cli", "version": "1.0"}}})
    init = recv(0)
    print('INIT:', init.get('result', {}).get('serverInfo'), flush=True)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    results = [{'initialize': init}]
    for i, call in enumerate(calls):
        if 'tool' in call:
            rpc = {"jsonrpc": "2.0", "id": i + 1, "method": "tools/call",
                   "params": {"name": call['tool'],
                              "arguments": call.get('args', {})}}
        else:
            rpc = {"jsonrpc": "2.0", "id": i + 1,
                   "method": call['method'],
                   "params": call.get('params', {})}
        send(rpc)
        resp = recv(i + 1)
        label = call.get('tool') or call.get('method')
        ok = 'error' not in resp
        print(f'[{i+1}/{len(calls)}] {label}: {"OK" if ok else "ERROR"}',
              flush=True)
        if not ok:
            print('   ', json.dumps(resp.get('error'), ensure_ascii=False)[:500],
                  flush=True)
        results.append({'call': call, 'response': resp})

    json.dump(results, open(out_path, 'w'), ensure_ascii=False, indent=2)
    print('WROTE:', out_path, flush=True)
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.terminate()


if __name__ == '__main__':
    main()
