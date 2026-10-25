# 六道八招：分技能 subagent 演出優化

日期：2026-10-25。使用者要求每個技能分別交由 subagent 優化；本輪八位 Codex native subagent 各自負責一招，領隊負責接線、逐幀擷取與原生回歸。依並行上限分批進行，未共用同一個技能實作任務。

## 分工與成果

| 技能 | 專責 subagent | 新模組 | 演出 | 最終畫面評分 |
| --- | --- | --- | --- | --- |
| 黑棒 | `basic_vfx` | `js/systems/pain-vfx/basic.js` | 實體黑棒與金屬邊、短氣流、發射及命中碎屑 | 91 |
| 萬象天引／神羅天征 | `gravity_vfx` | `js/systems/pain-vfx/gravity.js` | 朝內風痕與尖角、瞬間全半徑壓力圈及向外塵屑 | 91 |
| 修羅道飛彈 | `missiles_vfx` | `js/systems/pain-vfx/missiles.js` | 朝上機械發射管、升空、追蹤俯衝、尾焰／短煙、爆炸 | 91 |
| 畜生道通靈 | `summon_vfx` | `js/systems/pain-vfx/summon.js` | 通靈印、煙霧出場、真實犀牛、後蹄塵／短尾流、碰撞與消失 | 91 |
| 人間道 | `soul_vfx` | `js/systems/pain-vfx/soul.js` | 起終點瞬移殘影、手掌抓取、拉離本體的魂首、命中釋放 | 90 |
| 餓鬼道 | `absorb_vfx` | `js/systems/pain-vfx/absorb.js` | 就緒雙掌小印、真實接觸能量絲向掌心收束、整批吸收回饋 | 90 |
| 地獄道 | `repair_vfx` | `js/systems/pain-vfx/repair.js` | 既有閻王浮現／開口、倒下者局部修補、真實復活後完成碎光 | 91 |
| 地爆天星 | `planet_vfx` | `js/systems/pain-vfx/planet.js` | 保留完整月球下墜與480震波，增加下墜速度線、接觸影與波後碎屑 | 91 |

初版實際畫面檢查發現手機草地上的多項局部提示偏淡，專責 subagent 各自修正後重拍：天引描邊／向內尖角、飛彈發射高度、犀牛蹄塵、魂首分離、掌心線條對比、修復碎光。黑棒與地爆維持原尺度。天引第二輪由領隊檢視連續實際影格驗收，其餘由專責 subagent 回看整合畫面。

## 接線與原生規則

- `.omx/naruto-pain.js` 透過 `G.PainSkillVFX` 分派繪製；各模組使用原生 action、shot、effect 與 family 狀態，無獨立牆鐘計時或遊戲屬性加成。清理仍沿用既有世界／主人／暫停生命週期。
- 發射、命中、瞬移、吸收、復活的短暫視覺事件只在相應原生事件確認後產生。額外視覺事件總數受160效果上限保護，不能擠掉帶傷害的地爆震波，也不改變實際命中。
- `.omx/make_digimon.py` 與產生的 `.omx/digimon.html` 同步加入八模組，腳本版本以內容雜湊生成；`tools/build_digimon_site.py` 的既有新公開 JS 收集路徑會將八模組打包。
- 數量、傷害、冷卻、技能資格、吸收與復活機制沿用先前設定。地爆保留「整顆月球下墜觸地 → 480半徑傷害波前向外擴散」，不是僅有畫面震波。

### 使用者追加：飛彈先升空再找目標

領隊在原生戰鬥加入 `rise → seek` 階段：每枚先花0.22秒升空，期間世界地面位置不移動，也不提前碰敵；之後尋敵追蹤並逐漸降低視覺高度，接近地面才命中。原鎖定目標死亡時，在升空結束或飛行中重新選取剩餘射程內可見的活敵人。發射管及升空起點在腳底上方48處，俯衝視覺終點回到原12高度。仍維持5／5／6／7／8枚、30枚存活上限、320射程、48爆炸半徑及原冷卻／每枚傷害。

## 驗證與預覽

- `python tools/test_pain_skill_vfx.py`：八招桌機／手機正常入口、實際模組呼叫、真實犀牛／閻王來源、吸收數與復活數、重複繪製一致性、繪製前後戰鬥狀態不變，以及升空不移地面位置／不提前命中、追蹤俯衝、前後兩階段重尋敵與清場。
- `python tools/test_pain_auto.py`、`python tools/test_pain_efficiency.py`、`python tools/test_pain_planet_vfx.py`：原生並行群傷、五階數量、冷卻、吸收、瞬移、月球落地、外擴震波依距離命中、480邊界、牆體與暫停／清場。
- `python tools/test_pain_survival.py`、`python tools/test_pain_player_revive.py`：支援道生存與玩家實際復活回歸。
- 打包版桌機／手機再次核對十個 JS 檔案內容與來源相同、八模組已載入、確定性繪製及真實飛彈軌跡。證據 `.omx/state/pain-skill-vfx/build-report.json`。
- 最大數量場景同時存在40根黑棒與30枚飛彈；90次本機 Chrome Canvas 繪製樣本中位數約0.6ms、95百分位約0.9ms，清場無殘留。這是受控桌機繪製耗時，不代表實體手機幀率，亦不包含完整遊戲CPU／GPU成本。

八招動畫：`.omx/state/pain-skill-vfx/{skill}.gif`；實際手機圖：`mobile-{skill}-game.png`；連續影格：`{skill}-motion.png`。總預覽 `.omx/state/pain-skill-vfx/index.html`。每招及整體 visual-verdict 保存於該目錄下 `ralph-progress.json`。

## 查證與素材限制

各招查核來源及遊戲改編界線分別記錄於 `pain-basic-vfx.md`、`pain-gravity-vfx.md`、`pain-missiles-vfx.md`、`pain-summon-vfx.md`、`pain-soul-vfx.md`、`pain-absorb-vfx.md`、`pain-repair-vfx.md`、`pain-planet-agent-vfx.md`。本輪沒有宣稱觀看完整官方影片或逐格重現原作。

本輪採現有角色／犀牛／閻王圖集加 Canvas 演出，沒有新增位圖或依賴。閻王仍受既有四格素材限制，沒有完整吞入、吐出身體的新動畫；本輪完成的是浮現、開口、修復與實際復活收尾。手機驗證為瀏覽器尺寸與觸控模擬。
