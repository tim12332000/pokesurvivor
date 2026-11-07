# 當次候選驗證

2026-11-07，斑本體五組 48 格改為大頭 Q 版。內建 imagegen 原始輸出與提示集見 `generation-records.json`，所有新原圖和 runtime 圖集存於 `art-review/madara/`。

- 獨立美術與身份複核通過；正式選角、Lv1、鍵盤／觸控，以及桌機1280、手機390／360均確認新版。最後畫面與接點：`qa/candidate-final/`；同站高鳴人對照 `qa/candidate-final/naruto-madara-same-size.png`。
- `tools/test_madara_rework.py` 最終三尺寸通過，零失敗／頁面錯誤／缺檔；涵蓋學招、升階、數量卡、真正多段命中、移動與撤退、障礙、分身與生命週期。版本化摘要 `mechanics-final/summary.json`；完整當次原始資料留本機 `mechanics-final/report.json`。
- `tools/test_madara_framing.py` 三尺寸通過，完成體取景、暫停與恢復正常。報告 `framing-final/report.json`。
- 九項現行 Node 檢查通過：catalog、catalog boundary、baseline、enemy catalog、mission roster、growth contract、combat pulse、trial scope、Madara framing。
- Python 編譯、diff whitespace、48格名稱／順序、所有圖集 SHA 與PNG範圍檢查通過；非本體九組 metadata 和圖集保持原值。新版與舊生成入口重跑結果一致；舊入口直接呼叫新版，避免重建退回長身。

回歸曾抓到第一輪木分身掌擊揮空。因新圖掌點登記在手套內側 `(690,224)`，與目標碰撞差約0.09世界像素；重新實看原圖後改用同高度實際前緣 `(706,224)`，該像素alpha253。原測試未放寬、未改戰鬥程式或傷害，最終原案例第一輪命中且同一分身升階傷害 `46.12608→55.351296`，生命／動作時鐘／冷卻不重設。

範圍限制：當次是人物比例修正，沒有新增能力或調整戰鬥數值。不宣稱重跑整局自然養成、實機長局、音效聽評或替玩家證明主觀樂趣。公開版本另由發布紀錄與線上資產雜湊／正常入口檢查證明。
