# 手鞠可玩版本交付紀錄

日期：2026-10-24。以 v3 多軸堆疊設計為準，未提交、推送或部署。

## 最新修訂

效能修正：同次施放的風浪共用每幀原始搜尋候選，已命中的目標先略過，實際接觸時仍逐次檢查位置、角度與遮擋。Q13／精通5／30小怪＋1王的相同5秒壓測，更新p95由168.7ms降至9.8ms，命中69,216次、傷害3,176,986完全相同；沒有削減數量、連擊或傷害。30秒／60小怪＋1王，原生更新p95約5.2ms，另加3分身約20.6ms；這是CPU更新、不含繪圖，不能視為手機FPS保證。工具為tools/profile_temari_runtime.py，正式版temari-20261024-2。

最新操作與行為覆蓋下方早期紀錄：普攻改為整片風浪，五階角度45／75／105／135／180度，保留數量×連切；命中普通小怪時獨立吹起22高度、停步0.30秒，同一輪連切不延長，不覆寫原生跳躍。返風壁為Lv.15常駐被動、無開盾冷卻與施法扣血，範圍內遠程攻擊持續反彈。鐮多利在附近75–145範圍自行走走停停，走遠會回到附近，不固定貼身。單體／散射風刃程式已移除，沿用完整風浪判定與程序renderer；滿圈使用依弧長細分的曲線，避免固定低邊數多邊形。

本輪驗證全部通過：`temari-windwave/report.json`含五階扇角、滿級八方向及真實渲染唯讀；`report-wind-lift.json`含桌機／手機浮空停步、原生AI／影子／跳躍、主客機雙向權威、暫停清理與颱風兩次浮空後1.79秒完整2π；`report-permanent-pets.json`含遊走／休息與成長10項；`temari-reflect/report.json`及841封包完整反射連線、66封包內圈光束回歸；`temari-procedural-vfx/report-final-passives.json`含24案例／96時點、常駐10秒與遊走、無風效貼圖及渲染唯讀；`coop-report.json`最新完整1450封包通過。`report-windwave-final-regression.json`驗證傷害帳務與Q20四角色27,040次真實命中，繪製開關不改結果。實作主要修改naruto-temari.js、naruto-temari-reflect.js、temari-coop.js、temari-cyclone-vfx.js、naruto-skills.js、naruto-training.js、naruto.js、enemy.js、hud.js與temari-art.js；無新增套件。打包與來源bytes／cache hash一致，見`temari-windwave/build-verification.json`。

通靈・斬斬舞現為Lv.9被動：學會即出現常駐鐮多利，不占主動欄；附近閒逛、自動接敵、斬擊後繼續遊走。每隻獨立冷卻10秒，數量為floor(1.25^Q)，數量成長保留舊個體與進度。舊主動／融合欄位移除通靈技能後保留其餘招式與選中組；靠牆返回使用可通行替代站位。

整套風效改用程序化薄刃、真實波前與短暫命中演出，高數量副本合併顯示但保留所有獨立傷害。只載入4張角色／鼬圖集共56格；舊厚風圈圖留作歷史來源，不載入或打包。`tools/test_temari_passive.py`與`tools/test_temari_procedural_vfx.py`記錄本次驗證；下列較早交付紀錄中的主動通靈、48／64格與重疊召喚敘述已由本節覆蓋。

最新證據：常駐通靈桌機／手機各8項通過（`report-permanent-pets.json`）；手機完整回歸通過（`report-permanent-mobile-regression.json`）；程序風效36案例、108時點、零錯誤（`temari-procedural-vfx/report.json`）；颱風及反射雙視窗尺寸回歸通過。合作驗證保留原完整執行及其測試場景刷新失敗紀錄，另外重驗擋彈、換場、帶寵離線清理157封包通過（`coop-report-focused.json`）；合併報告明列兩次執行來源。精簡後的寵物封包另用兩個隔離VM執行正式收送程式，86隻寵物跨全部階段保持ID，主人344次命中、遠端零命中。

入口／打包檔案逐一比對及hash通過，見`temari-procedural/build-verification.json`；10個JS語法檢查、8個Python編譯、加權卡池與本次新增行空白檢查通過。無新增套件。手機為瀏覽器模擬，合作測試使用本地JSON傳輸及隔離VM，未測真實外網或實體手機。複雜迷宮回航未涵蓋，現有避障為掃掠碰撞與局部轉向。

## 遊玩入口

- 工作區：`http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW`
- 本機打包：`http://127.0.0.1:8004/dist-digimon/index.html?lang=zh-TW`
- 桌機預設進入原有直式外框；兩個預設入口皆驗證 iframe 內可選手鞠並開局。需要寬版可沿原有切換連結。

角色 dex 30011；基礎生命125／移速118，預設永久強化全滿時生命205。開局鐮鼬常駐，Lv.3可學三星・風遁精通，Lv.6大鐮鼬、Lv.9斬斬舞。主動選中後自動施放；數量、每實體連切、攻擊、冷卻、分身共同成長。沒有九刃／八斬／單鼬低上限。

## 實作接點

- 新戰鬥與協定：`.omx/naruto-temari.js`、`.omx/temari-coop.js`；在共用分派、原生多人協定與分身清理加必要接點。
- 角色、四技能、學習／常駐規則：naruto.js、naruto-skills.js、naruto-training.js；新增圖示、HUD數量／連切顯示，保留既有ID與其他角色技能池。
- 原創圖：24共通＋16施術＋8鐮多利，共48格；`temari-art.js` 懶載入、`temari-frames.json` 精確裁切／腳底與來源雜湊。共通前／後／側向、左側鏡射；技能上下方向使用明示側姿替代。
- 產生器、入口、正式載入與build白名單均包含新腳本／三張選用圖。來源與提示詞見 temari-provenance.json 和 temari-kamatari-repair.json。

## 驗證範圍

`python tools/test_temari.py`：桌機及390×844 Chromium手機模擬；里程碑、五階、36組數量／精通／招式組合，AOE內外、牆、物件、重疊召喚、傷害帳務、分身、暫停／切招／換場、鍵盤／觸控、真實PNG繪製來源。Q20＋三分身工作負載保留27,040次真實命中、1,040個最高同時風刃，繪製開／關不改傷害。

`python tools/test_temari_coop.py`：兩個獨立瀏覽器執行正式Coop協定，透過測試傳輸適配器JSON轉送。六組主客機招式、ghost不重複傷害、重疊鼬群、分身到期單次通知、主機權威擋彈、場景過期包及離線清理。

實際原生遊戲迴圈與預設入口另見 `.omx/state/temari/playable-smoke.json`、`default-entry-smoke.json`；完整測試證據與畫面在同一目錄。確切最終狀態以當次報告 `ok` 和證據雜湊為準。

另執行12個JS檔node語法檢查、5個Python檔編譯、既有加權卡池測試、入口重建與standalone build、diff空白檢查。無新增套件。架構獨立審查已檢查傷害歸屬、分身倍率、計時及網路清理。

## 限制與既有檢查狀態

- 手機為瀏覽器模擬，效能數字來自本機，未冒稱實體手機量測。
- 多人涵蓋正式協定邏輯，不涵蓋Firebase帳號、外網大廳、WebRTC信令或真實網路丟包。
- 舊 test_animation_assets.py 的固定清單不包含既有天天等動畫；目前59項metadata與HEAD相同，該固定數量失敗不是新增手鞠造成。
- 舊 test_redrawn_heroes.py 另有既有天天圖片provenance digest不符；未改寫他人素材來源來掩蓋失敗。舊分身卡池腳本仍假設同步載入，與現有懶載入入口不合；本次新測試獨立驗證手鞠分身／卡池。
- 多個.omx新runtime沿repo既有忽略規則不會自動列入一般git add；本次未代替使用者stage／commit。打包腳本已明確包含它們。

## 整理

依限定範圍cleanup計畫檢查新runtime與共享接點；刪除一個冗餘 summon `dead:false` 欄位及未選用的重複圖檔，不更動多軸成長或其他角色。保留使用者與其他工作中的天天／README改動。
