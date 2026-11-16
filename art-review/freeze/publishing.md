# Freeze 經典版首發紀錄

已公開：[遊玩 Freeze](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=freeze&release=96463fd5)。

- 產品提交：`5ff7f8beba95f60bbf03a5cb059e0424ed499435`。
- 發布工具修正後來源：`96463fd5b9852ce99778d72957bfb7032f0f0e44`；僅修改本機發布工具，公開產品檔案未變。
- 正式靜態提交：`cabe12e954e599105f076108ab69e924cb151ac8`。
- Pages 來源：`codex/freeze-classic-pages-96463fd5`，`/`，既有 legacy 模式；維持既有網址與 HTTPS。

從乾淨來源 checkout 建置，重要角色／控制／音效 runtime 與 Git blob 相符。正式包不含原安裝器、本機 state、原始研究素材或 QA 影片。Windows 生成檔以正式包原 bytes 建立發布 tree，避免來源換行設定改寫成品。

切換來源後公開入口起初仍為舊版，另呼叫標準 Pages build endpoint 取得 queued，再持續核對；沒有以 push 或 queued 當發布成功。最終34個公開檔（入口、runtime、metadata、全部PNG/WAV）bytes與正式包完全一致。公開桌機及390手機視窗均以全新訪客開局：DEX30018、Lv1、僅冰波、素材ready，無頁面錯誤／缺失資源。證據留於本機 `.omx/state/freeze/public/bytes.json`、`browser.json` 及截圖。

本機五組受控測試、正常Lv1桌機鍵盤／手機觸控自然選卡至Lv9與旋風收束、來源穩定的最終原生演出已驗。原版素材及動作對照見 [reference.md](reference.md)，成長與來源差異見 [verification.json](verification.json) 和 [qa/provenance.md](qa/provenance.md)。獨立品質與美術檢查的產品阻擋已清空。

未驗實體手機長局、多人網路與真人音效聽評。原作側向雙向動作、自動施放與俯視生存玩法的改編界線有明列，不宣稱完全移植LF2操作。後續feature分支push不會自動更新此靜態分支來源。
