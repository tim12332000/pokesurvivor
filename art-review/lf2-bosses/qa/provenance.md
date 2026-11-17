# LF2 隱藏角色 QA 來源與範圍

## 最終候選

`tools/test_lf2_bosses.py` 從正式選角入口啟動。Firzen、Julian 各六組受控檢查通過且來源穩定、零頁面錯誤：progression、mechanics、identity、growth、lifecycle、contactBoundary。包含原作釋放／接觸窗、真飛行與多目標範圍、牆與障礙、普通拳／條件式衝拳、移動與撤退、實際數量卡與上限排除、巨大化真手程、暫停／死亡／退學／換世界／局次及同波第一靶取消後的第二靶、分身歸屬隔離。

四份自然局均使用全新訪客、Lv1、零永久升級，僅透過真鍵盤或 CDP 觸控事件操作原生搖桿、實際點選出現的成長／道具卡。不直接修改角色等級、HP、XP、AI、敵潮、遊戲時間或技能時計。生命與屬性因真選卡正常成長。每局均取得全角色技能實際本體傷害，並在最後招牌首次命中後至少八秒、該招所有在途效果收束後才結束。

| 角色／輸入 | 遊戲秒 | 結束等級 | 實選卡 | 生命 | 完整招牌收束 |
| --- | ---: | ---: | ---: | --- | --- |
| Firzen 桌機鍵盤 | 87.84 | 8 | 7 | 314.6/314.6 | 是 |
| Firzen 390觸控搖桿 | 99.86 | 6 | 5 | 260/260 | 是 |
| Julian 桌機鍵盤 | 98.76 | 8 | 7 | 341.38/350 | 是 |
| Julian 390觸控搖桿 | 109.75 | 9 | 8 | 261.14/280 | 是 |

## 錄影與來源差異

每局 `natural-*` 目錄保存原生影片、實選卡截圖、逐招首段／接觸／收勢和獨立效果／消散取樣、完整 observer ledger。影像不是靜圖拼接。`final-cycles` 為另行受控 Lv30／技能一階、高HP零傷害靶的原生 RAF 演出，沒有手動推戰鬥時計；它不算自然成長。兩角最終循環檢查 `sourceStable:true`，來源／影片SHA保存在上層 `verification.json`。

Firzen 桌機自然局期間只有 `.omx/lf2-firzen-combat.js` hash 改變；作者說明為母彈升空與子彈繼承高度的 lift metadata 修正。**不能把該整份影片標成最終 hash 相同。** 此局保留原 before/after hash；當前候選另有來源完全穩定的 Firzen 手機自然局與桌機 final-cycles 原生演出，補核完整技能、成形、升空分裂與收束。Julian 兩自然局及 Firzen 手機自然局均來源穩定。

最初兩次同時錄影啟動 Julian，在進局前出現多個原生 JS 模組 undefined 並 timeout；失敗JSON保存為 `julian-natural-report-boot-failure-1.json` 及 `julian-natural-mobile-report-boot-failure-1.json`。改為安靜伺服器8768、逐局啟動後，同一產品可正常開局完成。這是進局前載入失敗紀錄，沒有改產品壓過錯誤，亦不假稱為自然遊戲死亡；原因未以未驗假設定論。

## 未驗

390瀏覽器與真觸控事件不代表實體手機長局；未驗多人網路、30分鐘耐久或真人音效聽評。來源音效接線與有音軌不代表已聽評。這些結果證明契約、自然成形與演出，沒有代替使用者主觀好玩判斷。

最終原生片完成後，主代理重新產生入口，只更新各 script／stylesheet 的快取查詢字串；移除查詢字串後 HTML 完全相同，runtime 與素材 bytes 未改。核對記錄為 `.omx/state/lf2-bosses/final-entry-update.json`。因此不把新入口 hash 冒稱舊影片來源，亦不因純快取字串變動重跑整份自然局。
