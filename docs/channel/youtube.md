# YouTube

## Identity

- **Name:** YouTube
- **ID (UUID):** `584db0ec-6678-4717-97ce-3f9768625d59`
- **ID (numeric):** not present in `profile.json`
- **Title:** _(none in profile)_
- **Harness:** temporal
- **Group:** YouTube pipeline
- **Pack file:** `bots/youtube.md`

## Description

_(empty in profile.json)_

## Owns

_(not specified beyond description)_

## Guardrails

- _(none explicitly stated in profile; follow fleet AGENTS.md hard rules)_

## Decision routing

Handoff within YouTube pipeline; decisions escalate to YouTube COS 1:1.

## Home paths / Gmail labels

**Home paths:** _(none extracted)_

**Gmail labels:** _(none extracted)_

## Related rooms

- [YouTube COS](youtube-cos.md)

---

*Source: `profile.json` on box. Secrets redacted as `[REDACTED]`. Do not invent roles beyond this file + fleet AGENTS.md.*
