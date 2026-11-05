# 四Agent遊戲設計與互評結果

**後續已授權實作，正式整合首版已可玩：[新版網址與實作紀錄](runtime-release.md)。** 本頁下文保留設計／互評階段紀錄。

本輪已完成四人並行獨立設計、直接交叉問答及共同稿複核。遊戲產品程式保持原樣；新增的是設計、證據和獨立可執行的程式特效原型。

**主文件：[共同遊戲設計](shared-design.md)**

**可操作CODE原型：[光束／天空折面／刀痕](http://127.0.0.1:8337/art-review/design-council/combat-vfx/prototype.html)**

## 四個角色

| Agent | 能力與責任 | 獨立設計 | 實際互評／修訂／核定 |
| --- | --- | --- | --- |
| 遊戲企劃 | 先理解有效遊戲、正常成長與獎勵，再設核心循環、角色流派和取捨 | [提案](gameplay/proposal.md)、[機制實證](gameplay/mechanics-evidence.md) | [互評](gameplay/peer-review.md)／[修訂](gameplay/revision.md)／[複核](gameplay/ratification.md) |
| 戰鬥／程式特效 | 能寫CODE、設計演算法與資料結構、製作原型、量測和定義接入契約 | [提案與做法](combat-vfx/proposal.md)、[CODE](combat-vfx/algorithms.js) | [互評](combat-vfx/peer-review.md)／[修訂](combat-vfx/revision.md)／[複核](combat-vfx/ratification.md) |
| 動漫／美術 | 核對原作與改編、角色身份、動作語意和畫面可讀性，區分原畫與程序效果 | [提案](anime-art/proposal.md)、[視覺簡報](anime-art/visual-brief.html) | [互評](anime-art/peer-review.md)／[修訂](anime-art/revision.md)／[複核](anime-art/ratification.md) |
| 玩家體驗／平衡 | 實際操作與選卡，挑戰成長成本、流派收斂、難度、手機與驗收方法 | [提案](player-balance/proposal.md)、[原生實玩](player-balance/evidence/native-playstudy.json) | [互評](player-balance/peer-review.md)／[修訂](player-balance/revision.md)／[複核](player-balance/ratification.md) |

## 討論確實改變了什麼

四人各向另外三人提出問題：12項主動交叉挑戰均有實際回覆，另有擴散等議題的追問。第一稿保留，沒有把原本歧見改寫成從來一致。

| 原先有爭議的做法 | 討論後決議 |
| --- | --- |
| 固定Lv5／6再送一層互斥專精 | 先測rank3／5功能投資；用10／19／35卡比較A/B/均衡。若長局收斂，才執行同一次二升三up的互斥形態實驗；不能宣稱較省工的軟分流已成功。 |
| 有自身分身就可能使數量牌有效 | 查到SelfClone每卡固定一隻。按真正count consumer判斷；乙骨／烏鷺只有SelfClone仍不使數量有效。 |
| 所有AOE按整cast只擴散一次 | 改按contactPulse：里香兩擊分開、石流同輪多ray共用，保留合法多段並消除主命中者互濺。 |
| 將擴散10%改成總額分攤 | MVP保留每個外圍鄰居的語意；總額分攤屬另一平衡實驗，不偷偷套用。明定primaryDirectDamage取值階段。 |
| 每owner都可配置大張背景快照 | 改全畫面總預算，保護敵方危險／玩家／HUD；capture與composite都在Hazards之前。 |
| 用Game.st判斷新局 | Game.st是穩定物件；新契約用明確runEpoch，body／companion／reaction各自有時鐘。 |
| JJK專用羈絆補償 | 原生審計發現鳴人／沛恩／君麻呂也有缺口；改全角色有效能力三態判斷，避免誤判尚未學足的角色。 |
| 先硬設兩個分身上限 | 退為壓測維度，未取得玩法／效能證據前不改傷害或存活數。裝飾可以降階，合法命中不能裁掉。 |
| 900秒就提示五王里程碑 | 等第五既定主線首領被擊敗，不混算裂縫boss，不新增收益倍率、不刪30分鐘挑戰。 |

## 程式特效Agent交出的演算法與做法

1. **額砲**：固定seed連續噪聲×漸縮包絡生成輪廓；障礙半徑外擴後做射線slab裁切，膠囊距離驗靶。外觀與命中共用幾何，釋放時只結算一次。
2. **天空折面**：共享網格頂點變形，逐三角解仿射矩陣，clip後drawImage背景裁片；原型真的彎曲背景，前景替身不改座標。另提供反射向量與DPR／相機矩陣做法。
3. **刀痕／爪痕**：三次Bezier建立弧長查表，等距取樣生成帶狀拖尾；多條視覺線仍共用指定contact事件，不能多次觸發吸血或附傷。

原型可切三模式、暫停／拖曳時間、切高低品質、DPR、相機與雙折面。實作在 [algorithms.js](combat-vfx/algorithms.js)、[prototype.js](combat-vfx/prototype.js)。詳細數學、資料結構、接入位置、效能上限與低階方案見[工程提案](combat-vfx/proposal.md)及[修訂](combat-vfx/revision.md)。

執行：

```text
node art-review/design-council/combat-vfx/test-algorithms.cjs
python art-review/design-council/combat-vfx/verify_prototype.py --prototype-only
python art-review/design-council/audit_design.py
python tools/serve_animation_lab.py --port 8337
```

## 已取得的證據與界線

- 四人均先讀現況並完成自己的第一稿，第一稿雜湊保存於[phase1-manifest.json](phase1-manifest.json)。
- 正常原生按鍵／選卡觀察、既有角色對照、20級試招，均留下原始JSON與畫面；未把隨機短局擊殺數當公平排名。
- 四份互評、四份修訂、四份共同稿複核；所有指定文字條件已逐項納入共同稿。
- 演算法Node斷言、Chrome三模式、暫停、畫質、DPR2／相機／雙折面、預算與手機版面檢查已執行。原型測量不等於正式遊戲手機FPS。
- 本輪沒有接入新玩法、實作六路線或執行540組未來平衡矩陣；未知與下一階段驗收詳列共同稿，不以設計同意冒充遊戲已平衡。

主代理逐項稽核：[completion-audit.md](completion-audit.md)。
