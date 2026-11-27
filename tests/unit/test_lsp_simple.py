"""Simplest possible test - read all stdout synchronously.

Manual 8 §1.2 — LSP initialize/initialized/shutdown
"""
import subprocess
import sys
import json
import time
import pytest


def test_lsp_initialize_shutdown():
    """Manual 8 §1.2: LSP initialize, initialized, didChange, shutdown."""
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
    stderr = proc.stderr.read().decode("utf-8", errors="replace")

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
        except Exception:
            pass
        pos = body_start + cl

    has_diagnostics = any(
        m.get("method") == "textDocument/publishDiagnostics"
        for m in messages
    )
    assert len(messages) > 0, f"No messages received. stderr: {stderr[:200]}"
    assert has_diagnostics, "No publishDiagnostics received"
