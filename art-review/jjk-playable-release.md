# 仙台三人組：本機可玩初版

本頁保留v1紀錄；目前最新版及實際動畫對照見 [v2修訂交付](jjk-refinement-v2-release.md)。

乙骨憂太、石流龍、烏鷺亨子已接入正常選角入口。選擇「跨界角色」，點選角色後開始遊戲；技能在 Lv.1／3／6／9 開放，從升級選卡學習後自動施放，不占主動槽。

本機原始入口：<http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW>

本機打包入口：<http://127.0.0.1:8337/dist-digimon/.omx/digimon.html?lang=zh-TW>

伺服器：`python tools/serve_animation_lab.py --port 8337`。

| 角色 | Lv.1 | Lv.3 | Lv.6 | Lv.9 |
| --- | --- | --- | --- | --- |
| 乙骨 | 咒力刀斬 | 里香協擊 | 咒言・別動 | 里香完全顯現 |
| 石流 | 花崗岩砲 | 散射咒力砲 | 咒力爆破 | 全力咒力砲 |
| 烏鷺 | 空面打擊 | 薄冰破 | 天空幕 | 空面震落 |

## 修改範圍

- `.omx/jjk-yuta.js`、`.omx/jjk-ryu.js`、`.omx/jjk-uro.js`：獨立戰鬥行為與演出。
- `.omx/jujutsu.js`：12 招、角色專屬技能池、學習限制與圖鑑。
- `.omx/jujutsu-art.js`、`art-review/jjk-frames.json`、四張 `art-review/redrawn/jjk-*-v1.png`、三張選角頭像：新角色動畫與素材。
- `.omx/naruto.js`、`.omx/redrawn-init.js`、`.omx/make_digimon.py`、`.omx/digimon.html`、`tools/build_digimon_site.py`：選角、正常入口、資源等待、版本雜湊與打包。
- `tools/test_jujutsu.py`：三角色桌機／手機驗收；既有 catalog 與 mission 瀏覽器測試更新至11位可玩角色。
- `tools/build_jujutsu_assets.py`、`art-review/jjk-art/`、各角色設計文件：可重建裁切、生成參考、提示詞、來源與雜湊。

沿用現有傷害歸屬、破壞物、升級選卡、角色目錄及動畫介面，未新增套件。原有召喚術等工作區修改保留。

## 驗證

- 三角色各通過1280×900桌機與390×844手機正常入口、移動、素材來源、角色專屬學習與技能卡。
- 20組範圍傷害測試，包含三個範圍內敵人、一個範圍外敵人、傷害歸屬與擊殺統計。
- 里香獨立圖像、完全顯現升階與到期、咒言普通敵人／首領抗性、天空幕反射歸屬／次數／到期／冷卻、無敵人時破壞寶箱。
- 暫停、清場、死亡與原生重新開局的待結算傷害清理。
- 最終原始入口驗收零 JavaScript 錯誤、零缺檔，前後執行檔雜湊一致。證據：`.omx/state/jujutsu/report.json`。
- 打包後入口亦通過三人各桌機／手機完整驗收，零錯誤、零缺檔；證據：`.omx/state/jujutsu-built/report.json`。
- 角色目錄、任務存檔修復、升級選卡回歸與語法檢查通過；打包成功。
- 同尺寸素材、正常選角與實際遊戲畫面視覺驗收93／100；證據：`.omx/state/jujutsu/ralph-progress.json`。

## 初版限制

角色有正面、背面、側面原畫，左側採鏡射；烏鷺側向步行共用同一張原畫。技能圖示沿用既有類型圖示。數值為遊戲改編；尚未做長時間平衡或真人連線對戰驗收。未發布到外部網站。

原作參考與改編細節見 `jjk-yuta-design.md`、`jjk-ryu-design.md`、`jjk-uro-design.md`；素材紀錄見 `jjk-art/provenance-v1.json`。
