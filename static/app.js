// ── Constants ──────────────────────────────────────────────────────────────────
const MIN_BET = 300;
const MAX_BET = 10000;
const MAX_NAME_LEN = 50;

const SUIT_SYMBOL = { S: '♠', H: '♥', D: '♦', C: '♣' };
const SUIT_COLOR  = { S: 'black', H: 'red', D: 'red', C: 'black' };

// ── State ──────────────────────────────────────────────────────────────────────
const state = {
  balance: 0,
  bets: [0],          // one entry per hand
  selectedHand: 0,    // 0-indexed: which hand is currently being configured
  numHands: 1,
  phase: 'setup',
  activeBet: 0,       // bet on the currently active branch (for optimistic Double/Split)
  sessionId: null,
};

// ── API helpers ────────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const url = state.sessionId ? `${path}?session_id=${state.sessionId}` : path;
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

// ── Session setup ──────────────────────────────────────────────────────────────
async function submitSession() {
  const name    = document.getElementById('player-name').value.trim();
  const capital = parseInt(document.getElementById('player-capital').value, 10);
  const errEl   = document.getElementById('session-error');

  if (name.length > MAX_NAME_LEN) {
    errEl.textContent = `Name must be ${MAX_NAME_LEN} characters or fewer.`;
    return;
  }
  if (!capital || capital < MIN_BET) {
    errEl.textContent = `Capital must be at least ${MIN_BET}.`;
    return;
  }
  errEl.textContent = '';

  const data = await api('POST', '/session/new', { player_name: name, capital });
  if (data.error) { errEl.textContent = data.error; return; }

  state.sessionId = data.session_id;
  state.balance = data.capital;
  renderBalance(state.balance);
  document.getElementById('session-overlay').classList.add('hidden');
  enterBettingPhase();
}

function showSessionOverlay() {
  document.getElementById('gameover-modal').style.display = 'none';
  document.getElementById('player-name').value = '';
  document.getElementById('player-capital').value = '';
  document.getElementById('session-error').textContent = '';
  document.getElementById('session-overlay').classList.remove('hidden');
}

['player-name', 'player-capital'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', e => {
    if (e.key === 'Enter') submitSession();
  });
});

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
  renderBalance(state.balance);  // bets reset to 0; restore full balance
  clearTable();
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
  renderBettingBalance();
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
  renderBettingBalance();
  clearBetError();
}

// ── Bet manipulation ───────────────────────────────────────────────────────────
function addBet(amount) {
  state.bets[state.selectedHand] += amount;
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
  renderBettingBalance();
}

function clearBet() {
  state.bets[state.selectedHand] = 0;
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
  renderBettingBalance();
}

function updateBetDisplay() {
  document.getElementById('bet-display').value =
    '$' + state.bets[state.selectedHand].toLocaleString();
}

// Re-render just the bet amount in a hand-sel-btn
function refreshHandSelBet(i) {
  const el = document.getElementById(`hs-bet-${i}`);
  if (el) el.textContent = '$' + state.bets[i].toLocaleString();
}

// ── Inline bet input commit ────────────────────────────────────────────────────
function commitBetInput() {
  const raw = document.getElementById('bet-display').value.replace(/\D/g, '');
  if (!raw) { updateBetDisplay(); return; }
  const val = parseInt(raw, 10);
  if (val < MIN_BET) {
    showBetError(`Minimum bet is $${MIN_BET.toLocaleString()}.`);
    updateBetDisplay();
    return;
  }
  if (val > MAX_BET) {
    showBetError(`Maximum bet is $${MAX_BET.toLocaleString()}.`);
    updateBetDisplay();
    return;
  }
  if (val % 100 !== 0) {
    showBetError('Amount must be a multiple of $100.');
    updateBetDisplay();
    return;
  }
  clearBetError();
  state.bets[state.selectedHand] = val;
  refreshHandSelBet(state.selectedHand);
  updateBetDisplay();
  renderBettingBalance();
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

  await updateUI(data);
}

// ── Early pay ──────────────────────────────────────────────────────────────────
async function doEarlyPay(choice) {
  await updateUI(await api('POST', '/round/early_pay', { choice }));
}

// ── Playing moves ──────────────────────────────────────────────────────────────
async function doHit()      { await updateUI(await api('POST', '/round/hit')); }
async function doStand()    { await updateUI(await api('POST', '/round/stand')); }
async function doDouble() {
  state.balance -= state.activeBet;
  renderBalance(state.balance);
  await updateUI(await api('POST', '/round/double'));
}
async function doSplit() {
  state.balance -= state.activeBet;
  renderBalance(state.balance);
  await updateUI(await api('POST', '/round/split'));
}
async function doSurrender(){ await updateUI(await api('POST', '/round/surrender')); }

// ── Phase transitions ──────────────────────────────────────────────────────────
function nextRound()  { enterBettingPhase(); }
function newSession() { showSessionOverlay(); }

// ── Master UI update ───────────────────────────────────────────────────────────
async function updateUI(data) {
  if (!data || data.error) { showMsg(data?.error || 'Server error'); return; }

  state.balance = data.capital;
  state.phase   = data.phase;
  renderBalance(data.capital);

  if (data.phase === 'settled') {
    // Hide action zone immediately so no clicks fire during animation.
    for (const p of ['betting', 'early-pay', 'playing', 'settled'])
      document.getElementById(`phase-${p}`).style.display = 'none';
    // Show only pre-decided profits (bust/surrender/early-pay/auto-BJ) while
    // dealer is still revealing cards; dealer-dependent profits appear after.
    renderHands(withPreDecidedProfitsOnly(data.hands), data.phase);
    await animateDealerReveal(data.dealer);
    renderHands(data.hands, data.phase);
    showPhase('settled');
    flashRoundResult(data.hands);
    if (data.capital < MIN_BET) setTimeout(showGameOver, 2500);
  } else {
    renderDealer(data.dealer);
    renderHands(data.hands, data.phase);
    if (data.phase === 'playing') {
      if (data.active_hand && data.active_branch) {
        const ah = data.hands.find(h => h.id === data.active_hand);
        const ab = ah && ah.branches.find(b => b.id === data.active_branch);
        if (ab) state.activeBet = ab.bet;
        if (ab && ab.is_aces_split) { showPhase('playing'); setPlayButtons([]); return; }
      }
      showPhase('playing');
      setPlayButtons(data.moves || []);
    } else if (data.phase === 'early_pay') {
      showPhase('early-pay');
      renderEarlyPayInfo(data.early_pay_hand, data.early_pay_chips);
    } else if (data.phase === 'insurance') {
      showPhase('insurance');
      renderInsuranceToggles(data.insurance_hands);
    }
  }
}

// ── Rendering helpers ─────────────────────────────────────────────────────────
// Outcomes whose profit is decided before dealer draws (show during animation).
const PRE_DECIDED_OUTCOMES = new Set(['bust', 'surrendered', 'early_pay', 'bj_auto']);

function withPreDecidedProfitsOnly(hands) {
  return hands.map(h => ({
    ...h,
    branches: h.branches.map(b => ({
      ...b,
      profit: PRE_DECIDED_OUTCOMES.has(b.outcome) ? b.profit : null,
    })),
  }));
}

// ── Rendering ──────────────────────────────────────────────────────────────────
function renderBalance(amount) {
  document.getElementById('balance').textContent = '$' + amount.toLocaleString();
}

// Show balance minus committed bets; called whenever bet amounts change during betting phase.
function renderBettingBalance() {
  const committed = state.bets.reduce((s, b) => s + b, 0);
  renderBalance(state.balance - committed);
}

function renderDealer(dealer) {
  const hand = document.getElementById('dealer-hand');
  const val  = document.getElementById('dealer-val');
  hand.innerHTML = '';
  dealer.cards.forEach(c => hand.appendChild(makeCardEl(c.rank, c.suit)));
  val.textContent = dealer.value_text;
}

// Animate dealer reveal card-by-card with 1-second delays (Fix 3).
async function animateDealerReveal(dealer) {
  const hand = document.getElementById('dealer-hand');
  const val  = document.getElementById('dealer-val');
  hand.innerHTML = '';

  if (!dealer.cards.length) { val.textContent = dealer.value_text; return; }

  // First card was visible during play — appear immediately, badge shows rank only.
  hand.appendChild(makeCardEl(dealer.cards[0].rank, dealer.cards[0].suit));
  val.textContent = dealer.cards[0].rank;

  // Each subsequent card drawn by the dealer appears after a 1-second pause.
  for (let i = 1; i < dealer.cards.length; i++) {
    await new Promise(r => setTimeout(r, 1000));
    hand.appendChild(makeCardEl(dealer.cards[i].rank, dealer.cards[i].suit));
  }

  // Final settled total, e.g. "18" or "22 — Busted" or "Blackjack".
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
      branchesRow.appendChild(makeBranchEl(branch, phase, hand.splits));
    }

    group.appendChild(branchesRow);
    row.appendChild(group);
  }
}

function makeBranchEl(branch, phase, handSplits = 0) {
  const el = document.createElement('div');
  const oc = branch.outcome;
  let stateClass = '';

  if (branch.active) {
    stateClass = 'active';
  } else if (oc === 'won' || oc === 'bj' || oc === 'bj_auto' || oc === 'early_pay') {
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
  // Post-split A+10 is never Blackjack — clamp to numeric value as a hard frontend guard.
  const vt = (handSplits > 0 && branch.value_text === 'Blackjack') ? '21' : branch.value_text;
  if (vt === 'Busted' || branch.bust)  valEl.classList.add('bust-val');
  else if (vt === 'Blackjack')         valEl.classList.add('bj-val');
  else if (branch.danger)              valEl.classList.add('danger-val');
  valEl.textContent = vt;
  info.appendChild(valEl);

  const betEl = document.createElement('div');
  betEl.className = 'bet-badge';
  betEl.textContent = '$' + branch.bet.toLocaleString();
  info.appendChild(betEl);

  if (branch.profit !== null && branch.profit !== undefined) {
    const pEl = document.createElement('div');
    const sign = branch.profit > 0 ? '+' : branch.profit < 0 ? '-' : '';
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
    `Dealer may draw Blackjack, however.<br>` +
    `Take <strong>+$${earlyPay.toLocaleString()}</strong> now, ` +
    `or wait for potential <strong>+$${waitPay.toLocaleString()}</strong> with push risk?`;

  document.getElementById('btn-early-take').textContent =
    `Take Early Pay (+$${earlyPay.toLocaleString()})`;
  document.getElementById('btn-early-wait').textContent =
    `Wait for ×1.5 (+$${waitPay.toLocaleString()})`;
}

// ── Phase switching ────────────────────────────────────────────────────────────
function showPhase(phase) {
  const phases = ['betting', 'early-pay', 'insurance', 'playing', 'settled'];
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
      const sign = row.Profit > 0 ? '+' : row.Profit < 0 ? '-' : '';
      tr.innerHTML =
        `<td>${row.Round}</td>` +
        `<td class="${cls}">${sign}$${Math.abs(row.Profit).toLocaleString()}</td>` +
        `<td>$${row.Capital.toLocaleString()}</td>`;
      tbl.appendChild(tr);
    }
  }

  document.getElementById('income-modal').classList.remove('hidden');
}

function hideIncome() {
  document.getElementById('income-modal').classList.add('hidden');
}

// ── Rules modal ────────────────────────────────────────────────────────────────
let _rulesLang  = 'english';
const _rulesCache = {};

function showRules() {
  // Force display via inline style — bypasses any CSS cascade issues.
  document.getElementById('rules-modal').style.display = 'flex';
  _loadRules(_rulesLang);
}

function hideRules() {
  document.getElementById('rules-modal').style.display = 'none';
}

function switchRulesLang(lang) {
  _rulesLang = lang;
  document.querySelectorAll('.lang-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(`tab-${lang}`).classList.add('active');
  _loadRules(lang);
}

async function _loadRules(lang) {
  const contentEl = document.getElementById('rules-content');
  if (_rulesCache[lang]) { contentEl.innerHTML = _rulesCache[lang]; return; }

  contentEl.innerHTML = '<p style="color:var(--ivory-dim)">Loading…</p>';
  const data = await api('GET', `/rules/${lang}`);
  if (!data.content) return;

  // Convert rule blocks (separated by blank lines) into <p> elements.
  const html = data.content
    .trim()
    .split(/\n\n+/)
    .filter(Boolean)
    .map(block => {
      const safe = block
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
      return `<p>${safe}</p>`;
    })
    .join('');

  _rulesCache[lang] = html;
  contentEl.innerHTML = html;
}

// ── Insurance phase ────────────────────────────────────────────────────────────
const _insuranceSelected = {};

function renderInsuranceToggles(insuranceHands) {
  const container = document.getElementById('insurance-toggles');
  container.innerHTML = '';

  for (const k in _insuranceSelected) delete _insuranceSelected[k];

  for (const hand of insuranceHands) {
    _insuranceSelected[hand.hand_id] = true;  // default: all selected

    const btn = document.createElement('button');
    btn.className = 'ins-toggle-btn selected';
    btn.dataset.hid = hand.hand_id;
    btn.innerHTML =
      `<span>Hand ${hand.hand_id}</span>` +
      `<span class="ins-toggle-amount">+$${hand.insurance_amount.toLocaleString()}</span>`;
    btn.addEventListener('click', () => {
      _insuranceSelected[hand.hand_id] = !_insuranceSelected[hand.hand_id];
      btn.classList.toggle('selected', _insuranceSelected[hand.hand_id]);
    });
    container.appendChild(btn);
  }
}

async function doInsurance() {
  const insured_hands = Object.keys(_insuranceSelected).filter(hid => _insuranceSelected[hid]);
  await updateUI(await api('POST', '/round/insurance', { insured_hands }));
}

// ── Game over modal ────────────────────────────────────────────────────────────
function showGameOver() {
  document.getElementById('gameover-modal').style.display = 'flex';
}

// ── GitHub modal ───────────────────────────────────────────────────────────────
function showGitHub() {
  document.getElementById('github-modal').style.display = 'flex';
}

function hideGitHub() {
  document.getElementById('github-modal').style.display = 'none';
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // bet-display handled via its own listeners in DOMContentLoaded
});

// Wire up inline bet display + rules modal close handlers
document.addEventListener('DOMContentLoaded', () => {
  const betEl = document.getElementById('bet-display');

  betEl.addEventListener('focus', function() {
    const val = state.bets[state.selectedHand];
    this.value = val > 0 ? String(val) : '';
    this.select();
  });

  betEl.addEventListener('blur', commitBetInput);

  betEl.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { this.blur(); return; }
    if (e.key === 'Escape') { updateBetDisplay(); this.blur(); return; }
    // Allow: digits, backspace, delete, arrows, tab, ctrl/meta combos
    if (!e.ctrlKey && !e.metaKey && e.key.length === 1 && !/[0-9]/.test(e.key)) {
      e.preventDefault();
    }
  });

  // Close rules modal when clicking the backdrop (but NOT when clicking inside the card).
  document.getElementById('rules-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) hideRules();
  });

  // Close rules modal via the X button.
  document.getElementById('rules-close-btn').addEventListener('click', hideRules);

  // Close GitHub modal when clicking the backdrop or the X button.
  document.getElementById('github-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) hideGitHub();
  });
  document.getElementById('github-close-btn').addEventListener('click', hideGitHub);
});

// ── Init ───────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  showPhase('betting');  // All panels start hidden; session overlay shows first
});
