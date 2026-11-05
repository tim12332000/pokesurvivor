# 四方設計：正式遊戲整合首版

使用者已授權實作。本版的新規則與程序特效已接入正常遊戲入口及打包，不再只是獨立原型。

**正式整合驗收完成。** 完成稽核曾發現同程式直式路線反例；重現確認舊比較混入隨機地形／路徑及不同抽卡後的亂數消耗，舊通過與失敗結果均不作公平路線證據。修正測試前提後，900組寬／直／手機同初始敵群比較通過；沒有為洗掉反例修改遊戲參數，原始報告保留。

**20級新版：** <http://127.0.0.1:8337/dist-digimon/.omx/digimon.html?lang=zh-TW&hero=jjk-yuta&startLevel=20&build=blade&v=council-v3>

**正常成長：** <http://127.0.0.1:8337/dist-digimon/.omx/digimon.html?lang=zh-TW&hero=jjk-yuta&v=council-v3>

20級選單可切「四招試招」及各角色兩種配裝／均衡配裝。標準配裝實際花19次合法選卡，包含三次學招，並保存每一步的選前／選後能力與階級；試招維持四招一階，不冒充自然20級成形。

## 已接入的玩法

- **卡牌收益與預覽**：依真正數量consumer及上限決定候選；乙骨／烏鷺只有卡片自身分身仍不會收到無效數量卡；石流用共用×1.25、最後取整、cap9，顯示累積門檻。滿血軍糧丸等無效選項排除，正常三選一保留通用選擇。
- **十二招功能階級**：三／五階加入刀術標記接力、里香接近／返回、咒言覆蓋、顯現恢復、精英／群聚索敵、散射扇面與基數、首目標加成、碎面控制、敵彈威脅預測及真反射後一次反擊等實際行為。
- **顯現與排程**：乙骨6秒顯現結束後才進入可受CD卡影響的恢復段；HUD區分作用、施放、恢復、冷卻、待出手。結算另記錄就緒時的動作等待秒數。
- **接觸pulse**：JJK即時AOE先收主命中集合；主目標不互濺，外圍每pulse取最大合法primaryDirectDamage一次。里香兩擊各自合法、石流同輪多ray共pulse、分身有獨立歸屬；次生不重觸發百分比附傷／吸血。其他原生單體與飛彈流程保留。
- **羈絆獎勵**：依有效能力分成可融合、暫未學足可暫存、結構不可融合轉精通；不是JJK ID特例。安全選擇成功後才扣token，拒絕重複／過期卡。
- **失敗與完成回饋**：記錄近身碰撞／飛彈／地面危險等承傷、實際HP＋盾損失的輸出分類、施放和等待；第五既定主線首領被擊敗且原生記帳完成後才出里程碑，可結算或繼續，不混算裂縫、不改30分鐘挑戰。

## 已接入的演算法效果

1. **額砲**：固定seed相干輪廓、白核與有界外殼，使用真實裁切長度及新圖額頭發射點。
2. **刀痕／爪痕**：Bezier弧長取樣與帶狀拖尾，跟隨原生接觸時序，不產生額外傷害。
3. **天空折面**：直接在正式地面／液體後、Hazards前擷取局部背景，以共享網格三角仿射貼圖彎折；玩家、敵人、阻擋props、彈道、危險及HUD不被貼入背景。

全場桌機2快照／48貼圖三角、低品質1快照／12三角，超額保留明暗折面；裝飾碎片全場24。暫停、死亡、清場、換局會凍結／清除；VFX關閉會真正停止新capture、composite與多邊形，開關前後傷害相同。

## 修改檔案

- `.omx/jujutsu-growth.js`、`.omx/jujutsu.js`：收益、卡池、功能階級、獎勵規則。
- `.omx/combat-pulse.js`、`.omx/damage-splash.js`、三個`.omx/jjk-*.js`：接觸／傷害／成長實作。
- `.omx/jujutsu-vfx.js`：正式程序特效。
- `.omx/trial-build.js`、`.omx/dev-controls.js`：19次合法配裝、試招區分、可操作選單。
- `.omx/run-insights.js`、`js/ui/hud.js`：狀態、記帳、結算與選擇介面。
- `js/game.js`、`js/systems/spawner.js`、`js/systems/combat.js`、`js/systems/hazards.js`：必要原生接點與來源標記。
- `.omx/make_digimon.py`、`.omx/digimon.html`、`tools/build_digimon_site.py`、`.omx/menu-layout.css`：正式載入、版本雜湊、打包及手機版面。

沿用現有傷害／護盾／附傷、角色素材與卡牌機制，沒有新增套件；未提交、推送或外部發布，其他工作區修改保留。

## 驗證證據與界線

- `tools/test_growth_contract.cjs`、`tools/test_combat_pulse.cjs`：原生卡牌與22項階級功能、獎勵安全扣除、pulse／secondary／epoch合約。
- `tools/test_council_runtime.py`：三角色與既有角色、正常入口、合法配裝、來源記帳、里程碑、真實背景像素與圖層、手機切換、移動敵人與多分身。
- `tools/test_council_balance.py`：最終900組公平配對比較通過，包括全角色全寬540組、烏鷺直式180組、烏鷺實際390px／DPR2手機模擬180組。每組配裝花相同卡數，先完成配裝再重設獨立場景亂數，清除受控場地的walkable／路徑快取，保存並驗證相同初始敵群指紋；未發現受測情境的結構收斂或全面支配。這不是完整真人長局平衡證據。
- `tools/test_jujutsu_vfx_runtime.py`：正式canvas像素映射、DPR1／2、四演員全場預算、開關不改傷害、清場／死亡／換局。
- 原有三角色桌機／手機、目錄／任務／存檔／選卡回歸及JS／Python語法檢查。

最新證據位於 `.omx/state/council-runtime/`、`.omx/state/jujutsu-vfx/`、`.omx/state/council-root/`。正式機制／壓力看`final-wide/`及`built-final/`；路線比較只採`balance-authoritative-wide/`、`balance-authoritative-portrait/`、`balance-authoritative-mobile/`。舊`balance-final/`、`balance-wide/`等報告保留歷史，不作公平配對證據；早期portrait壓測也不當成全寬效能結果。

正常移動／拾取／選卡嘗試已到185遊戲秒、Lv16並遇到第一個既定首領，結束時仍存活；沒有宣稱擊殺首領或完整通關。另對原生主線第五首領的生成標記、擊敗、記帳後提示與繼續／結算作機制測試。

尚未取得實體手機長時間熱降頻、真人雙端連線及完整長局／玩家訪談證據。六方向是已實作的功能投資配裝，軟分流在更長局若收斂仍須依設計繼續互斥比較；沒有假稱所有未來平衡問題已解決。
