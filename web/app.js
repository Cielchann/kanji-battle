const difficulties = ["easy", "medium", "hard", "extreme", "hell"];
const deviceTokenKey = "jlpt-kanji-battle-device-token";

function createDeviceToken() {
  if (window.crypto?.randomUUID) {
    return `kb-${window.crypto.randomUUID()}`;
  }
  if (!window.crypto?.getRandomValues) {
    return `kb-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }
  const bytes = new Uint8Array(16);
  window.crypto.getRandomValues(bytes);
  return `kb-${Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

function getDeviceToken() {
  let token = window.localStorage.getItem(deviceTokenKey);
  if (!token) {
    token = createDeviceToken();
    window.localStorage.setItem(deviceTokenKey, token);
  }
  return token;
}

const state = {
  selectedDifficulty: "easy",
  deviceToken: getDeviceToken(),
  battle: null,
  progress: null,
};

const els = {
  playerName: document.querySelector("#playerName"),
  language: document.querySelector("#language"),
  difficultyGrid: document.querySelector("#difficultyGrid"),
  startBattle: document.querySelector("#startBattle"),
  setupPanel: document.querySelector("#setupPanel"),
  battleView: document.querySelector("#battleView"),
  playerHp: document.querySelector("#playerHp"),
  monsterHp: document.querySelector("#monsterHp"),
  monsterHpReadout: document.querySelector("#monsterHpReadout"),
  monsterHpBar: document.querySelector("#monsterHpBar"),
  combo: document.querySelector("#combo"),
  score: document.querySelector("#score"),
  weaponName: document.querySelector("#weaponName"),
  monsterName: document.querySelector("#monsterName"),
  monsterPanel: document.querySelector("#monsterPanel"),
  battleStatus: document.querySelector("#battleStatus"),
  playerHpBox: document.querySelector("#playerHpBox"),
  slashEffect: document.querySelector("#slashEffect"),
  floatingDamage: document.querySelector("#floatingDamage"),
  questionPanel: document.querySelector("#questionPanel"),
  questionText: document.querySelector("#questionText"),
  questionPower: document.querySelector("#questionPower"),
  prompt: document.querySelector("#prompt"),
  choices: document.querySelector("#choices"),
  resultPanel: document.querySelector("#resultPanel"),
  resultTitle: document.querySelector("#resultTitle"),
  resultSummary: document.querySelector("#resultSummary"),
  xpEarned: document.querySelector("#xpEarned"),
  goldEarned: document.querySelector("#goldEarned"),
  newBattle: document.querySelector("#newBattle"),
  heroSummary: document.querySelector("#heroSummary"),
  unlockList: document.querySelector("#unlockList"),
  leaderboard: document.querySelector("#leaderboard"),
  shopList: document.querySelector("#shopList"),
  refreshProgress: document.querySelector("#refreshProgress"),
  refreshLeaderboard: document.querySelector("#refreshLeaderboard"),
  refreshShop: document.querySelector("#refreshShop"),
  toast: document.querySelector("#toast"),
  goldWallet: document.querySelector("#goldWallet"),
  shopGold: document.querySelector("#shopGold"),
};

function playerName() {
  return els.playerName.value.trim();
}

function hasPlayerName() {
  return playerName().length > 0;
}

function formatNumber(value) {
  return Number(value).toLocaleString("en-US");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || "Request failed.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

function playerQuery(extra = {}) {
  return new URLSearchParams({
    ...extra,
    device_token: state.deviceToken,
  });
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    els.toast.hidden = true;
  }, 2600);
}

function isDifficultyUnlocked(difficulty) {
  if (!state.progress) return ["easy", "medium", "hard"].includes(difficulty);
  const item = state.progress.difficulties.find((entry) => entry.difficulty === difficulty);
  return item ? item.unlocked : false;
}

function renderDifficulties() {
  els.difficultyGrid.innerHTML = "";
  difficulties.forEach((difficulty) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "difficulty-button";
    button.textContent = difficulty;
    const unlocked = isDifficultyUnlocked(difficulty);
    if (state.selectedDifficulty === difficulty) button.classList.add("active");
    if (!unlocked) button.classList.add("locked");
    button.addEventListener("click", () => {
      if (!unlocked) {
        const progress = state.progress?.difficulties.find((item) => item.difficulty === difficulty);
        showToast(progress?.locked_reason || "Locked.");
        return;
      }
      state.selectedDifficulty = difficulty;
      renderDifficulties();
      loadLeaderboard();
    });
    els.difficultyGrid.appendChild(button);
  });
}

function renderProgress(progress) {
  state.progress = progress;
  const gold = formatNumber(progress.gold);
  els.heroSummary.textContent = `${progress.hero_role} · ${formatNumber(progress.xp)} XP · ${gold} Gold`;
  els.goldWallet.textContent = gold;
  els.shopGold.textContent = `${gold} Gold`;
  els.unlockList.innerHTML = "";
  progress.difficulties.forEach((item) => {
    const row = document.createElement("div");
    row.className = "unlock-item";
    const status = item.unlocked ? "Unlocked" : "Locked";
    row.innerHTML = `
      <div>
        <strong>${item.difficulty}</strong>
        <small>${item.clears} clears · ${item.perfect_clears} perfect</small>
      </div>
      <strong class="${item.unlocked ? "unlocked" : "locked"}">${status}</strong>
    `;
    els.unlockList.appendChild(row);
  });
  renderDifficulties();
}

async function loadProgress() {
  if (!hasPlayerName()) {
    state.progress = null;
    els.heroSummary.textContent = "No player";
    els.goldWallet.textContent = "0";
    els.shopGold.textContent = "0 Gold";
    els.unlockList.innerHTML = "";
    renderDifficulties();
    return;
  }
  const progress = await api(
    `/players/${encodeURIComponent(playerName())}/progress?${playerQuery().toString()}`,
  );
  renderProgress(progress);
}

async function loadShop() {
  if (!hasPlayerName()) {
    els.shopList.innerHTML = "";
    return;
  }
  const params = playerQuery({ player_name: playerName() });
  const weapons = await api(`/shop/weapons?${params.toString()}`);
  els.shopList.innerHTML = "";
  weapons.forEach((weapon) => {
    const row = document.createElement("div");
    row.className = "shop-item";
    const actionLabel = weapon.equipped ? "Equipped" : weapon.owned ? "Equip" : `Buy ${formatNumber(weapon.price)}`;
    row.innerHTML = `
      <div>
        <strong>${weapon.name}</strong>
        <small>+${weapon.attack_bonus}% attack · ${weapon.description}</small>
      </div>
      <button type="button" ${weapon.equipped ? "disabled" : ""}>${actionLabel}</button>
    `;
    const button = row.querySelector("button");
    button.addEventListener("click", async () => {
      try {
        if (!weapon.owned) {
          await api("/shop/buy", {
            method: "POST",
            body: JSON.stringify({
              player_name: playerName(),
              device_token: state.deviceToken,
              weapon_id: weapon.id,
            }),
          });
        }
        await api("/shop/equip", {
          method: "POST",
          body: JSON.stringify({
            player_name: playerName(),
            device_token: state.deviceToken,
            weapon_id: weapon.id,
          }),
        });
        showToast(`${weapon.name} equipped.`);
        await loadProgress();
        await loadShop();
      } catch (error) {
        showToast(error.message);
      }
    });
    els.shopList.appendChild(row);
  });
}

async function loadLeaderboard() {
  const params = new URLSearchParams({
    limit: "5",
  });
  const entries = await api(`/leaderboard?${params.toString()}`);
  els.leaderboard.innerHTML = "";
  if (entries.length === 0) {
    const empty = document.createElement("li");
    empty.innerHTML = `<span>No clears this week</span><small>weekly total</small>`;
    els.leaderboard.appendChild(empty);
    return;
  }
  entries.forEach((entry) => {
    const row = document.createElement("li");
    row.innerHTML = `
      <span>#${entry.rank} ${entry.player_name}</span>
      <small>${entry.score} pts · ${entry.max_combo} combo</small>
    `;
    els.leaderboard.appendChild(row);
  });
}

function renderBattle(battle) {
  state.battle = battle;
  els.battleView.hidden = false;
  els.playerHp.textContent = formatNumber(battle.player_hp);
  els.monsterHp.textContent = formatNumber(battle.monster.hp);
  els.monsterHpReadout.textContent = `${formatNumber(battle.monster.hp)} HP`;
  els.combo.textContent = battle.combo;
  els.score.textContent = formatNumber(battle.score);
  els.weaponName.textContent = battle.weapon_name
    ? `${battle.weapon_name} (+${battle.weapon_attack_bonus}%)`
    : "None";
  els.monsterName.textContent = battle.monster.name;
  els.battleStatus.textContent = battle.status.replace("_", " ");
  const monsterPercent = Math.round((battle.monster.hp / battle.monster.max_hp) * 100);
  els.monsterHpBar.style.width = `${monsterPercent}%`;
  window.KanjiBattleArena?.setBattle(battle);

  const finished = battle.status !== "in_progress";
  els.questionPanel.hidden = finished;
  els.resultPanel.hidden = !finished;

  if (finished) {
    els.resultTitle.textContent = battle.status === "won" ? "Stage Clear" : "Defeated";
    els.resultSummary.textContent = `${battle.player_name} scored ${formatNumber(battle.score)} with ${battle.combo} combo.`;
    els.xpEarned.textContent = `${battle.xp_earned} XP`;
    els.goldEarned.textContent = `${battle.gold_earned} Gold`;
    return;
  }

  const question = battle.current_question;
  els.questionText.textContent = question.question_text;
  els.questionPower.textContent = `Power ${question.power}`;
  els.prompt.textContent = question.prompt;
  els.choices.innerHTML = "";
  question.choices.forEach((choice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "choice-button";
    button.textContent = choice;
    button.addEventListener("click", () => answerQuestion(question.id, choice));
    els.choices.appendChild(button);
  });
}

function restartAnimation(element, className) {
  element.classList.remove(className);
  void element.offsetWidth;
  element.classList.add(className);
}

function playAnswerAnimation(result) {
  if (result.is_correct) {
    window.KanjiBattleArena?.playHit(result);
    els.floatingDamage.textContent = `-${formatNumber(result.damage_dealt)}`;
    restartAnimation(els.monsterPanel, "hit");
    restartAnimation(document.querySelector("#combo").parentElement, "combo-pop");
  } else {
    window.KanjiBattleArena?.playWrong(result);
    restartAnimation(els.playerHpBox, "damaged");
  }

  if (result.state.status !== "in_progress") {
    window.setTimeout(() => {
      window.KanjiBattleArena?.playFinish(result.state.status);
    }, 320);
  }
}

function setChoicesDisabled(disabled) {
  els.choices.querySelectorAll("button").forEach((button) => {
    button.disabled = disabled;
  });
}

function scrollToBattle() {
  const target = window.matchMedia("(max-width: 640px)").matches
    ? els.monsterPanel
    : els.battleView;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function startBattle() {
  try {
    if (!hasPlayerName()) {
      showToast("Enter a player name.");
      return;
    }
    const body = {
      player_name: playerName(),
      device_token: state.deviceToken,
      difficulty: state.selectedDifficulty,
      language: els.language.value,
    };
    const battle = await api("/battle/start", {
      method: "POST",
      body: JSON.stringify(body),
    });
    renderBattle(battle);
    showToast("Battle started.");
    window.requestAnimationFrame(scrollToBattle);
  } catch (error) {
    showToast(error.message);
    await loadProgress().catch(() => {});
  }
}

async function answerQuestion(questionId, answer) {
  if (!state.battle) return;
  setChoicesDisabled(true);
  try {
    const result = await api("/battle/answer", {
      method: "POST",
      body: JSON.stringify({
        battle_id: state.battle.battle_id,
        question_id: questionId,
        answer,
      }),
    });
    renderBattle(result.state);
    playAnswerAnimation(result);
    showToast(result.is_correct ? `Correct! ${formatNumber(result.damage_dealt)} damage.` : `Wrong! -${result.damage_taken} HP.`);
    if (result.state.status !== "in_progress") {
      if (result.state.status === "won") {
        restartAnimation(els.resultPanel, "clear");
      }
      await loadProgress();
      await loadLeaderboard();
    }
  } catch (error) {
    setChoicesDisabled(false);
    showToast(error.message);
  }
}

function resetBattleView() {
  state.battle = null;
  els.battleView.hidden = true;
  els.resultPanel.hidden = true;
  els.questionPanel.hidden = false;
  window.KanjiBattleArena?.clearBattle();
}

els.startBattle.addEventListener("click", startBattle);
els.newBattle.addEventListener("click", resetBattleView);
els.refreshProgress.addEventListener("click", () => loadProgress().catch((error) => showToast(error.message)));
els.refreshLeaderboard.addEventListener("click", () => loadLeaderboard().catch((error) => showToast(error.message)));
els.refreshShop.addEventListener("click", () => loadShop().catch((error) => showToast(error.message)));
els.playerName.addEventListener("change", () => {
  loadProgress().catch((error) => showToast(error.message));
  loadLeaderboard().catch((error) => showToast(error.message));
  loadShop().catch((error) => showToast(error.message));
});

renderDifficulties();
loadProgress().catch((error) => showToast(error.message));
loadLeaderboard().catch((error) => showToast(error.message));
loadShop().catch((error) => showToast(error.message));
