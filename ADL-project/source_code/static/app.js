// Conversation history lives in the browser (localStorage), so it survives a page
// reload. The last turns are sent with every question so follow-ups work.

const KEY = "handbook-chat-history";
const FLEURON = `<svg class="orn" viewBox="0 0 40 20" aria-hidden="true"><path d="M20 2 L26 10 L20 18 L14 10 Z" fill="currentColor"/><circle cx="8" cy="10" r="2.2" fill="currentColor"/><circle cx="32" cy="10" r="2.2" fill="currentColor"/><circle cx="20" cy="10" r="2" fill="var(--bg)"/></svg>`;
const log = document.getElementById("log");
const intro = document.getElementById("intro");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const meta = document.getElementById("meta");

let history = load();
let busy = false;

function load() {
  try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; }
}
function save() {
  try { localStorage.setItem(KEY, JSON.stringify(history)); } catch { /* private mode */ }
}

// ---------- Tiny, safe markdown: paragraphs, lists, **bold**, `code`, (p. 7) ----------

function escape(text) {
  return text.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function inline(text) {
  return escape(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\((p\.|pages?)\s?[\d,\s&and.p]+\)/gi, m => `<span class="cite">${m}</span>`);
}
function markdown(text) {
  const out = [];
  let list = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)/);
    const number = line.match(/^\d+[.)]\s+(.*)/);
    const item = bullet || number;
    if (item) {
      const tag = bullet ? "ul" : "ol";
      if (list !== tag) { if (list) out.push(`</${list}>`); out.push(`<${tag}>`); list = tag; }
      out.push(`<li>${inline(item[1])}</li>`);
      continue;
    }
    if (list) { out.push(`</${list}>`); list = null; }
    if (line) out.push(`<p>${inline(line)}</p>`);
  }
  if (list) out.push(`</${list}>`);
  return out.join("");
}

// ---------- Rendering ----------

function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

function renderFoot(section, turn) {
  section.querySelector(".turn-foot")?.remove();
  const foot = el("div", "turn-foot");
  if (turn.card) foot.append(el("span", "drawn", `Card drawn &nbsp;<b>${escape(turn.card)}</b>`));
  renderSources(foot, turn.sources);
  if (foot.childNodes.length) section.append(foot);
}

function renderSources(container, sources) {
  if (!sources || !sources.length) return;
  const pages = [...new Set(sources.map(s => s.page))].sort((a, b) => a - b);
  const details = el("details", "sources");
  details.append(el("summary", "", `Found on ${pages.length > 1 ? "pages" : "page"} ${pages.join(", ")}`));
  for (const s of sources) {
    const block = el("div", "excerpt");
    block.innerHTML = `<b>Page ${s.page}</b> &nbsp;<span>similarity ${s.score.toFixed(2)}</span><p>${escape(s.text)}...</p>`;
    details.append(block);
  }
  container.append(details);
}

function addTurn(turn) {
  intro.hidden = true;
  if (log.querySelector(".turn")) log.append(el("div", "fleuron", FLEURON));
  const section = el("section", "turn");
  section.append(el("h2", "question", escape(turn.question)));
  const answer = el("div", "answer");
  if (turn.answer) answer.innerHTML = markdown(turn.answer);
  section.append(answer);
  renderFoot(section, turn);
  log.append(section);
  return { section, answer };
}

function renderAll() {
  log.querySelectorAll(".turn, .log > .fleuron").forEach(n => n.remove());
  intro.hidden = history.length > 0;
  history.forEach(addTurn);
}

// ---------- Asking ----------

async function ask(question) {
  if (busy || !question.trim()) return;
  busy = true;
  send.disabled = true;

  const turn = { question: question.trim(), answer: "", sources: [] };
  const { section, answer } = addTurn(turn);
  answer.innerHTML = '<span class="thinking">Shuffling the deck</span>';
  shuffle();
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  const recent = history.slice(-4).map(t => ({ question: t.question, answer: t.answer }));

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: turn.question, history: recent }),
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const msg = JSON.parse(line);
        if (msg.type === "sources") {
          turn.sources = msg.sources;
          answer.innerHTML = '<span class="thinking">Reading the cards</span>';
        } else if (msg.type === "token") {
          turn.answer += msg.text;
          answer.classList.add("streaming");
          answer.innerHTML = markdown(turn.answer);
        } else if (msg.type === "error") {
          throw new Error(msg.text);
        }
      }
    }
    answer.classList.remove("streaming");
    turn.card = drawRandom();
    renderFoot(section, turn);
    history.push(turn);
    save();
  } catch (error) {
    answer.classList.remove("streaming");
    answer.classList.add("error");
    answer.textContent = "Could not get an answer. Is Ollama running? (" + error.message + ")";
  } finally {
    if (showingBack) reveal();
    busy = false;
    send.disabled = false;
    input.focus();
  }
}

// ---------- Events ----------

form.addEventListener("submit", e => {
  e.preventDefault();
  const q = input.value;
  input.value = "";
  grow();
  ask(q);
});

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});

function grow() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}
input.addEventListener("input", grow);

document.querySelectorAll(".suggestions .link").forEach(b =>
  b.addEventListener("click", () => ask(b.textContent))
);

document.getElementById("reset").addEventListener("click", () => {
  history = [];
  save();
  renderAll();
  input.focus();
});

// ---------- Theme (Noir / Vellum) ----------

const themeButton = document.getElementById("theme");
function setTheme(name) {
  document.documentElement.dataset.theme = name;
  themeButton.textContent = name === "noir" ? "Vellum" : "Noir";
  try { localStorage.setItem("handbook-theme", name); } catch { }
}
themeButton.addEventListener("click", () =>
  setTheme(document.documentElement.dataset.theme === "noir" ? "vellum" : "noir"));
let savedTheme = null;
try { savedTheme = localStorage.getItem("handbook-theme"); } catch { }
setTheme(savedTheme === "vellum" ? "vellum" : "noir");

// ---------- Tarot deck ----------
// Uses the card images exported into static/tarot/ (see /api/deck) when there are any,
// otherwise the six cards drawn in arts.js. Each question shuffles the deck and draws a card.

const artBox = document.getElementById("art");       // tilts with the mouse
const cardEl = document.getElementById("card");      // turns over
const artNumeral = document.getElementById("art-numeral");
const artName = document.getElementById("art-name");
const deckCount = document.getElementById("deck-count");

let deck = window.ARTS.map(a => ({ id: a.id, numeral: a.numeral, name: a.name, svg: a.svg }));
let backHtml = window.CARD_BACK();
let index = 0;
let showingBack = false;
let flipTimer = null;

function faceOf(card) {
  return card.url ? `<img src="${card.url}" alt="${escape(card.name)}" draggable="false">` : card.svg();
}

function flipTo(html, done) {
  clearTimeout(flipTimer);
  cardEl.classList.remove("flip-in");
  cardEl.classList.add("flip-out");
  flipTimer = setTimeout(() => {
    cardEl.innerHTML = html;
    cardEl.classList.remove("flip-out");
    cardEl.classList.add("flip-in");
    if (done) done();
  }, 260);
}

function showCard(i, instant = false) {
  index = (i + deck.length) % deck.length;
  const card = deck[index];
  showingBack = false;
  artBox.classList.remove("shuffling");
  if (instant) cardEl.innerHTML = faceOf(card);
  else flipTo(faceOf(card));
  artNumeral.textContent = card.numeral || "";
  artName.textContent = card.name;
  deckCount.textContent = `${index + 1} of ${deck.length}`;
  try { localStorage.setItem("handbook-card", card.id); } catch { }
}

function shuffle() {
  if (showingBack) return;
  showingBack = true;
  artNumeral.textContent = "";
  artName.textContent = "Shuffling";
  flipTo(backHtml, () => artBox.classList.add("shuffling"));
}

function reveal() { showCard(index); }

function drawRandom() {
  let next = index;
  if (deck.length > 1) while (next === index) next = Math.floor(Math.random() * deck.length);
  showCard(next);
  const card = deck[index];
  return (card.numeral ? card.numeral + " " : "") + card.name;
}

document.getElementById("prev").addEventListener("click", () => showCard(index - 1));
document.getElementById("next").addEventListener("click", () => showCard(index + 1));
document.getElementById("draw").addEventListener("click", () => {
  shuffle();
  setTimeout(drawRandom, 900);
});
document.addEventListener("keydown", e => {
  if (document.activeElement === input) return;
  if (e.key === "ArrowLeft") showCard(index - 1);
  if (e.key === "ArrowRight") showCard(index + 1);
});

// The card leans towards the mouse, like holding it up to the light.
artBox.addEventListener("mousemove", e => {
  const r = artBox.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width - 0.5;
  const y = (e.clientY - r.top) / r.height - 0.5;
  artBox.style.transform = `rotateY(${x * 14}deg) rotateX(${-y * 14}deg)`;
});
artBox.addEventListener("mouseleave", () => { artBox.style.transform = ""; });

function startDeck() {
  let saved = null;
  try { saved = localStorage.getItem("handbook-card"); } catch { }
  const found = deck.findIndex(c => c.id === saved);
  showCard(found >= 0 ? found : 0, true);
}

startDeck();
fetch("/api/deck").then(r => r.json()).then(data => {
  if (!data.cards || !data.cards.length) return;
  deck = data.cards;
  if (data.back) backHtml = `<img src="${data.back}" alt="Back of a card" draggable="false">`;
  startDeck();
  // CC BY 4.0: title, creator, source, licence, and a note that the images were adapted.
  const c = data.credit || {};
  const credit = document.getElementById("credit");
  credit.innerHTML = `Art by ${escape((c.artist || "").split(" (")[0])}, 1909. Via `
    + `<a href="${escape(c.source)}" target="_blank" rel="noopener">${escape(c.title)}</a>`
    + (c.author ? ` by ${escape(c.author)}` : "")
    + `, <a href="${escape(c.license_url)}" target="_blank" rel="noopener">${escape(c.license)}</a>. Resized.`;
  credit.hidden = false;
}).catch(() => {});

// ---------- Feathers drifting at the edges ----------

// A soft plume: a curved shaft with fine barbs on both sides, drawn as strokes.
const FEATHER = (() => {
  let barbs = "";
  for (let i = 0; i < 26; i++) {
    const t = i / 25;
    const y = 12 + t * 92;                    // along the shaft
    const x = 20 + Math.sin(t * 2.6) * 3;     // slight curve
    const len = 15 * Math.sin(Math.PI * Math.min(1, t * 1.15 + 0.08)) + 2;
    const lift = 7 + t * 4;
    barbs += `<path d="M${x.toFixed(1)} ${y.toFixed(1)} q${(-len * 0.6).toFixed(1)} ${(-lift * 0.3).toFixed(1)} ${(-len).toFixed(1)} ${(-lift).toFixed(1)}"/>`;
    barbs += `<path d="M${x.toFixed(1)} ${y.toFixed(1)} q${(len * 0.6).toFixed(1)} ${(-lift * 0.3).toFixed(1)} ${len.toFixed(1)} ${(-lift).toFixed(1)}"/>`;
  }
  return `<svg viewBox="0 0 40 124"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" opacity="0.9">${barbs}</g>
    <path d="M20 6 C23 40 23 80 20 122" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
})();
const featherBox = document.getElementById("feathers");
[[7, 5, -30], [37, 3, 25], [93, 10, 40], [96, 58, -20], [4, 76, 25]].forEach(([left, top, rot], i) => {
  const f = el("div", "feather", FEATHER);
  f.style.left = left + "%";
  f.style.top = top + "%";
  f.style.setProperty("--r0", rot + "deg");
  f.style.setProperty("--r1", rot + 25 + "deg");
  f.style.setProperty("--dx", (i % 2 ? -1 : 1) * (12 + i * 4) + "px");
  f.style.setProperty("--dy", 20 + i * 6 + "px");
  f.style.animationDuration = 8 + i * 2 + "s";
  featherBox.append(f);
});

fetch("/api/info").then(r => r.json()).then(info => {
  meta.textContent = `${info.model} ✦ ${info.embedding} ✦ ${info.top_k} passages ✦ kept on this machine`;
}).catch(() => {});

renderAll();
input.focus();
