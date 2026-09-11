#!/usr/bin/env python3
"""Tracados oficiais (KanjiVG) de caracteres japoneses, com cache offline.

Uso:
    python tools/caderno/kanjivg.py さしすせそ     # mostra os tracos (JSON) e quantos sao
    python tools/caderno/kanjivg.py --listar       # o que ja esta no cache
    python tools/caderno/kanjivg.py --vendor       # baixa todo o hiragana e katakana

O cache mora em tools/caderno/kanjivg/, um arquivo .json por caractere, e e
versionado junto com o repositorio. Com o cache cheio o gerador de aula funciona
sem rede nenhuma; so o que falta e buscado em raw.githubusercontent.com.

Dados: KanjiVG (c) Ulrich Apel, licenca CC BY-SA 3.0 - kanjivg.tagaini.net.
Ao publicar uma aula, mantenha o credito que ja vem no rodape do template.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BASE_URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg"
CACHE = Path(__file__).resolve().parent / "kanjivg"

# Faixas do silabario. Incluem os pequenininhos (ぁ, ゃ) e o ゛/゜ nao entra aqui:
# dakuten e handakuten tem caractere proprio no KanjiVG, ja dentro destas faixas.
HIRAGANA = range(0x3041, 0x3097)   # ぁ .. ゖ
KATAKANA = range(0x30A1, 0x30FB)   # ァ .. ヺ


class SemTracado(Exception):
    """Nao ha tracado para este caractere: nem no cache, nem na rede."""


def codigo(ch):
    return f"{ord(ch):05x}"


def arquivo_cache(ch):
    return CACHE / f"{codigo(ch)}.json"


def extrair_do_svg(svg, code):
    """Le os <path> do SVG do KanjiVG na ordem de escrita (kvg:<code>-s<N>)."""
    pares = []
    for p in re.findall(r"<path\b[^>]*>", svg):
        m_id = re.search(r'id="kvg:%s-s(\d+)"' % code, p)
        m_d = re.search(r'\sd="([^"]+)"', p)
        if m_id and m_d:
            pares.append((int(m_id.group(1)), m_d.group(1)))
    pares.sort()
    return [d for _, d in pares]


def baixar(ch, timeout=30):
    """Busca na rede e grava no cache. Devolve a lista de tracos."""
    code = codigo(ch)
    url = BASE_URL.format(code=code)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        svg = r.read().decode("utf-8")
    tracos = extrair_do_svg(svg, code)
    if not tracos:
        raise SemTracado(f"o SVG de {ch} ({code}) nao tem tracos legiveis")
    gravar_cache(ch, tracos)
    return tracos


def gravar_cache(ch, tracos):
    CACHE.mkdir(parents=True, exist_ok=True)
    dados = {
        "ch": ch,
        "codigo": codigo(ch),
        "tracos": tracos,
        "fonte": "KanjiVG (c) Ulrich Apel, CC BY-SA 3.0",
    }
    arquivo_cache(ch).write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def ler_cache(ch):
    alvo = arquivo_cache(ch)
    if not alvo.exists():
        return None
    try:
        dados = json.loads(alvo.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    tracos = dados.get("tracos")
    return tracos if tracos else None


def tracados(ch, offline=False):
    """Tracos de um caractere: cache primeiro, rede so se faltar.

    Com offline=True, um caractere fora do cache vira erro em vez de download -
    util para garantir que uma aula foi gerada sem depender da rede.
    """
    do_cache = ler_cache(ch)
    if do_cache:
        return do_cache
    if offline:
        raise SemTracado(
            f"{ch} nao esta no cache (tools/caderno/kanjivg/{codigo(ch)}.json) "
            f"e o modo offline esta ligado"
        )
    try:
        return baixar(ch)
    except urllib.error.HTTPError as e:
        raise SemTracado(f"{ch} nao existe no KanjiVG (HTTP {e.code})") from e
    except urllib.error.URLError as e:
        raise SemTracado(
            f"sem rede para buscar {ch} e ele nao esta no cache ({e.reason}). "
            f"Rode 'python tools/caderno/kanjivg.py --vendor' num ambiente com acesso "
            f"a raw.githubusercontent.com e commite o cache."
        ) from e


def comando_listar():
    if not CACHE.exists():
        print("Cache vazio: tools/caderno/kanjivg/ nem existe ainda.")
        return 0
    itens = []
    for arq in sorted(CACHE.glob("*.json")):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            print(f"  [ilegivel] {arq.name}", file=sys.stderr)
            continue
        itens.append((dados.get("ch", "?"), arq.name, len(dados.get("tracos") or [])))
    if not itens:
        print("Cache vazio.")
        return 0
    for ch, nome, n in itens:
        print(f"  {ch}  {nome}  {n} traco(s)")
    print(f"\n{len(itens)} caractere(s) no cache.")
    faltam = [chr(c) for c in list(HIRAGANA) + list(KATAKANA)
              if not arquivo_cache(chr(c)).exists()]
    if faltam:
        print(f"Fora do cache no silabario: {''.join(faltam)}")
        print("Para completar: python tools/caderno/kanjivg.py --vendor")
    else:
        print("Hiragana e katakana completos.")
    return 0


def comando_vendor(faixas=None, forcar=False):
    """Baixa o silabario inteiro para o cache. Rode uma vez, commite o resultado."""
    alvos = [chr(c) for faixa in (faixas or [HIRAGANA, KATAKANA]) for c in faixa]
    novos = pulados = ausentes = falhas = 0
    for ch in alvos:
        if not forcar and arquivo_cache(ch).exists():
            pulados += 1
            continue
        try:
            tracos = baixar(ch)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                ausentes += 1          # nem todo ponto da faixa existe no KanjiVG
            else:
                falhas += 1
                print(f"  erro em {ch} ({codigo(ch)}): HTTP {e.code}", file=sys.stderr)
            continue
        except (urllib.error.URLError, SemTracado, OSError) as e:
            falhas += 1
            print(f"  erro em {ch} ({codigo(ch)}): {e}", file=sys.stderr)
            continue
        novos += 1
        print(f"  {ch} {codigo(ch)}  {len(tracos)} traco(s)")
    print(f"\nnovos: {novos} · ja tinha: {pulados} · sem SVG no KanjiVG: {ausentes} · falhas: {falhas}")
    if falhas:
        print("Rode de novo para tentar de novo o que falhou.", file=sys.stderr)
        return 1
    print("Commite tools/caderno/kanjivg/ para as aulas saírem sem depender da rede.")
    return 0


def main():
    p = argparse.ArgumentParser(
        description="Tracados do KanjiVG com cache offline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("chars", nargs="*", help="caracteres, ex: さしすせそ")
    p.add_argument("--listar", action="store_true", help="mostra o que ja esta no cache")
    p.add_argument("--vendor", action="store_true",
                   help="baixa todo o hiragana e katakana para o cache")
    p.add_argument("--hiragana", action="store_true", help="com --vendor: so hiragana")
    p.add_argument("--katakana", action="store_true", help="com --vendor: so katakana")
    p.add_argument("--forcar", action="store_true",
                   help="com --vendor: rebaixa o que ja esta no cache")
    p.add_argument("--offline", action="store_true",
                   help="nunca usa a rede; falha se faltar no cache")
    args = p.parse_args()

    if args.listar:
        return comando_listar()
    if args.vendor:
        faixas = []
        if args.hiragana:
            faixas.append(HIRAGANA)
        if args.katakana:
            faixas.append(KATAKANA)
        return comando_vendor(faixas or None, forcar=args.forcar)

    chars = [c for arg in args.chars for c in arg]
    if not chars:
        p.print_help()
        return 1

    saida, erro = {}, 0
    for c in chars:
        try:
            saida[c] = tracados(c, offline=args.offline)
        except SemTracado as e:
            print(f"erro: {e}", file=sys.stderr)
            erro = 1
    json.dump(saida, sys.stdout, ensure_ascii=False, indent=1)
    print()
    for c, t in saida.items():
        print(f"  {c}: {len(t)} traco(s)", file=sys.stderr)
    return erro


if __name__ == "__main__":
    raise SystemExit(main())
