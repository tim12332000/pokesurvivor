# 原地束縛，取消跟隨玩家拖行

使用者指出「束縛住怎麼會被我拖著走」。先前由設計加入的同向位移模仿不再適用：被束縛的敵人留在原地，鹿丸移動只改影線來源及沿路佈札，不將玩家位移加到敵人座標。

`.omx/naruto-shikamaru.js` 移除moveBoard中的敵人位移迴圈及強制Walk；保留原生狀態時計、普通怪停止新攻擊、強敵原有攻擊差異、ABC接力／單根／影池與收束。技能和選角說明同步移除「帶敵走入札路」，不暗中改成追蹤或瞬移陷阱。

`tools/test_shikamaru_stationary_bind.py` 在真正命中A/B後，以本體／真分身 × 普通怪／強敵四組，讓擁有者實際位移(60,20)，跑原生Combat.tick、Enemy.update和影術update。四組被縛座標不變、dragged=0、影池來源跟擁有者且真影線長度變化；普通怪的背景動畫維持Idle（受擊Hurt一次性動畫可正常結束），clear後解除。另回歸真卡ABC成長、取消／牆及接觸傷害／DOT時計。

新測試對舊來源`11149aee`真實腳本路由可重現「owner movement dragged a bound enemy」失敗，對新版全部通過、來源穩定。原始紀錄在 `qa/stationary-bind/{baseline-report,report}.json`。此為有界控制修正，不重拍無關自然長局；舊「同向搬動」驗收已明確撤回，沒有改舊expect掩蓋差異。

尚未發布；公開版本及開局核對待主代理收束。未驗手機實機長局及音效聽評，不替玩家判定樂趣。
