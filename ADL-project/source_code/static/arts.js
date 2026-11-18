// Six built-in tarot cards, drawn as SVG in code. They are only used until the
// 78-card deck exported from Figma is placed in static/tarot/ (see README there).
// Every card shares one frame (numeral at the top, title at the bottom) and has its own
// illustration in the window. The card faces keep the same colours in both page themes,
// like a real printed deck.

const C = {
  paper: "var(--card-paper)",
  ink: "var(--card-ink)",
  gold: "var(--card-gold)",
  red: "var(--card-red)",
  blue: "var(--card-blue)",
};
const W = { x: 30, y: 64, w: 240, h: 360 };   // illustration window
const CX = 150;

function defs(extra = "") {
  return `<defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="var(--card-sky-top)"/>
      <stop offset="1" stop-color="var(--card-sky-bottom)"/>
    </linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="var(--card-blue)"/>
      <stop offset="1" stop-color="var(--card-sky-top)"/>
    </linearGradient>
    <radialGradient id="aura">
      <stop offset="0" stop-color="var(--card-gold)" stop-opacity="0.75"/>
      <stop offset="1" stop-color="var(--card-gold)" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="window"><rect x="${W.x}" y="${W.y}" width="${W.w}" height="${W.h}" rx="4"/></clipPath>
    ${extra}
  </defs>`;
}

function star(cx, cy, r, points = 8, inner = 0.42) {
  let d = "";
  for (let i = 0; i < points * 2; i++) {
    const a = (i * Math.PI) / points - Math.PI / 2;
    const rr = i % 2 ? r * inner : r;
    d += `${i ? "L" : "M"}${(cx + rr * Math.cos(a)).toFixed(1)} ${(cy + rr * Math.sin(a)).toFixed(1)} `;
  }
  return d + "Z";
}

function rand(seed) {
  return () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
}

function sprinkle(seed, n, yMax = 230) {
  const r = rand(seed);
  let s = "";
  for (let i = 0; i < n; i++) {
    s += `<circle class="twinkle" style="animation-delay:${(r() * 4).toFixed(2)}s" cx="${(W.x + 8 + r() * (W.w - 16)).toFixed(1)}" cy="${(W.y + 8 + r() * (yMax - W.y)).toFixed(1)}" r="${(0.6 + r() * 1.3).toFixed(2)}" fill="${C.paper}"/>`;
  }
  return s;
}

// The shared frame. `art` is drawn inside the window.
function card(numeral, title, art, extraDefs = "") {
  const corner = (x, y) => `<path d="${star(x, y, 6, 4, 0.35)}" fill="${C.gold}"/>`;
  return `<svg viewBox="0 0 300 500" role="img" aria-label="${numeral} ${title}">
    ${defs(extraDefs)}
    <rect x="3" y="3" width="294" height="494" rx="16" fill="${C.paper}"/>
    <rect x="3" y="3" width="294" height="494" rx="16" fill="none" stroke="${C.gold}" stroke-width="3"/>
    <rect x="14" y="14" width="272" height="472" rx="9" fill="none" stroke="${C.ink}" stroke-width="1.2"/>
    ${corner(26, 26)}${corner(274, 26)}${corner(26, 474)}${corner(274, 474)}
    <text x="150" y="47" text-anchor="middle" class="card-numeral" fill="${C.ink}">${numeral}</text>
    <g clip-path="url(#window)">
      <rect x="${W.x}" y="${W.y}" width="${W.w}" height="${W.h}" fill="url(#sky)"/>
      ${art}
    </g>
    <rect x="${W.x}" y="${W.y}" width="${W.w}" height="${W.h}" rx="4" fill="none" stroke="${C.ink}" stroke-width="1.6"/>
    <text x="150" y="461" text-anchor="middle" class="card-title" fill="${C.ink}">${title}</text>
  </svg>`;
}

// ---------- II  The High Priestess: an open book between two pillars ----------
function priestess() {
  let s = sprinkle(2, 26, 200);
  // veil of pomegranates behind the book
  s += `<rect x="86" y="150" width="128" height="200" fill="${C.red}" opacity="0.35"/>`;
  for (let y = 162; y < 345; y += 26) {
    for (let x = 98 + ((y / 26) % 2) * 13; x < 210; x += 26) {
      s += `<circle cx="${x}" cy="${y}" r="5" fill="${C.red}"/><path d="M${x - 2} ${y - 5} l2 -3 l2 3" stroke="${C.gold}" stroke-width="1" fill="none"/>`;
    }
  }
  // pillars: one dark, one light
  for (const [x, fill] of [[46, C.ink], [222, C.paper]]) {
    s += `<rect x="${x}" y="150" width="32" height="274" fill="${fill}" stroke="${C.gold}" stroke-width="1.5"/>
          <rect x="${x - 6}" y="138" width="44" height="14" fill="${C.gold}"/>
          <rect x="${x - 6}" y="412" width="44" height="12" fill="${C.gold}"/>`;
  }
  // crescent above
  s += `<circle cx="150" cy="108" r="40" fill="url(#aura)"/>
        <path d="M168 84 A28 28 0 1 0 168 132 A22 22 0 1 1 168 84 Z" fill="${C.gold}" filter="url(#glow)"/>`;
  // the open book (the handbook)
  s += `<ellipse cx="150" cy="335" rx="80" ry="40" fill="url(#aura)"/>
        <path d="M150 318 Q112 292 72 304 L72 368 Q112 356 150 384 Z" fill="${C.paper}" stroke="${C.ink}" stroke-width="1.4"/>
        <path d="M150 318 Q188 292 228 304 L228 368 Q188 356 150 384 Z" fill="${C.paper}" stroke="${C.ink}" stroke-width="1.4"/>`;
  for (let i = 0; i < 5; i++) {
    const y = 318 + i * 11;
    s += `<path d="M84 ${y} Q114 ${y - 8} 140 ${y + 6}" stroke="${C.ink}" stroke-width="0.8" fill="none" opacity="0.55"/>
          <path d="M216 ${y} Q186 ${y - 8} 160 ${y + 6}" stroke="${C.ink}" stroke-width="0.8" fill="none" opacity="0.55"/>`;
  }
  s += `<path d="M150 318 V384" stroke="${C.ink}" stroke-width="1.4"/>`;
  return card("II", "THE HIGH PRIESTESS", s);
}

// ---------- XVII  The Star: one great star over still water ----------
function theStar() {
  let s = sprinkle(17, 30, 300);
  s += `<circle cx="150" cy="160" r="80" fill="url(#aura)"/>
        <path class="pulse" d="${star(150, 160, 52, 8, 0.38)}" fill="${C.gold}" filter="url(#glow)"/>
        <path d="${star(150, 160, 22, 8, 0.45)}" fill="${C.paper}"/>`;
  const small = [[70, 100], [230, 100], [56, 172], [244, 172], [84, 236], [216, 236], [150, 78]];
  for (const [x, y] of small) s += `<path class="twinkle" d="${star(x, y, 9, 8, 0.38)}" fill="${C.paper}"/>`;
  // hills and water
  s += `<path d="M30 318 Q90 290 150 312 Q210 290 270 318 V424 H30 Z" fill="${C.ink}" opacity="0.65"/>
        <rect x="30" y="336" width="240" height="88" fill="url(#water)"/>`;
  for (let y = 346; y < 424; y += 12) {
    s += `<path d="M30 ${y} q15 -5 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0" stroke="${C.paper}" stroke-width="0.8" fill="none" opacity="0.35"/>`;
  }
  // reflection of the star
  for (let i = 0; i < 6; i++) {
    s += `<rect x="${140 + (i % 3) * 7}" y="${344 + i * 12}" width="${22 - i * 3}" height="2" fill="${C.gold}" opacity="${0.8 - i * 0.12}"/>`;
  }
  return card("XVII", "THE STAR", s);
}

// ---------- XVIII  The Moon: two towers, a winding path, falling dew ----------
function theMoon() {
  let s = sprinkle(18, 18, 200);
  s += `<circle cx="150" cy="140" r="90" fill="url(#aura)" opacity="0.8"/>`;
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2, r1 = 60, r2 = i % 2 ? 74 : 84;
    s += `<path d="M${150 + r1 * Math.cos(a)} ${140 + r1 * Math.sin(a)} L${150 + r2 * Math.cos(a)} ${140 + r2 * Math.sin(a)}" stroke="${C.gold}" stroke-width="${i % 2 ? 1.5 : 2.5}"/>`;
  }
  s += `<circle cx="150" cy="140" r="52" fill="${C.gold}" filter="url(#glow)"/>
        <path d="M150 88 A52 52 0 0 1 150 192 A38 52 0 0 0 150 88 Z" fill="${C.paper}" opacity="0.85"/>`;
  // dew drops
  const r = rand(5);
  for (let i = 0; i < 9; i++) {
    const x = 70 + r() * 160, y = 210 + r() * 50;
    s += `<path class="drop" style="animation-delay:${(r() * 3).toFixed(2)}s" d="M${x} ${y} q4 6 0 9 q-4 -3 0 -9 Z" fill="${C.gold}"/>`;
  }
  // towers
  for (const x of [40, 222]) {
    s += `<path d="M${x} 424 V262 h38 V424 Z" fill="${C.ink}"/>
          <path d="M${x - 3} 262 h44 v-10 h-6 v6 h-6 v-6 h-8 v6 h-6 v-6 h-6 v6 h-6 v-6 h-6 Z" fill="${C.ink}"/>
          <path d="M${x + 14} 300 v-8 a5 5 0 0 1 10 0 v8 Z" fill="${C.gold}" class="pulse"/>`;
  }
  // land, path and pool
  s += `<path d="M30 330 Q150 300 270 330 V424 H30 Z" fill="var(--card-sky-top)" opacity="0.7"/>
        <path d="M150 304 C135 330 172 345 150 365 C128 385 165 400 150 424" stroke="${C.paper}" stroke-width="7" fill="none" opacity="0.8"/>
        <ellipse cx="150" cy="420" rx="110" ry="22" fill="url(#water)"/>`;
  return card("XVIII", "THE MOON", s);
}

// ---------- X  Wheel of Fortune ----------
function wheel() {
  let s = sprinkle(10, 30, 420);
  // clouds in the four corners
  const cloud = (x, y) => `<g fill="${C.paper}" opacity="0.85"><circle cx="${x}" cy="${y}" r="14"/><circle cx="${x + 16}" cy="${y - 4}" r="12"/><circle cx="${x - 14}" cy="${y + 4}" r="10"/></g>`;
  s += cloud(52, 92) + cloud(248, 92) + cloud(52, 404) + cloud(248, 404);
  s += `<circle cx="150" cy="244" r="120" fill="url(#aura)"/>
        <g class="spin" style="transform-origin:150px 244px">
        <circle cx="150" cy="244" r="96" fill="${C.blue}" stroke="${C.gold}" stroke-width="3"/>
        <circle cx="150" cy="244" r="80" fill="none" stroke="${C.gold}" stroke-width="1.2"/>
        <circle cx="150" cy="244" r="50" fill="${C.ink}" stroke="${C.gold}" stroke-width="2"/>`;
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    s += `<path d="M${150 + 22 * Math.cos(a)} ${244 + 22 * Math.sin(a)} L${150 + 80 * Math.cos(a)} ${244 + 80 * Math.sin(a)}" stroke="${C.gold}" stroke-width="2"/>`;
    // alternating symbols on the rim: star, circle
    const x = 150 + 88 * Math.cos(a + Math.PI / 8), y = 244 + 88 * Math.sin(a + Math.PI / 8);
    s += i % 2
      ? `<circle cx="${x}" cy="${y}" r="4" fill="${C.paper}"/>`
      : `<path d="${star(x, y, 6, 4, 0.4)}" fill="${C.paper}"/>`;
  }
  s += `<circle cx="150" cy="244" r="22" fill="${C.gold}" filter="url(#glow)"/>
        <path d="${star(150, 244, 14, 8, 0.4)}" fill="${C.paper}"/></g>`;
  return card("X", "WHEEL OF FORTUNE", s);
}

// ---------- XIX  The Sun: a radiant sun over a garden wall of sunflowers ----------
function theSun() {
  let s = `<rect x="30" y="64" width="240" height="360" fill="var(--card-day)"/>`;
  s += `<g class="spin-slow" style="transform-origin:150px 160px">`;
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2;
    if (i % 2) {
      s += `<path d="M${150 + 58 * Math.cos(a - 0.08)} ${160 + 58 * Math.sin(a - 0.08)} L${150 + 104 * Math.cos(a)} ${160 + 104 * Math.sin(a)} L${150 + 58 * Math.cos(a + 0.08)} ${160 + 58 * Math.sin(a + 0.08)} Z" fill="${C.gold}"/>`;
    } else {
      s += `<path d="M${150 + 58 * Math.cos(a - 0.05)} ${160 + 58 * Math.sin(a - 0.05)} L${150 + 86 * Math.cos(a)} ${160 + 86 * Math.sin(a)} L${150 + 58 * Math.cos(a + 0.05)} ${160 + 58 * Math.sin(a + 0.05)} Z" fill="${C.red}" opacity="0.85"/>`;
    }
  }
  s += `</g><circle cx="150" cy="160" r="54" fill="${C.gold}" filter="url(#glow)"/>
        <circle cx="150" cy="160" r="40" fill="${C.paper}" opacity="0.35"/>`;
  // garden wall
  s += `<rect x="30" y="330" width="240" height="94" fill="${C.paper}" stroke="${C.ink}" stroke-width="1"/>`;
  for (let y = 330; y < 424; y += 16) {
    s += `<path d="M30 ${y} H270" stroke="${C.ink}" stroke-width="0.7" opacity="0.5"/>`;
    for (let x = 30 + ((y / 16) % 2) * 20; x < 270; x += 40) s += `<path d="M${x} ${y} v16" stroke="${C.ink}" stroke-width="0.7" opacity="0.5"/>`;
  }
  // sunflowers on the wall
  for (const [x, h] of [[66, 46], [118, 60], [182, 54], [234, 42]]) {
    s += `<path d="M${x} 330 V${330 - h}" stroke="var(--card-green)" stroke-width="3"/>`;
    for (let p = 0; p < 10; p++) {
      s += `<ellipse cx="${x}" cy="${330 - h - 11}" rx="4" ry="11" fill="${C.gold}" transform="rotate(${p * 36} ${x} ${330 - h})"/>`;
    }
    s += `<circle cx="${x}" cy="${330 - h}" r="7" fill="${C.ink}"/>`;
  }
  return card("XIX", "THE SUN", s);
}

// ---------- XXI  The World: a laurel wreath around a small globe ----------
function theWorld() {
  let s = sprinkle(21, 36, 420);
  s += `<ellipse cx="150" cy="244" rx="100" ry="140" fill="url(#aura)"/>`;
  // wreath: leaves along an ellipse
  for (let i = 0; i < 44; i++) {
    const t = (i / 44) * Math.PI * 2;
    const x = 150 + 72 * Math.cos(t), y = 244 + 118 * Math.sin(t);
    const deg = (Math.atan2(118 * Math.cos(t), -72 * Math.sin(t)) * 180) / Math.PI;
    s += `<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="9" ry="4" fill="var(--card-green)" stroke="${C.gold}" stroke-width="0.6" transform="rotate(${(deg + (i % 2 ? 30 : -30)).toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})"/>`;
  }
  // ribbons crossing at top and bottom
  for (const y of [126, 362]) {
    s += `<path d="M138 ${y - 8} L162 ${y + 8} M162 ${y - 8} L138 ${y + 8}" stroke="${C.red}" stroke-width="5" stroke-linecap="round"/>`;
  }
  // globe
  s += `<circle cx="150" cy="244" r="36" fill="${C.blue}" stroke="${C.gold}" stroke-width="1.6"/>
        <g class="spin-slow" style="transform-origin:150px 244px" fill="none" stroke="${C.gold}" stroke-width="0.9">
          <ellipse cx="150" cy="244" rx="14" ry="36"/><ellipse cx="150" cy="244" rx="28" ry="36"/>
        </g>
        <path d="M114 244 H186 M118 226 H182 M118 262 H182" stroke="${C.gold}" stroke-width="0.9"/>`;
  // four corner emblems: star, crescent, sun, diamond
  s += `<path d="${star(56, 92, 10, 8, 0.4)}" fill="${C.gold}"/>
        <path d="M252 82 A12 12 0 1 0 252 104 A9 9 0 1 1 252 82 Z" fill="${C.gold}"/>
        <circle cx="56" cy="396" r="9" fill="${C.gold}"/><circle cx="56" cy="396" r="14" fill="none" stroke="${C.gold}" stroke-dasharray="2 3"/>
        <path d="M244 384 L256 396 L244 408 L232 396 Z" fill="${C.gold}"/>`;
  return card("XXI", "THE WORLD", s);
}

// ---------- The back of every card ----------
function cardBack() {
  let s = `<svg viewBox="0 0 300 500" role="img" aria-label="Back of a tarot card">${defs()}
    <rect x="3" y="3" width="294" height="494" rx="16" fill="var(--card-back)"/>
    <rect x="3" y="3" width="294" height="494" rx="16" fill="none" stroke="${C.gold}" stroke-width="3"/>
    <rect x="16" y="16" width="268" height="468" rx="9" fill="none" stroke="${C.gold}" stroke-width="1"/>
    <rect x="24" y="24" width="252" height="452" rx="6" fill="none" stroke="${C.gold}" stroke-width="0.6" stroke-dasharray="2 4"/>`;
  const r = rand(77);
  for (let i = 0; i < 46; i++) {
    s += `<circle cx="${(34 + r() * 232).toFixed(1)}" cy="${(34 + r() * 432).toFixed(1)}" r="${(0.6 + r()).toFixed(2)}" fill="${C.gold}" opacity="0.7"/>`;
  }
  s += `<circle cx="150" cy="250" r="96" fill="url(#aura)" opacity="0.6"/>
    <g class="spin" style="transform-origin:150px 250px">
      <circle cx="150" cy="250" r="78" fill="none" stroke="${C.gold}" stroke-width="1.4"/>
      <path d="${star(150, 250, 76, 12, 0.72)}" fill="none" stroke="${C.gold}" stroke-width="1"/>
      <path d="${star(150, 250, 58, 8, 0.5)}" fill="none" stroke="${C.gold}" stroke-width="1.2"/>
    </g>
    <circle cx="150" cy="250" r="30" fill="${C.gold}" filter="url(#glow)"/>
    <path d="M160 228 A22 22 0 1 0 160 272 A17 17 0 1 1 160 228 Z" fill="var(--card-back)"/>
    <path d="${star(150, 110, 10, 4, 0.35)}" fill="${C.gold}"/>
    <path d="${star(150, 390, 10, 4, 0.35)}" fill="${C.gold}"/>
  </svg>`;
  return s;
}

window.CARD_BACK = cardBack;
window.ARTS = [
  { id: "priestess", numeral: "II", name: "The High Priestess", svg: priestess },
  { id: "wheel", numeral: "X", name: "Wheel of Fortune", svg: wheel },
  { id: "star", numeral: "XVII", name: "The Star", svg: theStar },
  { id: "moon", numeral: "XVIII", name: "The Moon", svg: theMoon },
  { id: "sun", numeral: "XIX", name: "The Sun", svg: theSun },
  { id: "world", numeral: "XXI", name: "The World", svg: theWorld },
];
