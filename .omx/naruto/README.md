# Naruto crossover section

目前火影版號：**火影 beta 0.01**。顯示於火影選角區塊、瀏覽器標題與畫面右下角。
日後修改 `.omx/naruto.js` 頂端的 `version`，三處會同步更新；不影響存檔鍵值。

Generation 11 follows Digimon in collection and gacha. The Naruto button appears
in the top navigation and in the first-time Digimon picker. Eight characters are
available: Naruto, Sasuke, Sakura, Kakashi, Hinata, Rock Lee, Gaara and Itachi.
Choosing a ninja uses the existing sandbox save without resetting the collection.
Naruto characters do not use the Digimon evolution system.

Twenty-six adapted skills cover three character techniques per ninja, with
Naruto also learning a fourth technique, the Nine-Tails Chakra Cloak,
Fireball shared only by Sasuke and Itachi, plus two common ninja tools.
The in-game skill guide links each character to official Naruto source articles.
Attack names and character identities are source-based; damage, ranges, cooldowns,
type mappings and crowd-control effects are survival-game design choices. In
particular, Lightning Blade's ranged beam and automated combo timings are gameplay
adaptations rather than literal reproductions of the manga.

Gaara's primary now sweeps a widening sand wave across enemies, briefly binds
ordinary enemies (bosses resist), and erupts across the swept area once. It no
longer fires a sand orb. Naruto can learn Rasenshuriken, Sasuke and Itachi can
learn Fireball Jutsu, and Kakashi can learn Water Dragon. The latter three use
area impacts, with real multi-target damage checks and character-specific pools.
The [AoE audit](aoe-audit.md) records references and separates canon ability from
the crossover's area, timeline and balance choices. Existing Sakura, Hinata and
Rock Lee close-range attacks also have tested multi-target areas.

## Naruto shadow clones

Naruto now starts with Multi Shadow Clone Jutsu. Lightweight actors move,
choose nearby enemies and punch; they share the owner's damage credit and never
become extra players, collect rewards or write saves. Normal pursuers can be
distracted by a closer clone; bosses retain their target. Contact or hostile
projectile hits disperse a clone with smoke. Initial lifetime is six seconds and
cooldown four seconds. Skill levels one through five support 8, 16, 24, 32 and
40 actors (+8 per upgrade). The level-up choice explicitly
shows the next quantity, and choosing it immediately fills the new vacancies,
even while another Naruto technique is selected. Recasting fills vacancies without refreshing existing
lifetimes. While at the cap, the active skill polls for a vacancy without wasting
a new four-second cooldown or repeatedly replaying Charge. Switching slots keeps
existing clones until they expire. A normal cast plays the original hands-together
seal for 0.4 seconds before smoke and actors appear. New actors start idle rather
than performing the summoning seal themselves. Death and scene changes cancel
pending summons. Quantity upgrades still fill immediately.

Character level three guarantees a Rasengan learning choice, and level six a
Rasenshuriken choice; level nine adds the Chakra Cloak. When four slots are full, the card explicitly offers to
replace a shared kunai/shuriken slot rather than removing a character skill.
Players may decline. The original Rasengan move ID is preserved. Switching to
learned Rasengan, Rasenshuriken, Kunai or Shuriken lets existing clones use that
technique autonomously, without waiting for the player's cast. Each maintains a
separate cooldown per technique across slot switches.
Each clone uses the full copied-technique damage: no division by clone count and
no aggregate damage ceiling. Both the direct hit and explosion retain that full
damage. Clones cannot recursively summon or borrow
other characters' techniques. While Shadow Clone is selected, they use basic
punches. Pause freezes their simulation time;
death and scene changes clear actors and smoke. A gold chevron marks the owner.

Run `python .omx/check_naruto_clones.py` for caps, lifetime, walls, distributed
attacks, contact/projectile dispersal, aggro, full per-clone damage, quantity cards,
pause and scene cleanup. Original ability reference:
https://naruto-official.com/en/news/01_1423 . Actor counts, automatic behavior,
timing and damage values are this game's adaptation. Multiplayer replication of
clone actors is not implemented in this guest-only edition.

## 影分身設定調整（單一設定入口）

修改 [naruto-clones.js](../naruto-clones.js) 頂端的 `config`，重新整理網頁即可：

```js
const config = Object.freeze({ counts: Object.freeze([8,16,24,32,40]), cooldown: 4,
  duration: 6, sealDuration: .4, punchDamage: 8, punchCooldown: .65 });
```

| 設定 | 意義 | 目前值 |
| --- | --- | --- |
| `counts` | 技能 Lv.1 起各級同時存在上限；須為正整數且遞增 | 8、16、24、32、40 |
| `cooldown` | 施放冷卻（秒，受玩家冷卻倍率影響） | 4 |
| `duration` | 每隻分身存活時間（秒） | 6 |
| `sealDuration` | 本體結印至分身出現的時間（秒，須大於 0） | 0.4 |
| `punchDamage` | 未選擇可模仿招式時的基本拳擊傷害 | 8 |
| `punchCooldown` | 基本拳擊間隔（秒） | 0.65 |

`counts` 同時決定技能最高等級、升級卡文字、技能說明和實際分身上限。
例如只改成 `[4,8,12,16,20]`，這四處會一起更新，不需要分別改檔案。
不要執行中修改凍結設定；直接修改原始碼後重新整理並開新局。
數量是上限：空間不足時只生成可站立的分身；再次施放補空缺，不重設舊分身壽命。
技能升級立即補到新上限，包括切換其他技能時。每隻模仿完整招式傷害，沒有總傷害封頂。
傷害仍依原招式、玩家攻擊倍率、屬性與首領機制計算。

改數量後同步更新 `.omx/check_naruto_clones.py` 的期望數量斷言（用來驗證需求）；
測試也會確認設定、技能最高等級、升級卡與生成上限一致。
本地執行 `python .omx/check_naruto_clones.py` 與
`python .omx/check_naruto_animations.py` 驗證。
只改平衡設定不需重產資料；若修改 `sprites.json`，先執行
`python .omx/make_digimon.py` 重產 `sprites-data.js`。
發布須把變更 commit / push 到個人分支 `feat/digimon-sandbox`，等待 Pages workflow 完成。

結印參考：[VIZ 官方 Shadow Clone Jutsu 片段](https://www.youtube.com/watch?v=OM-OzWJ2HTc)。
採用現有 DS 原圖 y237–268 的三格合手結印，而非原先 y364 的舉手轉身動作；
以最後一格停留到施放完成。素材只有正面結印，其他朝向共用正面，像素解析度無法逐根表現十字手指。
原始 PNG 不變；來源與裁切記錄在 `sources.json`、`sprites.json`。

## 通用被動：數量增幅

三選一新增「數量增幅」，所有角色均可抽到，不占四個技能槽。
每次選取，所有技能的下列有效數量 +1，最多選 20 次，僅持續到本局結束：

| 類型 | 實際效果 |
| --- | --- |
| 分身 | 基礎 8／16／24／32／40 加上被動總加成，選卡立即補空缺 |
| 投射物、散射、環繞物、迴旋投射物 | 每次發射或同時環繞數量增加 |
| 連鎖 | 可命中目標數增加，仍須有符合距離的目標 |
| 地雷、隕石 | 每次生成數量增加 |
| 砲台 | 同時存在的上限增加，仍每次施放放置一座 |
| 火焰軌跡、天照 | 同時存在的場地效果上限增加 |
| 有多段設定的近戰忍術 | 連擊段數增加，每段傷害維持原值 |
| 原本可穿透的投射物、一般疊層增益 | 穿透數、最大疊層增加 |

影分身模仿的投射物也增加，但每次發射只計一次被動。
例如選過 2 次，分身各級為 10／18／26／34／42，苦無一次 3 發，手裏劍一次 10 發。
普通單次近戰、光束、衝刺、治療與護盾沒有可增加的數量，就維持原招式機制；
不增加技能槽、傷害倍率、範圍、持續秒數、裝飾粒子或反覆觸發的治療次數。
穿透僅影響採用投射物穿透機制的招式；爆炸型投射物仍在首次命中引爆一次。

調整 [quantity.js](../quantity.js) 的單一設定：

```js
const config = Object.freeze({ perPick: 1, maxPicks: 20 });
```

`perPick` 為每次增加幾個（正整數），`maxPicks` 為可選次數（正整數）。
卡片說明與選取上限自動同步。數量公式為「技能自身等級／進化後數量 + 被動累積量」，
不改寫招式原始資料，因此先升技能或先選被動結果相同，新學招式亦自動生效。
延遲施放的忍術保留施放當時數量；本局重新開局會歸零，角色間各自計算。

執行 `python .omx/check_quantity.py` 驗證卡片、各數量機制、傷害、延遲快照與重開。
修改後不需重產資料，重新整理並開新局即可；發布沿用個人分支 Pages 流程。
這是本遊戲通用被動設計，不是新增原作忍術。

## 八角色技能表

| Character | Starting technique | Character level 3 choice | Character level 6 choice |
| --- | --- | --- | --- |
| Naruto | Multi Shadow Clone | Rasengan | Rasenshuriken |
| Sasuke | Chidori | Fireball | Sharingan prediction |
| Sakura | Cherry Blossom Impact | Medical ninjutsu | Regeneration |
| Kakashi | Short-range Lightning Blade | Water Dragon | Earth Wall |
| Hinata | Gentle Fist | Twin Lion Fists | Byakugan |
| Rock Lee | Leaf Whirlwind | Forward Lotus | Inner Gates |
| Gaara | Sand Tsunami / burial | Sand Coffin / burial | Sand Shield |
| Itachi | Single-target Tsukuyomi | Fireball | Amaterasu |

Naruto has an additional guaranteed level 9 choice: Nine-Tails Chakra Cloak.

Each role retains the four-slot choice system and can decline a learning card.
When full, an explicit card can replace a shared ninja tool in place, retaining
its key binding. Extra-starting-move perks cannot bypass character level gates.
Cooldowns and effect details are available in the source-backed in-game guide.

## 九尾查克拉外衣（紅色一尾）

新增鳴人限定的 `naruto-nine-tails-cloak`，角色 Lv.9 起出現在三選一。
滿四槽時可替換苦無或手裏劍，沿用原槽位與按鍵；不自動刪除已學的特色忍術。
學會後切到該技能，附近有威脅才會自動施放；再切回螺旋丸或其他技能，外衣仍會維持。

| 基礎設定 | 效果 |
| --- | --- |
| `cd: 18` | 冷卻 18 秒，受玩家冷卻加成影響；外衣存在時不能重複施放 |
| `fieldDuration: 8` | 持續 8 秒，切換技能不取消 |
| `atkMul: 1.5` / `speedMul: 1.25` | 攻擊 +50%、移速 +25%；與已選的強化相乘 |
| `damageTakenMul: .75` | 一般受擊傷害乘 0.75；保留屬性、減傷、無敵時間與真實傷害規則 |
| `radius: 76` / `pulseInterval: .65` | 每 0.65 秒反擊有效範圍內全部敵人，遇牆阻擋 |
| `pulseDamage: 12` / `knock: 18` | 每次反擊基礎傷害 12、普通敵人擊退 18；首領擊退降為 5 |

所有平衡值與升級表集中在 `.omx/naruto-skills.js` 的同名技能定義。
`learnLevel: 9` 控制學習門檻。技能升級依序改為：持續 9 秒、攻擊 +65%、移速 +35%、
冷卻減少 15% 且持續 10 秒。支援模組的安全界限目前為持續最多 12 秒、
攻擊倍率最多 1.8、移速倍率最多 1.5、一般傷害倍率最低 0.5；超出時須同步檢查測試。

影分身沿用本體當前攻擊，因此外衣期間的拳擊與模仿招式也會受益；
分身不會各自施放外衣或追加全周反擊。外觀固定一尾，屬於造型而非「數量增幅」的攻擊數量。
到期、死亡、場景或技能效果重設會移除外衣與加成，不覆寫永久升級。
暫停會凍結動畫與效果時間。視覺為程式繪製的像素查克拉、尾巴、狐耳及氣泡，
保留原始角色 PNG、臉部與行走／攻擊影格。

依據：[官方終末之谷回顧](https://naruto-official.com/en/news/01_1296)
明確描述外衣提升速度、以查克拉反擊並抵擋攻擊，附有少年鳴人紅色查克拉外衣畫面。
本版採紅色一尾外衣，不混同後期金色九尾查克拉模式；
全周定時反擊、加成、冷卻與持續時間皆為生存遊戲改編。

執行 `python .omx/check_naruto_cloak.py` 驗證學習、換槽、加成、三目標反擊、
範圍／牆體、死亡與到期清除、暫停及實際遊戲畫面。

Healing is capped at maximum health and suppressed when full; regeneration has
five timed ticks. Sharingan provides one dodge and one offensive-cast bonus.
Byakugan marks visible nearby threats and improves close-range precision. Gates
temporarily compose attack/speed multipliers, then fatigue, preserving concurrent
level-up gains. Sand Shield absorbs a finite damage budget and locks on break.
Earth Wall intercepts hostile swept projectiles and repels ordinary enemies;
friendly shots and the player can pass, and no permanent map tile is changed.

Lotus launches ordinary targets and gives other nearby enemies a smaller landing
impact; bosses resist launch. Sand Coffin captures one target, then damages it
once. Tsukuyomi prioritizes one visible elite, with reduced boss control. Amaterasu
creates up to two finite black-flame circles, ticking once per half second for
three seconds. All effects use simulation time and are cleared on run changes.
`naruto-support.js` and `naruto-offense.js` extend the existing engine rather than
replacing core player, room-provider or transport code.

Run `python .omx/check_naruto_roster.py` for eight isolated kits, level gates,
healing, defense, buffs, single-target control, real AoE budgets, wall geometry,
expiry, cleanup and startup. Multiplayer adapter regression is checked with
`node tools/test_multiplayer.js`; replication of these custom techniques remains
a separate verification gap. Extended gameplay balance is still provisional.

## Original artwork

The sprites are original downloaded sheets from *Naruto: Path of the Ninja 2*
(Nintendo DS), mirrored by Sprite Database. Sources, download hashes and sheet
credits are recorded in `sources.json`; the original PNGs retain their credits.
Sheet ripping is credited to **Hwdphg**. Character/game artwork remains the
property of its original rights holders; a public sprite download is not a new
license for that artwork. This is a free, unofficial fan crossover.

`sprites.json` records source frame rectangles. Six characters use overworld walk
frames. Sasuke and Itachi use side-facing battle poses with runtime mirroring;
these two do not have four-direction walking animation in this version. Runtime
Canvas removes the exact flat sheet background and draws with nearest-neighbor
scaling; downloaded PNGs are unchanged. Rendering keeps characters around 64
world pixels high, separate from menu-preview fitting.

Horizontal field rows are audited against the original face direction. The six
field sheets have right-facing frames above left-facing frames; the two battle
sheets face right in the original, so only left views are mirrored.

The renderer now plays available original attack/jutsu sequences for all eight
characters, Naruto's casting sequence, and the battle sheets' hurt/faint rows.
Attack and Shoot share the field combat sequences; missing action directions use
the documented default view or an explicit mirror. Field sheets without verified
hurt/faint art retain fallback flash/flatten presentation. Those fallbacks are not
claimed to be newly sourced animations. Scaling uses standing height, so extended
attacks and fallen poses retain their original proportions.

Regenerate metadata and the shared entry with `python .omx/make_digimon.py`.
Run `python .omx/check_naruto.py` for browser checks without a local HTTP server.
Run `python .omx/check_naruto_animations.py` for source direction, frame timing,
signature-animation checks and a labeled screenshot of all eight characters.
Run `python .omx/check_gaara.py` for sand-wave phases, three spread targets plus
outside controls, boss resistance, walls, cleanup, extra AoE ownership and range
upgrades. The reusable `$naruto-survivor-skills` policy is tracked under
`.codex/skills/naruto-survivor-skills/SKILL.md` and installed in the local Codex
skills directory for future character work.
Set `PAGES_LIVE=1` to check the deployed site instead. Tests require Python
Playwright and the installed Windows Chrome, matching the other sandbox checks.

Deployment remains https://tim12332000.github.io/pokesurvivor/ and uses only the
personal `feat/digimon-sandbox` branch. No upstream PR is created or changed.
