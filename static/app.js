// ── Constants ──────────────────────────────────────────────────────────────────
const MIN_BET = 300;
const MAX_BET = 10000;

const SUIT_SYMBOL = { S: '♠', H: '♥', D: '♦', C: '♣' };
const SUIT_COLOR  = { S: 'black', H: 'red', D: 'red', C: 'black' };

// ── State ──────────────────────────────────────────────────────────────────────
const state = {
  balance: 0,
  bets: [0],          // one entry per hand
  selectedHand: 0,    // 0-indexed: which hand is currently being configured
  numHands: 1,
  phase: 'setup',
};

// ── API helpers ────────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  return res.json();
}

// ── Session setup ──────────────────────────────────────────────────────────────
async function submitSession() {
  const name    = document.getElementById('player-name').value.trim();
  const capital = parseInt(document.getElementById('player-capital').value, 10);
  const errEl   = document.getElementById('session-error');

  if (!capital || capital < 300) {
    errEl.textContent = 'Capital must be at least $300.';
    return;
  }
  errEl.textContent = '';

  const data = await api('POST', '/session/new', { player_name: name, capital });
  if (data.error) { errEl.textContent = data.error; return; }

  state.balance = data.capital;
  renderBalance(state.balance);
  document.getElementById('session-overlay').classList.add('hidden');
  enterBettingPhase();
}

function showSessionOverlay() {
  document.getElementById('player-name').value = '';
  document.getElementById('player-capital').value = '';
  document.getElementById('session-error').textContent = '';
  document.getElementById('session-overlay').classList.remove('hidden');
}

// ── Betting phase ──────────────────────────────────────────────────────────────
function enterBettingPhase() {
  state.phase = 'betting';
  state.numHands = 1;
  state.selectedHand = 0;
  state.bets = [0];
  showPhase('betting');
  clearBetError();
  buildCountBtns();
  buildHandSelBtns();
  updateBetDisplay();
  clearTable();
  document.getElementById('manual-bet').value = '';
}

// Build the 1–6 count buttons
function buildCountBtns() {
  const container = document.getElementById('hands-count-btns');
  container.innerHTML = '';
  for (let i = 1; i <= 6; i++) {
    const btn = document.createElement('button');
    btn.className = 'hands-btn' + (i === 1 ? ' selected' : '');
    btn.textContent = i;
    btn.onclick = () => selectNumHands(i);
    container.appendChild(btn);
  }
}

function selectNumHands(n) {
  state.numHands = n;
  state.bets = Array(n).fill(0);
  state.selectedHand = 0;

  document.querySelectorAll('#hands-count-btns .hands-btn').forEach((b, i) => {
    b.classList.toggle('selected', i + 1 === n);
  });

  const selRow = document.getElementById('hand-sel-row');
  selRow.style.display = n > 1 ? 'flex' : 'none';

  buildHandSelBtns();
  updateBetDisplay();
  clearBetError();
}

// Build the H1…HN per-hand selector buttons (only when numHands > 1)
function buildHandSelBtns() {
  const container = document.getElementById('hand-sel-btns');
  container.innerHTML = '';
  if (state.numHands <= 1) return;

  for (let i = 0; i < state.numHands; i++) {
    const btn = document.createElement('button');
    btn.className = 'hand-sel-btn' + (i === state.selectedHand ? ' selected' : '');
    btn.dataset.idx = i;
    btn.innerHTML =
      `<span class="hs-label">H${i + 1}</span>` +
      `<span class="hs-bet" id="hs-bet-${i}">$${state.bets[i].toLocaleString()}</span>`;
    btn.onclick = () => selectBettingHand(i);
    container.appendChild(btn);
  }
}

function selectBettingHand(i) {
  state.selectedHand = i;
  document.querySelectorAll('.hand-sel-btn').forEach((b, idx) => {
    b.classList.toggle('selected', idx === i);
  });
  updateBetDisplay();
  clearBetError();
}

// ── Bet manipulation ───────────────────────────────────────────────────────────
function addBet(amount) {
  state.bets[state.selectedHand] += amount;
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
}

function clearBet() {
  state.bets[state.selectedHand] = 0;
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
}

function updateBetDisplay() {
  document.getElementById('bet-display').textContent =
    '$' + state.bets[state.selectedHand].toLocaleString();
}

// Re-render just the bet amount in a hand-sel-btn
function refreshHandSelBet(i) {
  const el = document.getElementById(`hs-bet-${i}`);
  if (el) el.textContent = '$' + state.bets[i].toLocaleString();
}

// ── Keyboard bet input ─────────────────────────────────────────────────────────
function confirmManualBet() {
  const input = document.getElementById('manual-bet');
  const raw = input.value.replace(/\D/g, '');  // strip non-digits
  if (!raw) return;

  const val = parseInt(raw, 10);
  if (val < MIN_BET) {
    showBetError(`Minimum input is $${MIN_BET.toLocaleString()}.`);
    return;
  }
  if (val > MAX_BET) {
    showBetError(`Maximum input is $${MAX_BET.toLocaleString()}.`);
    return;
  }
  if (val % 100 !== 0) {
    showBetError('Amount must be a multiple of $100.');
    return;
  }

  clearBetError();
  state.bets[state.selectedHand] += val;
  input.value = '';
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
}

function showBetError(msg) {
  document.getElementById('bet-error').textContent = msg;
}
function clearBetError() {
  document.getElementById('bet-error').textContent = '';
}

// ── Deal ───────────────────────────────────────────────────────────────────────
async function deal() {
  clearBetError();

  // Validate each hand's bet
  for (let i = 0; i < state.numHands; i++) {
    const b = state.bets[i];
    if (b < MIN_BET) {
      showBetError(`Hand ${i + 1} needs at least $${MIN_BET.toLocaleString()}.`);
      if (state.numHands > 1) selectBettingHand(i);
      return;
    }
    if (b > MAX_BET) {
      showBetError(`Hand ${i + 1} bet exceeds max $${MAX_BET.toLocaleString()}.`);
      return;
    }
    if (b % 100 !== 0) {
      showBetError(`Hand ${i + 1} bet must be a multiple of $100.`);
      return;
    }
  }

  const totalNeeded = state.bets.reduce((a, b) => a + b, 0);
  if (totalNeeded > state.balance) {
    showBetError('Total bets exceed your balance.');
    return;
  }

  const data = await api('POST', '/round/start', { bets: state.bets });
  if (data.error) { showBetError(data.error); return; }

  updateUI(data);
}

// ── Early pay ──────────────────────────────────────────────────────────────────
async function doEarlyPay(choice) {
  const data = await api('POST', '/round/early_pay', { choice });
  updateUI(data);
}

// ── Playing moves ──────────────────────────────────────────────────────────────
async function doHit()      { updateUI(await api('POST', '/round/hit')); }
async function doStand()    { updateUI(await api('POST', '/round/stand')); }
async function doDouble()   { updateUI(await api('POST', '/round/double')); }
async function doSplit()    { updateUI(await api('POST', '/round/split')); }
async function doSurrender(){ updateUI(await api('POST', '/round/surrender')); }

// ── Phase transitions ──────────────────────────────────────────────────────────
function nextRound()  { enterBettingPhase(); }
function newSession() { showSessionOverlay(); }

// ── Master UI update ───────────────────────────────────────────────────────────
function updateUI(data) {
  if (!data || data.error) { showMsg(data?.error || 'Server error'); return; }

  state.balance = data.capital;
  state.phase   = data.phase;
  renderBalance(data.capital);
  renderDealer(data.dealer);
  renderHands(data.hands, data.phase);

  if (data.phase === 'playing') {
    showPhase('playing');
    setPlayButtons(data.moves || []);
  } else if (data.phase === 'early_pay') {
    showPhase('early_pay');
    renderEarlyPayInfo(data.early_pay_hand, data.early_pay_chips);
  } else if (data.phase === 'settled') {
    showPhase('settled');
    flashRoundResult(data.hands);
  }
}

// ── Rendering ──────────────────────────────────────────────────────────────────
function renderBalance(amount) {
  document.getElementById('balance').textContent = '$' + amount.toLocaleString();
}

function renderDealer(dealer) {
  const hand = document.getElementById('dealer-hand');
  const val  = document.getElementById('dealer-val');
  hand.innerHTML = '';

  dealer.cards.forEach(c => hand.appendChild(makeCardEl(c.rank, c.suit)));

  if (dealer.face_down) {
    const hidden = document.createElement('div');
    hidden.className = 'card face-down';
    hand.appendChild(hidden);
  }

  val.textContent = dealer.value_text;
}

function renderHands(hands, phase) {
  const row = document.getElementById('hands-row');
  row.innerHTML = '';

  for (const hand of hands) {
    const group = document.createElement('div');
    group.className = 'hand-group';

    const groupLabel = document.createElement('div');
    groupLabel.className = 'hand-group-label';
    groupLabel.textContent = hand.label;
    group.appendChild(groupLabel);

    const branchesRow = document.createElement('div');
    branchesRow.className = 'branches-row';

    for (const branch of hand.branches) {
      branchesRow.appendChild(makeBranchEl(branch, phase));
    }

    group.appendChild(branchesRow);
    row.appendChild(group);
  }
}

function makeBranchEl(branch, phase) {
  const el = document.createElement('div');
  const oc = branch.outcome;
  let stateClass = '';

  if (branch.active) {
    stateClass = 'active';
  } else if (oc === 'won' || oc === 'bj' || oc === 'early_pay') {
    stateClass = 'won';
  } else if (oc === 'bust' || oc === 'lost') {
    stateClass = 'bust';
  } else if (oc === 'push' || oc === 'surrendered') {
    stateClass = 'push';
  } else if (oc === 'bj_pending') {
    stateClass = 'active';   // highlight the hand needing a decision
  } else if (branch.bust) {
    stateClass = 'bust';
  }

  el.className = `hand-card ${stateClass}`;

  // Label override for bj_pending
  if (oc === 'bj_pending') {
    const tag = document.createElement('div');
    tag.style.cssText =
      'position:absolute;top:-10px;font-size:0.55rem;letter-spacing:0.12em;color:var(--gold);' +
      'background:var(--felt);padding:1px 8px;border-radius:10px;border:1px solid var(--gold-dim);';
    tag.textContent = 'DECIDE';
    el.appendChild(tag);
  }

  // Branch label
  const lbl = document.createElement('div');
  lbl.className = 'hand-label';
  lbl.textContent = `Branch ${branch.id}`;
  el.appendChild(lbl);

  // Cards
  const cardsRow = document.createElement('div');
  cardsRow.className = 'hand-cards-row';
  branch.cards.forEach(c => cardsRow.appendChild(makeCardEl(c.rank, c.suit)));
  el.appendChild(cardsRow);

  // Info row
  const info = document.createElement('div');
  info.className = 'hand-info';

  const valEl = document.createElement('div');
  valEl.className = 'hand-value';
  const vt = branch.value_text;
  if (vt === 'Busted' || branch.bust)  valEl.classList.add('bust-val');
  if (vt === 'Blackjack')              valEl.classList.add('bj-val');
  valEl.textContent = vt;
  info.appendChild(valEl);

  const betEl = document.createElement('div');
  betEl.className = 'bet-badge';
  betEl.textContent = '$' + branch.bet.toLocaleString();
  info.appendChild(betEl);

  if (branch.profit !== null && branch.profit !== undefined) {
    const pEl = document.createElement('div');
    const sign = branch.profit >= 0 ? '+' : '';
    pEl.className = 'profit-badge ' +
      (branch.profit > 0 ? 'win' : branch.profit < 0 ? 'lose' : 'push');
    pEl.textContent = sign + '$' + Math.abs(branch.profit).toLocaleString();
    info.appendChild(pEl);
  }

  el.appendChild(info);
  return el;
}

function makeCardEl(rank, suit) {
  const el = document.createElement('div');
  el.className = `card ${SUIT_COLOR[suit]}`;
  el.innerHTML =
    `<div class="card-rank">${rank}</div>` +
    `<div class="card-suit">${SUIT_SYMBOL[suit]}</div>` +
    `<div class="card-rank-bot">${rank}</div>`;
  return el;
}

function renderEarlyPayInfo(handId, chips) {
  const earlyPay  = chips;         // 1× profit (same as bet)
  const waitPay   = Math.floor(chips * 1.5);  // 1.5× potential profit

  document.getElementById('early-pay-info').innerHTML =
    `Hand ${handId} has <strong>Blackjack!</strong> ` +
    `Dealer may also have Blackjack.<br>` +
    `Take <strong>+$${earlyPay.toLocaleString()}</strong> now, ` +
    `or wait for <strong>+$${waitPay.toLocaleString()}</strong> (or push)?`;

  document.getElementById('btn-early-take').textContent =
    `Take Early Pay (+$${earlyPay.toLocaleString()})`;
  document.getElementById('btn-early-wait').textContent =
    `Wait for ×1.5 (+$${waitPay.toLocaleString()})`;
}

// ── Phase switching ────────────────────────────────────────────────────────────
function showPhase(phase) {
  const phases = ['betting', 'early-pay', 'playing', 'settled'];
  for (const p of phases) {
    document.getElementById(`phase-${p}`).style.display = p === phase ? 'flex' : 'none';
  }
}

function setPlayButtons(moves) {
  document.getElementById('btn-hit').disabled     = !moves.includes('hit');
  document.getElementById('btn-stand').disabled   = !moves.includes('stand');
  document.getElementById('btn-double').disabled  = !moves.includes('double');
  document.getElementById('btn-split').disabled   = !moves.includes('split');
  document.getElementById('btn-sur').disabled     = !moves.includes('surrender');
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function clearTable() {
  document.getElementById('dealer-hand').innerHTML = '';
  document.getElementById('dealer-val').textContent = '—';
  document.getElementById('hands-row').innerHTML = '';
}

function showMsg(text) {
  const el = document.getElementById('msg-overlay');
  el.textContent = text;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2400);
}

function flashRoundResult(hands) {
  let totalProfit = 0;
  for (const hand of hands)
    for (const branch of hand.branches)
      if (branch.profit != null) totalProfit += branch.profit;

  if (totalProfit > 0)      showMsg(`+$${totalProfit.toLocaleString()} 🎉`);
  else if (totalProfit < 0) showMsg(`-$${Math.abs(totalProfit).toLocaleString()}`);
  else                      showMsg('Push — no change');
}

// ── Income modal ───────────────────────────────────────────────────────────────
async function showIncome() {
  const data = await api('GET', '/income');
  const tbl  = document.getElementById('income-table-body');

  tbl.innerHTML = '';
  if (!data.length) {
    tbl.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--ivory-dim)">No rounds played yet.</td></tr>';
  } else {
    for (const row of data) {
      const tr = document.createElement('tr');
      const cls = row.Profit > 0 ? 'profit-pos' : row.Profit < 0 ? 'profit-neg' : '';
      const sign = row.Profit >= 0 ? '+' : '';
      tr.innerHTML =
        `<td>${row.Round}</td>` +
        `<td class="${cls}">${sign}$${row.Profit.toLocaleString()}</td>` +
        `<td>$${row.Capital.toLocaleString()}</td>`;
      tbl.appendChild(tr);
    }
  }

  document.getElementById('income-modal').classList.remove('hidden');
}

function hideIncome() {
  document.getElementById('income-modal').classList.add('hidden');
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // Enter on manual-bet input
  if (e.key === 'Enter' && document.activeElement.id === 'manual-bet') {
    confirmManualBet();
    return;
  }
  // Allow only digit / backspace / arrow on manual-bet input to prevent decimals
  if (document.activeElement.id === 'manual-bet') {
    if (e.key === '.' || e.key === '-' || e.key === 'e') e.preventDefault();
  }
});

// Strip non-integer chars on input event
document.addEventListener('DOMContentLoaded', () => {
  const inp = document.getElementById('manual-bet');
  if (inp) {
    inp.addEventListener('input', function () {
      const cleaned = this.value.replace(/[^0-9]/g, '');
      if (this.value !== cleaned) this.value = cleaned;
    });
  }
});

// ── Init ───────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  showPhase('betting');  // All panels start hidden; session overlay shows first
});
