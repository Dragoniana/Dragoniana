#!/usr/bin/env python3
"""Generate self-hosted GitHub stats SVGs with the built-in Actions token."""
import json
import os
import pathlib
import urllib.request
from collections import Counter
from html import escape

USERNAME = os.environ.get('PROFILE_USERNAME', 'Dragoniana')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
OUT = pathlib.Path('assets')
COLORS = {
    'JavaScript': '#f1e05a', 'TypeScript': '#3178c6', 'Python': '#3572A5',
    'HTML': '#e34c26', 'CSS': '#663399', 'Shell': '#89e051',
    'Java': '#b07219', 'C#': '#178600', 'C++': '#f34b7d',
    'SQL': '#e38c00', 'Jupyter Notebook': '#DA5B0B', 'Vue': '#41b883',
    'PHP': '#4F5D95', 'Go': '#00ADD8', 'Rust': '#dea584',
}

def get_api(path):
    request = urllib.request.Request(
        'https://api.github.com' + path,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'dragoniana-profile-stats',
            'X-GitHub-Api-Version': '2022-11-28',
            **({'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)

def text(x, y, content, size=14, color='#c9d1d9', weight=400, anchor=None):
    attr = f' text-anchor="{anchor}"' if anchor else ''
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}"{attr}>{escape(str(content))}</text>')

def card_open(title, height=205):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="{height}" '
        f'viewBox="0 0 520 {height}" role="img" aria-label="{escape(title)}">',
        '<rect x="1" y="1" width="518" height="' + str(height-2) +
        '" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>',
        '<g font-family="Segoe UI, Arial, sans-serif">',
        text(25, 35, title, 19, '#be95ff', 700),
        '<path d="M25 51 H495" stroke="#30363d"/>',
    ]

def save(name, elements):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text('\n'.join(elements + ['</g>', '</svg>']) + '\n', encoding='utf-8')

def main():
    user = get_api('/users/' + USERNAME)
    repos = []
    for page in range(1, 21):
        part = get_api(f'/users/{USERNAME}/repos?type=owner&per_page=100&page={page}')
        repos.extend(repo for repo in part if not repo.get('private'))
        if len(part) < 100:
            break

    count = int(user.get('public_repos', len(repos)))
    stars = sum(int(repo.get('stargazers_count', 0)) for repo in repos)
    forks = sum(int(repo.get('forks_count', 0)) for repo in repos)
    followers = int(user.get('followers', 0))

    svg = card_open('GitHub em números  /  GitHub stats', 205)
    svg.append(text(25, 74, f'@{USERNAME}  ·  repositórios públicos / public repositories', 12, '#8b949e'))
    stats = [('Repositórios / Repos', count), ('Estrelas / Stars', stars),
             ('Seguidores / Followers', followers), ('Forks', forks)]
    for i, (label, value) in enumerate(stats):
        x = 25 + 245 * (i % 2)
        y = 116 + 63 * (i // 2)
        svg.append(text(x, y, f'{value:,}'.replace(',', '.'), 25, '#e6edf3', 700))
        svg.append(text(x, y+19, label, 12, '#a9b3c2'))
    save('github-stats.svg', svg)

    by_lang = Counter()
    for repo in repos:
        if repo.get('fork'):
            continue
        names = get_api('/repos/' + repo['full_name'] + '/languages')
        by_lang.update({k: int(v) for k, v in names.items()})

    svg = card_open('Linguagens  /  Top languages', 205)
    svg.append(text(25, 69, 'Distribuição do código em repositórios públicos', 12, '#8b949e'))
    total = sum(by_lang.values())
    if not total:
        svg.append(text(25, 118, 'Nenhum dado de linguagem disponível / No language data', 14))
    else:
        for i, (lang, size) in enumerate(by_lang.most_common(5)):
            y = 94 + i * 25
            pct = size / total * 100
            bar_width = 220 * pct / 100
            svg.append(text(25, y, lang[:20], 13, '#e6edf3'))
            svg.append(f'<rect x="214" y="{y-11}" width="220" height="10" rx="5" fill="#20273a"/>')
            svg.append(f'<rect x="214" y="{y-11}" width="{bar_width:.1f}" height="10" rx="5" fill="{COLORS.get(lang, "#be95ff")}"/>')
            svg.append(text(490, y-2, f'{pct:.1f}%', 12, '#a9b3c2', anchor='end'))
    save('top-langs.svg', svg)
    print(f'Generated stats for {USERNAME}: {count} repositories, {len(by_lang)} languages')

if __name__ == '__main__':
    main()
