(function () {
  const mount = document.querySelector("#phaserArena");
  const playerMaxHp = {
    easy: 100000,
    medium: 250000,
    hard: 600000,
    extreme: 1200000,
    hell: 2400000,
  };

  function formatNumber(value) {
    return Number(value || 0).toLocaleString("en-US");
  }

  const fallbackController = {
    setBattle() {},
    playHit() {},
    playWrong() {},
    playFinish() {},
    clearBattle() {},
  };

  if (!mount) {
    window.KanjiBattleArena = fallbackController;
    return;
  }

  if (!window.Phaser) {
    const fallback = mount.querySelector(".arena-loading");
    if (fallback) fallback.textContent = "Arena unavailable";
    window.KanjiBattleArena = fallbackController;
    return;
  }

  const controller = {
    scene: null,
    pendingBattle: null,
    setBattle(battle) {
      if (this.scene) {
        this.resize();
        this.scene.setBattle(battle);
      } else {
        this.pendingBattle = battle;
      }
    },
    playHit(result) {
      if (this.scene) this.scene.playHit(result);
    },
    playWrong(result) {
      if (this.scene) this.scene.playWrong(result);
    },
    playFinish(status) {
      if (this.scene) this.scene.playFinish(status);
    },
    clearBattle() {
      if (this.scene) this.scene.clearBattle();
    },
    resize() {
      if (!this.game) return;
      if (mount.clientWidth > 0 && mount.clientHeight > 0) {
        this.game.scale.resize(mount.clientWidth, mount.clientHeight);
      }
    },
  };

  class BattleArenaScene extends Phaser.Scene {
    constructor() {
      super("BattleArenaScene");
      this.battle = null;
      this.heroBase = { x: 0, y: 0 };
      this.monsterBase = { x: 0, y: 0 };
    }

    create() {
      this.bg = this.add.graphics();
      this.floor = this.add.graphics();
      this.flash = this.add.rectangle(0, 0, 10, 10, 0xcf3f3f, 0).setOrigin(0);
      this.playerBarBg = this.add.graphics();
      this.playerBarFill = this.add.graphics();
      this.monsterBarBg = this.add.graphics();
      this.monsterBarFill = this.add.graphics();
      this.stageLabel = this.add.text(0, 0, "Ready", {
        fontFamily: "Arial, sans-serif",
        fontSize: "18px",
        fontStyle: "bold",
        color: "#e7f0f7",
      });
      this.hpText = this.add.text(0, 0, "", {
        fontFamily: "Arial, sans-serif",
        fontSize: "13px",
        fontStyle: "bold",
        color: "#dce7ee",
      });

      this.hero = this.createHero();
      this.monster = this.createMonster();
      this.heroName = this.add.text(0, 0, "Hero", this.nameTextStyle("#dce7ee")).setOrigin(0.5, 0);
      this.monsterName = this.add.text(0, 0, "Kanji Oni", this.nameTextStyle("#ffd7d7")).setOrigin(0.5, 0);

      this.scale.on("resize", this.layout, this);
      this.layout();

      controller.scene = this;
      if (controller.pendingBattle) {
        this.setBattle(controller.pendingBattle);
        controller.pendingBattle = null;
      }
    }

    nameTextStyle(color) {
      return {
        fontFamily: "Arial, sans-serif",
        fontSize: "13px",
        fontStyle: "bold",
        color,
      };
    }

    createHero() {
      const container = this.add.container(0, 0);
      const shadow = this.add.ellipse(0, 48, 118, 22, 0x000000, 0.22);
      const cape = this.add.triangle(-18, -42, 0, 0, -58, 64, 8, 78, 0x614f9f, 0.86);
      const body = this.add.graphics();
      body.fillStyle(0x1769aa, 1);
      body.fillRoundedRect(-28, -66, 56, 78, 12);
      body.fillStyle(0xf2b05e, 1);
      body.fillCircle(0, -86, 23);
      body.fillStyle(0x1f2933, 1);
      body.fillRoundedRect(-21, -102, 42, 20, 8);
      body.fillStyle(0xffffff, 1);
      body.fillCircle(-8, -87, 4);
      body.fillCircle(8, -87, 4);
      body.fillStyle(0x1f2933, 1);
      body.fillCircle(-8, -87, 1.7);
      body.fillCircle(8, -87, 1.7);
      const sword = this.add.rectangle(40, -48, 8, 94, 0xe8eef5, 1).setRotation(-0.62);
      const guard = this.add.rectangle(20, -14, 38, 6, 0xf3b23f, 1).setRotation(-0.62);
      const hand = this.add.circle(18, -16, 7, 0xf2b05e, 1);
      container.add([shadow, cape, body, sword, guard, hand]);
      return container;
    }

    createMonster() {
      const container = this.add.container(0, 0);
      const shadow = this.add.ellipse(0, 64, 158, 28, 0x000000, 0.26);
      const body = this.add.graphics();
      body.fillStyle(0xcf3f3f, 1);
      body.fillRoundedRect(-58, -82, 116, 132, 30);
      body.fillStyle(0xffd15f, 1);
      body.fillTriangle(-38, -82, -18, -132, -4, -82);
      body.fillTriangle(38, -82, 18, -132, 4, -82);
      body.fillStyle(0x842929, 1);
      body.fillCircle(0, -88, 44);
      body.fillStyle(0xffffff, 1);
      body.fillCircle(-16, -94, 9);
      body.fillCircle(16, -94, 9);
      body.fillStyle(0x1f2933, 1);
      body.fillCircle(-16, -94, 3);
      body.fillCircle(16, -94, 3);
      body.fillStyle(0xffd15f, 1);
      body.fillTriangle(-8, -80, 0, -66, 8, -80);
      body.fillStyle(0xffffff, 1);
      body.fillTriangle(-18, -62, -9, -42, 0, -62);
      body.fillTriangle(18, -62, 9, -42, 0, -62);
      const club = this.add.rectangle(-72, -32, 16, 130, 0x72512b, 1).setRotation(0.38);
      const spikeA = this.add.triangle(-98, -90, 0, 0, 18, 8, 0, 20, 0xdce7ee, 1).setRotation(0.38);
      container.add([shadow, club, spikeA, body]);
      return container;
    }

    layout() {
      const width = this.scale.width;
      const height = this.scale.height;
      const isNarrow = width < 430;
      const scale = Phaser.Math.Clamp(width / 900, isNarrow ? 0.56 : 0.68, 1.15);

      this.drawBackground(width, height);
      this.flash.setSize(width, height);
      this.stageLabel.setPosition(18, 16);
      this.hpText.setPosition(18, 44);

      this.heroBase = { x: width * (isNarrow ? 0.23 : 0.24), y: height * (isNarrow ? 0.76 : 0.72) };
      this.monsterBase = { x: width * (isNarrow ? 0.7 : 0.74), y: height * (isNarrow ? 0.66 : 0.64) };
      this.hero.setPosition(this.heroBase.x, this.heroBase.y).setScale(scale);
      this.monster.setPosition(this.monsterBase.x, this.monsterBase.y).setScale(scale);
      this.heroName.setPosition(this.heroBase.x, this.heroBase.y + 64 * scale);
      this.monsterName.setPosition(this.monsterBase.x, this.monsterBase.y + 82 * scale);
      this.drawHpBars();
    }

    drawBackground(width, height) {
      this.bg.clear();
      this.bg.fillStyle(0x172231, 1);
      this.bg.fillRect(0, 0, width, height);
      this.bg.fillStyle(0x263848, 1);
      this.bg.fillRect(0, height * 0.52, width, height * 0.48);
      this.bg.fillStyle(0x2f5f58, 1);
      this.bg.fillRect(0, height * 0.52, width, 7);
      this.bg.fillStyle(0xf0b94d, 1);
      for (let i = 0; i < 9; i += 1) {
        this.bg.fillCircle(40 + i * (width / 8), 42 + (i % 3) * 15, 2.3);
      }

      this.floor.clear();
      this.floor.lineStyle(1, 0x425563, 0.45);
      for (let x = -width; x < width * 1.6; x += 72) {
        this.floor.lineBetween(x, height, x + width * 0.42, height * 0.54);
      }
      for (let y = height * 0.62; y < height; y += 34) {
        this.floor.lineBetween(0, y, width, y);
      }
    }

    drawHpBars() {
      if (!this.battle) return;

      const width = this.scale.width;
      const playerMax = playerMaxHp[this.battle.difficulty] || this.battle.player_hp || 1;
      const playerRatio = Phaser.Math.Clamp(this.battle.player_hp / playerMax, 0, 1);
      const monsterRatio = Phaser.Math.Clamp(this.battle.monster.hp / this.battle.monster.max_hp, 0, 1);
      const barWidth = Math.min(260, width * 0.34);
      const leftX = 18;
      const rightX = width - barWidth - 18;

      this.playerBarBg.clear();
      this.playerBarBg.fillStyle(0x101820, 0.72);
      this.playerBarBg.fillRoundedRect(leftX, 68, barWidth, 10, 5);
      this.playerBarFill.clear();
      this.playerBarFill.fillStyle(0x2bbf8a, 1);
      this.playerBarFill.fillRoundedRect(leftX, 68, barWidth * playerRatio, 10, 5);

      this.monsterBarBg.clear();
      this.monsterBarBg.fillStyle(0x101820, 0.72);
      this.monsterBarBg.fillRoundedRect(rightX, 68, barWidth, 10, 5);
      this.monsterBarFill.clear();
      this.monsterBarFill.fillStyle(0xff6363, 1);
      this.monsterBarFill.fillRoundedRect(rightX, 68, barWidth * monsterRatio, 10, 5);
    }

    update(time) {
      if (!this.hero || !this.monster) return;
      this.hero.y = this.heroBase.y + Math.sin(time / 520) * 5;
      this.monster.y = this.monsterBase.y + Math.sin(time / 610) * 7;
    }

    setBattle(battle) {
      this.battle = battle;
      this.stageLabel.setText(`${battle.difficulty.toUpperCase()} BATTLE`);
      this.hpText.setText(`Hero ${formatNumber(battle.player_hp)} HP   Oni ${formatNumber(battle.monster.hp)} HP`);
      this.monsterName.setText(battle.monster.name);
      this.heroName.setText(battle.player_name);
      this.hero.setAlpha(1).setAngle(0);
      this.monster.setAlpha(1).setAngle(0);
      this.layout();
      this.drawHpBars();
    }

    playHit(result) {
      const damage = result.damage_dealt || 0;
      this.tweens.add({
        targets: this.hero,
        x: this.heroBase.x + 58,
        duration: 110,
        yoyo: true,
        ease: "Quad.easeOut",
      });
      this.time.delayedCall(105, () => {
        this.cameras.main.shake(140, 0.006);
        this.tweens.add({
          targets: this.monster,
          x: this.monsterBase.x + 12,
          duration: 55,
          yoyo: true,
          repeat: 2,
        });
        this.spawnSlash();
        this.spawnFloatingText(`-${formatNumber(damage)}`, this.monsterBase.x, this.monsterBase.y - 122, "#ffdddd");
      });
    }

    playWrong(result) {
      const damage = result.damage_taken || 0;
      this.cameras.main.shake(180, 0.009);
      this.tweens.add({
        targets: this.hero,
        x: this.heroBase.x - 12,
        duration: 60,
        yoyo: true,
        repeat: 3,
      });
      this.tweens.add({
        targets: this.flash,
        alpha: 0.22,
        duration: 70,
        yoyo: true,
        repeat: 1,
      });
      this.spawnFloatingText(`-${formatNumber(damage)}`, this.heroBase.x, this.heroBase.y - 124, "#ffd15f");
    }

    playFinish(status) {
      if (status === "won") {
        this.spawnFloatingText("CLEAR", this.monsterBase.x, this.monsterBase.y - 154, "#ffd15f");
        this.tweens.add({
          targets: this.monster,
          alpha: 0.18,
          scaleX: this.monster.scaleX * 0.88,
          scaleY: this.monster.scaleY * 0.88,
          duration: 360,
          ease: "Back.easeIn",
        });
        this.tweens.add({
          targets: this.hero,
          y: this.heroBase.y - 34,
          duration: 180,
          yoyo: true,
          repeat: 1,
          ease: "Sine.easeOut",
        });
        return;
      }

      if (status === "lost") {
        this.spawnFloatingText("DOWN", this.heroBase.x, this.heroBase.y - 154, "#ffdddd");
        this.tweens.add({
          targets: this.hero,
          alpha: 0.35,
          angle: -8,
          duration: 260,
        });
      }
    }

    spawnSlash() {
      const slash = this.add.rectangle(this.monsterBase.x - 36, this.monsterBase.y - 92, 168, 8, 0xffffff, 0.95);
      slash.setRotation(-0.55);
      slash.setBlendMode(Phaser.BlendModes.ADD);
      this.tweens.add({
        targets: slash,
        x: slash.x + 64,
        y: slash.y + 34,
        alpha: 0,
        scaleX: 1.45,
        duration: 260,
        ease: "Quad.easeOut",
        onComplete: () => slash.destroy(),
      });
    }

    spawnFloatingText(text, x, y, color) {
      const label = this.add.text(x, y, text, {
        fontFamily: "Arial, sans-serif",
        fontSize: "28px",
        fontStyle: "bold",
        color,
        stroke: "#1f2933",
        strokeThickness: 5,
      });
      label.setOrigin(0.5);
      this.tweens.add({
        targets: label,
        y: y - 46,
        alpha: 0,
        scaleX: 1.12,
        scaleY: 1.12,
        duration: 760,
        ease: "Quad.easeOut",
        onComplete: () => label.destroy(),
      });
    }

    clearBattle() {
      this.battle = null;
      this.stageLabel.setText("Ready");
      this.hpText.setText("");
      this.heroName.setText("Hero");
      this.monsterName.setText("Kanji Oni");
      this.hero.setAlpha(1).setAngle(0);
      this.monster.setAlpha(1);
      this.playerBarBg.clear();
      this.playerBarFill.clear();
      this.monsterBarBg.clear();
      this.monsterBarFill.clear();
    }
  }

  const loading = mount.querySelector(".arena-loading");
  if (loading) loading.remove();

  const game = new Phaser.Game({
    type: Phaser.CANVAS,
    parent: mount,
    backgroundColor: "#172231",
    transparent: false,
    scale: {
      mode: Phaser.Scale.RESIZE,
      width: mount.clientWidth,
      height: mount.clientHeight,
    },
    render: {
      antialias: true,
      pixelArt: false,
    },
    scene: BattleArenaScene,
  });

  controller.game = game;
  window.KanjiBattleArena = controller;
})();
