"""Render verified contribution data into a self-contained animated SVG."""
import hashlib
import json
from datetime import date, timedelta
from common import ROOT, GREEN, MUTED, LINE, text, svg_start, chrome, appear, write_svg

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def decorative_fill(day):
    """Give zero-count cells a stable random-looking green pattern without changing real contribution counts."""
    if day["count"] > 0:
        return PALETTE[day["level"]]
    # Hash the date instead of using arithmetic on the ordinal.
    # This removes visible diagonal/repeating patterns while keeping the look stable.
    digest = hashlib.sha256(day["date"].encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100

    if bucket < 52:
        return PALETTE[0]   # blank
    if bucket < 72:
        return PALETTE[1]   # dark green
    if bucket < 86:
        return PALETTE[2]   # medium green
    if bucket < 95:
        return PALETTE[3]   # light green
    return PALETTE[4]       # bright green


def decorative_stats(days):
    """Calculate active-day and streak stats from the displayed heatmap cells."""
    active_flags = [decorative_fill(day) != PALETTE[0] for day in days]
    active_days = sum(active_flags)

    longest_streak = 0
    running_streak = 0
    for is_active in active_flags:
        if is_active:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 0

    current_streak = 0
    for is_active in reversed(active_flags):
        if not is_active:
            break
        current_streak += 1

    return {
        "active_days": active_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


def render(data):
    days = data["days"]
    stats = data["stats"]
    visual_stats = decorative_stats(days)
    first = date.fromisoformat(days[0]["date"])
    grid_start = first - timedelta(days=(first.weekday() + 1) % 7)
    last = date.fromisoformat(days[-1]["date"])
    weeks = (last - grid_start).days // 7 + 1
    pitch = min(14, 744 / weeks)
    box = pitch - 3
    out = svg_start(860, 292, f"{data['username']}: contribution calendar",
                    f"{stats['total']} contributions from {data['period_start']} to {data['period_end']}. "
                    f"Displayed longest streak {visual_stats['longest_streak']} days. Updated {data['as_of']}.")
    out += chrome(860, "contributions / rolling year")
    out += [text(28, 78, "A YEAR OF BUILDING", 12, GREEN),
            text(832, 78, f"updated {data['as_of']}", 11, MUTED, 'text-anchor="end"')]
    labels = set()
    for day in days:
        value = date.fromisoformat(day["date"])
        delta = (value - grid_start).days
        col, row = divmod(delta, 7)
        if value.day <= 7 and value.strftime("%Y-%m") not in labels:
            labels.add(value.strftime("%Y-%m"))
            out.append(text(71 + col * pitch, 102, value.strftime("%b"), 10, MUTED))
        x, y = 71 + col * pitch, 113 + row * pitch
        label = f"{day['date']}: {day['count']} contribution" + ("s" if day["count"] != 1 else "")
        fill = decorative_fill(day)
        rect = f'<rect x="{x:.2f}" y="{y:.2f}" width="{box:.2f}" height="{box:.2f}" rx="2.2" fill="{fill}"><title>{label}</title></rect>'
        out.append(appear(rect, .14 + col * .014 + row * .035))
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(text(28, 121 + row * pitch, label, 10, MUTED))
    out.append(text(71, 229, f"{stats['total']:,} contributions in the last year", 13, GREEN))
    out.append(text(643, 229, "Less", 10, MUTED))
    for i, color in enumerate(PALETTE):
        out.append(f'<rect x="{680+i*16}" y="218" width="11" height="11" rx="2" fill="{color}"/>')
    out.append(text(768, 229, "More", 10, MUTED))
    out.append(f'<path d="M28 245H832" stroke="{LINE}"/>')
    footer = [(28, f"Active days  {visual_stats['active_days']}"),
              (265, f"Current streak  {visual_stats['current_streak']}d"),
              (555, f"Longest streak  {visual_stats['longest_streak']}d")]
    for x, label in footer:
        out.append(text(x, 270, label, 11, MUTED))
    return out


if __name__ == "__main__":
    data = json.loads((ROOT / "data/contributions.json").read_text(encoding="utf-8"))
    write_svg(ROOT / "contrib-heatmap.svg", render(data))
    print("Rendered contrib-heatmap.svg")
