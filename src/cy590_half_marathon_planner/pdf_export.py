"""Render the generated training plan to a landscape PDF."""

import html as html_lib
import re
import tempfile
from datetime import datetime
from pathlib import Path

import markdown
from xhtml2pdf import pisa

from cy590_half_marathon_planner.coach import _flatten

# Tune TABLE_FONT_PT down if the weekly table overflows the page width.
PAGE_FONT_PT = 9
TABLE_FONT_PT = 6.5

STYLE = f"""
@page {{
    size: letter landscape;
    margin: 0.4in;
}}
body {{
    font-family: Helvetica, sans-serif;
    font-size: {PAGE_FONT_PT}pt;
    line-height: 1.35;
}}
h1 {{ font-size: 15pt; margin: 0 0 2pt 0; }}
h2 {{ font-size: 12pt; margin: 10pt 0 3pt 0; }}
h3 {{ font-size: 10pt; margin: 8pt 0 3pt 0; }}
.meta {{ font-size: 7.5pt; color: #666666; margin-bottom: 8pt; }}
table {{
    width: 100%;
    border: 0.5pt solid #999999;
    margin: 4pt 0 8pt 0;
}}
th, td {{
    border: 0.5pt solid #999999;
    padding: 2pt 3pt;
    font-size: {TABLE_FONT_PT}pt;
    vertical-align: top;
    word-wrap: break-word;
}}
th {{ background-color: #eeeeee; font-weight: bold; }}
ul, ol {{ margin: 2pt 0 6pt 14pt; }}
li {{ margin-bottom: 1.5pt; }}
"""

# Everything is escaped first; <br> is the single tag allowed back in.
_ALLOWED_BR = re.compile(r"&lt;br\s*/?&gt;", re.IGNORECASE)


def _latest_plan(history: list[dict]) -> str | None:
    """Return the most recent assistant message, or None."""
    for turn in reversed(history or []):
        if turn.get("role") == "assistant":
            text = _flatten(turn.get("content")).strip()
            if text:
                return text
    return None


def _markdown_to_html(plan_md: str) -> str:
    escaped = html_lib.escape(plan_md)
    escaped = _ALLOWED_BR.sub("<br/>", escaped)
    body = markdown.markdown(escaped, extensions=["tables", "sane_lists"])
    generated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return f"""<html>
<head><meta charset="utf-8"><style>{STYLE}</style></head>
<body>
<h1>Half-Marathon Training Plan</h1>
<div class="meta">Generated {generated}</div>
{body}
</body>
</html>"""


def export_plan_pdf(history: list[dict]) -> str:
    """Write the latest plan to a landscape PDF and return its path."""
    plan_md = _latest_plan(history)
    if plan_md is None:
        raise ValueError("No plan to export yet. Generate a plan first.")

    out_dir = Path(tempfile.gettempdir()) / "half_marathon_plans"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"training_plan_{stamp}.pdf"

    with out_path.open("wb") as fh:
        result = pisa.CreatePDF(
            src=_markdown_to_html(plan_md),
            dest=fh,
            encoding="utf-8",
        )

    if result.err:
        raise ValueError("The PDF renderer failed on this plan.")
    return str(out_path)