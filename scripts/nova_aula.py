#!/usr/bin/env python3
"""Coloca uma aula em site/aulas/<slug>/ e registra ela em site/data/aulas.json.

Uso tipico, com um HTML que voce ja gerou:

    python scripts/nova_aula.py --de ~/Downloads/japones/vogais.html
    python scripts/nova_aula.py --de vogais.html --tags kana,escrita --data 2026-09-12

Criar uma aula em branco, para preencher depois:

    python scripts/nova_aula.py --titulo "Aula 04: verbos ru"

Outras operacoes:

    python scripts/nova_aula.py --listar
    python scripts/nova_aula.py --remover vogais

O script nao reescreve o conteudo da sua aula. A unica coisa que ele mexe e
inserir a linha do pronuncia.js antes de </body>, e so quando o arquivo usa
data-ouvir e a linha esta faltando. Sem essa linha o data-ouvir nao vira botao.
"""

import argparse
import datetime
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

# O console do Windows abre em cp1252 e estoura ao imprimir kana. Como o titulo
# da aula quase sempre tem japones, sem isto o script morre depois de ja ter
# escrito os arquivos, que e o pior momento possivel para morrer.
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent
DIR_AULAS = RAIZ / "site" / "aulas"
INDICE = RAIZ / "site" / "data" / "aulas.json"

TAG_PRONUNCIA = '<script type="module" src="../../assets/js/pronuncia.js"></script>'
TAG_ESTILO = '<link rel="stylesheet" href="../../assets/css/aula.css">'

MODELO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<link rel="icon" href="../../assets/brand/favicon.svg" type="image/svg+xml">
{estilo}
</head>
<body>
<main class="aula">

  <a class="voltar" href="../../">&larr; todas as aulas</a>

  <h1>{titulo}</h1>
  <p class="subtitulo">{data}</p>

  <h2>Vocabulario</h2>
  <p class="jp"><span data-ouvir>こんにちは</span></p>

</main>
{pronuncia}
</body>
</html>
"""


def sem_acento(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def criar_slug(texto, data=None):
    """Kebab-case, sem acento e sem caractere que atrapalhe URL ou pasta.

    Kana e kanji somem aqui. Um titulo so em japones sobraria vazio, entao nesse
    caso o slug vira a data, que pelo menos e unica.
    """
    base = sem_acento(str(texto)).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if base:
        return base[:60].strip("-")
    return f"aula-{data}" if data else "aula"


def ler_texto(caminho):
    """HTML salvo no Windows as vezes vem em cp1252. Tenta utf-8 primeiro."""
    dados = caminho.read_bytes()
    for codec in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return dados.decode(codec)
        except UnicodeDecodeError:
            continue
    return dados.decode("utf-8", errors="replace")


def titulo_do_html(html):
    achado = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if not achado:
        return None
    limpo = re.sub(r"\s+", " ", achado.group(1)).strip()
    return limpo or None


def garantir_pronuncia(html):
    """Insere a tag do pronuncia.js se o arquivo usa data-ouvir e nao a tem.

    Nao insere numa aula sem data-ouvir: la o script nao teria o que fazer, e
    uma tag a mais so confunde quem for ler o HTML depois.
    """
    if "assets/js/pronuncia.js" in html:
        return html, False
    if not re.search(r"data-ouvir\b", html, re.I):
        return html, False
    if re.search(r"</body\s*>", html, re.I):
        return re.sub(r"</body\s*>", TAG_PRONUNCIA + "\n</body>", html, count=1, flags=re.I), True
    return html + "\n" + TAG_PRONUNCIA + "\n", True


def carregar_indice():
    if not INDICE.exists():
        return {"formato": "nihongo-notebook/aulas@1", "aulas": []}
    dados = json.loads(INDICE.read_text(encoding="utf-8"))
    dados.setdefault("aulas", [])
    return dados


def salvar_indice(dados):
    dados["aulas"].sort(key=lambda a: (a.get("data") or "", a.get("slug") or ""), reverse=True)
    INDICE.parent.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def comando_listar():
    dados = carregar_indice()
    if not dados["aulas"]:
        print("Nenhuma aula no indice.")
        return 0
    for aula in dados["aulas"]:
        tags = ", ".join(aula.get("tags") or []) or "-"
        existe = "" if (DIR_AULAS / aula["slug"] / "index.html").exists() else "   [PASTA SUMIU]"
        print(f'{aula.get("data", "?"):>10}  {aula["slug"]:<34} {tags}{existe}')
    print(f'\n{len(dados["aulas"])} aula(s).')
    return 0


def comando_remover(slug):
    dados = carregar_indice()
    antes = len(dados["aulas"])
    dados["aulas"] = [a for a in dados["aulas"] if a.get("slug") != slug]
    pasta = DIR_AULAS / slug

    if antes == len(dados["aulas"]) and not pasta.exists():
        print(f"Nada encontrado com o slug '{slug}'.", file=sys.stderr)
        return 1

    if pasta.exists():
        shutil.rmtree(pasta)
        print(f"Pasta removida: site/aulas/{slug}/")
    if antes != len(dados["aulas"]):
        salvar_indice(dados)
        print("Removida do indice.")
    return 0


def relatar_som(html):
    """Diz que caminho de audio a aula usa, porque os tres se comportam diferente."""
    linhas = []
    marcas = len(re.findall(r"data-ouvir\b", html, re.I))
    if marcas:
        linhas.append(f"  {marcas} marcacao(oes) data-ouvir: usam o botao compartilhado")
    if re.search(r"speechSynthesis", html):
        linhas.append("  a aula traz o proprio speechSynthesis (voz do sistema, "
                      "muda de maquina para maquina)")
    if re.search(r"<audio|new Audio\(", html, re.I):
        linhas.append("  a aula traz <audio>/new Audio() proprio")
    if not linhas:
        linhas.append("  nenhum som: nem data-ouvir, nem audio proprio")
    return linhas


def main():
    p = argparse.ArgumentParser(
        description="Adiciona uma aula ao caderno.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--de", metavar="ARQUIVO", help="HTML ja pronto que vira a aula")
    p.add_argument("--titulo", help="titulo da aula (padrao: o <title> do arquivo)")
    p.add_argument("--slug", help="nome da pasta e da URL (padrao: derivado do titulo)")
    p.add_argument("--data", help="AAAA-MM-DD (padrao: hoje)")
    p.add_argument("--tags", help="separadas por virgula, ex: kana,escrita")
    p.add_argument("--resumo", help="uma linha, aparece no hub")
    p.add_argument("--sem-estilo", action="store_true",
                   help="na aula em branco, nao inclui o aula.css")
    p.add_argument("--forcar", action="store_true", help="sobrescreve se o slug ja existir")
    p.add_argument("--listar", action="store_true", help="lista as aulas do indice")
    p.add_argument("--remover", metavar="SLUG", help="apaga a pasta e tira do indice")
    args = p.parse_args()

    if args.listar:
        return comando_listar()
    if args.remover:
        return comando_remover(args.remover)

    origem = None
    html = None
    titulo = args.titulo

    if args.de:
        origem = Path(args.de).expanduser()
        if not origem.is_file():
            print(f"Arquivo nao encontrado: {origem}", file=sys.stderr)
            return 1
        html = ler_texto(origem)
        titulo = titulo or titulo_do_html(html) or origem.stem
    elif not titulo:
        print("Informe --de ARQUIVO ou --titulo TEXTO.", file=sys.stderr)
        return 1

    data = args.data or datetime.date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        print(f"Data fora do formato AAAA-MM-DD: {data}", file=sys.stderr)
        return 1
    slug = criar_slug(args.slug or titulo, data)
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]

    destino = DIR_AULAS / slug
    if destino.exists() and not args.forcar:
        print(f"Ja existe site/aulas/{slug}/. Use --slug outro-nome ou --forcar.", file=sys.stderr)
        return 1

    if html is None:
        html = MODELO.format(
            titulo=titulo,
            data=data,
            estilo="" if args.sem_estilo else TAG_ESTILO,
            pronuncia=TAG_PRONUNCIA,
        )
        injetou = False
    else:
        html, injetou = garantir_pronuncia(html)

    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(html, encoding="utf-8", newline="\n")

    dados = carregar_indice()
    dados["aulas"] = [a for a in dados["aulas"] if a.get("slug") != slug]
    dados["aulas"].append({
        "slug": slug,
        "titulo": titulo,
        "data": data,
        "resumo": args.resumo or "",
        "tags": tags,
    })
    salvar_indice(dados)

    de_onde = f"copiada de {origem.name}" if origem else "em branco"
    print(f"site/aulas/{slug}/index.html  ({de_onde})")
    if injetou:
        print("  faltava a linha do pronuncia.js e foi inserida antes de </body>")
    for linha in relatar_som(html):
        print(linha)
    print(f"  registrada no indice como '{titulo}' em {data}")
    print("\nVer local:  python -m http.server --directory site 8080")
    print(f"            http://localhost:8080/aulas/{slug}/")
    print(f'Publicar:   git add -A && git commit -m "aula: {slug}" && git push')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
