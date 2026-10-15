"""Score member applications with a small Groq-hosted LLM.

The join form asks applicants to describe their research interests and why
they want to collaborate. A Groq chat model grades the essay 1–10 on
*genuine curiosity* and *willingness to collaborate*. Scores at or above
``APPLICATION_MIN_SCORE`` (default 7) approve the application; anything lower
is rejected with a polite e-mail.
"""

from __future__ import annotations

import json
import re

import requests
from flask import current_app

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """\
You are an admissions reviewer for ADHAYAN, a youth-driven academic research
network. Applicants answer one question:

"What is your research interest, and why do you want to collaborate?"

Grade the answer on TWO criteria only:
1. Curiosity — is there a real, specific intellectual spark? Names of topics
   they want to explore, questions they are chasing, eagerness to learn.
2. Willingness to collaborate — do they actually want to work with others,
   share, iterate, and contribute, or only to take something?

Scoring guide:
- 9–10: Clearly genuine curiosity + strong collaborative intent.
- 7–8:  Solid curiosity and collaborative intent; minor vagueness is fine.
- 5–6:  Superficial or generic; weak curiosity or little interest in others.
- 1–4:  Copy-paste, spam, or pure self-promotion with no real curiosity.

Respond with ONLY a JSON object, no markdown fences:
{"score": <integer 1-10>, "reason": "<one short sentence>"}
"""


def score_application(essay: str) -> tuple[int | None, str]:
    """Return ``(score, reason)``. Score is ``None`` when review is unavailable."""
    api_key = current_app.config.get("GROQ_API_KEY", "")
    if not api_key:
        return None, "Groq API key not configured."

    model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0.2,
                "max_tokens": 200,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": essay.strip()[:6000]},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # pragma: no cover - network dependent
        current_app.logger.warning("Application scoring failed: %s", exc)
        return None, f"Scoring request failed: {exc}"

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        current_app.logger.warning("Unexpected score payload: %s", content)
        return None, "Could not parse score."

    try:
        data = json.loads(match.group(0))
        score = int(data["score"])
        reason = str(data.get("reason", "")).strip()
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        current_app.logger.warning("Unparseable score payload: %s", content)
        return None, "Could not parse score."

    return max(1, min(10, score)), reason
