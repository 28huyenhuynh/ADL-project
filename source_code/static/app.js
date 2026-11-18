// The current conversation lives in the browser (localStorage) so a reload keeps it, and
// every finished turn is also saved on the server (chats.py, folder chat_history/) so it
// appears under "Past readings" and survives a browser reset. The last turns are sent with
// every question so follow-ups work.

const KEY = "handbook-chat-history";
const ID_KEY = "handbook-chat-id";
// Divider between readings: a small rose between two leaves (symbols defined in index.html).
const FLEURON = `<svg class="orn" viewBox="0 0 64 30" aria-hidden="true"><use href="#leaf" x="0" y="9" width="22" height="12"/><use href="#leaf" x="42" y="9" width="22" height="12" transform="rotate(180 53 15)"/><use href="#rose" x="18" y="0" width="28" height="30"/></svg>`;
const DECLINED = ["other_subject", "off_topic", "greeting"];
const log = document.getElementById("log");
const intro = document.getElementById("intro");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const meta = document.getElementById("meta");

function storeGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
function storeSet(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode */ } }

let history = load();
let chatId = storeGet(ID_KEY) || newId();
let busy = false;

function newId() {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  storeSet(ID_KEY, id);
  return id;
}
function load() {
  try { return JSON.parse(storeGet(KEY)) || []; } catch { return []; }
}
function save() {
  storeSet(KEY, JSON.stringify(history));
  storeSet(ID_KEY, chatId);
  if (!history.length) return;
  fetch(`/api/chats/${chatId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ turns: history }),
  }).catch(() => { /* server offline: the browser copy is kept */ });
}

// ---------- Interface language (English / Tiếng Việt) ----------

let uiLang = storeGet("handbook-lang") || ((navigator.language || "").toLowerCase().startsWith("vi") ? "vi" : "en");
if (!window.I18N[uiLang]) uiLang = "en";

function t(key, ...args) {
  const value = (window.I18N[uiLang] || window.I18N.en)[key] ?? window.I18N.en[key];
  return typeof value === "function" ? value(...args) : value;
}

const langButton = document.getElementById("lang");
function applyLanguage() {
  document.documentElement.lang = uiLang;
  document.querySelectorAll("[data-i18n]").forEach(n => { n.textContent = t(n.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach(n => { n.innerHTML = t(n.dataset.i18nHtml); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(n => { n.placeholder = t(n.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-aria]").forEach(n => { n.setAttribute("aria-label", t(n.dataset.i18nAria)); });
  // The button names the OTHER language, the one you switch to.
  const other = uiLang === "vi" ? "en" : "vi";
  langButton.textContent = window.LANG_NAMES[other];
  document.title = t("brand");
  renderAll();
  if (typeof deckCount !== "undefined" && deck.length) deckCount.textContent = t("of", index + 1, deck.length);
  renderMeta();
  renderCredit();
}
langButton.addEventListener("click", () => {
  uiLang = uiLang === "vi" ? "en" : "vi";
  storeSet("handbook-lang", uiLang);
  applyLanguage();
});

// ---------- Tiny, safe markdown: paragraphs, lists, **bold**, `code`, (p. 7) ----------

function escape(text) {
  return String(text).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function inline(text) {
  return escape(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\((p\.|pages?|tr\.|trang)\s?[\d,\s&and.p]+\)/gi, m => `<span class="cite">${m}</span>`);
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
  if (turn.unsupported?.length) foot.append(el("p", "unsupported",
    t("checkThis", turn.unsupported.map(n => `<b>${escape(n)}</b>`).join(", "))));
  if (turn.card) foot.append(el("span", "drawn", `${t("cardDrawn")} &nbsp;<b>${escape(turn.card)}</b>`));
  renderSources(foot, turn.sources);
  if (foot.childNodes.length) section.append(foot);
}

function renderSources(container, sources) {
  if (!sources || !sources.length) return;
  // Handbook pages by number; supplementary text sources (page 0) by their title.
  const pages = [...new Set(sources.filter(s => s.page).map(s => s.page))].sort((a, b) => a - b);
  const others = [...new Set(sources.filter(s => !s.page && s.title).map(s => s.title))];
  const details = el("details", "sources");
  details.append(el("summary", "", escape(t("foundOn", pages, others))));
  for (const s of sources) {
    const block = el("div", "excerpt");
    block.innerHTML = `<b>${escape(!s.page && s.title ? s.title : t("page", s.page))}</b> &nbsp;<span>${t("similarity")} ${s.score.toFixed(2)}</span><p>${escape(s.text)}...</p>`;
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
  if (turn.declined) answer.classList.add("declined");
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

  const turn = { question: question.trim(), answer: "", sources: [], time: Date.now() };
  const { section, answer } = addTurn(turn);
  answer.innerHTML = `<span class="thinking">${escape(t("shuffling"))}</span>`;
  shuffle();
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  // The English version of each question and how it was handled go back to the server,
  // so follow-ups work in any language (rag/language.py, normalize_history).
  const recent = history.slice(-4).map(h => ({
    question: h.question, answer: h.answer, question_en: h.question_en, scope: h.scope,
  }));

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
          turn.scope = msg.scope;
          turn.lang = msg.lang;
          turn.question_en = msg.question_en;
          turn.declined = DECLINED.includes(msg.scope);
          answer.classList.toggle("declined", turn.declined);
          const waiting = msg.lang && msg.lang !== "English" && !turn.declined ? "translating" : "reading";
          answer.innerHTML = `<span class="thinking">${escape(t(waiting))}</span>`;
        } else if (msg.type === "token") {
          turn.answer += msg.text;
          answer.classList.add("streaming");
          answer.innerHTML = markdown(turn.answer);
        } else if (msg.type === "warning") {
          turn.unsupported = msg.numbers;
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
    answer.textContent = t("error", error.message);
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

// A new reading starts a new saved conversation; the old one stays under "Past readings".
function startNewReading() {
  history = [];
  chatId = newId();
  storeSet(KEY, "[]");
  renderAll();
  input.focus();
}
document.getElementById("reset").addEventListener("click", () => { if (!busy) startNewReading(); });

// ---------- Past readings (saved conversations) ----------

const drawer = document.getElementById("drawer");
const shade = document.getElementById("drawer-shade");
const chatList = document.getElementById("chat-list");

function openDrawer() {
  drawer.hidden = false;
  shade.hidden = false;
  document.getElementById("close-history").focus();
  loadChatList();
}
function closeDrawer() {
  drawer.hidden = true;
  shade.hidden = true;
}
document.getElementById("open-history").addEventListener("click", openDrawer);
document.getElementById("close-history").addEventListener("click", closeDrawer);
shade.addEventListener("click", closeDrawer);
document.addEventListener("keydown", e => { if (e.key === "Escape" && !drawer.hidden) closeDrawer(); });

function formatDate(ms) {
  if (!ms) return "";
  return new Date(ms).toLocaleString(uiLang === "vi" ? "vi-VN" : "en-GB",
    { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

async function loadChatList() {
  chatList.innerHTML = "";
  let chats = [];
  try {
    chats = await (await fetch("/api/chats")).json();
  } catch {
    chatList.append(el("li", "chat-empty", escape(t("historyError"))));
    return;
  }
  if (!chats.length) {
    chatList.append(el("li", "chat-empty", escape(t("historyEmpty"))));
    return;
  }
  for (const c of chats) {
    const li = el("li", "chat-item" + (c.id === chatId ? " current" : ""));
    const open = el("button", "link chat-open");
    open.type = "button";
    open.innerHTML = `<span class="chat-title">${escape(c.title || t("untitled"))}</span>`
      + `<span class="chat-meta">${escape(formatDate(c.updated))} ✦ ${escape(t("turns", c.turns))}`
      + (c.id === chatId ? ` ✦ ${escape(t("current"))}` : "") + "</span>";
    open.addEventListener("click", () => openChat(c.id));
    const del = el("button", "link chat-delete", "×");
    del.type = "button";
    del.title = t("deleteChat");
    del.setAttribute("aria-label", `${t("deleteChat")}: ${c.title || t("untitled")}`);
    del.addEventListener("click", () => deleteChat(c.id));
    li.append(open, del);
    chatList.append(li);
  }
}

async function openChat(id) {
  if (busy) return;
  try {
    const chat = await (await fetch(`/api/chats/${id}`)).json();
    history = chat.turns || [];
    chatId = id;
    storeSet(KEY, JSON.stringify(history));
    storeSet(ID_KEY, chatId);
    renderAll();
    closeDrawer();
    log.lastElementChild?.scrollIntoView({ block: "start" });
  } catch {
    chatList.prepend(el("li", "chat-empty", escape(t("historyError"))));
  }
}

async function deleteChat(id) {
  if (!confirm(t("confirmDelete"))) return;
  await fetch(`/api/chats/${id}`, { method: "DELETE" }).catch(() => {});
  if (id === chatId) startNewReading();
  loadChatList();
}

// Export the open conversation as a file the user keeps (Markdown or JSON).
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = el("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function exportName(ext) {
  return `reading-${new Date().toISOString().slice(0, 10)}.${ext}`;
}
document.getElementById("export-md").addEventListener("click", () => {
  const lines = [`# ${t("exportTitle")}`, "", formatDate(Date.now()), ""];
  history.forEach((h, i) => {
    lines.push(`## ${i + 1}. ${h.question}`, "", h.answer, "");
    const pages = [...new Set((h.sources || []).map(s => s.page || s.title).filter(Boolean))];
    if (pages.length) lines.push(`*${t("exportPages")}: ${pages.join(", ")}*`, "");
  });
  download(exportName("md"), lines.join("\n"), "text/markdown");
});
document.getElementById("export-json").addEventListener("click", () => {
  download(exportName("json"), JSON.stringify({ id: chatId, exported: new Date().toISOString(), turns: history }, null, 2),
    "application/json");
});

// ---------- Theme (Noir / Vellum) ----------

const themeButton = document.getElementById("theme");
function setTheme(name) {
  document.documentElement.dataset.theme = name;
  themeButton.textContent = name === "noir" ? "Vellum" : "Noir";
  storeSet("handbook-theme", name);
}
themeButton.addEventListener("click", () =>
  setTheme(document.documentElement.dataset.theme === "noir" ? "vellum" : "noir"));
setTheme(storeGet("handbook-theme") === "vellum" ? "vellum" : "noir");

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
let credit = null;

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
  deckCount.textContent = t("of", index + 1, deck.length);
  storeSet("handbook-card", card.id);
}

function shuffle() {
  if (showingBack) return;
  showingBack = true;
  artNumeral.textContent = "";
  artName.textContent = t("shufflingCard");
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
  if (document.activeElement === input || !drawer.hidden) return;
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
  const saved = storeGet("handbook-card");
  const found = deck.findIndex(c => c.id === saved);
  showCard(found >= 0 ? found : 0, true);
}

// CC BY 4.0: title, creator, source, licence, and a note that the images were adapted.
function renderCredit() {
  if (!credit) return;
  const c = credit;
  const box = document.getElementById("credit");
  box.innerHTML = `${escape(t("credit"))} ${escape((c.artist || "").split(" (")[0])}, 1909. ${escape(t("via"))} `
    + `<a href="${escape(c.source)}" target="_blank" rel="noopener">${escape(c.title)}</a>`
    + (c.author ? ` by ${escape(c.author)}` : "")
    + `, <a href="${escape(c.license_url)}" target="_blank" rel="noopener">${escape(c.license)}</a>. ${escape(t("resized"))}`;
  box.hidden = false;
}

startDeck();
fetch("/api/deck").then(r => r.json()).then(data => {
  if (!data.cards || !data.cards.length) return;
  deck = data.cards;
  if (data.back) backHtml = `<img src="${data.back}" alt="" draggable="false">`;
  startDeck();
  credit = data.credit || {};
  renderCredit();
}).catch(() => {});

// ---------- Rose petals drifting down the margins ----------

const PETAL = `<svg viewBox="0 0 24 30"><path d="M12 29 C3 23 0 13 3 6 C5 1 10 2 12 6 C14 1 20 1 22 6 C24 14 20 23 12 29 Z" fill="url(#rose-shade)" stroke="var(--rose-deep)" stroke-width="1"/><path d="M12 9 C11 15 11 21 12 27" fill="none" stroke="var(--rose-deep)" stroke-width="0.8" opacity="0.6"/></svg>`;
const petalBox = document.getElementById("petals");
// [left %, seconds to fall, delay, size px, opacity]: kept to the margins, away from the text
[[3, 26, 0, 18, 0.8], [33, 31, 9, 14, 0.55], [96, 24, 4, 20, 0.8], [88, 34, 15, 13, 0.5], [12, 29, 18, 15, 0.6], [62, 38, 24, 12, 0.35]]
  .forEach(([left, tFall, delay, size, o], i) => {
    const p = el("div", "petal", PETAL);
    p.style.left = left + "%";
    p.style.width = size + "px";
    p.style.setProperty("--t", tFall + "s");
    p.style.setProperty("--delay", -delay + "s");
    p.style.setProperty("--o", o);
    p.style.setProperty("--r0", i * 47 + "deg");
    p.style.setProperty("--dx", (i % 2 ? -1 : 1) * (30 + i * 9) + "px");
    petalBox.append(p);
  });

let info = null;
function renderMeta() {
  if (info) meta.textContent = t("meta", info.model, info.embedding, info.top_k);
}
fetch("/api/info").then(r => r.json()).then(data => { info = data; renderMeta(); }).catch(() => {});

applyLanguage();
if (history.length) save();   // a conversation from before saving existed gets saved too
input.focus();
