# 企劃／成長規則實作交付

本輪使用者已授權實作。此檔描述本工作範圍已寫入的程式與已跑驗證，不把同儕負責的戰鬥行為／全局平衡當成自己已驗收。

## 擁有及修改的檔案

- `.omx/jujutsu.js`：12招的三／五階功能參數與原生升階說明，既有角色ID、學習等級、傷害階梯與四招成本保留。
- `.omx/jujutsu-growth.js`：共用卡片受益查詢、原生候選前資格、數值預覽、保留通用選項、能力型羈絆分類及安全消費。
- `tools/test_growth_contract.cjs`：使用正式Moves／LevelUp／Training模組的合約測試。
- 本目錄新增驗證JSON與文件。未改別人負責的三個戰鬥模組、VFX、game入口或UI。

## 三／五階功能參數

每次仍是原本一次`up:`選卡。未新增免費專精、角色副本、貨幣或操作鍵。傷害升階仍按原1／1.2／1.45／1.75／2.1，功能修改與既有升階同次取得；數值為待平衡版本。

| 技能 | 三階 | 五階 |
| --- | --- | --- |
| 刀斬 | 真命中標記1.2秒，里香優先該可達目標 | 扇角2.5弧度 |
| 里香 | 接近速度650 | 半徑126、返回速度720 |
| 咒言 | 普通敵人移動限制1.5秒 | 半徑／射程184 |
| 完全顯現 | 結束後基礎恢復10.5秒 | 結束後基礎恢復9秒；基礎為12，持續6秒不變 |
| 基本額砲 | 優先可達精英 | 射程414 |
| 散射 | 砲道間隔0.24弧度 | 基本道數4，乘算後cap9 |
| 爆破 | 半徑108 | 優先可達敵群密集位置，仍起手鎖點 |
| 全力砲 | 砲線上首個有效目標+15%直接傷害 | 射程495，寬度不變 |
| 空面打擊 | 弧度1.15 | 普通敵人推退18，特殊不搬動 |
| 宇守羅彈 | 弧度2.1 | 普通減速25%／0.45秒，特殊弱化 |
| 天空幕 | 只在預測0.55秒內入界敵彈時部署 | 真攔截授予一次3秒內下次宇守羅彈+15%條件紅利 |
| 空面震落 | 半徑126.5 | 普通減速60%／0.8秒，特殊弱化 |

定義寫在 `G.Jujutsu.functional`，戰鬥作者已直接確認欄位並回報實際命中／目標／條件消費驗證；最終瀏覽器驗收由QA與主代理執行。

## Growth API

```text
G.JujutsuGrowth.quantityBenefit(player)
  {id, eligible, before:Q, after:Q+1, consumers[], text}
  consumer = {id,name,before:{數值名:數值},after:{...},nextChangeAt,nextChanged}

G.JujutsuGrowth.benefit(player, statId)
  {id,eligible,before,after,text}（沒有自訂預覽的原生卡維持合法性）

G.JujutsuGrowth.preview(player, nativeCard)
G.JujutsuGrowth.legalOffers(player,n=3)
G.JujutsuGrowth.bondState(player)
  {mode:'fusion'|'bank'|'growth',reason,options:[nativeCard,...]}
G.JujutsuGrowth.applyBondCard(player, issuedCard) -> boolean
G.JujutsuGrowth.registerQuantityConsumer(mode,pureReadFunction)
```

新模組應在所有卡片／訓練包裝後、main前載入，由主代理負責入口及打包。`legalOffers(p,100)`供標準配裝取得目前所有原生合法候選，原生`apply`、學習門檻／封禁／rank成本維持；不直接塞技能或改十九次卡數。

### Quantity

乙骨／烏鷺沒有count consumer時不出卡；單純有自身分身不算。石流散射讀shared `G.Quantity.count`、基數3／五階4、cap9。3→3仍可累積，預覽顯示到下一個有效門檻需要幾張；所有consumer封頂或到20張才排除。

現有角色亦按實際模組公式保留受益：影分身、千鳥追擊、小李束縛／裏蓮華連擊、砂彈／砂縛柩／砂護衛、君麻呂目標／指骨／骨迴旋及穿透、手鞠風刃／切擊／召喚／颱風／反射、沛恩基礎彈／飛彈、天天忍具、草薙劍與原生count型招式。Pain的公開`projectileCount(owner,m)`已核對為純Q容量函式；手鞠`snapshot`會建立actor state，故預覽改用其公開純mastery／heavy公式而不呼叫帶狀態的snapshot。君麻呂骨盾沒有Q消費，未虛列為consumer。

### 原生選卡

Quantity、立即回血與已到基礎減傷上限的卡在原生抽選前先套`eligible`。保留原生候選與權重；特色保底衝突時若有合法通用卡，三格至少保留一格通用選擇，不全部塞特色招。`onShown`仍只在真正UI顯示時消耗，不因預覽或列全部候選改掉首顯機會。

### 羈絆

不按JJK dex硬列例外。有`bondOptions()`就保留fusion；沒有時以隔離Player複製目前moves／已融合slots，沿真正addMove包裝嘗試完整可學池，判斷是否有未來合法融合。這能分開「一級手鞠尚未學足」與「完整鳴人只有一個主動群組」。探測結果依有效池與激活簽章快取，清除probe擁有的戰鬥狀態，不改玩家／存檔。

結構性無融合時提供一次當前有效的原生成長選擇，不加角色level。這是一個可消費的共通fallback，並未宣稱一張成長已與原融合強度等價。主代理UI顯示原因與選項；失去有效選項仍bank，不吞token。

`applyBondCard`只接受發給當前玩家的該次卡實例；檢查狀態簽章、資格、剩餘bond、角色存活，成功後才扣1。已選卡、改狀態舊卡、舊局owner、被封禁／已無效的卡均拒絕；同一張不能二次消費。

## 已完成驗證

- `node tools/test_growth_contract.cjs`：PASS。使用正式Moves、LevelUp、NarutoTraining、Quantity及JJK註冊；22項三／五階實例與原生levelUp欄位、3→3→4、cap9、無consumer卡排除、滿血回血排除、只預覽不花卡、原生升階成本、三態reward、成功一次消費、變狀態舊卡拒絕。
- 正常Chrome九組能力查核：乙骨／石流／烏鷺20級、手鞠1／20級、鳴人／沛恩／君麻呂／我愛羅20級。零JS錯。手鞠1級bank，手鞠／我愛羅完整可融合，其餘結構性無融合者growth；growth成功只扣一個bond，重複套用拒絕。滿血均無軍糧丸。
- 原始查核結果：`growth-native-check.json`。這些20級是機制測試，不冒稱自然成長平衡局。
- 兩個修改JS的`node --check`通過。

待整合驗證：原生獎勵DOM選卡與局次清理、六路線同預算對照、共同快照／脈衝的完整戰鬥、手機與打包。這些由分工中的主代理／QA接續，不把本單元合約通過當成整體完成。
