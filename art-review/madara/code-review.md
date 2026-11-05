# 宇智波斑獨立程式審查

2026-11-06。審查者只讀產品程式，與戰鬥作者分開；本檔記錄具體發現及修正追查，不以讀碼代替實際遊玩驗證。

## 第一輪

範圍：`.omx/naruto-madara.js`、`.omx/naruto.js`、`art-review/madara/runtime.js`，並對照原生 Moves、Naruto training、JujutsuGrowth、CombatPulse、World path 接點。

- 原生初始池使用獨立 starting 旗標，只提供一級體術；addMove 另核角色 ID、學習等級與重複，額外起始招不應繞過門檻。追加 ID 30016，既有角色 ID 未挪動。
- 專屬技為 passive + autoCast，不占主動槽；byDex、extraPools、definitions、圖示與學習列均有登記，技能池不傳入其他角色。數量預覽與施放同讀 profile/vector，設有實際段數及分身數上限。
- 每次施放有獨立 CombatPulse cast，每段獨立 index；onHit 在傷害回呼後重新核查 state identity、owner、技能存在及木分身歸屬，失效時撤銷 cast，阻止同波後續目標與未來段數。
- 世界、epoch、死亡、失去控制、退學及 clearFields 有檢查；木分身不是可遞迴召喚自身的玩家分身，攻擊來源位置獨立，施放傷害歸原 owner。
- 移動路徑與範圍命中走現行 World/EnemyMgr，分身每次移動有最多32小步；數量與活動時間有上限，未發現無界迴圈或繪製造成傷害。

實際提出的修正：

1. 隕石 draw 重用要求 playing 的 damage legal，導致 paused/levelup 時未落巨岩和落點消失。已要求將凍結可見性與可造成傷害的條件分開；暫停仍不得前進時鐘或傷害。
2. 動作圖集依 pose.kind / age / aim 取格。初稿把整次多段施放 age 傳入，後續段會一直停在收勢圖；已要求本體及木分身改用每段局部 age。
3. 初稿體術基數3，第一張數量卡取整不增段。共享預覽能顯示累積門檻，但與本輪「第一張可見」方向不合；作者已將起始體術改為4段，第一張變5段。

## 第二輪

- 已重新讀取作者凍結版：隕石改用 drawable；傷害仍使用 legal，二者分開。測試報告已有 playing / paused / levelup 三態各48883非透明像素且狀態快照不變的獨立證據。
- 本體及木分身 draw 共用 poseFor；體術／須佐按每段局部時間重播，火遁維持吐息後收勢。
- 基礎體術已改4段，第一張數量卡5段；傷害／射程／段數升階文字由真實 instance/profile/vector 產生。
- 主代理另找到木分身技能傷害升階未消費的問題。二輪已確認 `cloneDamageMultiplier = m.dmg / 32` 經 spawn 快照傳入分身，再在分身 action 乘進真實 damage；所有階數有火力受益，人數不變的第二／第四階亦然。作者未以新抽象層繞過既有命中管線。
- `.omx/naruto-madara.js`、`.omx/naruto.js`、`art-review/madara/runtime.js` 均通過 `node --check`。

目前未發現阻擋發布的讀碼問題。凍結版完整獨立接受測試及木分身實際HP差異仍以 `verification/report.json` 最終結果為準；美術／動漫動作辨識、正常入口手機、自然選卡與實機長局由對應證據分別判定，不由本讀碼審查代替。

## 第三輪：原生障礙物與已移除敵人

獨立接受測試擴查發現無敵人時無法攻擊可破壞物，以及空間索引仍返回已移除活敵的整合缺口。修正後重新讀取 Madara 與 CombatPulse：

- 索敵優先原生敵人，無敵人時選原生 props；`projectilePathClear` 的 target 傳入欲攻擊的 prop 本體，因此允許攻擊進入該物件自身 solid 半徑，但其他先擋的物件或牆仍阻擋。範圍、扇面與隕石固定圓心都在真傷害路徑重新核對，呼叫原生 World.damageProp，保留原生破壞／掉落流程。
- 每個 prop 傷害前重新核 legal，若敵人或物件的傷害回呼取消施放，同波物件與之後波次不再補打；木分身沿用自己的攻擊源點及既有火力倍率，沒有新增可遞迴施放來源。
- 敵人索敵先與 EnemyMgr.all 的註冊集合交叉檢查，排除 stale grid；cast.targetIsLegal 在 primary 收集、primary 每筆傷害、outer 收集與 secondary 每筆傷害均重查。已真正落下的 primary 記入 landed，secondary 只取其中來源，避免被略過的舊目標發出假擴散。沒有傳 guard 的現有角色保留原來批次行為。

審查曾用最小 Node fixture 真正重現「只修 primary 的 hit.isLegal 仍讓 stale outer 損失1HP」；作者改為 cast guard 後，獨立重跑三案全通過：stale outer 零傷害、primary.onHit 移除 outer 後零傷害、仍註冊 outer 保持精確1點擴散（primary10、rate0.1）。CombatPulse 與 Madara 再次通過 node --check。

本輪未再發現阻擋發布的具體讀碼問題。完整原生障礙物與傷害回呼接受結果以更新後 `verification/report.json` 為準。
