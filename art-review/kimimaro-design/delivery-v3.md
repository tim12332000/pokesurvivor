# v3設計交付

2026-10-27。完成八攻擊候選＋咒印的設計擴充，未改遊戲執行檔。主稿 [design-v3.md](design-v3.md)，補充 [balance-v3.md](balance-v3.md)、[presentation-v3.md](presentation-v3.md)、[12格概念板](concept-extra-skills-v3.png)。新增 [計算器](calculate-v3.py)、[結果](calculation-results-v3.json)、[完整提示詞與雜湊](provenance-v3.json)、[概念審查](visual-review-v3.json)。README已標示v3優先。

使用數值與演出兩個subagent並行補稿，第三個subagent只讀審查。整合修正：穿彈逐彈瞄準與身體方向同步、花短鎖腳、單蔓與羈絆的控制時間分開、羈絆按技能ID配對不要求重排、.54秒短等政策支撐8.54秒周期、其他同組招式公平排程。增加爽感要求：柳加速連斬、穿彈雙手連射、骨鑽局部重拍、鬼百合寬幅雙圈與三波骨林。

驗證：calculate-v3.py與verify-design.py通過，檢查五階、數量上限、三敵分彈、傷害守恆、獨立CD周期及連結；另核對新圖與參考圖SHA256、完整提示詞及文字編碼。概念審查91分只對靜態提案用途；正式像素密度、比例與腳底仍需重繪。diff空白檢查通過。

限制：沒有動態動畫、音效、正式圖集、遊戲接線或實玩驗收。單蔓48傷／8秒的學習價值、15彈手機可讀性、骨鑽命中率及同組排程仍需原型。沒有把紙面算術當成已證明好玩或平衡。
