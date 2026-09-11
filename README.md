# nihongo-notebook

Caderno de estudo de japones. Uma pagina HTML por aula, com botao para ouvir a
pronuncia, publicado em:

**https://marcelasantoro.github.io/nihongo-notebook/**

Site estatico. Sem build, sem backend, sem dependencia de CDN: o que esta em
`site/` e exatamente o que fica no ar.

## A divisao de trabalho

Voce gera o HTML da aula por fora, do jeito que preferir. O repositorio nao tem
opiniao sobre como a aula virou HTML — so sobre o que o arquivo precisa ter
quando chega, e esse minimo e uma linha. Esta em
[`docs/CONTRATO-AULA.md`](docs/CONTRATO-AULA.md).

## Subir uma aula

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
docs/                        architecture.md e CONTRATO-AULA.md
.cursor/rules/aulas.mdc      convencoes, lidas pelo editor de IA
.github/workflows/pages.yml  publica site/ a cada push na main
ingest/                      git-ignored, material bruto da aula
```

Como funciona por baixo: [`docs/architecture.md`](docs/architecture.md).
