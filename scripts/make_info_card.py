"""Regenerate the info card from the user's existing, editable profile details."""
from common import ROOT, GREEN, AMBER, MUTED, LINE, config, text, svg_start, chrome, appear, write_svg


def render(profile):
    out = svg_start(490, 442, profile["name"], profile["bio"])
    out += chrome(490, "profile / neofetch")
    out += [appear(text(25, 88, profile["name"], 26), .15),
            appear(text(25, 113, profile["username"] + "@github", 13, GREEN), .25),
            f'<path d="M25 133H465" stroke="{LINE}"/>']
    for index, (key, value) in enumerate(profile["card_rows"]):
        y = 162 + index * 25
        content = text(25, y, key, 12, AMBER) + text(93, y, value, 12.5)
        out.append(appear(content, .4 + index * .09))
    out.append(appear(text(25, 410, profile["tagline"], 13, GREEN), 1.4))
    for i, color in enumerate(["#293b2d", "#3c5c43", "#6aa577", "#7ee787", "#776351", "#a38666", "#d2ac7a", "#e6edf3"]):
        out.append(f'<rect x="{285+i*22}" y="397" width="19" height="14" rx="2" fill="{color}"/>')
    return out


if __name__ == "__main__":
    write_svg(ROOT / "info-card.svg", render(config()))
    print("Rendered info-card.svg")
