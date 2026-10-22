#!/usr/bin/env python3
"""Direct MCP-over-HTTP client for pascal (bypasses hung stdio bridge).
Usage: pascal_mcp_http.py <tool> '<json-args>'"""
import json, os, sys, urllib.request

URL = "http://127.0.0.1:52658/mcp"
TOKEN = open(os.path.expanduser("~/.pascal/run/mcp-token")).read().strip()

def _post(payload, session=None):
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream",
         "Authorization": f"Bearer {TOKEN}"}
    if session: h["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h)
    # bypass macOS system proxy: urllib getproxies() picks it up and 502s loopback
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    resp = opener.open(req, timeout=60)
    sid = resp.headers.get("mcp-session-id")
    raw = resp.read().decode()
    # SSE stream: take the last data: line
    data = None
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
    return (data if data is not None else json.loads(raw)) if raw.strip() else {}, sid

def call(tool, args):
    _, sid = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                               "clientInfo": {"name": "direct", "version": "1.0"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    resp, _ = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": tool, "arguments": args}}, sid)
    return resp

if __name__ == "__main__":
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = call(tool, args)
    # extract text content if present
    c = r.get("result", {}).get("content")
    if c and isinstance(c, list) and c[0].get("type") == "text":
        print(c[0]["text"][:6000])
    else:
        print(json.dumps(r, ensure_ascii=False)[:6000])
