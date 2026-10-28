# Naruto crossover section

目前火影版號：**火影 beta 0.01**。版本可於瀏覽器標題及設定的「關於」查看，遊戲畫面不再放置非營利／原作署名浮水印。
日後修改 `.omx/naruto.js` 頂端的 `version` 會同步版本顯示；不影響存檔鍵值。免費、非營利與原作者介紹集中於「設定 → 關於」，法律與素材署名保留。

本修改版免費遊玩、非營利、無廣告、無付費內容。原始 **PokéSurvivor** 由
[JPTER78](https://github.com/JPTER78/pokesurvivor) 開發，感謝原作者的創作與專案分享。
本站為非官方跨界修改版；原始版網站為 https://pokesurvivor.com 。原始授權與版權聲明保留。
個人發布版已移除資助入口與結算提示，且不打包舊的付款設定或舊壓縮程式。

首次進入、尚未選擇角色且沒有遊玩紀錄的人，預設夥伴為鳴人，直接進入主選單。
既有存檔已選擇的角色與遊玩紀錄保持不變，仍可自行切換火影、數碼寶貝或寶可夢角色。

## 個人測試：升一等

只有目前設定的公網 IPv4 符合時，遊戲進行中的左上方才會顯示「升一等」。
按一次增加一級並開啟原本的三選一，選完後可繼續按；選卡、暫停、主選單與連線遊戲不顯示。
同一個出口 IP 的裝置皆可能看到。查詢失敗或網路改變後不符時隱藏，不影響一般遊玩。

`.omx/dev-network.json` 只記錄允許 IP 的 SHA-256，比對使用 [ipify IPv4 API](https://www.ipify.org/)。
完整 IP 不寫入遊戲存檔或公開設定；設定不是伺服器端權限驗證，只用於顯示本地遊戲的測試控制。
按鈕沿用 `G.Game.debugLevelUp()`，該局會被既有邏輯標記為測試局。
出口 IP 更換時，重新計算 SHA-256 並更新 `allowedIpv4Sha256` 後重新整理／發布。
執行 `python .omx/check_dev_controls.py` 驗證符合、不符、查詢失敗及升級選卡。

本地測試網址：`http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW`。
完成後先本地測試，GitHub 推送照常進行，無須等待 Pages 排隊結束。

## 手機直向遊玩

上鎖寶箱接觸即在地圖原位置開蓋：演出 0.65 秒，之後再等 1 秒才顯示升級選擇。演出期間可自由移動與攻擊，沒有全畫面遮罩，不暫停戰鬥或連線隊友；只有真正選卡時沿用原本暫停流程。金幣、票券、道具與升級經驗在等待結束時結算一次，避免還要追拾經驗球。手動暫停會凍結演出；新局、死亡、退出與裂縫傳送會取消未結算的開箱並恢復寶箱可互動狀態。連線沿用主機結算，舊破箱事件仍相容。驗證：`python tools/test_gaara_chests.py`、`node tools/test_chest_coop.js`。

電腦瀏覽器預設以置中的手機比例直式畫面遊玩，沿用手機選單、鏡頭與技能／暫停配置，鍵盤移動和滑鼠按鈕仍可使用。右上角「切換寬版」可回到完整瀏覽器寬度；網址加 `layout=wide` 也可直接開寬版。角色預選、語言、網址片段與同源存檔均保留。手機仍直接使用原有直向／橫向畫面，不套第二層框架。

`.omx/desktop-portrait.js` 只在個人沙盒入口啟用，`.omx/portrait.html` 提供真正的直式 iframe 視窗；不是拉伸橫向 canvas。入口與打包由 `.omx/make_digimon.py`、`tools/build_digimon_site.py` 接線。執行 `python tools/test_desktop_portrait.py` 驗證三種電腦尺寸、鍵盤移動、滑鼠暫停、縮放、切換寬版、角色／語言保留及手機不重複嵌套。舊桌面角色回歸可指定 `TENTEN_URL` 為帶 `layout=wide` 的遊戲網址。

手機直向、橫向皆可遊玩；旋轉時持續遊戲並釋放舊搖桿觸控，切到其他 App 仍會自動暫停。
全螢幕及加入主畫面不再鎖定橫向。手機直向寬度不超過 600px 時：

- 技能固定在右下角 2×2 四格，道具放在技能上方；浮動搖桿可在空白處拖曳。
- 血量、計時與暫停分列，鏡頭維持可辨識的角色大小，選單／三選一／設定可直向捲動。
- 「設定 → 控制 → 配置按鈕」可個別儲存直向與橫向布局，重設只影響目前方向。
- 底部版號縮為單行，避開拇指操作區，並保留瀏海及底部手勢安全距離。

`G.Touch.controlLayout()` 統一實際 HUD 與編輯器的矩形；直向設定使用 `padPortrait`，
原橫向 `pad` 保留。直向樣式位於 `.omx/mobile-portrait.css`，由入口產生器載入。
`G.Camera.viewportScale()` 同時供一般鏡頭與數碼寶貝尺寸調整使用，避免直向縮放被覆蓋。
執行 `python .omx/check_mobile_portrait.py` 驗證五種尺寸、觸控移動、雙指切招、暫停、
旋轉、三選一與布局儲存；此為瀏覽器手機模擬，實體裝置的瀏海、主畫面模式與效能仍須實機觀察。

Generation 11 follows Digimon in collection and gacha. The Naruto button appears
in the top navigation and in the first-time Digimon picker. Eight characters are
available: Naruto, Sasuke, Sakura, Kakashi, Hinata, Rock Lee, Gaara and Itachi.
Choosing a ninja uses the existing sandbox save without resetting the collection.
Naruto characters do not use the Digimon evolution system.

Twenty-seven adapted skills cover three character techniques per ninja, with
Naruto also learning the Nine-Tails Chakra Cloak and Sasuke learning Fuma Shuriken,
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

另有三選一「吸血 +1%」卡，每次增加 1 個百分點的傷害吸血比例，可重複疊加且不占技能槽。例如 3 層時造成 100 傷害，回復 3 點生命；小額回復保留小數，最多補至滿血。適用於有玩家傷害歸屬的忍術、影分身與一般招式，死亡後不會靠吸血復活，新一局重新計算。程式與單次加成在 `.omx/lifesteal.js`。

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
例如選過 2 次，分身各級為 10／18／26／34／42，千鳥各級追擊次數為 7／12／17／22／27。
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
Sasuke has an additional guaranteed level 9 choice: Fuma Shuriken.

Each role retains the four-slot choice system and can decline a learning card.
When full, an explicit card can replace a shared ninja tool in place, retaining
its key binding. Extra-starting-move perks cannot bypass character level gates.
Cooldowns and effect details are available in the source-backed in-game guide.

## 九尾查克拉外衣（紅色一尾）

新增鳴人限定的 `naruto-nine-tails-cloak`，角色 Lv.9 起出現在三選一。
舊版本存留的共通忍具可在滿四槽時被特色技能替換，沿用原槽位與按鍵；不自動刪除已學的特色忍術。
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

## 佐助：風魔手裏劍（大型手裏劍）

`naruto-fuma-shuriken` 為佐助限定，Lv.9 起保證出現在三選一；
豪火球 Lv.3、寫輪眼 Lv.6 的學習順序維持。舊版本忍具占滿槽位時可被特色技能替換，保留槽位與按鍵。

參考 [TAMASHII NATIONS 官方少年佐助資料](https://tamashiiweb.com/item/14256/?wovn=en)：
明確記載佐助在再不斬戰使用風魔手裏劍，並展示大型四片彎刃、中央握環的忍具。
另有 [BANPRESTO 官方場景商品](https://bsp-prize.jp/item/2643350/) 對應波之國篇的持武器姿勢。
此招是實體忍具，不等同鳴人的螺旋手裏劍；不附加爆炸或燃燒。自動弧形返回是本版的遊戲改編，不宣稱為原作效果。

| 設定 | 基礎值／意義 |
| --- | --- |
| `cd: 1.6` / `charge: .2` | 冷卻 1.6 秒、投出前準備 0.2 秒 |
| `dmg: 34` / `count: 1` | 每枚基礎傷害 34，一次 1 枚 |
| `speed: 460` / `life: 4` / `range: 552` | 基準飛速、最多存活秒數與選敵距離；回到佐助身邊立即回收 |
| `fumaReturn: true` / `boom: .65` / `fumaCurve: 130` | 去程 0.65 秒、大弧線中段側彎 130；再弧形返回並追隨佐助，穿透耗盡時提早返回 |
| `size: 32` / `pierce: 3` | 寬幅碰撞、去回各最多命中 4 名敵人，同敵每程一次；牆仍會阻擋 |
| `arc: .24` / `knock: 24` | 無有效目標時用前方方向差；命中施加擊退 |
| `vis.projScale: .9` | 35×35 像素造型以固定比例顯示，準備與飛行時保持大小一致 |

升級依序：多 1 枚且穿透 +1、傷害 +20%、冷卻 -15%、再多 1 枚且傷害 +25%。
滿級一次 3 枚；通用「數量增幅」再加發射枚數與穿透，各枚保留完整傷害。
延遲施放沿用數量快照，不會在等待期間重複加成。回程刷新各枚獨立的命中與穿透額度；回程額度耗盡仍會飛回，但不再造成傷害。數值、往返、命中上限與 Lv.9 門檻均為本作改編。
去程採二次貝茲曲線，鎖定投出瞬間有效目標的腳底位置快照；目標移動後不會無限追逐，沒有目標時則繞向前方約 299 單位。額外手裏劍左右交錯、弧度略增，最後匯向同一快照位置。曲線子步參與敵人、物件與牆壁的碰撞，不能沿直線弦穿牆；死亡、真正移除已學技能或新局會清除，切換技能則照常返回。

這是沿路貫穿多目標的忍具，不取代佐助豪火球的爆炸範圍技。
投擲沿用原始素材的四格 `Shoot`（Perform Jutsu）動作與既有朝向鏡射；
原圖沒有獨立的風魔手裏劍投擲影格，因此不宣稱新增完整的原作武器動作。
外觀依使用者提供的風魔手裏劍參考圖改畫：四片同向反曲黑色刀身、窄銀色切刃與小型中央鉚釘，不再使用大空心握環與整片灰色刀身。
35×35 像素造型採獨立 `naruto-fuma-steel` 黑鋼色盤，保持既有大小與旋轉；不修改其他鋼系招式的色盤。刀身與旋轉特效為程式繪製，角色 PNG 保留不變。

所有平衡設定集中在 `.omx/naruto-skills.js` 同名定義；
執行 `python .omx/check_sasuke_shuriken.py` 驗證學習門檻、替換、數量、貫穿、牆體與畫面；`python .omx/check_fuma_return.py` 驗證弧形往返、移動追隨、每程傷害與清除。

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

## 目前開放角色

火影 beta 暫時只開放鳴人（30001）與佐助（30002）。`.omx/naruto.js` 的 `availableDexes` 集中控制開放名單；其他角色的資料、素材與已擁有／升級紀錄均保留。數碼寶貝由 `.omx/digimon.js` 的 `enabled = false` 暫停開放，隱藏選角、圖鑑世代與抽卡入口，直接呼叫選角也無法選取。舊存檔若使用停用角色，進入時會切回鳴人，保留其他進度；已選佐助與寶可夢不受影響。恢復開放時修改這兩處設定並重新載入即可。

## 寫輪眼五階段進化

寫輪眼已改為[五階段進化型被動](sharingan-evolution.md)：一勾玉 → 二勾玉 → 三勾玉 → 天照 → 須佐能乎。學會後切換到其他攻擊仍生效；完整效果、可調數值與原作／改編界線見該文件。

## 千鳥分級追擊

發動千鳥時保存佐助原位與鏡頭中心。整個連段固定鏡頭並關閉畫面震動；首次及後續目標皆限於該畫面邊界加上 `config.screenPadding`（48 世界像素），不能一路追到遠方。達到追擊次數或找不到下一個合格目標後，以 `config.returnDuration`（0.12 秒）快速回到原位，回程不造成額外傷害。去回程皆無敵，返回完成後才開始收招保護及最低冷卻。死亡、換場或清場則直接解除鏡頭鎖定，不把失效角色拉回舊位置。

同一連段每命中一名敵人，下一段突進速度增加基礎速度的 15%：1000 → 1150 → 1300…，最高 3000 世界像素／秒。轉向間隔每次乘 0.85，最低 0.012 秒。每次重新施放從速度 1000 與初始轉向間隔 0.045 秒重新計算。調整 `.omx/naruto-chidori.js` 的 `config.speedStep`（0.15）、`maxSpeedMultiplier`（3）、`retargetDelayDecay`（0.85）、`minRetargetDelay`（0.012）即可修改加速曲線。每段開始時保存該段速度，移動仍逐 4 世界像素處理，避免高速略過命中。

傷害另依成功命中次數複利遞增：第一擊原傷，之後每擊再乘 1.05，第 n 擊倍率為 `1.05^(n-1)`，不設增傷封頂。滿級 25 次加上 20 層數量增幅，最多 45 擊，第 45 擊約為原傷 8.56 倍；增加數量仍會繼續累乘。重新施放時從原傷開始，不跨連段繼承。調整 `config.damageStep`（0.05）可修改每擊增幅；既有暴擊、屬性、傷害歸屬與吸血照常套用。

千鳥實際冷卻至少 0.5 秒（`config.minCooldown`），技能升級與冷卻加成無法降到下限以下。連段結束返回原位後，至少等待 0.5 秒才能再次施放；若剩餘冷卻更長，保留較長時間。

佐助千鳥命中後自動選取範圍內除了上一個命中者以外的敵人，同一目標可以隔次再次追擊：允許 A→B→A→B，不允許 A→A。Lv1～5 基礎追擊上限依序為 5／10／15／20／25 次，數量增幅每層再加 1 次；這些是總命中次數，不是不同敵人的數量，回頭命中同一目標也會繼續累積速度與傷害。例如 Lv1 加一層為 6 次，Lv5 加三層為 28 次。突進直接穿過牆壁與障礙物；僅剩上一個目標時返回原位，玩家死亡或清場則取消。基礎傷害 44、冷卻 1.05 秒，升級沿用原本傷害與範圍加成。施放瞬間保存技能等級與數量增幅，途中升級或增加被動在下次施放才生效，不重複計算數量加成。

`.omx/naruto-chidori.js` 的 `config` 集中控制 `counts`（凍結陣列 `[5,10,15,20,25]`）、`followupRangeMultiplier`（3）、`endInvulnerability`（0.3 秒）、`speed`（1000 世界像素／秒）、`retargetDelay`（0.045 秒）與移動細分距離 `step`（4 世界像素）。首擊搜尋與突進維持技能原射程 170；命中後，後續搜尋與實際突進上限同步增為三倍（510），升級射程時同比例增加，較分散的目標也能連續追擊。結印時間仍由技能定義 `charge`（0.09 秒）控制。飛行期間阻擋受傷；結印與轉向間隔正常受傷。已開始突進的千鳥自然結束、找不到下一個敵人或耗盡射程時，再給 0.3 秒收招無敵（保留更長的既有無敵）。結印取消、死亡、換世界或清場不補無敵。此分級追擊與飛行無敵為使用者指定的遊戲改編，並非宣稱漫畫原作設定；千鳥名稱的原官方來源仍見技能圖鑑。

## 生命剝奪卡牌

戰鬥右上角的「已獲得屬性」由 `.omx/run-attributes.js` 顯示這局選過的永久能力牌，隨選牌即時更新，重開局清空；即時回血不列入。攻擊、移速、冷卻、拾取與經驗以卡牌累積倍率顯示，減傷顯示目前永久減傷比例，數量、吸血與生命剝奪顯示目前局內累積值。手機直式面板避開計時、Boss 血條與觸控操作區。

局內三選一新增「生命剝奪 +1%」，不佔技能欄。每選一次，玩家每次命中額外造成目標「最大生命值」的 1%，第二次為 2%，可重複疊加、不設上限；新局歸零。修改 `.omx/percent-health-damage.js` 的 `perPick` 可調整每層比例。

額外傷害與原傷合併為單次命中，先扣護盾，再扣血；普通怪與 Boss 使用相同比例，不再乘攻擊、暴擊、屬性或千鳥連段倍率。千鳥每次追擊、風魔手裏劍每次有效命中、分身攻擊、豪火球每次傷害脈衝，以及寫輪眼反擊、天照黑炎與須佐能乎命中均適用。範圍攻擊對每個被命中者分別計算；同一次命中不會遞迴觸發。這會讓多段與範圍技能有明顯的後期成長。

沿用原本傷害統計與吸血慣例，包含護盾吸收與過量傷害；額外傷害有玩家歸屬且可觸發吸血。沒有玩家歸屬的原版燃燒、毒素、地形熔岩不觸發，敵方攻擊與遠端純視覺分身也不觸發。岩石頭盔的玩家反擊可觸發。

## 敵方支援怪上限

敵方支援怪沿用原作者 main 的限制：回血、護盾、召喚寶可夢各自最多同時存活 3 隻。滿額時改刷目前名單內其他未滿額敵人；若整份名單都已滿額，略過該次生成。死亡後名額立即釋出，所有玩家共用同一組上限。設定為 `js/systems/spawner.js` 的 `SUPPORT_MAX`，驗證可執行 `node tools/test_support_cap.js`。

## 開局永久強化全滿基礎

個人版本由 `.omx/starter-balance.js` 的 `G.StarterBalance.enabled` 控制，預設開啟。每次開局直接使用 `G.Upgrades.LIST` 所有強化的最高等級及原有 `perks` 公式；包含生命 +80、傷害 ×1.4、速度 ×1.24、冷卻 ×0.76、減傷 16%、每秒回復 1、拾取 ×1.72、經驗 ×1.4、金幣 ×1.64、暴擊 30%、起始最多 2 招、額外重抽 5 次及禁招 3 格。

苦無投擲與手裏劍散射已從火影學習池、升級卡與圖鑑說明移除；保留底層定義供寫輪眼反擊等內部機制使用。火影開局尚未解鎖其他特色忍術，因此先持有主技能 1 招，角色 Lv.3／6／9 才依原門檻追加特色技能，不為湊足兩招提前解鎖。

新玩家與已買滿的玩家得到相同基礎，不會重複相加；不修改金幣、購買紀錄、禁招選擇與按鍵。局內升級仍可繼續加強，火影專屬忍術的等級解鎖條件不變。停用 `enabled` 即恢復依已購買等級開局。

## 君麻呂試玩版（2026-10-28）

目前十一招（含白骨壁與骨回力鏢）全部學會即自動生效，不需切換、不占主動欄。仍需按原等級花正常學招選擇；早蕨Lv12首次解鎖優先出卡，不要求先拿羈絆。舊主動配置會遷移並保留技能物件／階級／冷卻。實際驗證為 `python tools/test_kimimaro_all_auto.py`，完整規則見 `art-review/kimimaro-all-auto.md`。

追加角色30012，不改原有角色ID。正式入口可選君麻呂：Lv1柳之舞為常駐普攻；Lv3椿／十指穿彈／骨回力鏢、Lv6唐松／鐵線花・蔓／白骨壁、Lv9鐵線花・花／鬼百合、Lv12早蕨加入學招候選；Lv15可學地之咒印。攻擊招式依條件與各自冷卻公平輪流施放，蔓花可自動連動；咒印與白骨壁各依自身條件觸發，骨回力鏢接回且1秒基礎冷卻結束後再射，不一次贈送未學招式。

實際戰鬥模組為 `.omx/naruto-kimimaro.js`，美術由 `art-review/kimimaro-art.js` 按需載入。普通與咒印二各24姿勢，含正背常用動作、受傷與倒下；攻擊採側向與明確左鏡射。三張執行圖約645KiB、解碼約3.99MiB，共用72骨柱／20次要粒子上限。不載入獨立預覽場景、假敵人或整個設計來源包。

驗證執行 `python tools/test_kimimaro.py`，預設測試8341埠；本機建議用 `python tools/serve_animation_lab.py --port 8341`，避免一般HTTP伺服器的小型連線佇列漏接大量同時腳本請求。設計與試玩交付紀錄在 `art-review/kimimaro-playable-delivery.md`。
