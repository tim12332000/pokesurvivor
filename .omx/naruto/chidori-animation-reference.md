# 雷切／千鳥原圖動作

使用既有《Naruto: Path of the Ninja 2》佐助素材（Hwdphg 擷取，[原圖](https://spritedatabase.net/files/ds/59/Sprite/Sasuke.png)）最下方 Charging Chidori 三張姿勢，取代雷切蓄力時的一般施術姿勢。裁切、腳底 anchor 與手部位置記在 `sprites.json` 的 `sasuke.chidori`；不更動其他招式共用的 Charge／Shoot。

初次蓄力依原有 0.09 秒時長依序顯示無雷光、兩張帶雷光的原圖。各裁切含有不同範圍的雷光，使用腳底 anchor 對齊人物。突進、追擊轉向及返回原位使用原 Attack 最後一張前伸姿勢；額外藍色雷光對齊其手部，左向鏡射。原素材沒有專屬千鳥奔跑或上下方向動作，這部分沿用側面原圖。

只有正在施放雷切的角色套用此姿勢；選角預覽、其他佐助實體及普通施術動作不套用。結束、死亡或清場後恢復原本動畫。追擊數量、傷害、冷卻、加速與無敵數值保持既有設定。
