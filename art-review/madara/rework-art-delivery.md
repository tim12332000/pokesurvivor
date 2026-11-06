# 斑重製美術交付：真身體、具身須佐與物質效果

前輪成品已被使用者否定，92分結論撤回。此文件記2026-11-06重製的實際資產與驗證範圍，不自行替獨立總監或玩家宣告達標。

## 凍結產品

- `runtime.js` SHA256：`847dd6f37ed6a2b159f6f3c027a5b79249b31c01e2a57b36d20e7d035d8d41ce`。
- `frames.json` SHA256：`3a29565396bdc850a0d3c35ece1df7e2e5b6b805c1f4c8df5f9064c861e88477`。
- `tools/build_madara_assets.py`可從保留的原始生成圖重建精裁runtime atlas與逐格資料。角色站高按同sheet基準規格化；蹲、踢、倒下不按每張crop高放大。
- common加13個具名sheet，共14個runtime PNG，transfer `5,135,408` bytes，解碼RGBA `17,209,584` bytes；原始高解析生成圖不在metadata.source內。選斑才載入，不預載到其他角色；白閃canvas首次需要才建立，未給所有巨神／元素複製一整套白圖。
- metadata fetch使用腳本完整query，PNG帶sheet.sha256，避免新runtime讀到同URL舊metadata。每個packed frame保留originalSource／originalSha256／sourceRect及實量socket記錄。

## 與舊版有實質差異的內容

本體保留可用身份待機／受傷／倒下。近身新增踏入、真掌伸臂、收臂轉腰、肘尖領先、轉身、抬膝、伸腿、回身踢及落足收勢；前／後另有真正對鏡頭與背鏡頭的掌、肘、踢接觸。不是把單掌手勢重播配扇圈。前後走路使用獨立雙步素材，取樣4.5fps與側向四相位9fps的實際雙步接觸頻率相同，不用整身bob或攻擊腿冒充步態。

火遁前後向各有結印、可見嘴部吐息和收束圖。嘴點以原圖格線量測，包含側向源圖(848,422)、前向吐息(806,223)、背向吐息(822,612)，之後才套pack scale及鏡射。火牆有炙亮核心、橘紅卷焰和不規則前緣，讀取戰鬥前進火面的width/depth/aim，不再以透明sector當成品。寬火牆tile的橫向長軸沿front寬度，火舌向前，不把整張壓成細長直條。

須佐用三個不同身體：開口肋骨與關節骨臂、厚甲胄雙臂持刀的半身武神、具長鼻／額晶／角冠／背層片／完整雙腿的完成體。四向有實際正後姿勢，側向才鏡射；不能旋轉整個直立身體或單獨旋socket冒充。主刀蓄勢、橫斬、低位跟進與回收有專圖，另一柄刀護勢，沒有宣稱不存在的交替雙臂攻擊。

投射守護是本作改編：肋骨／半身包住唯一地面本體，完成體兩腳落同一地面、本體仍在前景近身／吐火。ownerSocket表示本體腳底，ownerChest另列；canonicalSocket只記動漫agent實量可見額晶，不搬動64px人到額晶、不宣稱已證明原作座艙。armored原本把本體放在裙腰外的失敗已依每相位下胸量測修正。沒有在地面硬clip整張avatar，向下伸出的手／刀仍完整可見。

隕石改不均勻輪廓、明暗塊面與坑裂的巨大岩體，第一岩裂開殘留、第二岩砸碎與重碎塊各有材質。木分身出生有木根／纖維／剖分／顯形，消失有散塊；戰鬥讀真emerge／dismiss相位，並非只將透明本體疊一條綠腳線。

## 接觸／繪製共用資料

`sample`／`socketFor`與`avatarSample`／`avatarSocketFor`使用同一source frame、scale與鏡射。回傳`space:'visual-world'`的x/y是可見世界點，沒有偷偷旋轉到aim或先加地面偏移；戰鬥只在damage端做一次已約定的人體高度／guardian投影。真刀碰撞取同圖bladeBase→bladeTip及前後格掃掠，成品不再另外畫一柄線刀或以遠扇面結算。

特殊純下方反例曾全部miss：原rib正面掌實際位在胸骨左約71個game像素，不能靠移socket補。已新增`ribDown`中央前伸巨掌專姿；原source虛擬腰(768,620)、掌(765,727)、指尖(770,1009)，骨掌真的在畫面向下前景。總監以fresh原生場景重新驗到20至100距離真hurt，並看到當次中央掌圖。這不是為補傷而畫不可見延長線。

最後還以原圖格線抓出完成體背向刀尖名義點(925,639)落透明區，修為真正刀尖(893,639)。RGBA診斷用於查註冊，不代替實際敵身接觸和完整動畫驗收。

## 本輪確實看的證據

- 新當前基準正常入口：`rework-baseline/kimimaro-signature.png`的握骨鑽前衝、`pain-normal.png`的六具具身、`temari-signature.png`的握扇出力、鳴人正常／螺旋手裏劍圖。詳失敗盤點見`rework-art-audit.md`，沒有把數量當品質門檻。
- 原創新source已逐張實看：體術、正後體術、正後施術、三形須佐、其正後相位、卷火／岩體／裂岩材質及中央前伸骨掌。用alpha數據及瀏覽器真合成確認空隙透明；raw PNG查看器會顯示alpha0像素的殘RGB，不以該顯示追假霧。曾有rib v2最低alpha134的真背景問題，保留原圖並以imagegen清除至v3。
- `rework-baseline/body-64px-contact-sockets.png`：正常64px四向掌／肘／伸腳／落足，每點覆蓋畫中實肢。未把抬膝或蓄勢格稱作接觸。
- `rework-baseline/avatar-*-contact.png`與`avatar-armored-*-anchor-v2.png`：真runtime草地合成，owner64px、guardian170／235／380，標blade根尖、手及腳底；rib開肋包本體、armor修後頭胸在甲胄臂間、完成體完整雙腳與前景唯一斑。這些是API合成，不冒稱自然成長。
- `rework-baseline/avatar-rib-down-fixed-v2.png`：中央骨掌的真新source與同圖掌／指尖點、ground及64px本體合成，手完整伸到前景未裁。
- 動漫agent另親跑fresh正常入口與360，確認新armor本體進胸甲、真正正後嘴、rib包覆；總監另以normal-entry四向真敵、木質出生與卷焰前緣交叉看。詳細當次原生證據由各獨立lane保留，不拿美術自評分數替代。

## 待獨立總控最終核對的範圍

完成體原本在桌機正常鏡頭裁頭，獨立合成完整仍不能放行；root持有的窄camera framing只在本體完成體窗口按viewport留白／必要拉遠處理，最終正常入口由總監／動漫核對，不靠本文件宣告鏡頭完成。自然480秒成長、高數量連續畫面、巨人卡、手機／低畫質完整循環與所有傷害／生命週期由凍結候選的測試lane執行。

本次不宣稱實機長局、真人已覺得好玩、全動畫逐幀或音色已聽評。前輪92分已在原`art-review.md`明示撤回，`.omx/state/madara/ralph-progress.json`維持rework/revise直到獨立總控完成全部既定反例。選定素材的生成提示、原始輸出路徑和SHA見`generation-records-v2.json`、`supplement-generation-records-v2.json`及root的walk／wood provenance；有跨格或背景失敗的源版本亦留存且未用作runtime。
