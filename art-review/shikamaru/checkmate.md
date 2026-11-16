# 鹿丸：奈良流・詰將

鹿丸原本能捕群、苦無連投、高拱影縫、沿路佈札，但沒有可學的終局大招。這次新增 **Lv5「奈良流・詰將」**，保留停用的影首縛相容 ID，不重啟舊黑手演出。

學會後，在正常收網階段自動發動：對已真正接住的目標發出三輪粗厚高拱影縫；尖端實際掃過身體才扣血，首次命中在當次世界落點埋下三張可見起爆札。最後各札位同時爆破，145 半徑、三倍單輪傷害；重疊爆區對同一敵人只結算一次。起爆札不跟著敵人滑動，原目標死亡後仍可波及走入爆區的新敵人。冷卻 12 秒；繼續自由走位，沒有附加無敵或停止強敵攻擊。

數量前兩張各增加一輪真連刺；前八張各加 5 爆破半徑。技能三、五階再各增加一輪，升階同時增傷、擴大爆區。最高七輪、沿既有影真似最多 16 個接影目標，實測 112 條有效高拱、16 札位。第一張數量卡和每一階升階的預覽都由同一 `profile()` 取得真收益。

本招名稱、影縫送札、自動收網和群體數值是本作改編。身份參照為官方對鹿丸的影術、戰術佈局及飛段戰的回顧：[NARUTO 官方鹿丸專欄](https://naruto-official.com/en/news/01_1910)。沒有聲稱「奈良流・詰將」是原作同名術。

## 修改與重用

- `.omx/naruto-shikamaru.js`：新增詰將能力資料、收網接線、真穿刺後埋札、定點終爆、正式前後景演出與 HUD 狀態。沿用既有高拱掃掠、傷害歸屬、生命週期及取消檢查，沒有另建傷害時鐘。
- `.omx/naruto-skills.js`：Lv5 技能池、技能說明、升階說明和像素圖示。
- `.omx/jujutsu-growth.js`：數量卡、升階共用真實輪次和爆區預覽。
- `.omx/naruto.js`：選角學習列的「詰將」。
- `art-review/shikamaru-art.js`：沿用既有結印／投擲／跑步素材，接入大招姿勢及移動朝向。
- `.omx/digimon.html`：更新以上資產快取版本。
- `tools/test_shikamaru_checkmate.py`：受控命中、原生自動施放及真 Lv1 成長驗證。

未新增依賴或點陣素材，也未削弱其他角色。重用同一影縫演員、幾何及清理路徑，避免複製一套近似大招系統。

## 當次驗證

- `python tools/test_shikamaru_checkmate.py`：三目標各三次真穿刺＋一次真終爆；範圍外、牆阻、相疊爆區去重、固定札、目標死亡後新敵入場、暫停／死亡／清場／換世界／退學、穿刺與終爆的 hurt／onDealt 同波取消、只讀繪製、移動姿勢和最高容量通過。原生 RAF 自動施放在桌機與 360／390 視窗都到達終爆。報告：[受控與原生證據](qa/checkmate/report.json)。
- `python tools/test_shikamaru_checkmate.py --natural`：全新 Lv1 單普攻開局，沒有修改 HP、XP、AI 或遊戲時鐘。實際 UI 選卡 Lv2 影縫、Lv3 起爆札、Lv4 精修、Lv5 詰將；之後正常選到分身及拾取。約 78.15 遊戲秒、Lv7 仍存活時已觀察到詰將終爆傷害。報告中的 `blasts=5` 是終爆傷害回呼數，**不是五次施放**。報告與原生錄影：[自然成長紀錄](qa/checkmate/natural/report.json)、[原生錄影](qa/checkmate/natural/native-growth.webm)。
- `python tools/test_shikamaru_parallel_kunai.py`：既有並行接影、苦無多段、閃避、牆阻、生命週期及最高 16 目標／80 苦無命中回歸通過；當次報告留在 `qa/checkmate/parallel-kunai-regression.json`。
- `node tools/test_shikamaru_art_phases.cjs`、`node tools/test_shikamaru_geometry_perf.cjs`、修改 JS 的 `node --check`、`git diff --check` 皆通過。
- `python tools/build_digimon_site.py`：成功建置 `dist-digimon`；`python tools/test_shikamaru_checkmate.py --package` 另逐位元組核對五個修改資產，並由打包後入口在桌機與 360／390 視窗驗證正常選角、可見且不溢出的「詰將 Lv5」、技能池及 Lv1 開局。見 `qa/checkmate/package/report.json`。

當次實看：粗黑高拱與一般苦無可分辨；調整源點到已接地影前段後，鹿丸本體完整可見。實際埋札影格以 `sites.size>0` 取樣，札位固定；終爆中段保留玩家、敵人血條及頂底 HUD。短暫黑弧可局部遮住被刺敵人的身體，未遮掉血條。

手機為瀏覽器 360／390 視窗，未測手機實機長局；未聽評音效，也不以測試宣稱玩家主觀樂趣。此輪完成本機可玩包，未提交、推送或部署公開站。

[本機可玩入口](http://127.0.0.1:8348/dist-digimon/?lang=zh-TW&hero=shikamaru)
