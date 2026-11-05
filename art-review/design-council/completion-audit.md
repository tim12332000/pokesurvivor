# 完成稽核

目標原文：4個Agent同時設計&之後互相討論 設計遊戲。

追加要求：程式特效具有演算法與寫CODE能力，提出用演算法產生良好效果的方式及實作做法。

| 要求 | 可接受的證據 | 目前狀態 |
| --- | --- | --- |
| 四人同時獨立設計 | 四個原生子Agent已啟動、各有獨立寫入範圍；草案完成前不互讀 | 完成。四人同時running已由原生Agent列表確認；全部first-draft-ready後才送Phase2指令。phase1-manifest.json保存四稿。 |
| 充分了解現有遊戲 | 當前有效覆寫程式引用、正常操作與選卡證據、試玩模式與正常成長分清 | 完成。gameplay/mechanics-evidence.md與native-play-report.json、player-balance/evidence/native-playstudy.json、anime-art/runtime-study.json、combat-vfx/evidence/report.json可追溯。分清max永久基礎、倍速、slotless覆寫與試玩零配裝。 |
| 四份完整設計 | 每人有核心循環、玩家選擇、三角色／流派、卡牌／成長與驗收規格 | 完成。四子目錄proposal.md已逐份檢視，包含六路線候選、機會成本、敵人與未驗證項。 |
| 之後互相討論 | 各人直接向其餘三位提出質疑；對方實際回應；保存接受／拒絕／修訂 | 完成。四份peer-review.md對應G/V/A/B各三個外送問題，12個主動挑戰均有回應，另有contactPulse等追問；四份revision.md保留真實意見變更。 |
| 共同遊戲設計 | 有共同決策、反對意見、未知項、實作順序與驗收；不把設計說成已實作 | 完成。shared-design.md與四份ratification.md；直接傷害、同卡位分歧、主線首領擊敗、每owner里香、服裝改編與預算分類條件均已落文。 |
| 程式特效演算法 | 至少三種具體演算法、資料結構／數學、可運行CODE、整合和效能／命中契約 | 完成。combat-vfx的proposal.md／revision.md／algorithms.js／prototype.js提供有界光束、分片仿射背景折面、弧長刀痕；另有Quantity／pulse／epoch／global budget純函數契約測試。 |
| 原型真的可運行 | 實際瀏覽器畫面／互動與測試輸出，不只提案文字或偽代碼 | 完成。主代理重跑Node斷言、JS語法與verify_prototype.py --prototype-only通過；evidence/prototype-peer-review.json及截圖可查。另有主代理獨立三模式事件／畫質／暫停／手機檢查與兩位同儕實開DPR2證據。 |
| 保留現有工作 | 遊戲本體、既有素材與其他未提交變更不被本輪修改 | 完成。本輪編輯工具與四位成員寫入範圍僅design-council及其證據；沒有宣稱共同方案已接入正式入口。 |

沒有完成證據的項目不得列為完成。測試通過不能代替玩法平衡實測；短期隨機實玩不代表整局或跨角色平衡已證實。

## 第三輪複核條件落文檢查

- 企劃：outgoing直接傷害取值階段、盾／overkill／附傷邊界 → 第5節明定primaryDirectDamage，連同pulse.primaryHits欄位。
- 程式特效：同一傷害欄位＋貼圖三角／網格頂點／碎片／輪廓分類 → 第5／6節。
- 動漫美術：每owner而非全場一個里香＋烏鷺服裝改編＋倍率精確 → 第1／3／7節。
- 玩家平衡：同一傷害欄位＋二升三同一張up＋第五既定首領擊敗而非900時鐘／混算bosses → 第2／3／5節。

以上四份複核都明示套用精確文字後無其他設計交付阻礙。此稽核證明設計／討論／原型交付，不證明未實作的下一版平衡。

最終可重跑檢查：`python art-review/design-council/audit_design.py` 已通過，確認四份獨立稿雜湊保持不變、12份互評／修訂／核定文件、50個本機連結、各核定修訂及最新DPR／相機／雙折面原型證據。結果保存 `.omx/state/design-council/final-audit.json`。
