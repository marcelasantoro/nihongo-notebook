# Contrato de uma aula

O que o seu HTML precisa ter para funcionar dentro do caderno. Nada aqui limita o
conteudo da aula: e so o minimo para o botao de pronuncia achar as palavras e
para o hub achar a pagina.

## O minimo

Nada. Um HTML qualquer ja vira aula:

```bash
python scripts/nova_aula.py --de caminho/da/aula.html
```

Ele vai para `site/aulas/<slug>/index.html` e aparece no hub. O resto deste
documento e sobre o que voce **ganha** se marcar algumas coisas.

## Ouvir a pronuncia

Duas coisas. Uma linha antes de `</body>`:

```html
<script type="module" src="../../assets/js/pronuncia.js"></script>
```

O caminho tem dois niveis de subida porque toda aula mora em
`site/aulas/<slug>/index.html`. Se esquecer, o `nova_aula.py` insere sozinho
quando encontra `data-ouvir` no arquivo.

E um `data-ouvir` em cada coisa que se ouve:

```html
<span data-ouvir="あ">あ</span>              <!-- le o valor do atributo -->
<span data-ouvir>こんにちは</span>            <!-- sem valor: le o proprio texto -->
<span data-ouvir="ねこ" data-audio="neko.mp3">猫</span>
<td class="jp"><span data-ouvir="やま">山</span></td>
```

O botao aparece **logo depois** do elemento marcado. Marque o `<span>` de dentro,
nao a linha inteira, senao o botao cai no fim do paragrafo.

### De onde sai o som

Nesta ordem, e a primeira que der certo vence:

1. **Arquivo de audio** em `site/assets/audio/`. Vem do `data-audio="arquivo.mp3"`
   ou do mapa em `audio.json`. E o unico caminho que soa igual em todo aparelho.
2. **Voz japonesa do sistema**, se houver uma instalada.
3. **Aproximacao**: o kana virado em grafia portuguesa, lido pela voz de pt-BR.

O passo 3 nao se disfarca: o botao vira `≈ aproximação`, em laranja, e a pagina
mostra uma faixa explicando. Se voce quer o japones de verdade, resolva o passo 1
ou o 2.

### Sobre o passo 2, o que mais confunde

**O Windows nao vem com voz japonesa instalada.** Uma aula que so usa
`speechSynthesis` parece funcionar para quem tem o pacote e cai na aproximacao
para quem nao tem. Para instalar:

Configuracoes › Hora e idioma › Idioma e regiao › Adicionar idioma › 日本語 —
marcando **Fala** na lista de recursos opcionais. Depois reinicie o navegador.

### Dar som real a uma aula ja publicada

Sem reeditar o HTML dela. Ponha o arquivo em `site/assets/audio/` e registre no
mapa:

```json
{
  "mapa": {
    "あ": "a.mp3",
    "こんにちは": "konnichiwa.mp3"
  }
}
```

A chave e exatamente o texto que esta no `data-ouvir`. Vale para todas as aulas
de uma vez.

MP3 ou M4A, mono, o mais curto possivel. Audio de kana da uns 5 a 10 KB e pode
entrar no git tranquilo — o repositorio e publico, entao nao coloque gravacao com
voz de outras pessoas sem falar com elas.

## Aparecer no hub

O hub le `site/data/aulas.json`. Uma pasta que existe mas nao esta no indice abre
pela URL e nao aparece na lista. Quem escreve no indice e o `nova_aula.py`:

```bash
python scripts/nova_aula.py --de aula.html --tags hiragana,escrita \
  --resumo "uma linha que aparece no cartao" --data 2026-09-12
```

Editar o JSON na mao tambem funciona. Campos: `slug`, `titulo`, `data`
(AAAA-MM-DD), `resumo`, `tags`.

**A tag de sequencia e o que ordena o hub**, em ordem crescente: `etapa-0`,
`bloco-1`, `bloco-2`, `bloco-3`... O caderno e um curso, entao a posicao da aula
e a posicao dela na materia, e nao a data em que o arquivo entrou no repositorio
— refazer o bloco 2 hoje nao joga ele na frente do bloco 3. Uma aula sem tag de
sequencia (uma pagina de referencia, por exemplo) cai no fim da lista.

A `data` aparece no cartao e so desempata aulas sem numero, entao nao precisa
mais ser corrigida para acertar a ordem do curso: o numero do bloco faz isso.

As `tags` tambem viram os filtros no topo do hub, entao vale manter um
vocabulario pequeno e repetido (`hiragana`, `katakana`, `kanji`, `gramatica`,
`bloco-1`...).

## Estilo (opcional)

Se quiser que a aula pareca as outras:

```html
<link rel="stylesheet" href="../../assets/css/aula.css">
```

| Classe | Para que serve |
| --- | --- |
| `.aula` | container central, no `<main>` |
| `.voltar` | link de volta para o hub |
| `.stamp` | selo vermelho de carimbo |
| `.subtitulo` | linha cinza abaixo do `<h1>` |
| `.jp` | texto japones, fonte e entrelinha maiores |
| `.romaji` | transliteracao, cinza e italico |
| `.vocab` | tabela de vocabulario |
| `.kanji-grade` + `.kanji` + `.glifo` + `.leitura` | cartoes de kanji |
| `.exemplo` + `.traducao` | frase de exemplo com borda verde |
| `.nota` / `.atencao` | caixas de destaque |
| `.tags` + `.tag` | etiquetas |

`<ruby>`/`<rt>` ja vem estilizado para furigana. A pilha de fontes japonesas usa
o que o sistema tem (Hiragino, Yu Gothic, Noto Sans JP, Meiryo): nenhuma fonte
vem de CDN, para a pagina abrir offline.

**Se o seu HTML ja vem com estilo proprio, ignore o `aula.css`.** O
`pronuncia.js` injeta o CSS dos botoes por conta propria, com prefixo `.pron-`, e
nao depende dessa folha.

## Contexto seguro

Audio e sintese de voz so funcionam em `https://` ou `localhost`. No GitHub Pages
funciona. Abrindo o arquivo direto por `file://` o navegador bloqueia o `fetch` do
mapa e os modulos ES nem carregam. Para testar local:

```bash
python -m http.server --directory site 8080
```
