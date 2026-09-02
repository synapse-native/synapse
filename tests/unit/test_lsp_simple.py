"""Simplest possible test - read all stdout synchronously.

Manual 8 §1.2 — LSP initialize/initialized/shutdown
"""
import subprocess
import sys
import json

proc = subprocess.Popen(
    [sys.executable, "-u", "main.py", "--lsp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

def send(obj):
    payload = json.dumps(obj)
    msg = f"Content-Length: {len(payload)}\r\n\r\n{payload}"
    proc.stdin.write(msg.encode())
    proc.stdin.flush()

send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"processId": None, "capabilities": {}}})
import time
time.sleep(1)

send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
time.sleep(1)

send({"jsonrpc": "2.0", "method": "textDocument/didChange",
      "params": {
          "textDocument": {"uri": "file:///t.syn", "version": 1},
          "contentChanges": [{"text": "#lang: es\nfuncion principal() -> nulo:\n    x = indefinido\n"}]
      }})
time.sleep(3)

send({"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": {}})
time.sleep(2)
proc.kill()

raw = proc.stdout.read()
print(f"STDOUT ({len(raw)} bytes):")
print(raw[:500])
print("...")
print(raw[-200:])

stderr = proc.stderr.read().decode("utf-8", errors="replace")
print(f"\nSTDERR ({len(stderr)} bytes):")
for line in stderr.split("\n"):
    safe = line.encode("ascii", errors="replace").decode("ascii")
    print(f"  {safe}")

# Parse all messages from raw bytes
parts = raw.split(b"\r\n\r\n")
print(f"\nRaw split into {len(parts)} parts")
for i, p in enumerate(parts[:6]):
    print(f"  Part {i}: {p[:100]}")

# Manual parse
messages = []
pos = 0
while pos < len(raw):
    hdr_end = raw.find(b"\r\n\r\n", pos)
    if hdr_end == -1:
        break
    header = raw[pos:hdr_end]
    cl = 0
    for line in header.decode().split("\r\n"):
        if "content-length:" in line.lower():
            cl = int(line.split(":", 1)[1].strip())
    body_start = hdr_end + 4
    body = raw[body_start:body_start + cl]
    try:
        msg = json.loads(body.decode("utf-8"))
        messages.append(msg)
    except Exception as e:
        print(f"  PARSE ERROR at pos {pos}: {e}")
        print(f"  body={body[:200]}")
    pos = body_start + cl

print(f"\nParsed {len(messages)} messages:")
for msg in messages:
    method = msg.get("method", "?")
    mid = msg.get("id", "?")
    if method == "textDocument/publishDiagnostics":
        diags = msg.get("params", {}).get("diagnostics", [])
        print(f"  publishDiagnostics: {len(diags)} errors")
        for d in diags:
            r = d["range"]["start"]
            print(f"    L{r['line']+1}:{r['character']} [{d['code']}] {d['message']}")
    else:
        print(f"  method={method} id={mid} result={msg.get('result', '?')}")