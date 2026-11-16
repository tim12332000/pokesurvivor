# 九尾化正背面補齊

2026-11-16。本機候選，未提交／推送／發布。

向上移動使用真正的背面（後腦、綁帶與背部漩渦），向下移動使用正面（臉與護額）；左右繼續使用既有側身與鏡射。影分身與卡牌分身沿用各自演員的方向，並承接既有的變身時間與還原機制。

使用內建 `image_gen` 新增透明 4×8 圖集：`art-review/redrawn/one-tail-vertical-v1.png`。原始生成結果以未修改像素的檔案保存在此路徑，提示詞與參考位於本目錄 `generation.json`；輸出與參考 SHA256、來源與校準方式位於 `art-review/redrawn/one-tail-vertical-v1.provenance.json`。不是官方素材擷取，沒有新增依賴。

正背面分別有四格待機、四格奔跑、四格爪擊、四格螺旋丸／施術。變身使用待機列；投擲適配爪擊列、受傷適配收勢格，所有既有動作分派都保持相同面向。沒有把側身圖旋轉或拉伸來代替正背面。

以正背面待機的髮型寬度中位數對齊現有側身，所有新圖格共用一個倍率，不逐格放大蹲姿。實際渲染待機高度：正背面約 52–53px，側面約 54px；奔跑正背面約 53–55px，側面約 51–53px。每格由實際 alpha 邊界定位並註冊腳底錨點。不同視角的尾巴寬度不強制拉成相同寬度。

螺旋丸的正背面可見球心已逐格註冊；實際場域特效改取變身圖的球心與身體倍率。背面被軀幹遮住的球不另畫前景光絲，避免身體朝上而特效仍停在舊側身手部。

變更：

- `art-review/kyuubi-form.js`：兩張圖集原子載入、正背面完整動作分派、來源／倍率／球心。
- `art-review/kyuubi-frames.json`：新正背面圖格、錨點、共用倍率及球心。
- `.omx/naruto-rasengan-vfx.js`：正背面變身球心與遮擋。
- `tools/register_kyuubi_directions.py`：可重現註冊；`tools/build_redrawn_atlases.py` 接回生成流程。
- `tools/build_digimon_site.py`：新圖集列入公開打包並驗證清單。
- `tools/test_naruto_cloak_directions.py`、`tools/test_kyuubi_frames.py`、`tools/test_kyuubi_form.py`：方向、真實繪製來源、素材與既有行為回歸。
- `tools/test_naruto_cloak_normal_entry.py`：手動推進驗證改用正式暫停切換，確保 Animator 的模擬時間真的前進。

驗證：正常桌機入口 1100 與直式手機入口 390；實際鍵盤與觸控四向移動；本體和影分身的待機、奔跑、真實拳擊／震擊、全部正背面動作分派、到期清除。逐次攔截 `drawImage`，核對真正使用的圖集與矩形，不只檢查 metadata。生成器重跑結果一致、素材 alpha／範圍／球心／頭部尺度測試通過；原有九尾化過渡與生命週期測試、語法／空白檢查及打包通過。另以真實 `G.DigimonSkills.cast` 和 `rasenganFor` 場域驗證正背面集氣與出掌，逐項核對可見球心、實際特效中心和背部遮擋。詳本目錄 `report.json`、`*-gameplay.png` 與 `*-live-rasengan-*-gameplay.png`。

限制：手機為瀏覽器模擬，未測實機長局或音效；圖片與自動化不能替代使用者對手感及美術的最後判斷。本次不調整上一輪戰鬥數值。
