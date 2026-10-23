# DeepSeek Harness (dsh) — installed, and what it still needs

## State: installed and running

```
C:\Users\avina\AppData\Local\Temp\claude\...\scratchpad\dshtry\
    node_modules\@deepseek-ai\dsh    0.1.0-rc.7
~\.dsh\profiles\headless\            (bootstrapped by dsh itself)
```

Verify:

```bash
export PATH="$PATH:/c/Users/avina/AppData/Roaming/npm"
cd <scratchpad>/dshtry
node node_modules/@deepseek-ai/dsh/lib/bin.js --help
```

## How it got installed, after npm failed five times

`npm install @deepseek-ai/dsh` never completed — the tree is 502 packages and
every attempt (npx via bash, npx via PowerShell, npm backgrounded twice, npm
foregrounded once) was killed or timed out during dependency resolution.

**pnpm did it in one pass.** corepack could not enable pnpm because it wants to
write to `C:\Program Files\nodejs` (EPERM), so install it into the user prefix
instead, which is already on PATH:

```bash
npm install -g pnpm          # 14 seconds
pnpm add @deepseek-ai/dsh    # 502 resolved, 443 added
```

If you ever reinstall this, skip npm entirely.

## What it still needs: one API key

The headless profile boots with:

```yaml
- id: agent-default-model
  config:
    provider: deepseek-official
    model: deepseek-v4-flash
```

There is no DeepSeek key on this machine, so `dsh --profile headless "<task>"`
cannot answer anything. **This is the only thing standing between the harness
and being usable** — everything else is in place.

**CORRECTION — it IS DeepSeek-only as installed.** I earlier said the bundled
LLM layer carried ten provider routes (anthropic-messages, openai, openrouter,
bedrock, zai...) and that any key would drive it. That was wrong. Those ids
live in `@deepseek-ai/dsh-llm-pi-ai`, whose own package description calls it a
"design-verification twin" — a test double. The real adapter is
`@deepseek-ai/dsh-llm-deepseek`:

```
endpoint     https://api.deepseek.com
provider id  deepseek-official
env          DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
```

Running it on a real task gives exactly one error:

```
$ dsh --profile headless "List the movement names in reels5.MOVE_FOOTAGE
                          pinned to a video rather than a still."
dsh: MISSING_CREDENTIAL: llm-deepseek: no API key for provider route
"deepseek-official"; store DEEPSEEK_API_KEY through the credentials service
(the web Models page writes it), or export DEEPSEEK_API_KEY in the
launching environment
```

So: get a key at platform.deepseek.com and `export DEEPSEEK_API_KEY=...`.
`DEEPSEEK_BASE_URL` is also honoured, so any OpenAI-compatible
chat-completions endpoint works too — a local Ollama would do it, but Ollama
is not installed on this machine and no model is pulled.

## IT RUNS. Here is the wire.

`DEEPSEEK_BASE_URL` accepts any OpenAI-compatible chat-completions endpoint,
and fal.ai's `any-llm` serves `deepseek/deepseek-v3.1-terminus` - and the
FAL_KEY in `../.env.local` works. `fal_openai_shim.py` bridges the two.

```bash
python3 fal_openai_shim.py 8880                     # terminal 1
export DEEPSEEK_BASE_URL=http://127.0.0.1:8880/v1   # terminal 2
export DEEPSEEK_API_KEY=local-shim                  # only checked non-empty
dsh --profile headless "Reply with exactly one word: CONNECTED"
# -> CONNECTED
```

Three things had to be fixed to get there, each found by reading the error:

1. `MISSING_CREDENTIAL` - no key. Solved by the shim + BASE_URL.
2. `fal 400: maximum context length is 163840 tokens, you requested 259147
   (3147 of text input, 256000 in the output)`. **dsh asks for 256000 output
   tokens by default.** The shim clamps `max_tokens` to 8192.
3. `STREAM_CLOSED: SSE stream ended without [DONE]` - dsh sets `stream:true`
   and waits for the terminating event. The model had already answered; the
   shim now emits `chat.completion.chunk` events and `data: [DONE]`.

## Tool calling — the part that makes it actually useful

fal's `any-llm` has NO function calling. dsh offers **26 tools** (glob, grep,
read, edit, bash...) and the model could reach none of them, so it answered
from imagination — that is exactly how it invented a `cue_positions()` that
does not exist.

`fal_openai_shim.py` now bridges that too: it appends the tool list to the
system prompt with a strict json protocol, parses the model's reply, and
promotes it to a real OpenAI `tool_calls` response so dsh executes the tool and
loops. Two rounds of fixing were needed — the model narrates before the json
("I'll use the grep tool...") so the parser takes the first balanced `{...}`
rather than requiring the reply to start with one.

Proof it works end to end:

```
$ dsh --profile headless "Use grep to find where 'def cue_positions' is
                          defined. Reply with filename and line number."
The function `cue_positions` is defined in `cues.py` at line 164.
```

Shim log for that run:

```
-> tools_offered=26 [create_goal, edit, exit_plan_mode, get_goal, glob, grep]
<- tool_call grep({"pattern": "def cue_positions", "path": "."})
-> prompt 8349b        <- dsh fed the grep RESULT back
<- 32b [stream]
```

`cues.py:164` is correct. Same question without tools produced a fabrication.

**Always verify its output anyway** — with tools it is right, without them it is
confidently wrong, and nothing in the answer tells you which happened.

## Verified working without a key

`dsh plugin` needs no model. The vision plugin went in through dsh's own
plugin command in 1.1 seconds:

```bash
dsh plugin --profile headless add @liustack/modlens     # -> 3.22.0
```

## Why you would bother

Two modes are useful here:

- `dsh --profile headless "<task>"` — answers one task and exits. Scriptable,
  so it can be called from a build step.
- `dsh plugin --profile headless add <package>` — its plugin command forwards
  to pnpm inside the profile. This is how `@liustack/modlens` (the vision
  plugin) would go in.

## Honest assessment for this project

The harness will not improve the film by itself. It has no media packages —
its job is running agents, the same role Claude Code plays here. What it offers
is a second, scriptable agent runtime with a plugin ecosystem (~9,700 repos,
including vision and video plugins).

The thing that DID come out of examining it — `ocr_sweep.py`, which reads every
shot for foreign burned-in text — is already in this repo and needs no harness
to run.
