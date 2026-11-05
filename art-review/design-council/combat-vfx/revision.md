# 程式特效方案修訂與目前立場

本文件取代第一稿中與下表衝突的主張；原稿保留供追溯。本輪沒有改正式遊戲程式。

## 決議狀態

| 項目 | 第一稿主張 | 討論後立場 |
| --- | --- | --- |
| 新互斥卡 | Lv6左右先加獨立互斥變體 | 修改：先卡效用＋功能rank＋固定19卡預算；仍同質才測互斥變體。第三階同一升階選擇或另吃一張卡的UI／成本尚需root定稿，不冒稱已共識。 |
| 卡片自身分身與Quantity | 寫成「可增數機制」例子 | 更正錯誤：卡片分身固定每卡一actor，不讀Quantity。繼承Q旗標不是consumer；只有其實際複製招式讀Q才有間接受益。乙骨／烏鷺加卡分身本身仍不能恢復Quantity資格。 |
| 擴散總額 | 偏好每命中10%總預算分攤鄰居 | 修改：MVP保留per-neighbor語意；總預算屬真實削弱，保留B候選、未獲採用。 |
| 擴散去重 | 每cast外圍一次 | 更正：每contactPulse外圍一次，保留里香兩個合法contact與獨立飛彈impact。 |
| CastEvent | 同型資料packet | 明確：body／companion／reaction獨立channel／clock，不立刻重寫總戰鬥引擎。 |
| Run識別 | 原稿提run token但不精確 | 明確：startRun新增遞增runEpoch／Symbol，不能使用穩定的G.Game.st指標。 |
| 特效預算 | 各owner預算，512²快照 | 改全畫面預算；本體接觸優先、分身降裝飾，任何LOD不得砍傷害／敵方預告。 |
| 折面層序 | actors之前抓背景 | 更精確：capture與composite都在WorldLiquid之後、Hazards之前；代表阻擋的props及所有危險資訊不warp。 |
| 動態幕 | 提到每三幀refresh候選 | 首版只≤0.45秒單次snapshot；持續2.3秒幕刷新另列測項，不能沿用原型的靜態draw成本。 |

## 傷害事件契約：先訂邊界，再寫效果

```text
runEpoch                         // startRun新建，不是G.Game.st
ownerId / sourceOwnerId           // 實際本體或clone，非只存角色dex
castId / rootActionId             // rootActionId僅歸屬與統計
actorKind / channel               // body | companion | reaction
contactPulseIndex / contactTimes  // 同cast可有多次真正接觸
shapeSnapshot / occlusionPolicy
primaryDirectDamage              // 原生出手輸入，不改盾/過量傷害語意
seed / emitterAnchor / visibilityClass
```

- 同一即時AOE pulse先確定primary集，再處理primary傷害與外圍擴散。primary們不互相再吃同pulse擴散；同外圍target每pulse一次，數值取能觸及它的primaryDirectDamage最大值×rate。secondary仍不遞迴，不觸發百分比附傷、吸血、控制。
- 石流一輪多射線屬一pulse；里香0.22／0.48兩contact是兩pulse；各卡分身有獨立cast及真正1/3傷害。rootActionId不拿來跨分身扣掉合法攻擊。
- 飛行彈未來會命中誰不可預知，每個原生impact即時處理；不等彈生命結束、不回滾已發生傷害。需要跨彈整輪排除時必須另設計，不能偷用AOE batch規則。
- 真正傷害事件數的去重可令外圍每pulse至多M筆；朴素找最高鄰居傷仍O(P×M)，grid只是減候選，不是假裝已證線性演算法。
- 現有原生吸血／百分比附傷／盾／overkill計算保持，任何更改都需另列平衡項，不混在「修特效」或「修文案」。

`PulseLedger`／`outerSplash`純函數只是上述去重邊界的可運行說明，**不是完整runtime服務**：正式版還要遵守原生牆／props遮擋、友方／死亡過濾與controller權限，並在cast生命結束清掉ledger；原型沒有宣稱這些已整合。

## 全畫面特效資源預算（假說，非效能保證）

| 資源 | 桌機初測 | 手機初測 |
| --- | --- | --- |
| 同時背景快照 | 2×512² | 1×256² |
| 應用層RGBA像素下界 | 2MiB | 0.25MiB |
| 貼圖三角片總額 | 48 | 12 |
| 共享網格頂點上限 | 96 | 較低品質網格 |
| 裝飾碎片總額 | 24 | 優先減少，不改碰撞 |

瀏覽器／GPU可能額外保存、合成或雙緩衝，不能把RGBA下界說成總記憶體上限。未量測texture upload／GC／實機熱降頻。

分配：本體正在接觸的cast優先，其次可見分身／距鏡頭較近者，以castId穩定排序；已分配快照可固定到本次短效果結束，避免每幀搶奪跳閃。超額仍畫一條主折線＋兩片有明暗面的平面，不能變成魔法圈或完全不顯示接觸。敵方可傷預告與命中輪廓優先於友方碎片，不因Q／分身增多而被budget淘汰。

正式render提案位置：

```text
World.drawGround
World.drawLiquid
[新增背景特效hook：局部capture + mesh composite]
Hazards.draw
Combat.drawGroundFields（保持危險輪廓）
按Y排序的props/actors
Projectiles / 其他安全排序的特效
HUD
```

能影響實際路徑的props輪廓不進扭曲快照。若未來某動態地面hazard被背景shader覆蓋，需搬其預告到安全層／遮罩排除，不以「它仍有碰撞」辯護。

## 實際原型與測試修訂

1. 可操作原型新增DPR2、相機位移、雙fold；高品質兩fold共48貼圖三角、低品質主fold12片＋副fold兩個平面。實際背景紋理在變形、前景替身未被貼進快照。
2. 原型共用一張靜態程序背景，不是正式遊戲的snapshot allocator；其全局分配函數可測選取與tri預算，但沒有把GPU／畫面capture成本當成已驗證。
3. Node新增：Quantity3→3但保留下一張達4的累積預覽；cap已滿失效；有／無count consumer；clone copied skill相同收益；同pulse重複target拒絕、下一pulse保留、獨立clone保留、換epoch拒絕；n=1/3/10 primary×m=0/3/20 outer矩陣；遍歷順序不變；DPR1/2與相機仿射映射／反算；多cast全畫面budget。
4. Chrome實際驗證DPR2 backing1720×980、camera開啟、雙fold高48片／低12＋2平面，暫停時間與接觸事件在切換品質後不變；無pageerror。`evidence/prototype-peer-review.json`與兩張新截圖留存。

執行：

```text
node art-review/design-council/combat-vfx/test-algorithms.cjs
python art-review/design-council/combat-vfx/verify_prototype.py --prototype-only
```

## 仍需驗證／保留分歧

- 功能rank在第一首領前及19卡配裝是否真的形成不同走位／失敗情境；長局全滿會收斂，這是可接受的後期終局還是需永久形態分歧，尚未有玩家資料。我的立場是不先新增互斥卡，也不宣稱投資順序本身就足夠。
- 總額分攤Splash候選B明確會削弱單體命中周圍5怪時每怪10%→2%的體感；需標示改動並做A/B，不是本輪共識。
- 真正手機預算需要64移動怪、fan/ranged/beamer、0/2/6卡分身、Q/CD/擴散不同投資、DPR1/2、相機位移及單／雙端的壓測，記p95/p99/max與輸入延遲；原型靜態平均值不支持這個結論。
- 一般完整遊玩、自然20級19卡、20級白板試招仍分開，不把本次原型或既有20級URL當整局平衡證明。
