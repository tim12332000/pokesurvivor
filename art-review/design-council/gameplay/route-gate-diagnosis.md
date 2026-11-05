# 烏鷺19卡路線門檻：反例與量測前提校正

本次沒有修改遊戲執行碼，也沒有偷偷更換成對既有設計有利的視窗。主代理要求保留並解釋同源portrait反例，再決定是否觸發共同約定的互斥形態後備。

## 原反例必須保留

`.omx/state/council-runtime/balance-final/report.json`：540案例完成且來源雜湊穩定，但路線門檻失敗，烏鷺19卡control在四威脅／五種子支配counter。這是真正被產出的不利結果，不能因wide另有通過就丟棄。

同時，先前wide通過也不能直接當作設計已成功。需要確認「同種子」是否真的同敵群／同可走地面，而不是只比較檔名、viewport或最後green。

## 發現並實際討論的混淆

企劃檢查 `tools/test_council_balance.py` 後，指出scenario RNG原本在 `G.TrialBuild.apply` 之前設定；原生候選枚舉與加權選卡會依route耗不同數量亂數，敵人生成／起始技能CD卻接續用同一串RNG。因此相同seed不能自動保證不同配裝面對相同初始敵位與時序。

QA／主代理另確認World.walkable／Pathclear未完全隔離原生世界，viewport／camera差異會透過碰撞／路徑條件進入所謂平場比較。這不是「手機不算」或放寬門檻，而是原量測未滿足其自稱的對照前提。

## 校正後的權威focused證據

以下三份各60案例，包含烏鷺19卡×control/counter/balanced×四威脅×五種子：

- `.omx/state/council-runtime/uro19-matched-mobile/report.json`
- `.omx/state/council-runtime/uro19-matched-portrait/report.json`
- `.omx/state/council-runtime/uro19-matched-wide/report.json`

企劃已自行讀取三份JSON，而非只轉述QA結論。三份皆：

1. `ok=true`、`routeGatePassed=true`、來源前後hash相同。
2. fixture明確記錄 `flatWalkable=true`、`independentEncounterRng=true`。
3. 對每個threat／seed，比較三route完整 `initialEnemies`，其x／y／hp／spd／dmg／behavior／shotCd／skillCd逐項完全相同。
4. 沒有controlledDominance或softConvergence反例。

因此此時**沒有觸發互斥形態的有效證據**。舊wide通過和舊portrait失敗均保留為受混淆的歷史結果；不能只保留其中有利的一份。

## 後備仍在，不是刪除門檻

如後續權威完整矩陣再次在受控對照下發現烏鷺路線同質／支配，再依原共同設計啟用Uro-only同一rank2→3升階機會的A/B形態比較。已與程式特效作者準備的介面概念：

- 必須已學Screen及ThinIce才可提供；一個原升階選卡成本，不是免費天賦或新彈窗。
- `control`保清群優勢、削弱幕；`counter`可考慮真威脅時獨立reaction，不覆寫body pose，換取較低直接群傷。
- 真反射才給條件紅利，無敵彈不送免費AOE；本局只一形態，clone讀來源形態並只快照一次，不逐幀改move。
- 唯一card key需明確的moveId／formId metadata，標準配裝也須記錄選擇與成本；未通過原型／行為測試不接入正式版。

這些只是未測的後備做法，沒有寫入目前Growth／defs／combat，也沒有以調數字去湊舊測試通過。

完整900個校正案例及自然／人類／實機的驗證層級仍由主代理與QA追蹤。本focused結果只排除目前烏鷺19卡反例，不能宣稱長局或真人平衡已完成。
