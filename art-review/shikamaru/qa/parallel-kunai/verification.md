# 鹿丸：同時捕捉與苦無連投驗證

本輪為單招調整；後續已依使用者授權發布，詳見[發布紀錄](../../parallel-kunai-publishing.md)。保留工作區既有修改，無新增依賴。

## 變更檔案

- `.omx/naruto-shikamaru.js`：固定投影光向；取消 A→B 依賴，各分支從玩家出發；鎖定後各自連投苦無，以飛行掃掠碰撞逐枚結算，繪製在途苦無。
- `art-review/shikamaru/reference-shadow-geometry.js`：來源動畫格遮罩快取；取消投影光柵讀取／逐像素遮擋與接觸掃描，改用仿射投影、可見區裁切、至多32個輪廓支點與解析身體掃掠。
- `.omx/naruto-skills.js`、`.omx/naruto.js`、`.omx/jujutsu-growth.js`：同步招式說明、選角介紹、同時捕捉與苦無枚數成長預覽。
- `tools/test_shikamaru_parallel_kunai.py`、`tools/test_shikamaru_geometry_perf.cjs`：新增針對本輪契約的回歸驗證。

## 驗證證據

`python tools/test_shikamaru_parallel_kunai.py` 通過，詳見 `report.json`。

- 正式入口載入：三階同時捕捉3名目標，各真實命中4枚，捕捉當下不直接扣血。
- 上限16個目標各5枚，共80筆獨立傷害，沒有裁掉攻擊。
- A死亡不影響B/C；移開、牆阻、暫停、死亡、換世界、退學與清除均通過。
- hurt／onDealt 回呼清除後，同輪其他目標與未來苦無不補傷害。
- 原生RAF自動戰鬥成功完成3目標各4次命中，鍵盤移動通過。
- 實看桌機與390寬截圖，多條影子與在途苦無可見；視覺判定存於 `.omx/state/shikamaru-parallel-kunai/ralph-progress.json`。

`node tools/test_shikamaru_geometry_perf.cjs` 通過：100次移動投影只讀一次來源像素；至多32個輪廓支點；高速、越頂與牆阻驗證通過。

5個修改的JavaScript均通過 `node --check`；`git diff --check` 通過。

## 限制

這是受控機制與短時間原生戰鬥驗證，不是手機實機長局效能、完整自然養成或玩家主觀樂趣認可。來源動畫格初次建立遮罩仍讀取一次像素；移動投影、地影接觸與苦無判定不逐像素掃描。舊A→B接力與投影光柵陣列測試反映已替換的行為，未宣稱全套舊測試通過。
