"""Compose GitHub-safe HTML; all animation stays inside the SVG image files."""
from html import escape
from common import ROOT, config


def build(profile):
    name = escape(profile["name"])
    links = [("Portfolio", profile["portfolio"]), ("LinkedIn", profile["linkedin"]),
             ("Email", "mailto:" + profile["email"]), ("Instagram", profile["instagram"])]
    nav = " &nbsp;·&nbsp; ".join(f'<a href="{escape(url, quote=True)}">{label}</a>' for label, url in links)
    out = [
        "<!-- Generated from profile.json by scripts/make_readme.py. -->",
        '<div align="center">',
        f'<h3>{name}</h3>',
        f'<p>{escape(profile["title"])} · {escape(profile["location"])}</p>',
        f'<p>{nav}</p>',
        '<br>',
        '<h3><code>pushpraj@github ~ $ ./contributions.sh</code></h3>',
        '<img src="./contrib-heatmap.svg" width="860" alt="Pushpraj Patil’s real contribution calendar, refreshed daily by GitHub Actions." />',
        '<br><br>',
        '<h3><code>pushpraj@github ~ $ whoami</code></h3>',
        '<table role="presentation"><tr>',
        '<td valign="top"><img src="./pushpraj-ascii.svg" width="370" alt="Typing ASCII portrait of Pushpraj Patil, made from his existing portfolio photo." /></td>',
        '<td valign="top"><img src="./info-card.svg" width="490" alt="Pushpraj Patil — Engineering Student &amp; Developer, Talegaon, Pune. Web development, AI, and interactive design." /></td>',
        '</tr></table>',
        '<br>',
        f'<p>{escape(profile["bio"])}</p>',
        '</div>',
        '',
        '<h3><code>pushpraj@github ~ $ ls projects/</code></h3>',
        '<table>',
        '<tr><th align="left">Project</th><th align="left">About</th><th>Explore</th></tr>',
    ]
    for project in profile["projects"]:
        out.append(f'<tr><td><strong>{escape(project["name"])}</strong></td><td>{escape(project["description"])}</td>'
                   f'<td><a href="{escape(project["live"], quote=True)}">Live</a> · <a href="{escape(project["repository"], quote=True)}">Code</a></td></tr>')
    out += [
        '</table>', '',
        '<details>', '<summary>Technology &amp; tools</summary>', '<br>',
        '<p>' + ' · '.join(f'<code>{escape(item)}</code>' for item in profile["technology"]) + '</p>',
        '</details>', '', '<br>',
        '<div align="center">', f'<p><code>{escape(profile["tagline"])}</code></p>',
        '<sub>Profile art inspired by <a href="https://www.avivashishta.com/blog/build-animated-github-profile-readme.html">Avi Vashishta’s guide</a>. Built from my own details, portrait, and GitHub contributions.</sub>',
        '</div>', '',
    ]
    return "\n".join(out)


if __name__ == "__main__":
    (ROOT / "README.md").write_text(build(config()), encoding="utf-8")
    print("Rendered README.md")
