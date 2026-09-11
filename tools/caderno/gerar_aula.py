#!/usr/bin/env python3
"""Gera o HTML de uma aula no formato do caderno de escrita.

    python tools/caderno/gerar_aula.py aula.json hiragana-linha-sa.html

Entra um JSON (modelo em tools/caderno/exemplo_aula.json), sai uma pagina
autocontida: animacao do tracado, passo a passo traco por traco, quadro para
escrever com o dedo e botao de pronuncia em cada letra e cada palavra.

    {
      "titulo": "Bloco 3 · A linha さ — sa shi su se so",
      "stamp":  "Etapa 2 · Bloco 3 · Caderno de escrita",
      "intro":  "texto curto opcional (aceita HTML)",
      "letras": [
        {"ch": "さ", "romaji": "sa", "som": "soa como o SA de sala",
         "instr": ["uma frase por traco, na ordem de escrita"]}
      ],
      "palavras": [{"jp": "さけ", "romaji": "sake", "pt": "saquê"}],
      "dica": "observacao de fechamento (opcional)"
    }

As instrucoes sao a parte mais didatica da aula: uma frase por traco, em
linguagem de professora de alfabetizacao ("desce fazendo barriguinha",
"pinguinho por ultimo"). Se faltarem, o gerador completa com "traco N" e avisa -
conte os tracos antes com 'python tools/caderno/kanjivg.py <letras>'.

Os tracados saem do cache em tools/caderno/kanjivg/ e so vao a rede se faltar
algum. Depois de gerar, registre a aula no caderno:

    python scripts/nova_aula.py --de hiragana-linha-sa.html --slug hiragana-linha-sa \
        --tags bloco-3,hiragana,tracado --data AAAA-MM-DD --resumo "uma linha"
"""

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kanjivg import SemTracado, tracados  # noqa: E402

for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

AQUI = Path(__file__).resolve().parent
TEMPLATE = AQUI / "template_aula.html"


def esc(s):
    return html.escape(str(s), quote=True)


def gerar(entrada, saida, offline=False):
    spec = json.loads(Path(entrada).read_text(encoding="utf-8"))
    letras = spec.get("letras") or []
    palavras = spec.get("palavras") or []
    if not letras and not palavras:
        sys.exit("aula.json precisa ter 'letras' e/ou 'palavras'")

    DATA, SOM, ROMAJI, INSTR = {}, {}, {}, {}
    avisos = []
    for L in letras:
        ch = L["ch"]
        try:
            DATA[ch] = tracados(ch, offline=offline)
        except SemTracado as e:
            sys.exit(
                f"erro: {e}\n"
                f"Nao da para entregar uma aula com letra sem tracado. "
                f"Complete o cache com 'python tools/caderno/kanjivg.py --vendor'."
            )
        SOM[ch] = L.get("som", "")
        ROMAJI[ch] = L.get("romaji", "")
        instr = list(L.get("instr") or [])
        n = len(DATA[ch])
        if len(instr) != n:
            avisos.append(
                f"  {ch}: {n} traco(s) no KanjiVG, {len(instr)} instrucao(oes) no JSON"
            )
        if len(instr) < n:
            instr += [f"traço {i + 1}" for i in range(len(instr), n)]
        INSTR[ch] = instr[:n] if n else instr

    for P in palavras:
        ROMAJI[P["jp"]] = P.get("romaji", "")

    if not TEMPLATE.exists():
        sys.exit(f"template nao encontrado: {TEMPLATE}")
    tpl = TEMPLATE.read_text(encoding="utf-8")

    out = (
        tpl.replace("{{TITULO}}", esc(spec.get("titulo", "Caderno de japonês")))
        .replace("{{STAMP}}", esc(spec.get("stamp", "Caderno de escrita")))
        .replace("{{INTRO}}", spec.get("intro", ""))
        .replace("{{DICA}}", spec.get("dica", "Mão devagar: capricho primeiro, velocidade depois."))
        .replace("{{DATA}}", json.dumps(DATA, ensure_ascii=False))
        .replace("{{SOM}}", json.dumps(SOM, ensure_ascii=False))
        .replace("{{ROMAJI}}", json.dumps(ROMAJI, ensure_ascii=False))
        .replace("{{INSTR}}", json.dumps(INSTR, ensure_ascii=False))
        .replace("{{PALAVRAS}}", json.dumps(palavras, ensure_ascii=False))
    )

    sobraram = [m for m in ("{{", "}}") if m in out]
    if sobraram:
        sys.exit("erro: sobrou marcador nao substituido no HTML (procure por '{{')")

    Path(saida).write_text(out, encoding="utf-8", newline="\n")

    print(f"ok -> {saida}  ({len(letras)} letra(s), {len(palavras)} palavra(s))")
    for ch in DATA:
        print(f"  {ch}: {len(DATA[ch])} traco(s)")
    if avisos:
        print("\naviso: numero de instrucoes diferente do numero de tracos:", file=sys.stderr)
        for a in avisos:
            print(a, file=sys.stderr)
        print("  as instrucoes sao a parte mais didatica - confira antes de publicar.",
              file=sys.stderr)
    return 0


def main():
    p = argparse.ArgumentParser(
        description="JSON da aula -> HTML do caderno de escrita.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("entrada", help="aula.json")
    p.add_argument("saida", help="arquivo .html de saida")
    p.add_argument("--offline", action="store_true",
                   help="proibe a rede: exige que todo tracado ja esteja no cache")
    args = p.parse_args()
    return gerar(args.entrada, args.saida, offline=args.offline)


if __name__ == "__main__":
    raise SystemExit(main())
