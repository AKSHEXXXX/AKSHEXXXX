#!/usr/bin/env python3
"""Render contrib-heatmap.svg (animated, GitHub-style) from contributions.json.

Recreates the exact look of the template SVG: 13-month grid, monthly labels,
Mon/Wed/Fri day labels, slide-in animation, legend and streak stats.
"""
import json
import os
from datetime import date, timedelta

CONTRIB = os.environ.get("CONTRIB_JSON", "contributions.json")
OUT = os.environ.get("OUT_SVG", "contrib-heatmap.svg")

COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
PITCH = 14          # column / row spacing in px
CELL = 11           # cell size in px
X0, Y0 = 28, 22     # grid origin
TEXT_TOP = 16       # month labels baseline

MONTH_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

CSS = f"""
  @keyframes slideIn{{0%{{opacity:0;transform:translateY(-5px) scale(0.55)}}65%{{opacity:1;transform:translateY(1px) scale(1.07)}}100%{{opacity:1;transform:translateY(0) scale(1)}}}}
  .box{{animation:slideIn 350ms cubic-bezier(0.22,1,0.36,1) both}}
  .lbl{{font:10px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#7d8590}}
  .sv {{font:bold 11px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#e6edf3}}
  .sl {{font:10px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#7d8590}}
"""


def level_of(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 3:
        return 1
    if count <= 6:
        return 2
    if count <= 9:
        return 3
    return 4


def compute_stats(data: dict[str, int], today: date) -> tuple[int, int, int]:
    window_start = today - timedelta(days=364)

    active = 0
    day = window_start
    while day <= today:
        if data.get(day.isoformat(), 0) > 0:
            active += 1
        day += timedelta(days=1)

    current = 0
    day = today
    while day >= window_start and data.get(day.isoformat(), 0) > 0:
        current += 1
        day -= timedelta(days=1)

    longest = 0
    run = 0
    day = window_start
    while day <= today:
        if data.get(day.isoformat(), 0) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        day += timedelta(days=1)

    return active, current, longest


def main() -> None:
    with open(CONTRIB, encoding="utf-8") as fh:
        data = json.load(fh)

    today = date.today()
    window_start = today - timedelta(days=364)

    start = window_start
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday

    weeks: list[date] = []
    col = start
    while col <= today:
        weeks.append(col)
        col += timedelta(days=7)

    n_cols = len(weeks)
    width = X0 + (n_cols - 1) * PITCH + CELL + 26
    height = 178

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append("<defs><style>")
    lines.append(CSS)
    lines.append("</style></defs>")
    lines.append(f'<rect width="{width}" height="{height}" fill="#0d1117" rx="8"/>')

    month_labels = []
    for ci, wstart in enumerate(weeks):
        for delta in range(7):
            day = wstart + timedelta(days=delta)
            if day.day == 1:
                month_labels.append((ci, MONTH_ABBR[day.month]))
                break
    for ci, label in month_labels:
        lines.append(f'<text x="{X0 + ci * PITCH}" y="{TEXT_TOP}" class="lbl">{label}</text>')

    for row, label, baseline in ((1, "Mon", 46), (3, "Wed", 74), (5, "Fri", 102)):
        lines.append(f'<text x="0" y="{baseline}" class="lbl">{label}</text>')

    cell_index = 0
    for ci, wstart in enumerate(weeks):
        for row in range(7):
            day = wstart + timedelta(days=row)
            count = data.get(day.isoformat(), 0) if day <= today else 0
            color = COLORS[level_of(count)]
            x = X0 + ci * PITCH
            y = Y0 + row * PITCH
            delay = cell_index * 12
            cell_index += 1
            lines.append(
                f'<rect class="box" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" style="animation-delay:{delay}ms"/>'
            )

    lines.append('<text x="28" y="136" class="lbl">Less</text>')
    for i, color in enumerate(COLORS):
        lines.append(f'<rect x="{58 + i * 15}" y="126" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    lines.append('<text x="133" y="136" class="lbl">More</text>')

    active, current, longest = compute_stats(data, today)
    centers = (round(width * 0.195), round(width * 0.517), round(width * 0.838))
    stats = [
        (f"{active} active days", "in the last year"),
        (f"{current} day streak", "current"),
        (f"{longest} day streak", "longest"),
    ]
    for (sv, sl), cx in zip(stats, centers):
        lines.append(f'<text x="{cx}" y="150" class="sv" text-anchor="middle">{sv}</text>')
        lines.append(f'<text x="{cx}" y="163" class="sl" text-anchor="middle">{sl}</text>')

    lines.append("</svg>")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Rendered {OUT}: {n_cols} weeks, {active} active days")


if __name__ == "__main__":
    main()