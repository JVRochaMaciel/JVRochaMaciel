#!/usr/bin/env python3
"""Recorta a grade de contribuições gerada pelo snk na área das células.

O snk começa e termina a animação com a cobrinha acima da grade, usa células
fora da borda para fazer curvas e desenha uma barra de progresso embaixo.
Este script ajusta o viewBox para a área exata das células e remove a barra,
então a cobrinha parece entrar e sair pelas bordas do quadro.

Uso: python3 .github/scripts/clip_contributions.py profile/contributions.svg
"""

import re
import sys
from pathlib import Path

CELL = 16  # tamanho de cada célula no snk (sizeCell)


def clip(path):
    file = Path(path)
    svg = file.read_text(encoding="utf-8")

    cells = re.findall(r'<rect class="c[^"]*" x="([\d.]+)" y="([\d.]+)"', svg)
    root = re.search(r'<svg viewBox="[^"]*" width="[^"]*" height="[^"]*"', svg)
    if not cells or not root:
        print(f"{path}: formato inesperado, arquivo mantido sem alterações")
        return

    width = (int(max(float(x) for x, _ in cells)) // CELL + 1) * CELL
    height = (int(max(float(y) for _, y in cells)) // CELL + 1) * CELL

    svg = re.sub(r'<rect class="u [^>]*/>', "", svg)
    svg = svg.replace(
        root.group(0),
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"',
        1,
    )
    file.write_text(svg, encoding="utf-8")
    print(f"{path}: recortado para {width}x{height}")


if __name__ == "__main__":
    clip(sys.argv[1])
