"""Lint Moodstay narration for property-name leaks, direct comment CTAs, and endings.

Usage: python tools/validate_script.py projects/starville-jeju/script.md --property-name "제주 스타빌"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DIRECT_COMMENT_CTA = re.compile(
    r"(?:댓글|코멘트).{0,24}(?:남겨|달아|적어|써\s*주|물어|보내|알려)|"
    r"(?:궁금하면|궁금하시?면).{0,16}(?:댓글|코멘트)|"
    r"(?:댓글|코멘트).{0,20}(?:정보|숙소|이름).{0,12}(?:보내|알려|남겨|달아)",
    re.IGNORECASE,
)
EXPERIENCE_ENDING = re.compile(
    r"(?:다녀왔어요|힐링하고 왔어요|쉬다 왔어요|왔어요|왔더라고요|"
    r"좋더라고요|좋았어요|괜찮더라고요|괜찮았어요|딱이었어요|되더라고요|"
    r"추천하고 싶어요|추천해요|잘 쉬었어요|잘 놀다 왔어요|"
    r"아깝지 않더라고요|아깝지 않았어요)[.!…]*$"
)


def narration_text(markdown: str) -> str:
    """Return blockquoted spoken lines, or plain text if no quote block exists."""
    quoted = [line[1:].strip() for line in markdown.splitlines() if line.lstrip().startswith(">")]
    if quoted:
        return " ".join(quoted)
    content = [line.strip() for line in markdown.splitlines() if line.strip() and not line.startswith("#")]
    return " ".join(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--property-name", help="Exact property name that must not appear in spoken narration")
    args = parser.parse_args()

    text = narration_text(args.script.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not text:
        errors.append("spoken narration is empty")
    if args.property_name and args.property_name.casefold() in text.casefold():
        errors.append(f"property name appears in narration: {args.property_name}")
    if DIRECT_COMMENT_CTA.search(text):
        errors.append("direct comment CTA found; let the unnamed property create curiosity")
    if text.rstrip().endswith(("?", "？")):
        errors.append("narration ends with a question instead of an experience-style verdict")
    if not EXPERIENCE_ENDING.search(text.rstrip()):
        errors.append("ending does not match an experience-style personal verdict")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: unnamed property, no direct comment CTA, experience-style ending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
