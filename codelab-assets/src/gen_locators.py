#!/usr/bin/env python3
"""Per-chapter 'you are here' locator strips, in the same Swiss/editorial
language as four-memories.svg.

Four dials: which memory · how long it lives · what shape it is · where it sits.
Edit CHAPTERS, re-run, re-render. One config change beats nine hand-edits.

Canvas is 1150 wide on purpose: claat renders body images at 752px max, so a
wider canvas only shrinks the type. At 1150 the scale is 0.65 and 30px reads
as ~20px on the page. The one-line takeaway is NOT baked in — it goes in the
codelab as markdown right under the image, at full body size.
"""
import pathlib

W, H = 1150, 280
COLS = [76, 336, 596, 856]
DIVIDERS = [306, 566, 826]
Y0, LH = 104, 46

INK = "#0F172A"
OFF = "#D9DFE6"
MUTED = "#94A3B8"
RULE = "#E8EBF0"

TYPE_COLOR = {
    "Working": "#3730A3",
    "Episodic": "#B45309",
    "Semantic": "#6D28D9",
    "Procedural": "#94A3B8",
}
TYPES = list(TYPE_COLOR)
SPANS = ["short-term", "long-term"]
SHAPES = ["structured", "unstructured"]
HOMES = ["in the process", "on disk", "managed cloud"]

# line = the takeaway rendered as markdown under the image, not baked into it
CHAPTERS = {
    "r1": dict(
        types=["Working"], spans=["short-term"],
        shapes=["structured", "unstructured"], homes=["in the process"],
        line="Two channels inside one conversation: the transcript the model reads, and the state your code trusts.",
    ),
    "r2": dict(
        types=["Working"], spans=["short-term"],
        shapes=["structured", "unstructured"], homes=["on disk"],
        line="Only one dial moved. Persistence changes *where* the conversation lives — not what kind of memory it is.",
    ),
    "r3": dict(
        types=["Episodic", "Semantic"], spans=["long-term"],
        shapes=["unstructured"], homes=["in the process"],
        line="A new kind of memory — but still inside the process, so it dies with the server. The next chapter fixes that.",
    ),
    "membank": dict(
        types=["Episodic", "Semantic"], spans=["long-term"],
        shapes=["unstructured"], homes=["managed cloud"],
        line="Same two policies, same two lines as rung 3. Only the home moved — and now it survives restarts, machines, and days.",
    ),
    "r4": dict(
        types=["Episodic"], spans=["long-term"],
        shapes=["unstructured"], homes=["on disk"],
        line="The upload gets a home of its own; the facts you extract from it land back in short-term working state.",
    ),
    "r5": dict(
        types=["Semantic"], spans=["long-term"],
        shapes=["structured"], homes=["on disk"],
        line="The company's records, traversed on a fixed path — the agent supplies a parameter, never a query.",
    ),
    "w1": dict(
        types=["Semantic"], spans=["long-term"],
        shapes=["structured"], homes=["managed cloud"],
        line="The same records, moved into the warehouse the rest of the company already queries.",
    ),
    "w2": dict(
        types=["Semantic"], spans=["long-term"],
        shapes=["unstructured"], homes=["managed cloud"],
        line="Meaning computed beside the rows — recall that still works when no keyword matches.",
    ),
    "w3": dict(
        types=["Semantic"], spans=["long-term"],
        shapes=["structured", "unstructured"], homes=["managed cloud"],
        line="Both shapes, one agent: a vector search for meaning and a join for connection.",
    ),
}

SANS = "-apple-system,\"SF Pro Text\",\"Helvetica Neue\",Arial"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def column(x, header, options, active, colors=None):
    out = [
        f'<text x="{x}" y="48" font-family=\'{SANS}\' font-size="20" '
        f'font-weight="700" fill="{MUTED}" letter-spacing="1.6">{header}</text>'
    ]
    for i, opt in enumerate(options):
        y = Y0 + i * LH
        on = opt in active
        color = (colors or {}).get(opt, INK) if on else OFF
        weight = 700 if on else 500
        if on:
            out.append(f'<circle cx="{x - 22}" cy="{y - 10}" r="6" fill="{color}"/>')
        out.append(
            f'<text x="{x}" y="{y}" font-family=\'{SANS}\' font-size="30" '
            f'font-weight="{weight}" fill="{color}" letter-spacing="-0.5">{esc(opt)}</text>'
        )
    return "\n  ".join(out)


def build(cfg):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'  <rect width="{W}" height="{H}" fill="#FFFFFF"/>',
    ]
    for dx in DIVIDERS:
        parts.append(f'  <line x1="{dx}" y1="24" x2="{dx}" y2="258" stroke="{RULE}" stroke-width="1.5"/>')

    parts.append("  " + column(COLS[0], "WHICH MEMORY", TYPES, cfg["types"], TYPE_COLOR))
    parts.append("  " + column(COLS[1], "HOW LONG", SPANS, cfg["spans"]))
    parts.append("  " + column(COLS[2], "WHAT SHAPE", SHAPES, cfg["shapes"]))
    parts.append("  " + column(COLS[3], "WHERE IT SITS", HOMES, cfg["homes"]))
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    for name, cfg in CHAPTERS.items():
        (here / f"locator-{name}.svg").write_text(build(cfg))
        print(f"wrote locator-{name}.svg")
