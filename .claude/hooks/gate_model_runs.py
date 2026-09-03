#!/usr/bin/env python3
"""PreToolUse(Bash) guard: block MPP model runs unless the latest user prompt says "execute".

Enforces the standing rule that model solves never launch without explicit approval. A model-run
command is any Bash command invoking run.py / run_gcam_ladder.py / run_poc.py / main.py. For those,
the user's most recent typed prompt (from the transcript) must contain the keyword "execute"
(case-insensitive); otherwise the call is denied. All other Bash commands pass through untouched.
Fails closed: if a model-run command is seen and approval can't be confirmed, it is denied.
"""

import json
import re
import sys

MODEL_RUN = re.compile(r"\b(run_gcam_ladder|run_poc|run|main)\.py\b")


def latest_user_prompt(transcript_path):
    """Text of the most recent genuinely-typed user message (skips tool_result blocks)."""
    text = ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") != "user":
                    continue
                content = (obj.get("message") or {}).get("content")
                if isinstance(content, str):
                    got = content
                elif isinstance(content, list):
                    got = "\n".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text")
                else:
                    got = ""
                if got.strip():
                    text = got  # keep the last one
    except Exception:
        return None
    return text


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # unparseable input: don't interfere
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command", "") or ""
    if not MODEL_RUN.search(command):
        sys.exit(0)  # not a model run

    prompt = latest_user_prompt(data.get("transcript_path"))
    if prompt is None:
        deny('Model run blocked: could not read the transcript to confirm approval. '
             'Include the keyword "execute" in a prompt to launch a model run.')
    if re.search(r"execute", prompt, re.IGNORECASE):
        sys.exit(0)  # approved
    deny('Model run blocked: your most recent prompt must contain the keyword "execute" to '
         'launch a model run (run.py / run_gcam_ladder.py / run_poc.py / main.py). Ask the user, '
         'then re-run only after they send a prompt containing "execute".')


if __name__ == "__main__":
    main()
