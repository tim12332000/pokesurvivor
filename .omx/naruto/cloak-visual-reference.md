# 九尾查克拉外衣：一尾視覺參考

## 最新實作：重新繪製，原遊戲圖僅供研究

依使用者後續指示，鳴人、佐助與一尾現已統一重新繪製。現用一尾為 `art-review/redrawn/one-tail-v2.png`，不是下列研究用原遊戲圖。共通動作、招式和變身以同一套比例與描邊製作；完整提示詞與雜湊見 `art-review/redrawn/provenance.json`。下面保留前次素材查核經過，不代表仍直接使用該原始素材。

## 動作組切換：修正前次方案

使用者指出，變身外衣應搭配專用動作。查得以下遊戲將九尾鳴人另列為獨立角色素材：

- [Jump Ultimate Stars：Naruto Uzumaki (Nine-Tails/Kyubi)](https://www.spriters-resource.com/ds_dsi/jus/asset/20888/)，獨立 Fighters 圖集，1840 × 2424，來源頁列 FRET／Dazz。
- [Path of the Ninja 2：角色素材清單](https://www.spriters-resource.com/ds_dsi/narutopotn2/)，普通 Naruto 與 Naruto (Nine-Tails) 分開收錄；後者素材頁編號 79187。
- [Sprite Database 的同遊戲清單](https://spritedatabase.net/game/59)也分別列 Naruto 與 Naruto (Kyuubi)。

已取得與使用者提供圖片相同的原尺寸一尾圖集，並接入內測的變身動畫組。[下載鏡像](https://spritecollection.weebly.com/uploads/7/8/7/7/7877225/kyubi_naruto_sheet.png)保留原圖署名 **Ripped by Neimad / Give credit if used**。原圖完整保存在 `art-review/candidates/naruto-one-tail-source.png`；98 個影格、14 組動畫的裁切與腳底位置記錄於 `art-review/kyuubi-frames.json`。

前版的受傷姿勢、旋轉和輪廓特效屬改編，並不是九尾專用動作。現在效果啟動時切換原圖的變身動畫組，期間的待機、移動、攻擊、施術及受傷採該組；到期、死亡、換場時還原。原圖外衣／尾巴已畫入影格，變身期間停用程序外衣，避免重複。原圖朝右，朝左鏡射，上下沿用側面。共通忍具與影分身等跨遊戲招式採該圖的投擲／防禦姿勢銜接，戰鬥機制保持現行版本。

以下外觀筆記仍有效，但只能作為專用動作素材的外觀參考。

2026-10-20 對照[官方終末之谷篇回顧](https://naruto-official.com/en/news/01_1296)的 071、072 動畫截圖。這裡採少年鳴人的紅色一尾外衣；後期金色九尾查克拉模式與重粒子模式不在本招範圍內。

- 紅橙色半透明查克拉貼合身體，保留人物、服裝與臉部辨識；不是固定紅色衣服或盔甲。
- 輪廓有沸騰氣泡與不規則邊緣。頭頂有查克拉形成的尖耳輪廓，背後只有一根粗而漸細、彎曲向上升起的尾巴。
- 低重心、前傾與伸手是主要姿態。實驗版以既有候選姿勢改編蹲伏與前傾，並非新增的四足專用動畫。
- 查克拉反擊只在既有反擊階段畫出伸展痕跡；傷害、範圍、持續時間與冷卻不變。

直接圖片來源：

- [071：低姿態、一尾與沸騰外衣](https://cmsapi-frontend.naruto-official.com/site/api/naruto/Image/get?path=%2Fnaruto%2Fjp%2Fnews%2F2022%2F10%2F17%2FBYOTc1iASab9eSiA%2F071.jpg)
- [072：前傾、查克拉爪與頭部輪廓](https://cmsapi-frontend.naruto-official.com/site/api/naruto/Image/get?path=%2Fnaruto%2Fjp%2Fnews%2F2022%2F10%2F17%2FNBwZ4NvKnbwLCEWZ%2F072.jpg)

舊版程序外衣只留作關閉新版動作時的對照；新版由完整變身影格呈現人物、外衣與尾巴，依模擬時間播放，暫停時不繼續播放。
