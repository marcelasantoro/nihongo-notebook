/* Pronuncia — botao de ouvir compartilhado entre as aulas.
 *
 * Uma linha na aula liga tudo:
 *
 *     <script type="module" src="../../assets/js/pronuncia.js"></script>
 *
 * e cada coisa que se ouve leva um data-ouvir:
 *
 *     <span data-ouvir="あ">あ</span>
 *     <span data-ouvir>こんにちは</span>            (sem valor = usa o texto)
 *     <span data-ouvir="ねこ" data-audio="neko.mp3">猫</span>
 *
 * A ordem de resolucao do som, da melhor para a pior:
 *
 *   1. arquivo em site/assets/audio/ — som real, igual em todo aparelho.
 *      Vem de data-audio="" ou do mapa em assets/audio/audio.json.
 *   2. voz japonesa do sistema (speechSynthesis com uma voz ja-*).
 *   3. aproximacao: o kana virado em grafia portuguesa, lido pela voz de pt-BR.
 *
 * O passo 3 existe porque o Windows nao vem com voz japonesa instalada, entao
 * sem ele o botao simplesmente nao faz nada na maquina da maioria das pessoas.
 * Mas ele NAO se disfarca de som real: o botao muda para "≈ aproximacao" e a
 * pagina mostra uma faixa dizendo o que esta acontecendo. Uma aproximacao
 * silenciosa ensinaria pronuncia errada sem avisar, que e o pior resultado
 * possivel num caderno de estudo.
 */

/* A pasta de audio sai de import.meta.url, nao do endereco da pagina. Assim o
 * caminho continua certo esteja a aula em site/aulas/<slug>/ ou em qualquer
 * outro nivel, e continua certo se o site um dia mudar de subpasta. */
const BASE_AUDIO = new URL('../audio/', import.meta.url);

const RATE = 0.8;

/* ---------------------------------------------------------------- kana ---- */

const BASE = {
  'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
  'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
  'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
  'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
  'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
  'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
  'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
  'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
  'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
  'わ': 'wa', 'ゐ': 'i', 'ゑ': 'e', 'を': 'o', 'ん': 'n',
  'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
  'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
  'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
  'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
  'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
  'ゔ': 'vu',
  'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o'
};
const YOON = { 'ゃ': 'a', 'ゅ': 'u', 'ょ': 'o' };
const VOGAIS = 'aiueo';

/* Katakana ocupa o mesmo bloco do hiragana deslocado de 0x60. Converter em vez
 * de repetir a tabela evita as duas ficarem fora de sincronia. */
function paraHiragana(texto) {
  let saida = '';
  for (const ch of texto) {
    const c = ch.codePointAt(0);
    saida += (c >= 0x30A1 && c <= 0x30F6) ? String.fromCodePoint(c - 0x60) : ch;
  }
  return saida;
}

/** Quebra o texto em silabas romanizadas (Hepburn). Devolve [] se nao houver
 *  kana nenhum — kanji solto cai fora, e ai so o arquivo de audio resolve.
 *
 *  Silaba, e nao string inteira, porque a grafia portuguesa la embaixo precisa
 *  ser um de-para exato. Com regex encadeada sobre a string toda uma troca come
 *  a anterior: 'chi' virava 'tchi', que ainda contem 'hi', que a regra do ha-gyo
 *  transformava de novo. Uma silaba se traduz uma vez e acabou. */
function silabas(texto) {
  const kana = paraHiragana(String(texto).trim());
  const saida = [];
  let achouKana = false;
  let sokuon = false;

  for (let i = 0; i < kana.length; i++) {
    const ch = kana[i];

    if (ch === 'っ') { sokuon = true; achouKana = true; continue; }

    if (ch === 'ー') {                        // prolonga a vogal da silaba anterior
      const anterior = saida[saida.length - 1] || '';
      const ultima = anterior[anterior.length - 1];
      if (VOGAIS.includes(ultima)) saida[saida.length - 1] = anterior + ultima;
      achouKana = true;
      continue;
    }

    const base = BASE[ch];
    if (!base) { saida.push(ch); continue; }  // kanji, pontuacao, latim: passa direto
    achouKana = true;

    let silaba = base;
    const proximo = kana[i + 1];
    if (proximo && YOON[proximo] && base.length > 1 && base.endsWith('i')) {
      const tronco = base.slice(0, -1);       // ki -> k, shi -> sh, chi -> ch
      const vogal = YOON[proximo];
      // sh/ch/j ja carregam o som de i: viram sha/cho/ju, nao shya/chyo.
      silaba = /(sh|ch|j)$/.test(tronco) ? tronco + vogal : tronco + 'y' + vogal;
      i++;
    }

    if (sokuon) { silaba = silaba[0] + silaba; sokuon = false; }
    saida.push(silaba);
  }
  return achouKana ? saida : [];
}

/** Kana -> romaji Hepburn, ou '' quando nao ha kana. */
export function romaji(texto) {
  return silabas(texto).join('');
}

/* Grafia que a voz de pt-BR le mais perto do japones. E aproximacao declarada,
 * nao transcricao, e as escolhas menos obvias tem motivo:
 *   ha-gyo -> 'rr' : o RR do portugues e o mesmo /h/ do japones.
 *   ra-gyo -> 'l'  : o L fica mais perto do tepe japones do que o R inicial,
 *                    que sairia /h/ e trocaria ら por は.
 *   sa-gyo -> 'ss' : S entre vogais em portugues vira /z/ ('asa'), SS nao.
 *   ki/ke  -> 'qui/quê' : 'ki' e 'ke' nao sao grafia portuguesa. */
const PT_SILABA = {
  a: 'a', i: 'i', u: 'u', e: 'ê', o: 'ô',
  ka: 'ca', ki: 'qui', ku: 'cu', ke: 'quê', ko: 'cô',
  sa: 'ssa', shi: 'xi', su: 'ssu', se: 'ssê', so: 'ssô',
  ta: 'ta', chi: 'tchi', tsu: 'tsu', te: 'tê', to: 'tô',
  na: 'na', ni: 'ni', nu: 'nu', ne: 'nê', no: 'nô',
  ha: 'rra', hi: 'rri', fu: 'fu', he: 'rrê', ho: 'rrô',
  ma: 'ma', mi: 'mi', mu: 'mu', me: 'mê', mo: 'mô',
  ya: 'iá', yu: 'iu', yo: 'ió',
  ra: 'la', ri: 'li', ru: 'lu', re: 'lê', ro: 'lô',
  wa: 'uá', n: 'n',
  ga: 'ga', gi: 'gui', gu: 'gu', ge: 'guê', go: 'gô',
  za: 'za', ji: 'dji', zu: 'zu', ze: 'zê', zo: 'zô',
  da: 'da', de: 'dê', do: 'dô',
  ba: 'ba', bi: 'bi', bu: 'bu', be: 'bê', bo: 'bô',
  pa: 'pa', pi: 'pi', pu: 'pu', pe: 'pê', po: 'pô',
  vu: 'vu',
  kya: 'quiá', kyu: 'quiu', kyo: 'quiô',
  sha: 'xá', shu: 'xu', sho: 'xô',
  cha: 'tchá', chu: 'tchu', cho: 'tchô',
  nya: 'niá', nyu: 'niu', nyo: 'niô',
  hya: 'rriá', hyu: 'rriu', hyo: 'rriô',
  mya: 'miá', myu: 'miu', myo: 'miô',
  rya: 'liá', ryu: 'liu', ryo: 'liô',
  gya: 'guiá', gyu: 'guiu', gyo: 'guiô',
  ja: 'djá', ju: 'dju', jo: 'djô',
  bya: 'biá', byu: 'biu', byo: 'biô',
  pya: 'piá', pyu: 'piu', pyo: 'piô'
};

function ptSilaba(s) {
  if (PT_SILABA[s]) return PT_SILABA[s];

  // sokuon: a silaba chegou com a consoante dobrada ('kko').
  if (s.length > 1 && s[0] === s[1] && VOGAIS.indexOf(s[0]) === -1) {
    const b = ptSilaba(s.slice(1));
    return b[0] + b;
  }

  // vogal longa: a silaba chegou com a vogal repetida ('kaa', 'too').
  const m = /^(.+?)([aiueo])\2+$/.exec(s);
  if (m && PT_SILABA[m[1] + m[2]]) {
    const b = PT_SILABA[m[1] + m[2]];
    return b + b[b.length - 1];
  }

  return s;                                   // nao e kana: sai como entrou
}

export function grafiaPt(texto) {
  return silabas(texto).map(ptSilaba).join('');
}

/* --------------------------------------------------------------- vozes ---- */

function vozJaponesa() {
  const vozes = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  return vozes.find(function (v) {
    return v.lang && v.lang.toLowerCase().replace('_', '-').indexOf('ja') === 0;
  }) || null;
}

/** As vozes chegam de forma assincrona no Chrome. Resolve quando a lista existir
 *  ou depois de 1,5 s — nunca deixa a pagina pendurada esperando. */
function vozesProntas() {
  return new Promise(function (resolve) {
    if (!window.speechSynthesis) return resolve();
    if (speechSynthesis.getVoices().length) return resolve();
    const pronto = function () {
      clearTimeout(t);
      speechSynthesis.onvoiceschanged = null;
      resolve();
    };
    const t = setTimeout(pronto, 1500);
    speechSynthesis.onvoiceschanged = pronto;
  });
}

function falar(texto, lang, voz) {
  return new Promise(function (resolve) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    if (voz) u.voice = voz;
    u.lang = lang;
    u.rate = RATE;
    u.onend = resolve;
    u.onerror = resolve;
    speechSynthesis.speak(u);
  });
}

/* --------------------------------------------------------------- audio ---- */

let mapaAudio = null;
async function carregarMapa() {
  if (mapaAudio) return mapaAudio;
  try {
    const r = await fetch(new URL('audio.json', BASE_AUDIO));
    mapaAudio = r.ok ? ((await r.json()).mapa || {}) : {};
  } catch (e) {
    mapaAudio = {};                           // sem mapa o botao continua vivo
  }
  return mapaAudio;
}

const cache = new Map();
function tocar(arquivo) {
  return new Promise(function (resolve, reject) {
    let a = cache.get(arquivo);
    if (!a) { a = new Audio(new URL(arquivo, BASE_AUDIO)); cache.set(arquivo, a); }
    a.onended = resolve;
    a.onerror = function () { reject(new Error('arquivo nao carregou: ' + arquivo)); };
    a.currentTime = 0;
    a.play().catch(reject);
  });
}

/* ------------------------------------------------------------------ ui ---- */

/* CSS proprio, todo com prefixo .pron-, injetado num <style>. A aula pode ter o
 * visual que quiser: o botao continua legivel sem depender de aula.css. */
const CSS = [
  '.pron-btn{display:inline-flex;align-items:center;gap:.35em;vertical-align:middle;',
  '  margin-left:.4em;border:1.5px solid #2F7D5B;color:#2F7D5B;background:#E4F2EA;',
  '  border-radius:999px;padding:.15em .7em;font:inherit;font-size:.8em;font-weight:700;',
  '  line-height:1.5;cursor:pointer;white-space:nowrap;transition:background .12s}',
  '.pron-btn:hover{background:#D3E9DD}',
  '.pron-btn:active{background:#2F7D5B;color:#fff}',
  '.pron-btn[disabled]{opacity:.5;cursor:not-allowed}',
  '.pron-btn.pron-aprox{border-color:#B07A1E;color:#8A5E14;background:#FFF4E5}',
  '.pron-btn.pron-aprox:hover{background:#FBE9CD}',
  '.pron-faixa{position:sticky;top:0;z-index:50;background:#FFF4E5;color:#5C4410;',
  '  border-bottom:1px solid #E0A030;padding:.6em 1em;font-size:13.5px;line-height:1.5}',
  '.pron-faixa code{background:#FBE9CD;border-radius:4px;padding:0 .3em}',
  '.pron-faixa button{float:right;border:0;background:none;color:#8A5E14;font:inherit;',
  '  font-size:17px;cursor:pointer;padding:0 .2em;line-height:1}'
].join('\n');

function injetarCss() {
  if (document.getElementById('pron-css')) return;
  const s = document.createElement('style');
  s.id = 'pron-css';
  s.textContent = CSS;
  document.head.appendChild(s);
}

let faixaMostrada = false;
function faixa(html) {
  if (faixaMostrada) return;
  faixaMostrada = true;
  const d = document.createElement('div');
  d.className = 'pron-faixa';
  d.innerHTML = '<button title="fechar" aria-label="fechar">&times;</button>' + html;
  d.querySelector('button').onclick = function () { d.remove(); };
  document.body.prepend(d);
}

/* ------------------------------------------------------------------ main -- */

async function iniciar() {
  const alvos = Array.prototype.slice.call(document.querySelectorAll('[data-ouvir]'));
  if (!alvos.length) return;                  // aula sem marca: nao faz nada

  injetarCss();
  const resultado = await Promise.all([carregarMapa(), vozesProntas()]);
  const mapa = resultado[0];
  const voz = vozJaponesa();
  let usouAproximacao = false;

  alvos.forEach(function (el) {
    const texto = (el.getAttribute('data-ouvir') || el.textContent || '').trim();
    if (!texto) return;

    const arquivo = el.getAttribute('data-audio') || mapa[texto] || null;
    const r = romaji(texto);
    const aproximando = !arquivo && !voz && !!r;
    if (aproximando) usouAproximacao = true;

    // Sem arquivo, sem voz japonesa e sem kana para aproximar (kanji solto):
    // nao ha som nenhum a oferecer, entao nao se cria um botao que engana.
    if (!arquivo && !voz && !r) return;

    const rotulo = aproximando ? '≈ aproximação' : '🔊 ouvir';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pron-btn' + (aproximando ? ' pron-aprox' : '');
    btn.textContent = rotulo;
    btn.title = aproximando
      ? 'Sem som real para ' + texto + ': lendo "' + r + '" com a voz de português'
      : 'Ouvir ' + texto + (r ? ' (' + r + ')' : '');

    btn.addEventListener('click', async function () {
      btn.disabled = true;
      btn.textContent = '🔈 …';
      try {
        if (arquivo) await tocar(arquivo);
        else if (voz) await falar(texto, voz.lang, voz);
        else await falar(grafiaPt(texto), 'pt-BR', null);
      } catch (e) {
        btn.textContent = '🔇 erro';
        faixa('Não consegui tocar <b>' + texto + '</b>: ' + (e.message || e) +
              '. Se você abriu o arquivo direto do disco, sirva a pasta por HTTP.');
        setTimeout(function () { btn.textContent = rotulo; btn.disabled = false; }, 2500);
        return;
      }
      btn.textContent = rotulo;
      btn.disabled = false;
    });

    el.after(btn);
  });

  if (usouAproximacao) {
    faixa('Este computador não tem <b>voz japonesa</b> instalada, então os botões ' +
          'sem áudio gravado leem uma <b>aproximação em português</b>. Para o som ' +
          'real: Configurações &rsaquo; Hora e idioma &rsaquo; Idioma e região &rsaquo; ' +
          'Adicionar idioma &rsaquo; 日本語, marcando <i>Fala</i>. Ou ponha um MP3 em ' +
          '<code>site/assets/audio/</code> e registre em <code>audio.json</code>.');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', iniciar);
} else {
  iniciar();
}
