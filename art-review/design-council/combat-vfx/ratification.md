# 第三輪共同設計複核：程式特效

結論：**同意，附兩項精確文字修訂**。已完整閱讀 `../shared-design.md`，沒有把整合稿當成正式遊戲已實作，也沒有把原型視覺或短局觀察當作完整平衡證據。

## 要求整合稿納入的兩項修訂

1. 第5節擴散規則第2點的「最大已結算直接傷害」應改成：

   **最大 `primaryDirectDamage`，即現有 `DamageSplash.hit` 的出手輸入，已包含攻擊／屬性／天氣／暴擊，排除百分比附傷及secondary；不是目標HP實際損失或盾後重算的數字。**

   原因：三方已明確同意不在本次去重順便改盾、overkill或外圍屬性計算。泛稱resolved容易被未來實作者誤解為受害者實際掉血，造成無聲平衡變更。

2. 第6節的形變預算應精確區分類別：

   **背景折面全畫面最多桌機48／手機12個貼圖三角片，網格共享頂點上限96；24片裝飾碎片另作全畫面預算。光束／刀痕另遵守輪廓點與可見事件數預算，96不是整個遊戲所有幾何的總cap。**

   原因：同一場可以有背景mesh、光束輪廓、ribbon與碎片。把96誤讀成全部友方＋敵方幾何總量，會導致無法渲染或錯誤刪掉危險資訊。兩個快照的48／12是全局貼圖片數，不是每owner可再乘一次。

已將以上完整替代文字送root；不自行修改整合稿。

## 逐項核定

| 共同規則 | 我的核定 |
| --- | --- |
| Quantity MVP改共用×1.25、最後取整、石流cap9 | 同意作為選定MVP政策。這是強度修訂，不能說原本四人第一稿已一致或只是改字；保留與線性版本比較。 |
| 受益查詢與SelfClone | 同意。固定每卡一clone不讀Q；只有真正count-consuming的複製技能受益。永久無效與取整累積不同。 |
| 六路線先功能rank | 同意，需10／19／35預算與A/B/均衡、四敵情、共同seed。軟分流若失敗必須執行互斥形態比較，不能以較省工方案代替原目標。 |
| 同pulse擴散排除primary、每外圍一次 | 同意，套用上述primaryDirectDamage術語；保留單體每外圍10%體感，總額分配B另作假說。 |
| 里香兩次接觸與分身 | 同意，pulse0／1分開，clone獨立owner/cast。不得用rootAction統計或視覺budget吞掉真實傷害。 |
| 飛行彈impact | 同意，不等待未來primary、不回滾；每個原生impact即時獨立pulse。 |
| CPU複雜度 | 同意，傷害事件去重不證明查鄰居CPU線性；仍需grid、遮擋與64怪/分身壓測。 |
| runEpoch及channel | 同意，明確新nonce／Symbol；不是穩定的Game.st。body、companion、reaction結構一致但時鐘獨立。 |
| 顯現有效期＋恢復期 | 同意作待測節奏實驗。12秒恢復是假說，未以原型驗證其遊戲強度。 |
| 背景capture與composite層序 | 同意，兩者都在Liquid後、Hazards前；阻擋props／actors／危險／彈道／HUD不warp。 |
| 全畫面資源與DPR | 同意，按上述類別精確化。RGBA僅應用buffer下界，不宣稱GPU／手機總量或FPS。 |
| 原型完成範圍 | 同意，原型是位置替身與示意接觸，不是正式敵人HP、地形與長局測試。 |
| 遊戲內容與存檔 | 同意本輪不改執行碼、不新增貨幣／未證實領域，不以角色ID特例掩蓋獎勵能力缺口。 |

## 可獨立重跑的CODE與證據

原型檔案：

- `art-review/design-council/combat-vfx/prototype.html`
- `art-review/design-council/combat-vfx/prototype.js`
- `art-review/design-council/combat-vfx/algorithms.js`
- `art-review/design-council/combat-vfx/test-algorithms.cjs`
- `art-review/design-council/combat-vfx/verify_prototype.py`

執行：

```text
node art-review/design-council/combat-vfx/test-algorithms.cjs
python art-review/design-council/combat-vfx/verify_prototype.py --prototype-only
```

最後一次執行以上命令皆通過。證據：

- `evidence/report.json`：第一輪真實原生Ryu／Uro觀察、三種原型draw檢查，原始限制保留。
- `evidence/prototype-peer-review.json`：最後一次Chrome原型三模式、pause／品質、DPR2 backing1720×980、相機、雙fold高48tri／低12tri＋2明暗面檢查，無pageerror。
- `evidence/sky-dpr2-camera-twofold-high.png`、`evidence/sky-dpr2-camera-twofold-low.png`：實際開啟並檢視的高低品質對照。
- `evidence/visual-verdict.json`：只對獨立原型的視覺／功能範圍評判，不是正式遊戲總分。

純函數測試另覆蓋：牆／光束邊界、固定seed、仿射點映射與DPR相機組合、弧長取樣、暫停／取消、Quantity消費者與取整、擴散primary排除／順序／n×m、pulse／clone／epoch歸屬，以及多fold全畫面分配。

仍未取得正式整合snapshot、實機手機、多人及長局資料。這些在共同稿中正確列為後續驗收，並不阻礙本輪「四人設計＋互相討論＋產生可運行演算法做法」的交付。
