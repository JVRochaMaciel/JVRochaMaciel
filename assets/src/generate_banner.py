#!/usr/bin/env python3
"""Gera assets/banner.svg (cabeçalho do README).

O efeito de digitação é feito com animações SMIL dentro do próprio SVG, sem
JavaScript e sem serviços externos, então funciona no GitHub como uma imagem
comum. Para trocar as frases ou os textos, edite as constantes abaixo e rode:

    python3 assets/src/generate_banner.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

# ---------------------------------------------------------------- conteúdo --
FIRST_NAME = "JOÃO VITOR"
LAST_NAME = "ROCHA MACIEL"
PROMPT_USER = "joao@jvrm"
PHRASES = ["Future Software Engineer", "Learning. Building. Evolving."]
CHIPS = ["SOFTWARE", "LINUX", "REDES", "INFRAESTRUTURA", "CYBERSECURITY"]
# Texto codificado no painel "xxd -b" (somente ASCII, 3 bytes por linha).
HEXDUMP_TEXT = "JOAO.VITOR.ROCHA.MACIEL.DEV"

# ------------------------------------------------------------------ paleta --
BURGUNDY = "#800020"
WINE = "#4A001F"
BLACK = "#0D0D0F"
GRAPHITE = "#25252B"
ICE = "#F1F1F1"
RED = "#C2183A"

# ----------------------------------------------------------------- layout --
W, H = 1000, 340
X0 = 48  # margem esquerda do painel principal
PANE_X = 704  # início do painel "xxd"
MONO = ("'JetBrains Mono','Fira Code','Cascadia Code','SF Mono',Menlo,"
        "Consolas,'Liberation Mono','DejaVu Sans Mono',monospace")
ADVANCE = 0.6  # largura de um caractere monoespaçado, em em

NAME_SIZE = 44
TYPE_SIZE = 24
TYPE_Y = 216
CW = TYPE_SIZE * ADVANCE  # largura de um caractere digitado

# ----------------------------------------------------------------- tempos --
TYPE_STEP = 0.075  # segundos por caractere digitado
ERASE_STEP = 0.03  # segundos por caractere apagado
HOLD = 2.6  # tempo com a frase completa na tela
GAP = 0.5  # pausa entre frases


def build_timeline():
    """Retorna a duração do ciclo e, por frase, a lista (t, largura)."""
    t = GAP
    tracks = []
    for phrase in PHRASES:
        n = len(phrase)
        points = [(0.0, 0.0)]
        for k in range(1, n + 1):
            points.append((t + k * TYPE_STEP, k * CW))
        erase_start = t + n * TYPE_STEP + HOLD
        for k in range(1, n + 1):
            points.append((erase_start + k * ERASE_STEP, (n - k) * CW))
        tracks.append(points)
        t = erase_start + n * ERASE_STEP + GAP
    return t, tracks


def smil(points, cycle, offset=0.0):
    """Converte (t, valor) em keyTimes/values para calcMode="discrete"."""
    key_times, values = [], []
    for t, v in points:
        kt = round(t / cycle, 4)
        if key_times and kt <= key_times[-1]:
            continue
        key_times.append(kt)
        values.append(round(v + offset, 1))
    return (";".join(f"{k:g}" for k in key_times),
            ";".join(f"{v:g}" for v in values))


def cursor_points(tracks):
    merged = {}
    for points in tracks:
        for t, v in points[1:]:
            merged[t] = v
    return [(0.0, 0.0)] + sorted(merged.items())


def chips_svg(y):
    out, x = [], X0
    size, pad, gap = 13, 10, 8
    for label in CHIPS:
        w = len(label) * size * ADVANCE + 2 * pad
        out.append(
            f'<rect x="{x:g}" y="{y}" width="{w:g}" height="28" rx="4" '
            f'fill="{BURGUNDY}" fill-opacity=".12" stroke="{BURGUNDY}"/>'
            f'<text x="{x + pad:g}" y="{y + 19}" font-size="{size}" '
            f'fill="{ICE}" fill-opacity=".86" letter-spacing=".4">'
            f'{escape(label)}</text>')
        x += w + gap
    return "\n    ".join(out)


def hexdump_svg():
    data = HEXDUMP_TEXT.encode("ascii")
    rows, y = [], 118
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        bits = " ".join(f"{b:08b}" for b in chunk)
        ascii_col = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        opacity = max(0.28, 0.9 - (i // 3) * 0.075)
        rows.append(
            f'<text y="{y}" fill-opacity="{opacity:.2f}">'
            f'<tspan x="{PANE_X + 16}" fill="{ICE}" fill-opacity=".38">{i:08x}:</tspan>'
            f'<tspan x="{PANE_X + 82}" fill="{RED}">{bits}</tspan>'
            f'<tspan x="{PANE_X + 260}" fill="{ICE}" fill-opacity=".55">'
            f'{escape(ascii_col)}</tspan></text>')
        y += 18
    return "\n      ".join(rows)


def main():
    cycle, tracks = build_timeline()
    name_len = len(FIRST_NAME) + 1 + len(LAST_NAME)
    name_width = round(name_len * NAME_SIZE * ADVANCE)
    text_x = X0 + 2 * CW

    clips, typed = [], []
    for i, (phrase, points) in enumerate(zip(PHRASES, tracks)):
        kt, vals = smil(points, cycle)
        clips.append(
            f'<clipPath id="type{i}"><rect x="{text_x:g}" y="{TYPE_Y - 26}" '
            f'height="34" width="0"><animate attributeName="width" '
            f'dur="{cycle:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        typed.append(
            f'<text x="{text_x:g}" y="{TYPE_Y}" font-size="{TYPE_SIZE}" '
            f'fill="{ICE}" textLength="{len(phrase) * CW:g}" '
            f'clip-path="url(#type{i})">{escape(phrase)}</text>')

    clips_svg = "\n    ".join(clips)
    typed_svg = "\n    ".join(typed)
    ckt, cvals = smil(cursor_points(tracks), cycle, offset=text_x + 2)
    name_text = (f'<tspan fill="{ICE}">{escape(FIRST_NAME)} </tspan>'
                 f'<tspan fill="{RED}">{escape(LAST_NAME)}</tspan>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(FIRST_NAME.title())} {escape(LAST_NAME.title())} — {escape(PHRASES[0])}</title>
  <desc id="desc">Terminal com o nome {escape(FIRST_NAME.title())} {escape(LAST_NAME.title())} e as frases: {escape(" / ".join(PHRASES))}</desc>
  <defs>
    <radialGradient id="glow" cx="0.86" cy="0" r="0.75">
      <stop offset="0" stop-color="{WINE}" stop-opacity=".75"/>
      <stop offset="1" stop-color="{WINE}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="0.08" cy="1" r="0.55">
      <stop offset="0" stop-color="{BURGUNDY}" stop-opacity=".22"/>
      <stop offset="1" stop-color="{BURGUNDY}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M28 0H0V28" fill="none" stroke="{GRAPHITE}" stroke-width="1"/>
    </pattern>
    <radialGradient id="fade" cx="0.32" cy="0.5" r="0.7">
      <stop offset="0" stop-color="#fff" stop-opacity=".55"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <mask id="gridMask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{RED}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{RED}" stop-opacity=".16"/>
      <stop offset="1" stop-color="{RED}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="window"><rect width="{W}" height="{H}" rx="12"/></clipPath>
    <clipPath id="pane"><rect x="{PANE_X}" y="100" width="{W - PANE_X}" height="176"/></clipPath>
    {clips_svg}
  </defs>
  <style>
    text {{ font-family: {MONO}; }}
    .blink {{ animation: blink 1.05s step-end infinite; }}
    .glitch-a {{ animation: glitch-a 7s infinite; }}
    .glitch-b {{ animation: glitch-b 7s infinite; }}
    .scan {{ animation: scan 5.5s linear infinite; }}
    .pulse {{ animation: pulse 2.4s ease-in-out infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes glitch-a {{
      0%, 90%, 92%, 95%, 100% {{ opacity: 0; transform: translate(0, 0); }}
      91% {{ opacity: .9; transform: translate(-4px, -1px); }}
      94% {{ opacity: .7; transform: translate(3px, 1px); }}
    }}
    @keyframes glitch-b {{
      0%, 90%, 92%, 95%, 100% {{ opacity: 0; transform: translate(0, 0); }}
      91% {{ opacity: .8; transform: translate(4px, 1px); }}
      94% {{ opacity: .6; transform: translate(-2px, 0); }}
    }}
    @keyframes scan {{ from {{ transform: translateY(70px); }} to {{ transform: translateY(290px); }} }}
    @keyframes pulse {{ 50% {{ opacity: .3; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .blink, .glitch-a, .glitch-b, .scan, .pulse {{ animation: none; }}
    }}
  </style>

  <g clip-path="url(#window)">
    <rect width="{W}" height="{H}" fill="{BLACK}"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
    <rect width="{W}" height="{H}" fill="url(#glow2)"/>
    <rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridMask)"/>

    <!-- barra de título -->
    <rect width="{W}" height="38" fill="#121216"/>
    <path d="M0 38.5H{W}" stroke="{GRAPHITE}"/>
    <circle cx="24" cy="19" r="5.5" fill="{WINE}"/>
    <circle cx="42" cy="19" r="5.5" fill="{BURGUNDY}"/>
    <circle cx="60" cy="19" r="5.5" fill="{RED}"/>
    <text x="{W / 2:g}" y="24" font-size="13" fill="{ICE}" fill-opacity=".5" text-anchor="middle">{escape(PROMPT_USER)}: ~</text>
    <text x="{W - 24}" y="24" font-size="12" fill="{ICE}" fill-opacity=".5" text-anchor="end">online</text>
    <circle class="pulse" cx="{W - 80}" cy="19.5" r="3.5" fill="{RED}"/>

    <!-- painel principal -->
    <text x="{X0}" y="92" font-size="17"><tspan fill="{RED}">{escape(PROMPT_USER)}</tspan><tspan fill="{ICE}" fill-opacity=".55">:~$</tspan><tspan fill="{ICE}" fill-opacity=".9"> whoami</tspan></text>

    <g font-size="{NAME_SIZE}" font-weight="700" letter-spacing="1">
      <text class="glitch-a" x="{X0}" y="152" fill="{RED}" textLength="{name_width}">{escape(FIRST_NAME)} {escape(LAST_NAME)}</text>
      <text class="glitch-b" x="{X0}" y="152" fill="{ICE}" fill-opacity=".6" textLength="{name_width}">{escape(FIRST_NAME)} {escape(LAST_NAME)}</text>
      <text x="{X0}" y="152" textLength="{name_width}">{name_text}</text>
    </g>
    <rect x="{X0}" y="171" width="64" height="3" fill="{RED}"/>
    <rect x="{X0 + 72}" y="172" width="{name_width - 72}" height="1" fill="{GRAPHITE}"/>

    <text x="{X0}" y="{TYPE_Y}" font-size="{TYPE_SIZE}" font-weight="700" fill="{RED}">&gt;</text>
    {typed_svg}
    <g class="blink">
      <rect x="{text_x + 2:g}" y="{TYPE_Y - 20}" width="12" height="25" fill="{RED}">
        <animate attributeName="x" dur="{cycle:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{ckt}" values="{cvals}"/>
      </rect>
    </g>

    <g>
    {chips_svg(246)}
    </g>

    <!-- painel xxd -->
    <path d="M{PANE_X - 0.5} 39V304" stroke="{GRAPHITE}"/>
    <text x="{PANE_X + 16}" y="92" font-size="12"><tspan fill="{RED}">$</tspan><tspan fill="{ICE}" fill-opacity=".75"> xxd -b -c 3 id.bin</tspan></text>
    <g font-size="11">
      {hexdump_svg()}
    </g>
    <g clip-path="url(#pane)">
      <rect class="scan" x="{PANE_X}" y="-30" width="{W - PANE_X}" height="40" fill="url(#scan)"/>
    </g>

    <!-- barra de status -->
    <rect y="304" width="{W}" height="36" fill="#121216"/>
    <path d="M0 304.5H{W}" stroke="{GRAPHITE}"/>
    <rect x="0" y="305" width="86" height="35" fill="{BURGUNDY}"/>
    <text x="43" y="327" font-size="12" font-weight="700" fill="{ICE}" text-anchor="middle">[jvrm]</text>
    <text x="102" y="327" font-size="12" fill="{ICE}" fill-opacity=".6">0:bash*  1:xxd</text>
    <text x="{W - 24}" y="327" font-size="12" fill="{RED}" text-anchor="end">01001010 01010110</text>
  </g>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="11.5" fill="none" stroke="{WINE}" stroke-width="1.5"/>
</svg>
'''
    out = Path(__file__).resolve().parent.parent / "banner.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"{out} ({len(svg.encode())} bytes, ciclo de {cycle:.2f}s)")


if __name__ == "__main__":
    main()
