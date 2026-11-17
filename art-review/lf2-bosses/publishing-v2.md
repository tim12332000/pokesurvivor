# LF2 完整原招修正版：已發布並公開核對

[遊玩 Julian 邪鬼](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=julian&release=d46395d6)／[遊玩 Firzen 冰火人](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=firzen&release=d46395d6)。

使用者要求所有技能後，前版省略 Mirror Image 的完整結論已撤回。本版依原包 readme 保留 **Firzen 原三招＋Julian 原六招**，每招都有實際功能、正式學習與HUD／技能說明；沒有再以功能取捨省略原招。

| Julian 原招 | 正常學習 | 真實功能 |
| --- | --- | --- |
| Skull Blast | Lv1 | 原五發骷髏逐次飛行與接觸 |
| Soul Punch | Lv2 | 向近敵移動時的實體前衝、接觸和原收勢；撤退不強拉追身 |
| Uppercut | Lv3 | 原上勾拳兩個接觸窗與完整收勢 |
| Mirror Image | Lv4 | 依玩家方向安全閃身、原位原版假影、真實原生敵人追身／瞄準轉移，假影59/30秒消散；本體原103僅2/30–13/30秒無攻擊碰撞，地形／狀態傷害仍生效；假影不攻擊或擋彈 |
| Soul Bomb | Lv5 | 真正飛行的大球、穿透與獨立撞擊爆裂 |
| Big Bang | Lv8 | 原巨柱近身爆發與完整消散 |

Firzen 的 Cannon、Overwhelming Disaster、Arctic Volcano 保留，並已定點回歸共用索敵／碰撞管線。Freeze 亦有完整受控瀏覽器回歸通過。原版素材不變，新增迴避／假影沿用原106／103／104／105和240–251圖格；受傷閃白不覆蓋103的原本透明格。

- 產品來源：`d46395d6de420124f2fc7bd3e7c97d2338fcd61a`。
- 正式靜態提交：`169ef1d2da64058fb6655c20893c7ada5797a35e`。
- Pages來源：`codex/lf2-bosses-pages-d46395d6`，沿用既有網址、legacy模式和HTTPS。
- 乾淨checkout建置，重要runtime與Git blob一致；不含原安裝器、研究原檔、QA影片或本機state。Windows靜態包以原bytes發布，原碼換行修正另有正規化一致證明。

公開 **110個檔案** 與正式包bytes完全一致。三位LF2角色各桌機及390手機視窗共六個新訪客Lv1開局均通過，無頁面錯誤／缺失請求。公開實際能力與學習圖示同時核對：Freeze4、Firzen3、Julian6，兩種公開Julian畫面均含正式衝拳與Mirror Image。

新版Julian七組受控驗證、兩份全六招正常Lv1鍵盤／真觸控自然成長、完整六招原生演出均通過。自然局含五種攻擊實際命中，以及Mirror造成31／25個原生敵人重新追蹤；匹配遭遇原生敵彈落空與假影不擋彈另有獨立反例。考據、美術及品質總監都重新按六招放行，沒有沿用舊四招完成結論。證據見[verification.json](verification.json)、[qa/provenance.md](qa/provenance.md)、[director.md](director.md)。公開證據留在本機`.omx/state/lf2-bosses/public/`。

未驗實體手機長局、多人網路與真人聲音聽評。數值、冷卻、俯視投影及自動施放仍為本作改編；沒有宣稱完整搬入原LF2引擎／Z軸物理。
