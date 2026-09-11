# nihongo-notebook

Caderno de estudo de japones. Uma pagina HTML por aula, com botao para ouvir a
pronuncia, publicado em:

**https://marcelasantoro.github.io/nihongo-notebook/**

Site estatico. Sem build, sem backend, sem dependencia de CDN: o que esta em
`site/` e exatamente o que fica no ar.

## A divisao de trabalho

O HTML da aula nasce por fora; o repositorio so cuida de onde ele mora e de
como aparece no hub. O minimo que um arquivo precisa ter e uma linha, e esta em
[`docs/CONTRATO-AULA.md`](docs/CONTRATO-AULA.md).

Para o caderno de escrita — a aula com tracado animado, quadro para escrever com
o dedo e botao de ouvir — quem gera o HTML e
[`tools/caderno/`](tools/caderno/README.md), aqui dentro.

## O fluxo, de ponta a ponta

```bash
# 1. gerar: JSON da aula -> HTML (tracados vem do cache em tools/caderno/kanjivg/)
python tools/caderno/gerar_aula.py aula.json hiragana-linha-sa.html

# 2. registrar: copia para site/aulas/<slug>/ e escreve no indice do hub
python scripts/nova_aula.py --de hiragana-linha-sa.html --slug hiragana-linha-sa \
    --tags bloco-3,hiragana,tracado --data 2026-09-11 --resumo "uma linha para o cartao"

# 3. publicar: push na main dispara o workflow, a pagina entra no ar
git add -A && git commit -m "aula: hiragana-linha-sa" && git push
```

O passo 1 vale para o caderno de escrita. Uma aula que voce escreveu a mao, ou
gerou de outro jeito, pula direto para o passo 2:

```bash
python scripts/nova_aula.py --de caminho/da/aula.html --tags hiragana,escrita
git add -A && git commit -m "aula: nome-da-aula" && git push
```

O script copia o HTML para `site/aulas/<slug>/index.html`, registra a aula em
`site/data/aulas.json` e, se o arquivo usa `data-ouvir` sem ter a linha do
`pronuncia.js`, insere ela antes de `</body>`. Fora isso ele nao toca no seu
conteudo.

O `git push` na `main` dispara o workflow e a pagina fica no ar em poucos minutos.

Outras operacoes:

```bash
python scripts/nova_aula.py --listar
python scripts/nova_aula.py --remover hiragana-vogais
python scripts/nova_aula.py --titulo "Aula 04: verbos ru"   # aula em branco
```

## Ouvir a pronuncia

Marque o que se ouve com `data-ouvir` e inclua o script uma vez:

```html
<span data-ouvir="あ">あ</span>
<span data-ouvir>こんにちは</span>

<script type="module" src="../../assets/js/pronuncia.js"></script>
```

O botao aparece sozinho ao lado. Ele busca o som nesta ordem:

1. **arquivo de audio** em `site/assets/audio/` — som real, igual em todo aparelho;
2. **voz japonesa do sistema**, se houver uma instalada;
3. **aproximacao**: o kana virado em grafia portuguesa, lido pela voz de pt-BR.

O passo 3 se identifica: o botao vira `≈ aproximação` e a pagina mostra uma
faixa explicando. Detalhes e como registrar um MP3 em
[`docs/CONTRATO-AULA.md`](docs/CONTRATO-AULA.md).

## Ver antes de publicar

```bash
python -m http.server --directory site 8080
```

Abra `http://localhost:8080/`. Servir por HTTP nao e capricho: por `file://` o
`fetch` do indice e bloqueado e os modulos ES nao carregam.

## Estrutura

```
site/                        publicado como esta, sem build
  index.html                 hub, autocontido
  aulas/<slug>/index.html    uma pasta por aula, o arquivo e seu
  assets/
    js/pronuncia.js          botao de ouvir, compartilhado
    css/aula.css             folha opcional das aulas
    audio/                   MP3 de pronuncia + audio.json (o mapa)
    brand/favicon.svg
  data/aulas.json            indice da listagem
scripts/nova_aula.py         importa a aula e escreve no indice
tools/caderno/               gerador do caderno de escrita (JSON -> HTML)
  gerar_aula.py              o comando que gera a pagina da aula
  kanjivg.py                 tracados oficiais, com cache offline
  kanjivg/                   o cache: um .json por caractere, versionado
  template_aula.html         a pagina em si (CSS + JS + marcadores)
  exemplo_aula.json          modelo do JSON de entrada
  formato.md                 o formato visual descrito
docs/                        architecture.md e CONTRATO-AULA.md
.cursor/rules/aulas.mdc      convencoes, lidas pelo editor de IA
.github/workflows/pages.yml  publica site/ a cada push na main
ingest/                      git-ignored, material bruto da aula
```

Como funciona por baixo: [`docs/architecture.md`](docs/architecture.md).
O gerador do caderno: [`tools/caderno/README.md`](tools/caderno/README.md).

Tracados das letras: base **KanjiVG** (c) Ulrich Apel, licenca CC BY-SA 3.0.
