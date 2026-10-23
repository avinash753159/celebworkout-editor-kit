"""An OpenAI chat-completions endpoint backed by fal.ai `any-llm`.

Why: the DeepSeek Harness (dsh) refuses to answer anything without
DEEPSEEK_API_KEY. There is no DeepSeek key on this machine and no local model
server. But its real adapter also honours DEEPSEEK_BASE_URL, and fal.ai's
`any-llm` endpoint serves `deepseek/deepseek-v3.1-terminus` - and we DO have a
working FAL_KEY.

So this is the missing wire: it speaks OpenAI chat-completions on the front,
calls fal on the back, and lets dsh run against a real DeepSeek model.

    python3 fal_openai_shim.py 8877          # any free port
    export DEEPSEEK_BASE_URL=http://127.0.0.1:<port>/v1
    export DEEPSEEK_API_KEY=local             # dsh only checks it is non-empty
    dsh --profile headless "<task>"

Deliberately minimal: no streaming, no tool-calls, no token accounting. It
exists to prove the harness runs end to end and to let it answer a question,
not to be a production gateway.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

FAL_URL = "https://fal.run/fal-ai/any-llm"
MODEL = os.environ.get("SHIM_MODEL", "deepseek/deepseek-v3.1-terminus")
MAX_OUT = int(os.environ.get("SHIM_MAX_OUT", "8192"))


def fal_key() -> str:
    k = os.environ.get("FAL_KEY", "").strip()
    if k:
        return k
    env = Path(__file__).resolve().parent.parent / ".env.local"
    m = re.search(r"^FAL_KEY=(.+)$", env.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit("no FAL_KEY in environment or ../.env.local")
    return m.group(1).strip()


KEY = fal_key()


def call_fal(system: str, prompt: str, max_tokens: int | None) -> str:
    body = {"model": MODEL, "prompt": prompt, "priority": "latency"}
    if system:
        body["system_prompt"] = system
    # dsh asks for 256000 output tokens by default, which alone blows past
    # any-llm's 163840 context window - the 400 says "3147 of text input,
    # 256000 in the output". Clamp it; nothing here needs a novel back.
    body["max_tokens"] = min(int(max_tokens or MAX_OUT), MAX_OUT)
    req = urllib.request.Request(
        FAL_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # fal puts the real reason in the body; without it a 400 is unreadable
        raise RuntimeError(f"fal {e.code}: {e.read().decode('utf-8', 'replace')[:600]}") from None
    if d.get("error"):
        raise RuntimeError(str(d["error"])[:400])
    return d.get("output", "")


def flatten(messages: list[dict]) -> tuple[str, str]:
    """OpenAI messages -> (system_prompt, prompt).

    any-llm takes a single prompt string, so the turns are laid out as a
    transcript. Content can be a plain string or a list of typed parts.
    """
    sys_parts, turns = [], []
    for m in messages:
        c = m.get("content", "")
        if isinstance(c, list):
            c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
        c = (c or "").strip()
        if not c:
            continue
        role = m.get("role", "user")
        if role == "system":
            sys_parts.append(c)
        else:
            turns.append(f"{role.upper()}: {c}")
    return "\n\n".join(sys_parts), "\n\n".join(turns)


TOOL_PROTOCOL = """
You can call tools. To call one, reply with ONE json object and NOTHING else:
{"tool": "<name>", "arguments": {...}}
Do not wrap it in markdown. Do not explain first. Do not invent a tool name.
Never guess a file's contents - read it with a tool. When you have enough
information, reply with your final answer as ordinary prose instead.

Available tools:
"""


def tool_brief(tools):
    lines = []
    for t in tools:
        f = t.get("function") or {}
        params = ", ".join((f.get("parameters") or {}).get("properties", {}))
        lines.append("- %s(%s): %s" % (f.get("name"), params,
                                       str(f.get("description", ""))[:130]))
    return TOOL_PROTOCOL + "\n".join(lines)


def parse_tool_call(text):
    """A bare json tool call, with or without a ```json fence."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    if '"tool"' not in t:
        return None
    if not t.startswith('{'):
        # the model narrates first ("I'll use the grep tool...") and puts the
        # json after it; take the first balanced object that mentions a tool
        i = t.find('{')
        if i < 0:
            return None
        depth = 0
        for j in range(i, len(t)):
            if t[j] == '{':
                depth += 1
            elif t[j] == '}':
                depth -= 1
                if depth == 0:
                    t = t[i:j + 1]
                    break
        else:
            return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    name = d.get("tool")
    return (name, d.get("arguments") or {}) if isinstance(name, str) else None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):                       # /v1/models, so clients can probe
        self._send(200, {"object": "list", "data": [
            {"id": "deepseek-chat", "object": "model", "owned_by": "fal"},
            {"id": MODEL, "object": "model", "owned_by": "fal"}]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": {"message": f"bad json: {e}"}})
        system, prompt = flatten(req.get("messages") or [])
        if not prompt:
            return self._send(400, {"error": {"message": "no prompt"}})
        tools = req.get("tools") or []
        print(f"  -> {MODEL}  system {len(system)}b  prompt {len(prompt)}b  "
              f"tools_offered={len(tools)}"
              + (f" [{', '.join(t.get('function',{}).get('name','?') for t in tools[:6])}]"
                 if tools else ""), flush=True)
        if tools:
            system = (system + chr(10) + tool_brief(tools)).strip()
        try:
            text = call_fal(system, prompt, req.get("max_tokens"))
        except Exception as e:
            print(f"  !! {e}", flush=True)
            return self._send(502, {"error": {"message": str(e)[:400]}})
        call = parse_tool_call(text) if tools else None
        if call:
            nm, ar = call
            print('  <- tool_call %s(%s)' % (nm, json.dumps(ar)[:90]), flush=True)
            return self._send_tool_call(nm, ar, req.get('model') or MODEL,
                                        bool(req.get('stream')))
        print(f"  <- {len(text)}b{' [stream]' if req.get('stream') else ''}", flush=True)
        if req.get("stream"):
            return self._send_sse(text, req.get("model") or MODEL)
        self._send(200, {
            "id": f"chatcmpl-{int(time.time()*1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.get("model") or MODEL,
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        })

    def _send_tool_call(self, name, args, model, stream):
        """fal's any-llm has no function calling, so the model is asked to emit
        a json tool call as text and it is promoted to a real tool_calls
        response here. Without this dsh offers 26 tools, the model can reach
        none of them, and answers from imagination - which is exactly how it
        invented a cue_positions() that does not exist."""
        cid, now = "chatcmpl-%d" % int(time.time() * 1000), int(time.time())
        tc = [{"index": 0, "id": "call_%d" % now, "type": "function",
               "function": {"name": name, "arguments": json.dumps(args)}}]
        if not stream:
            return self._send(200, {
                "id": cid, "object": "chat.completion", "created": now,
                "model": model,
                "choices": [{"index": 0, "finish_reason": "tool_calls",
                             "message": {"role": "assistant", "content": None,
                                         "tool_calls": tc}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0,
                          "total_tokens": 0}})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for delta, fin in (({"role": "assistant", "tool_calls": tc}, None),
                           ({}, "tool_calls")):
            chunk = {"id": cid, "object": "chat.completion.chunk",
                     "created": now, "model": model,
                     "choices": [{"index": 0, "delta": delta,
                                  "finish_reason": fin}]}
            self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
    def _send_sse(self, text: str, model: str) -> None:
        """Stream the answer as chat.completion.chunk events.

        dsh sets stream:true and waits for a terminating `data: [DONE]`; a
        plain JSON body makes it fail with STREAM_CLOSED even though the model
        already answered. fal's any-llm is not itself streaming, so the whole
        answer arrives at once and is emitted as a single content delta.
        """
        cid, now = f"chatcmpl-{int(time.time()*1000)}", int(time.time())
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def event(delta: dict, finish=None) -> None:
            chunk = {"id": cid, "object": "chat.completion.chunk", "created": now,
                     "model": model,
                     "choices": [{"index": 0, "delta": delta,
                                  "finish_reason": finish}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()

        event({"role": "assistant", "content": ""})
        event({"content": text})
        event({}, "stop")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def log_message(self, *a):              # keep the console readable
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 877
    print(f"fal shim on http://127.0.0.1:{port}/v1  ->  {MODEL}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
