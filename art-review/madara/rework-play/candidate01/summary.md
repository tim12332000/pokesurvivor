# 候選01：真機制與自然成形成片

候選 identity：`ea303177f57c0868`。測試與長局都使用獨立凍結的 `candidate-site01`；`candidate-manifest.json` 中174個runtime檔逐項SHA256重驗一致。engine為 `14da27cef657835fb2e45e69a6fa7e50aa182af6c189112f12e75f57998ef078`，包含最後Giant broadphase窄修。原生長局前後來源雜湊相同，沒有在錄製中換源。

發布時唯一後改為技能描述「獨立須佐護體六秒」→「須佐投射現身六秒」，避免虛暗示盾。發布engine為 `57977e23cf17568f8e8fcaa4f1f8e4a8b4c37e1f3194feb2e10e2d28c92b5915`；`../../rework-release-text-delta.json`保存反向替換後整份byte恰等候選的證明。數值、碰撞、時序、卡牌、掛鉤、素材與渲染完全未改，故保留同候選長局／三view證據，不為純文字重拍。

這些是機制／實況證據，不是玩家主觀樂趣或美術評分。動漫、美術及總監須看同版完整動作與連續週期，另行判定。

## 自然單局結果

正常選角Lv1起始、永久升級全0、地形seed231106與同初始PRNG流；順時針小方形真鍵盤，每1.5game秒換邊，真UI選卡、無重抽，策略與現版／小李基線相同。不改level／XP／無敵／傷害／spawner，不手動cast或advance。原生預設2倍速度保留。

| 觀察 | 候選01實況 |
| --- | --- |
| 原生game時間／實際遊玩wall時間 | 480.17秒／262.48秒（不含初始載入） |
| 局次／死亡 | 單局、無死亡、無重試 |
| 等級／真卡成本 | Lv1→46，共45張 |
| 首筆敵人hurt | 10.21秒 |
| 終局HP | 456.24／540.72；生命、治療、Giant等都來自真卡／原生流程 |
| 終局技能 | 五招皆rank5，數量4、CD卡3、Giant卡2、自身分身卡1等，完整成本見ledger |
| 完成體 | 首次可見293.48秒起，共19個完整可見窗口；每窗取樣覆蓋5.60–5.93game秒 |
| 軍團與完成體並存 | 423筆取樣同時有army與perfect狀態 |
| 頁面錯誤／缺失請求 | 0／0 |

自然學招／升階成本沒有被省略：

| 時間（game秒） | 卡成本 | 真選項 |
| --- | --- | --- |
| 14.69 | 1 | 生命+10% |
| 25.62 | 2 | 學豪火 |
| 31.13 | 3 | 豪火rank2，真火面寬／推進射程成長 |
| 45.33 | 4 | 體術rank2，踢掃接觸 |
| 56.21 | 5 | 學須佐 |
| 71.35 | 6 | 豪火rank3，真留焰 |
| 99.45 | 8 | 學雙隕石 |
| 149.04 | 11 | 學木分身 |
| 183.93 | 12 | 須佐rank2 |
| 291.98 | 23 | 須佐rank3，完成體解鎖 |

兩張須佐升階確實是兩個專屬投資，但在這個固定選卡策略與真offer序列中，實際佔總第12／23張卡，不能宣稱起始幾張卡就已自然完成體。現版基線120秒只有Lv7／6卡、未齊後期招；候選初120秒到Lv10／9卡，並在後續真正學齊、解鎖與施放。這不是同敵潮DPS或平衡結論：不同戰鬥／影格會消耗不同亂數，卡與敵潮也會分歧。

## 軍團前後的勢能讀法

學木分身前後相鄰各60秒，真本體hurt為24→7、真本體火面hurt為118→95；後段軍團有494筆primary hit。兩段perfectCount增量都0，但當時須佐分別rank1→1及rank1→2，**尚未解鎖完成體**，勢能也已封頂3，不能把0增量誤稱軍團搶勢bug。

須佐rank3後實際出現19個完整完成體窗口，且與軍團同時存在的取樣有423筆，因此本次未觀察到「成軍後永久不能再次變身」。這不證明軍團對本體末擊比例沒有影響；不同波次／階數不構成因果對照。原始pulse按body／field-fire／guardian／army-*／自身分身等來源保留，供後續按真條件判讀。

## 受控機制與畫面

`../candidate01-mechanics/report.json`：桌機1280×900、390×844、360×800各58個機制／生命週期case，`ok=true`，零failures／errors／missing，來源測前後一致。`../candidate01-low/report.json`：360px明確quality=low／fx=0，同樣通過。

- 手腳短接觸、正常同段draw/socket同幀、未來腳位不預傷、移動world endpoint及高數量尾段掃掠；原生tick重試方向可達性與真KeyD撤退。
- 前推火面近敵先中／遠敵後中、活嘴出源與舊火面固定；真刀道與三form四方向來源。
- Q4／CD倍率0.5，在普通及**由三次真火輪賺得的完成體窗口**內，原生自動體術與新豪火都有cast與真hurt，不靠canCast欄位放行。
- 空招／箱子／軍團／自身分身／留焰／碎岩不額外餵勢；完結不刪已發火面；雙岩事件因果與不同碎岩落點、物質源點／高度、一次真殘岩接力。
- 軍團角色實際來源／站位／保留目標與失效重配；rank1真近戰fallback→兩張合法卡後rank3真後衛刀；遠群後衛真移入刀程。
- 活軍團首Q只補1名真出生演員，舊actor身份／位置／時計／action不刷新；rank1→2同舊前鋒palm真傷46.12608→55.351296（1.2倍），沒有免費刷新召軍CD。
- 原World／epoch／同波回呼取消／stale grid／擴散outer／props／暫停／凍結／重開／分身owner隔離及live卡預覽邊界保留。

原生RAF受控相位入口：[gallery](../candidate01-mechanics/gallery.html)。這批停隨機出生、用受控高HP靜靶與指定階數／數量，並非自然養成影片；相機和招式由真正RAF推進，首末接觸與收勢另有實際phase／geometry紀錄。

## 影片與review

完整原始全窗：[native-play.webm](madara/attempt-1/native-play.webm)，82,529,749 bytes；不剪接、不變速，含啟動、真卡畫面與整局。Playwright原WebM有seek兼容陷阱，不能設currentTime後沒驗HUD就宣稱看了指定時間；原檔保持不變，精確節選／可seek轉碼由主代理與總監另存來源SHA與區間。

公開純轉碼節選：[起始MP4](../../../../assets/previews/madara-natural-start.mp4)（原片wall 0–32秒）、[成形MP4](../../../../assets/previews/madara-natural-formed.mp4)（wall146–190秒）。這些是連續區間節選，不是完整8分鐘game時間。首三個完成體可見窗口分別約原片wall155.17–158.81、161.67–164.71、167.26–170.20秒；連看146–190段可含普通窗、恢復及多輪完成體。HUD game時計為最終核對，wall索引可能有少量navigation lead。

總監的本機seekable審稿片為 `../../director-review/natural-first-windows.mp4`（原片wall153–175）及 `../../director-review/natural-late-army.mp4`（234–262.4）；有效實播放／逐樣本currentTime與sourceTime證據是 `../../director-review/natural-playback-review-corrected.json`，來源區間見同目錄 `review-clips.json`。先前raw WebM seek回0的 `natural-playback-review.json` 是無效工具歷程，不作成形證據。大型審稿片不加入公開preview，公開入口仍使用主代理的壓縮MP4。

完整offers、每張成本／前後快照、1,873筆狀態取樣、13,175筆敵hurt及11,599筆有傷pulse在 `madara/attempt-1/run.json`；`report.json`保存來源穩定性、manifest及成形分析。原片與凍結site只留本機，不加入正常開局下載；兩個公開MP4由獨立preview入口載入。

未涵蓋：實體手機8分鐘長局、人手策略與主觀樂趣、音色聽評。自然影片是桌機1100×850；手機是正常入口／觸控及受控相位驗證，兩者分開報告。
