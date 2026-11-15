# 鹿丸發布完成 — 2026-11-16

[直接遊玩鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=cedfcbe1)。

- 遊戲來源：`cedfcbe114b25c5207e107bda5adb75c8bde8472`。
- 正式靜態提交：`444f08a585f75e10938e0fb39aa86f889a7e5720`。
- 當前 Pages source：`codex/shikamaru-pages-cedfcbe1`，`/`，沿用 legacy、原網址與 HTTPS，沒有改服務保護。
- 從獨立來源 worktree 執行正式 `tools/build_digimon_site.py`；靜態提交以當前公開分支為 parent，共用既有資產，保留實際 artifact bytes，不讓 git 換行轉換改動發布檔。
- 更新來源後另請求 Pages build（HTTP201 queued），直到公開內容真正相符才判定完成；queued／push 本身不是成功證據。

## 公開驗證

14檔（入口、實際遊戲HTML、角色／技能／成長／控制runtime、metadata、PNG）公開 bytes 同時符合靜態提交與 canonical artifact；`.omx/state/shikamaru/public-assets.json` 保存逐檔 SHA256。

真 Chrome 從公開根入口，在桌機、390及360手機視窗正常選角並開始 Lv1；三組 dex30017、素材ready=true、零pageerror。已保存選角、正常開局與桌機鍵盤輸入截圖；`.omx/state/shikamaru/public-browser/report.json` 保存實際結果。主代理另實看公開390開局畫面。

## 版本與驗證界線

完整候選經至少三輪實質修正，企劃、戰鬥、美術、動漫、QA及獨立總監有界分工；[總監](director.md)、[美術](art.md)、[動漫](anime.md)、[QA](qa/summary.md)各記具體退回及重驗。九個標準Node檢查、相關JS語法、Python編譯與diff檢查通過。未新增依賴，沿用既有原生狀態／傷害接點；既有角色數值保持原調校。

正常Lv1真選卡自然到Lv23、22卡、五招成形，285.3秒死亡如實保留；後續僅修方向分派與首縛視覺錨點，另有當輪相位及影片，不混稱同一來源。canonical Windows換行與原始工作樹raw SHA不同時，公開比較以正式靜態提交及artifact為準。

手機視窗不等於手機實機長局；未做音效聽評，玩家主觀樂趣仍待實玩。未更動工作區原有其他角色報告或攜入無關未追蹤素材。
