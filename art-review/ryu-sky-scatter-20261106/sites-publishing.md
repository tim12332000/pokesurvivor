# 合併版外部發布：Sites

公開網址：[PokéSurvivor：石流龍與烏鷺](https://tim-pokesurvivor-sendai-20261107.handymusic1.chatgpt.site)。Sites於台北2026-11-07 02:30:26回報正式部署 `succeeded`，已設為公開。

| 項目 | 實際值 |
| --- | --- |
| 遊戲來源 | `190c500e583aa012b965c7c8b0e3718f554b6223`，已合併到`feat/digimon-sandbox` |
| Site project_id | `appgprj_6aee192bee748191aaf485c8e270b52b` |
| 儲存版本 | `1`／`appgprj_6aee192bee748191aaf485c8e270b52b~appgver_230a1e885bec8191a93b6ffe791f919d` |
| 部署 | `appgdep_6aee1c64a61481919eccea0fd5720f5f` |
| Sites來源提交 | `54defcefa60b6bfce1032cfaa985220630779991` |
| 完整Sites來源tree | `d9ae7c967f55f0defe150549bb41be7a67b06579` |
| 原始遊戲靜態tree | `b8667f37562d5978250839e6586a3436bc79d6c8` |
| 封裝內容 | 13,847檔（原遊戲13,846檔＋hosting metadata），內容hash `sha256:1d7869e350e9700f9c588d0b0b6633c1b2c37b88d7a09703999ecbf5392c6915` |

## 內容及傳輸

GitHub Pages仍未生效時，依使用者「發布到外部」要求，使用Sites提供獨立公開網址。完整沿用已驗證的canonical遊戲包，石流龍升空迴旋追蹤散射與烏鷺完整繞彈回射均包含在內；十個關鍵入口／執行檔在複製後逐一驗證bytes相同。沒有新增遊戲依賴、刪減素材或變更GitHub服務保護。

初次來源推送遭163.4MiB單次資料量超限拒絕，服務明確回覆每次上限64MiB。改以五段各不超過40MiB原始檔案的前進提交同步；只有最後完整提交被儲存為版本並部署，中間提交未部署。最終tree與原完整快照`15dfddd7957458a44349aa1544b5fd69d62b37f1`完全相同。認證僅在記憶體／程序stdin中使用，未保存token。

## 驗證與限制

Sites原生部署結果及公開權限均已確認。遊戲的桌機／手機正常入口、合法選卡、射程與命中、美術及打包驗證沿用[實作記錄](implementation.md)。封裝未改動該遊戲內容。

部署後的自動HTTP讀取被Cloudflare邊緣防護以403／error1010拒絕；不是取得公開檔案後的hash不符，也不能由此推論一般訪客一定無法開啟。內建瀏覽器連線另回報`The browser access host is unavailable`。因此本次**確認正式部署成功，但未完成新主機上的公開檔案雜湊及線上實玩驗收**，沒有繞過防護或宣稱這部分通過。原生結果與限制見[發布資料](qa/sites-release.json)。

原GitHub Pages發布嘗試保留在[原發布追蹤](publishing.md)。Sites本機來源位於`C:/Git/pokesurvivor/.omx/sites/ryu-sendai-external/`，其`.openai/hosting.json`已保存此project_id；後續更新須重用該Site，不另建重複站。
