# 角色製作：現行基準到正常入口

路徑以目前PokéSurvivor專案根目錄為準。完整新增／重做角色先走 [完整角色 SOP](new-character-sop.md)，手感與素材標準讀 [品質準則](character-quality.md)；本頁處理素材與接線，單點任務只取相關段落。不要把歷史角色數量或早期玩法當現況。

## 查現況與定角色

確認工作樹、既有ID、時期／服裝、正常入口和載入覆寫。先查已實作連動，避免重新提議同一功能。只有影響身份／玩法的重大分歧才詢問，其餘沿任務與現況判斷。

核對官方來源、動作鏈與改編界線。火影像素研究由 `https://spritedatabase.net/game/55` 開始，不把研究圖直接當成品，也不要求其他作品使用同一來源。先定完整循環和第一張／少量卡／成形變化，再決定招數；近戰、夥伴、連射、地面場與反射各選合適模型。

## 判斷素材需求

先看現用圖集、metadata和正式分派，分清缺姿勢、錨點、時鐘、排程或程序效果。有圖不等於正常入口有播放。

- 按需要列待機／移動／出手／命中／收勢／受傷／倒下，以及變身／夥伴；鏡射或側面代上下方向如實標記，不宣稱獨立八方向。
- 用現用角色定頭身、描邊、像素密度與色彩。蹲姿／倒下不放大成站姿高度，特效邊界不算人物身高。
- 新點陣圖用imagegen，透明背景與足夠影格間距；保存原始輸出、提示詞、參考和SHA256，新增版本不覆寫。先查alpha，再看草地／棋盤合成；裁切不假定生成格線等距。
- 每格有 `rect` 和腳底 `anchor`；手／嘴／頭發射點依當格、方向、鏡射量測。畫中已有衣物／尾巴／能量不再疊第二份。

## 接入現有管線

| 接點 | 核對內容 |
| --- | --- |
| `.omx/naruto.js` | roster、DEX、選角／學習列；不重排存檔ID，技能數與標籤依角色產生。 |
| `.omx/naruto-skills.js`、`.omx/jujutsu.js` | 現用作品的技能登記、專屬池、門檻、升階、圖示和短說明；不把被動當手動／自動出招。 |
| `.omx/naruto-training.js`、`.omx/jujutsu-growth.js` | 真選卡、有效成長、取整與上限；起始隨機招同樣受門檻限制，新增被動不破壞滿槽／綁定。 |
| 現用戰鬥模組、`.omx/combat-pulse.js` | 沿用傷害／歸屬／狀態管線，逐段接觸索引和身體／夥伴／反應／場域仲裁。 |
| `art-review/animation-assets.json`、`art-review/animation-runtime.js` | 火影素材與語意分派；查當前登記，不假設只有四角。 |
| `.omx/jujutsu-art.js`、`art-review/jjk-skills-v2.json` | 咒術現用圖格、語意分派、逐角色載入、尺寸與發射點。 |
| `tools/build_redrawn_atlases.py`、`tools/build_jujutsu_v2_assets.py` | 選現用產生器並擴充對應，不只把PNG丟進資料夾。一尾專用 `art-review/kyuubi-form.js`／`art-review/kyuubi-frames.json` 不套別人。 |
| `.omx/redrawn-init.js`、`js/main.js` | 正常入口等必要素材，審稿iframe不重複安裝，headless不退回舊圖。 |
| `.omx/make_digimon.py`、`tools/build_digimon_site.py` | 重建順序、雜湊、metadata／圖集清單正確，本機審稿與狀態不混入發布。 |

移動／跳躍沿用碰撞及獨立視覺高度，不破壞原生 `jumpLift` 或外部控制。加血／護盾只同步差額，不每幀或升級重加整筆、覆蓋卡牌。接近迴圈有步數上限與距離容差。

## 收集夠用的當次證據

確認服務來自目前worktree，可用 `python tools/serve_animation_lab.py --port <空閒埠>`，正常入口 `/.omx/digimon.html?lang=zh-TW`。各測試URL指向同一服務，避免測到另一工作樹或固定舊埠。

依改動選工具並增加新角色案例，不機械執行所有歷史測試，也不刪掉仍有效的回歸來過關：

- 素材可查 `tools/test_animation_assets.py`、`tools/test_animation_complete.py`和角色專屬工具。
- 多段／成長例子為 `tools/test_ryu_barrage.py`、`tools/test_yuta_duet.py`、`tools/test_uro_fracture.py`，不是所有角色的固定模板。
- 共用邊界看 `tools/test_growth_contract.cjs`、`tools/test_combat_pulse.cjs`、`tools/test_trial_build_scope.cjs`及現行CI。
- 正常入口／畫面看 `tools/test_hero_identity_play.py`、`tools/test_jujutsu_vfx_runtime.py`等；依新行為更新技能數、真相位與幾何邊界。

驗真學招／升階／選卡、正常自動出招和鍵盤／觸控；三個有效範圍內與一個範圍外／牆後目標；移動源點、首末段和真收勢、受傷／死亡／重開及夥伴／變身清理。新增技能另查360／390實際可見性、HUD和門檻。同波多目標回呼取消必測，詳品質準則。

原生短片和同尺寸相位圖核對來源、低畫質真幅度、普通／強化與高配遮擋；聲軌和聽評分開。實際drawImage來源／雜湊、正常入口和打包對上；登記數量依當次metadata核算，不抄舊十一圖集等數字。

## 收尾

先定完成條件；通過後只因新改動、失敗或未解風險重跑。交付可玩網址、改動、當次證據、素材／方向缺口和未驗部分，不用更多測試名稱代替結果。

已有有效發布授權就提交、推送並核對公開版本／資產；未授權不因本流程自行發布。原生影片放獨立預覽，正常開局不下載整批展示片。
