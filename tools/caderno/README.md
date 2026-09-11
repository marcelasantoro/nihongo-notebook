# Gerador do caderno de escrita

Transforma um JSON de aula na página HTML do caderno: animação do traçado,
passo a passo traço por traço, quadro para escrever com o dedo e botão 🔊 em
cada letra e em cada palavra.

```bash
python tools/caderno/gerar_aula.py aula.json hiragana-linha-sa.html
python scripts/nova_aula.py --de hiragana-linha-sa.html --slug hiragana-linha-sa \
    --tags bloco-3,hiragana,tracado --data 2026-09-11 --resumo "uma linha para o hub"
git add -A && git commit -m "aula: hiragana-linha-sa" && git push
```

## O que tem aqui

| Arquivo | Para que serve |
| --- | --- |
| `gerar_aula.py` | JSON → HTML. É o comando que você roda. |
| `kanjivg.py` | traçados oficiais, com cache offline. |
| `kanjivg/` | o cache: um `.json` por caractere, versionado no repositório. |
| `template_aula.html` | a página em si (CSS + JS + os marcadores `{{...}}`). |
| `exemplo_aula.json` | modelo do JSON de entrada — copie e edite. |
| `formato.md` | o formato visual descrito: cores, seções, áudio, rodapé. |

## O JSON da aula

```json
{
  "titulo": "Bloco 3 · A linha さ — sa shi su se so",
  "stamp":  "Etapa 2 · Bloco 3 · Caderno de escrita",
  "intro":  "parágrafo curto de abertura (aceita HTML) — opcional",
  "letras": [
    {"ch": "さ", "romaji": "sa", "som": "soa como o SA de sala",
     "instr": ["uma frase por traço, na ordem de escrita"]}
  ],
  "palavras": [{"jp": "さけ", "romaji": "sake", "pt": "saquê"}],
  "dica": "observação de fechamento — opcional"
}
```

- **`instr` é a parte que faz a aula ser aula.** Uma frase por traço, concreta:
  "desce fazendo barriguinha", "pinguinho por último", "como um tobogã". Nunca
  deixe cair no "traço 1, traço 2" — o gerador completa assim e avisa no
  terminal quando isso acontece.
- Confira o número de traços antes de escrever:
  `python tools/caderno/kanjivg.py さしすせそ`.
- **`palavras`**: 4 a 8 palavras reais usando só os kana já vistos (os da aula
  e os das aulas anteriores).
- As três regras de ouro (cima → baixo, esquerda → direita, pinguinhos por
  último) já vêm impressas na página; não repita no `intro`.

## O cache de traçados

Os traçados vêm do [KanjiVG](https://kanjivg.tagaini.net). Ficam em
`tools/caderno/kanjivg/`, um arquivo por caractere, dentro do repositório — com
o cache cheio, gerar aula não depende de rede.

```bash
python tools/caderno/kanjivg.py --listar    # o que já está no cache e o que falta
python tools/caderno/kanjivg.py --vendor    # baixa todo o hiragana e katakana
python tools/caderno/kanjivg.py さしすせそ   # os traços de umas letras (e quantos são)
```

`--vendor` roda uma vez, num ambiente com acesso a `raw.githubusercontent.com`,
e o resultado é commitado. `gerar_aula.py --offline` proíbe a rede: serve para
conferir que a aula sai só com o cache.

Se faltar traçado de alguma letra e não houver rede, o gerador **falha de
propósito** — página com letra sem traçado não é caderno de escrita.

## Antes de publicar

- nenhum `{{` sobrou no HTML (o gerador já barra isso);
- botão 🔊 em cada letra e em cada palavra;
- rodapé com o crédito do KanjiVG — é exigência da licença CC BY-SA 3.0,
  não apague.

A pré-visualização dentro do chat bloqueia áudio: para ouvir, abra o arquivo no
Chrome/Edge ou pelo site publicado.

## Slugs já usados

`hiragana-vogais`, `hiragana-linha-ka`, `hiragana-linha-sa`, … O padrão é
minúsculas, sem acento, kebab-case: `dakuten`, `katakana-linha-ka`,
`vocab-familia`.

---

Traçados: base **KanjiVG** © Ulrich Apel, licença CC BY-SA 3.0.
