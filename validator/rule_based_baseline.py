"""
Rule-based baseline for the LLM comparison study.

Runs the exact research prompts (directory ``prompts/``) through a classic
rule-based conversational system - the ELIZA implementation shipped with NLTK
(nltk.chat.eliza), i.e. the pattern-matching paradigm described in chapter 2.1
of the thesis - and scores the result with the same rubric used for the LLMs.

The run is deterministic: the response template chosen inside a matched rule is
drawn from a seeded PRNG, so repeated runs produce byte-identical output.

Usage:
    pip install nltk
    python validator/rule_based_baseline.py --prompts prompts --out results

Outputs:
    results/rule_based_baseline.csv        - one row per prompt
    results/rule_based_transcripts.md      - full transcripts (evidence)
"""

import argparse
import csv
import os
import random
import re
import sys

from nltk.chat.eliza import eliza_chatbot

SEED = 20260922

# Markers of an actual programming answer (any of these => the system produced code).
CODE_MARKERS = re.compile(
    r"(^|\s)(def |class |import |from \w+ import|@app\.|async def|SELECT |CREATE TABLE|<html|```)",
    re.IGNORECASE,
)

# Polish diacritics / function words - used to detect the language of a reply.
PL_MARKERS = re.compile(r"[ąćęłńóśźż]|\b(nie|jest|oraz|plik|kod|zwraca)\b", re.IGNORECASE)

# Prompts 1-10 were issued in Polish, prompt 11 onwards in English.
def prompt_language(name: str) -> str:
    m = re.match(r"p(\d+)", name)
    if not m:
        return "unknown"
    return "pl" if int(m.group(1)) <= 10 else "en"


def matched_rule(text: str):
    """Return (rule_index, pattern) of the ELIZA rule that fired, or (None, None)."""
    for idx, (pattern, _responses) in enumerate(eliza_chatbot._pairs):
        if pattern.match(text):
            return idx, pattern.pattern
    return None, None


def is_fallback(rule_index: int) -> bool:
    """The last rule of the ELIZA rule base is the catch-all '(.*)' rule."""
    return rule_index == len(eliza_chatbot._pairs) - 1


def respond(text: str) -> str:
    """Return the engine reply, or an explicit error marker.

    The NLTK ELIZA engine treats '%' as a wildcard placeholder and raises on
    inputs that contain a bare percent sign, which several research prompts do.
    A crash is recorded as a failure of the rule base, not hidden.
    """
    try:
        return eliza_chatbot.respond(text)
    except Exception as exc:  # noqa: BLE001 - engine failure is a measured outcome
        return f"[ENGINE ERROR: {type(exc).__name__}]"


def run(prompts_dir: str, out_dir: str) -> None:
    random.seed(SEED)
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(
        (f for f in os.listdir(prompts_dir) if not f.startswith(".")),
        key=lambda f: [float(x) for x in re.findall(r"\d+", f)] or [0],
    )
    if not files:
        sys.exit(f"No prompt files found in {prompts_dir}")

    rows = []
    transcript_lines = [
        "# Rule-based baseline - full transcripts",
        "",
        f"System: ELIZA (nltk.chat.eliza), seed={SEED}. Every research prompt was sent "
        "turn by turn, exactly as it was sent to the language models.",
        "",
    ]

    for fname in files:
        path = os.path.join(prompts_dir, fname)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        turns = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not turns:
            continue

        replies, own_replies, fallbacks, errors = [], [], 0, 0
        transcript_lines.append(f"## {fname}")
        for turn in turns:
            idx, _pattern = matched_rule(turn)
            reply = respond(turn)
            if idx is None or is_fallback(idx) or reply.startswith("[ENGINE ERROR"):
                fallbacks += 1
            if reply.startswith("[ENGINE ERROR"):
                errors += 1
            replies.append(reply)
            # ELIZA echoes fragments of the user turn; strip them so that the
            # language check measures the system's own wording, not the echo.
            turn_tokens = set(re.findall(r"\w+", turn.lower()))
            own_replies.append(
                " ".join(
                    w for w in re.findall(r"\w+", reply.lower()) if w not in turn_tokens
                )
            )
            transcript_lines.append(f"- **USER:** {turn}")
            transcript_lines.append(f"- **ELIZA:** {reply}")
        transcript_lines.append("")

        joined = "\n".join(replies)
        joined_own = "\n".join(own_replies)
        lang = prompt_language(fname)
        rows.append(
            {
                "prompt": fname,
                "prompt_language": lang,
                "turns": len(turns),
                "chars_in": len(text),
                "chars_out": len(joined),
                "generic_fallback_replies": fallbacks,
                "engine_errors": errors,
                "fallback_rate": round(fallbacks / len(turns), 2),
                "code_produced": bool(CODE_MARKERS.search(joined)),
                "files_created": 0,
                "echoes_user_text": any(
                    t.lower()[:25] in r.lower() for t, r in zip(turns, replies) if len(t) > 25
                ),
                "reply_language": "pl" if PL_MARKERS.search(joined_own) else "en",
                "language_instruction_met": (
                    "pl" if PL_MARKERS.search(joined_own) else "en"
                ) == lang,
                "app_runs": False,
                "score_1_5": 1,
            }
        )

    csv_path = os.path.join(out_dir, "rule_based_baseline.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = os.path.join(out_dir, "rule_based_transcripts.md")
    open(md_path, "w", encoding="utf-8").write("\n".join(transcript_lines))

    total_turns = sum(r["turns"] for r in rows)
    total_fallback = sum(r["generic_fallback_replies"] for r in rows)
    print(f"prompts processed : {len(rows)}")
    print(f"total turns       : {total_turns}")
    print(f"generic fallbacks : {total_fallback} ({total_fallback / total_turns:.0%})")
    print(f"engine errors     : {sum(r['engine_errors'] for r in rows)}")
    print(f"prompts with code : {sum(r['code_produced'] for r in rows)}")
    print(f"files created     : {sum(r['files_created'] for r in rows)}")
    print(f"mean score        : {sum(r['score_1_5'] for r in rows) / len(rows):.2f}")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default="prompts")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    run(args.prompts, args.out)
