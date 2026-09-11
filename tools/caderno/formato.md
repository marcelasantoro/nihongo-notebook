# Formato visual do caderno (referência rápida)

O template em `tools/caderno/template_aula.html` já carrega tudo isto. Este arquivo existe para
quando for preciso editar o template ou explicar o formato — não é preciso lê-lo para gerar
uma aula.

## Identidade
- Papel `#FAF7F0`, tinta `#26241F`, suave `#6B6557`, índigo `#2E4272` (botões/quadro do dedo),
  verde hiragana `#2F7D5B` + fundo `#E4F2EA` (guias e sons), vermelho hanko `#C63D2F` (ponto
  de início do traço, selo de etapa), linha `#E4DED2`.
- Título em serifa (Iowan Old Style / Georgia); texto em sans do sistema; japonês em
  "Hiragino Sans", "Yu Gothic", "Noto Sans JP".
- Largura máxima 760px, cantos arredondados 14–18px, cards brancos com borda `--line`.

## Estrutura de cada lição de letra (gerada pelo template)
1. Cabeçalho: letra grande em verde · "Como escrever X" · dica de som · **botão 🔊 ouvir**.
2. Animação do traçado (SVG 109×109, KanjiVG) com botão "▶ desenhar de novo".
3. Passos: um mini-SVG por traço — traços anteriores em preto, atual em verde tracejado com
   seta, futuros quase invisíveis; bolinha vermelha marca onde a caneta encosta.
4. Instruções numeradas, uma frase por traço, linguagem de professora de alfabetização
   ("desce fazendo barriguinha", "pinguinho por último").
5. Quadro do dedo: canvas azul sobre o tracejado cinza para escrever com o dedo; botão limpar.

## Seção de palavras
Grade de cards: hiragana grande, romaji pequeno, tradução, botão 🔊. Aparece só se houver
`palavras` no JSON.

## Áudio
Web Speech API com voz `ja-JP` (no Chrome, a "Google 日本語" já vem embutida — sem instalar
nada). Se não houver voz japonesa, lê o romaji com a voz disponível e mostra aviso amarelo.
O botão mostra estado (⏳ carregando / 🔈 falando / 🔇 erro). Velocidade 0.75.
Importante: a pré-visualização dentro do chat do Claude bloqueia áudio; o arquivo precisa ser
aberto direto no navegador.

## Rodapé
"Japonês do zero · turma にほんご５ · Traçados oficiais: base KanjiVG © Ulrich Apel,
licença CC BY-SA 3.0" — manter, é exigência da licença.
