# 火影角色：現用動作覆蓋清單

更新：2026-10-21。現行 `redrawn/atlas-map.json` 登記 **11 張圖集、264 個實體影格**，`animation-assets.json` 登記 **46 組動畫序列**。角色為鳴人、佐助、小李與少年我愛羅，另含一尾與八門形態。序列可共用實體影格，兩種數量不混算。

正常入口：[火影內測](http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW)；[動作實玩審稿](http://127.0.0.1:8004/art-review/playtest.html)；[圖集審閱室](index.html)。請確認服務來自目前工作目錄，不沿用其他 worktree 的 8318。

## 圖集與動作

| 現用圖集 | 覆蓋內容 |
| --- | --- |
| `naruto-common-v1.png` | 鳴人待機、走跑、受傷、倒下與投擲；實體分身也使用本角色圖 |
| `naruto-skills-v2.png` | 結印分身、螺旋丸、螺旋手裏劍等施術姿勢 |
| `sasuke-common-v1.png` | 佐助待機、走跑、受傷、倒下與投擲 |
| `sasuke-skills-v2.png` | 千鳥、豪火球、風魔手裏劍、草薙劍與寫輪眼等專用姿勢 |
| `one-tail-v2.png` | 鳴人一尾專用待機、移動、受傷、攻擊、投擲與查克拉螺旋丸 |
| `lee-common-v1.png` | 小李普通形態待機、走跑、受傷、倒下與普通攻擊 |
| `lee-skills-v1.png` | 木葉旋風、表蓮華、開門起手與裏蓮華 |
| `lee-gates-common-v1.png` | 開門後紅臉、白眼、豎髮形態的共通動作 |
| `lee-gates-skills-v1.png` | 開門後完整技能專用動作，施術不回退普通臉 |
| `gaara-common-v1.png` | 我愛羅待機、走跑、受傷、倒下、攻擊與投擲 |
| `gaara-skills-v1.png` | 砂時雨、砂縛柩、砂之盾與流砂瀑流／大葬操砂姿勢 |

我愛羅新增十組序列：`gaara-idle`、`gaara-movement`、`gaara-hurt`、`gaara-death`、`gaara-attack`、`gaara-throw`、`gaara-sand-burst`、`gaara-coffin`、`gaara-shield`、`gaara-tsunami`。登記及裁切的存在只證明有素材，不代表技能命中、選角或清理已通過實玩驗收。

普通角色共通圖包含正面、背面與側面；側面向左使用鏡射。技能及變身圖以側面動作為主，上下施術可共用側面，不宣稱獨立八方向。倒下停在最後一格，移動與施術腳底一致，不能逐格放大蹲姿造成比例跳動。

## 行為契約與來源

[遊戲演出契約](gameplay-contract.md) 說明真實遊戲的起手、命中、收勢與清理；[小李技能設計](lee-skill-design.md) 與 [我愛羅技能設計](gaara-skill-design.md) 保留原作考據、官方遊戲參考及本作數值改編。素材提示詞、參考與 SHA256 由 [製作來源](redrawn/provenance.json) 追蹤，使用者指定的 [Ninja Council 3 研究入口](https://spritedatabase.net/game/55) 保留為風格和動作研究，未當成新繪成品。

早期 `coverage.json` 的 17 組鳴人／佐助候選與退稿屬歷史審稿資料，不能再用其「正式遊戲未套用」文字判定現行分支。現用列表以 `manifest.json`、`animation-assets.json`、`redrawn/atlas-map.json` 和實際載入來源為準；瀏覽器「認可」紀錄亦不等於程式測試通過。

## 驗收證據

由目前工作目錄啟動 `python tools/serve_animation_lab.py --port 8004`，執行下列對應檢查；是否通過只以此次輸出與報告為準，不因列表已有檔案就宣稱完成。

| 驗證範圍 | 指令／證據 |
| --- | --- |
| 圖集裁切、透明、影格與瀏覽器載入 | `python tools/test_animation_assets.py --browser` |
| 正常入口全角色、真實素材與動作 | `python tools/test_redrawn_heroes.py`、`python tools/test_animation_complete.py`、`python tools/test_sandbox_redrawn.py` |
| 小李連段與開門 | `python tools/test_rock_lee.py`、`python tools/test_lee_gates.py` 及對應專屬回歸 |
| 我愛羅選角、學習、AOE、砂盾與手機 | `python tools/test_gaara.py`；`.omx/state/gaara/report.json` 及同目錄畫面 |
| 發佈包實際包含新增資產 | `python tools/build_digimon_site.py` |

我愛羅必驗：砂時雨與砂浪各三名範圍內、範圍外及隔牆敵人的實際 HP；砂縛柩束縛後單次傷害；砂浪分兩段且不重複結算；首領弱控制；砂盾切招持續、破盾不即補、升階差額、不疊加；冷卻卡、暫停、死亡、新局清理；桌機與手機的真實 `drawImage` 來源、腳底、比例及操作遮擋。
