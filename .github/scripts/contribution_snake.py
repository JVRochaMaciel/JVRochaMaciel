#!/usr/bin/env python3
"""Gera a grade de contribuições com uma cobrinha que nunca sai da grade.

Substitui o snk, cuja cobrinha começa a animação fora da grade e usa células
fora da borda para fazer curvas. Aqui o caminho passa só por células
existentes: a cobrinha sai do canto superior esquerdo, come as contribuições
(sempre a mais próxima primeiro) e volta ao ponto de partida, então a
animação se repete sem cortes.

Uso no workflow (busca os dados públicos da conta pela API GraphQL):
    GITHUB_TOKEN=... python3 contribution_snake.py profile/contributions.svg --user LOGIN

Teste local com dados em JSON ([{"x": 0, "y": 0, "level": 0}, ...]):
    python3 contribution_snake.py saida.svg --data dias.json
"""

import argparse
import json
import os
import urllib.request
from collections import deque
from pathlib import Path

CELL = 16  # distância entre células
DOT = 12  # tamanho de cada célula
STEP_MS = 100  # tempo da cobrinha para andar uma célula
# Segmentos da cobrinha, da cabeça à cauda: (tamanho, raio da borda).
SNAKE = [(14.4, 4.5), (12.3, 4.1), (10.8, 3.6), (9.9, 3.3)]

COLORS = {
    "ce": "#8B8B9526",  # célula vazia
    "cb": "#1b1f230a",  # contorno das células
    "cs": "#C2183A",  # cobrinha
    "c1": "#C2183A40",
    "c2": "#C2183A73",
    "c3": "#C2183AA6",
    "c4": "#C2183AD9",
}
LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}
QUERY = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionLevel weekday } }
      }
    }
  }
}
"""


def fetch_days(login, token):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-contribution-snake",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", payload["errors"]))
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        {"x": x, "y": day["weekday"], "level": LEVELS[day["contributionLevel"]]}
        for x, week in enumerate(weeks)
        for day in week["contributionDays"]
    ]


def shortest_path(start, goals, cells, blocked):
    """Caminho mais curto (sem o ponto inicial) até a meta mais próxima."""
    previous = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in goals and current != start:
            path = []
            while current != start:
                path.append(current)
                current = previous[current]
            return path[::-1]
        x, y = current
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in cells and nxt not in previous and nxt not in blocked:
                previous[nxt] = current
                queue.append(nxt)
    return None


def plan_route(cells, targets):
    """Ciclo que começa e termina na mesma célula e passa por todas as metas."""
    ordered = sorted(cells)
    start = next((c for c in ordered if c not in targets), ordered[0])
    route = [start]
    remaining = set(targets) - {start}

    def step_to(goals, avoid=()):
        # Evita que a cabeça atravesse o próprio corpo; se não houver saída, ignora o corpo.
        body = set(route[-len(SNAKE):-1]) | set(avoid)
        return (shortest_path(route[-1], goals, cells, body)
                or shortest_path(route[-1], goals, cells, set()))

    while remaining:
        leg = step_to(remaining)
        if not leg:
            break
        route += leg
        remaining -= set(leg)
    if len(route) > 1:
        # Volta ao início por outro lado: ao recomeçar, a cabeça não vira sobre o corpo.
        route += step_to({start}, route[1:len(SNAKE)]) or []
    return route[:-1] if len(route) > 1 and route[-1] == start else route


def pct(value):
    return f"{value:.3f}".rstrip("0").rstrip(".") + "%"


def segment_keyframes(name, route, lag):
    """Keyframes de um segmento; guarda só os pontos onde a direção muda."""
    total = len(route)
    points = [route[(k - lag) % total] for k in range(total + 1)]
    frames = []
    for k, (x, y) in enumerate(points):
        if 0 < k < total:
            before, after = points[k - 1], points[k + 1]
            if (x - before[0], y - before[1]) == (after[0] - x, after[1] - y):
                continue
        frames.append(f"{pct(100 * k / total)}{{transform:translate({x * CELL}px,{y * CELL}px)}}")
    return f"@keyframes {name}{{{''.join(frames)}}}"


def render(days):
    cells = {(d["x"], d["y"]) for d in days}
    levels = {(d["x"], d["y"]): d["level"] for d in days if d["level"] > 0}
    width = (max(x for x, _ in cells) + 1) * CELL
    height = 7 * CELL

    route = plan_route(cells, set(levels)) if levels else []
    animated = len(route) > 1
    duration = max(len(route), 1) * STEP_MS
    eaten = {}
    for k, cell in enumerate(route):
        eaten.setdefault(cell, k)

    variables = ";".join(f"--{k}:{v}" for k, v in COLORS.items())
    css = [
        f":root{{{variables}}}",
        ".c{shape-rendering:geometricPrecision;fill:var(--ce);stroke-width:1px;"
        f"stroke:var(--cb);animation:none {duration}ms linear infinite}}",
        f".s{{shape-rendering:geometricPrecision;fill:var(--cs);animation:none linear {duration}ms infinite}}",
        "@media (prefers-reduced-motion:reduce){.c{animation:none!important}.s{display:none}}",
    ]
    rects = []
    for n, (x, y) in enumerate(sorted(cells)):
        level = levels.get((x, y), 0)
        cls = "c"
        if level:
            cls = f"c e{n}"
            css.append(f".e{n}{{fill:var(--c{level})}}")
            if animated and (x, y) in eaten:
                at = 100 * eaten[(x, y)] / len(route)
                css.append(f".e{n}{{animation-name:e{n}}}")
                css.append(f"@keyframes e{n}{{{pct(at)}{{fill:var(--c{level})}}"
                           f"{pct(at + 0.01)},100%{{fill:var(--ce)}}}}")
        rects.append(f'<rect class="{cls}" x="{x * CELL + 2}" y="{y * CELL + 2}" '
                     f'width="{DOT}" height="{DOT}" rx="2" ry="2"/>')

    if animated:
        for i, (size, radius) in enumerate(SNAKE):
            offset = round((CELL - size) / 2, 2)
            css.append(f".s{i}{{animation-name:s{i}}}")
            css.append(segment_keyframes(f"s{i}", route, i))
            rects.append(f'<rect class="s s{i}" x="{offset}" y="{offset}" width="{size}" '
                         f'height="{size}" rx="{radius}" ry="{radius}"/>')

    return (f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'xmlns="http://www.w3.org/2000/svg"><desc>Grade de contribuições com a cobrinha '
            f'gerada por .github/scripts/contribution_snake.py</desc><style>{"".join(css)}</style>'
            f'{"".join(rects)}</svg>\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", help="arquivo SVG de saída")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--user", help="usuário do GitHub (usa a variável GITHUB_TOKEN)")
    source.add_argument("--data", help="arquivo JSON com os dias, para testes locais")
    args = parser.parse_args()

    if args.user:
        days = fetch_days(args.user, os.environ["GITHUB_TOKEN"])
    else:
        days = json.loads(Path(args.data).read_text(encoding="utf-8"))
    Path(args.output).write_text(render(days), encoding="utf-8")
    print(f"{args.output}: {sum(1 for d in days if d['level'])} dias com contribuições")


if __name__ == "__main__":
    main()
