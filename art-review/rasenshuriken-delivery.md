# 螺旋手裏劍正式遊戲接線

採用使用者認可的第六版：立體螺旋丸球心、四片彎曲白色風刃、持續旋轉、角向殘影、像素化風刃爆開。正常入口：`http://127.0.0.1:8015/.omx/digimon.html?lang=zh-TW`。

## 變更檔案與簡化

- `.omx/naruto-rasenshuriken-vfx.js`：從認可預覽抽出共用繪製器。沿用 `G.Sprites.PX`、`naruto-blue` 五色、24 fps 旋轉取樣與影格快取；爆開依模擬時間更新，依 owner/world 清除。
- `js/entities/projectile.js`：只將 `naruto-rasenshuriken` 的繪製交給新模組，其他投射物仍走原路徑。
- `.omx/digimon-skill-combat.js`：原爆炸結算點觸發風刃演出，替換此招的通用圓環。傷害與敵人物件結算沿用既有程式。
- `.omx/make_digimon.py`、`.omx/digimon.html`：正常入口載入新模組並更新內容雜湊。
- `tools/build_digimon_site.py`：明確包含新模組，即使尚未 commit 也不漏包。
- `art-review/rasenshuriken-preview/preview.js`：移除獨立複本，改呼叫正式共用繪製器；保留第三版平滑風格對照與旋轉檢視。
- `tools/test_naruto_rasenshuriken.py`：正常入口的桌機／真實觸控直式視窗驗收。

沒有新增依賴、重繪角色圖或覆寫其他既有工作。預覽的 .48 秒蓄力時間本來是展示用；正式技能維持既有立即投擲，未將展示時間套成新的戰鬥延遲。傷害 58、冷卻 2.5 秒、速度 350、碰撞半徑 15、壽命 1.3 秒及原有分身／數量規則皆保留。

## 驗證結果

- `python tools/test_naruto_rasenshuriken.py` 通過桌機與手機兩組。開啟／停用新版繪製器後傷害完全一致；控制場景的三個範圍內目標傷害為 `[107,86,86]`，範圍外為 `0`。分身等同比對為 `[32,26,26,0]`。這些是測試角色攻擊與屬性倍率下的實際結算，非技能基礎值。
- 驗證原生自動施術、四張不同旋轉影格、暫停不推進、繪製不修改戰鬥狀態、每次碰撞僅一個爆開、持續演出不重複傷害、數量升級、實際自主影分身使用新繪製器。
- 分身卡角色的投射物與爆開保持獨立擁有權；清除卡分身不刪除本體演出。另驗證死亡、owner clear、技能 clear、換世界與到期清除。
- `python tools/test_naruto_passive_clones.py` 通過既有影分身回歸，包括五階傷害、數量、冷卻、到期、死亡與清場。
- `python tools/build_digimon_site.py` 成功；再以相同專項驗收載入 `dist-digimon`，桌機與手機均通過，繪製器雜湊一致。
- 預覽改用共用繪製器後仍可播放旋轉。變更 JS 通過 `node --check`，Python 通過 `py_compile`，接線 diff 通過空白檢查。專案沒有現成 eslint／TypeScript 設定，未宣稱執行這些工具。

證據：`.omx/state/naruto-rasenshuriken/gameplay/` 的 `report.json`、桌機飛行、手機飛行／命中截圖；打包證據在同層 `packaged/`。研究來源及逐格參考在 [預覽研究紀錄](rasenshuriken-preview/research.md)。

## 已知限制

既有 `test_self_clone_naruto_effects.py` 使用「鳴人共四招且全為主動」的舊前提，與目前影分身已改為常駐被動的工作區不符；停用本次繪製器仍在同一斷言失敗，紀錄於 `gameplay/legacy-fixture.json`。本次新增測試另行通過分身卡繪製與獨立清除驗證，未替無關測試改寫玩法假設。

沿用現有側向投擲格與鏡射，沒有新增獨立上下方向施術素材。未推送或部署線上。

後續已依新指示改為基礎冷卻 6 秒、學會後常駐自動且不占主動槽；本文件前段 2.5 秒與既有選招描述屬於演出交付當時。現行規則與驗收見 [雙螺旋常駐自動](naruto-automatic-attacks.md)。
