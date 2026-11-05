# 文太直接噴火

依使用者「希望文太直接噴出火焰」調整第④／⑤階：取消吐油、鳴人起爆符投擲與接觸點火，改為召喚後 3.1 秒由文太嘴部直接噴出火焰。這是本作玩法改編，不宣稱原作中可獨立施放的招式。

油炎持續 0.75 秒，前 0.25 秒向前伸展至 240；半寬由嘴部 12 漸增至末端 67。最後 0.15 秒收束，命中射程同步收回。每個敵人每次最多受到一次當階基傷 50% 的火屬性傷害。數量卡不增加噴火次數；障礙阻擋命中與火焰顯示。死亡、世界切換、清場立即終止，暫停不推進。

已開始的連段不再因清光敵人而取消噴火；無目標時沿最後朝向完成噴吐。張嘴圖使用獨立嘴部錨點，油炎由同一點向前下方噴出。同步重新產生本機入口的腳本雜湊，避免仍引用舊版。新增清空敵人後仍進入火焰階段的回歸案例。

## 專用演出重製

使用內建 `image_gen.imagegen`，以既有 `gamabunta-oil-v1.png` 為畫風及角色參考，產出兩張透明圖：

- `art-review/redrawn/gamabunta-breath-actor-v1.png`：保留鼓腮／張嘴兩姿勢，移除烘焙在張嘴圖中的油柱與油滴。
- `art-review/redrawn/gamabunta-oil-flame-v1.png`：油火合一的六格手繪動畫；起噴、擴張、三格翻捲循環與收尾。

刪除重複疊放通用小火焰的繪製，改為單一完整火流圖。每格明確登記裁切區與出嘴錨點，使用自然輪廓縮放完成起收，不以裁掉尖端製造伸展；障礙仍裁切可見區域。左右使用鏡射，不宣稱獨立八方向。

完整提示詞位於 `art-review/naruto-summoning-oil-flame-prompts.json`；輸入／輸出雜湊與透明度紀錄位於 `art-review/naruto-summoning-oil-flame-provenance.json`。兩張新圖已列入打包名單，未新增依賴。連段測試驗證六格皆由專用圖集繪出，桌機／手機各保留起噴、擴張、三個循環與收尾畫面。

本機 `allSkills=1` 正常遊戲迴圈另驗證全五階鳴人，在文太連段 2.7 秒後清空敵人，仍於 3.1062 秒開始油炎，3.4277 秒顯示翻捲影格。當時存活敵人數 0、五招皆五階、瀏覽器錯誤 0；資料見 `.omx/state/naruto-summoning/combo/native-empty-wave-report.json`。

更新 `.omx/naruto-summoning.js`、中英文技能說明與 `tools/test_naruto_summoning_combo.py`。此規格取代舊連段審查中的油區／起爆符點火流程。

驗證：`python tools/test_naruto_summoning.py` 與 `python tools/test_naruto_summoning_combo.py`，正常入口桌機／手機皆通過。噴火三個範圍內敵人傷害為 `[177,177,177]`，側面與射程外敵人皆為 0；包含左右朝向、牆壁、單次傷害、暫停、死亡及場景清除。截圖及報告位於 `.omx/state/naruto-summoning/combo/`。
