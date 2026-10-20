# 小李：少年篇體術角色

定位：近身掃群、踏入接觸後集中連擊。美術以現有重繪鳴人／佐助的身材比例、像素尺度、輪廓及腳底錨點製作；Ninja Council 3 只作研究，不直接裁切遊戲圖。

| 解鎖 | 招式 | 本作玩法 |
| --- | --- | --- |
| Lv.1 | 木葉旋風 | 0.86 秒冷卻、37 傷害、124 半徑、3.9 弧度近身踢擊；既有平衡保留。 |
| Lv.3 | 表蓮華 | 3 秒冷卻、145 起手距離；真實踏入接觸後上踢及摔落，總計 70 傷害。 |
| Lv.6 | 八門遁甲・開門 | 15 秒冷卻；5 秒攻擊 +30%、速度 +20%，之後 2 秒速度 -20%。 |
| Lv.9 | 裏蓮華 | 5 秒冷卻、180 起手距離；上踢、五段高速連擊與摔落，主目標總計 145 傷害。 |

表／裏蓮華落地對其他附近目標造成基礎傷害的 35%，這是生存遊戲改編。裏蓮華可獨立施放，與開門攻擊加成相容；獨立施放及所有數值皆為本作機制，不作原作設定聲明。少年小李不使用朝孔雀、夜凱或成年高階八門。

動作流程：approach → windup → lift → combo（僅裏蓮華）→ slam → recovery。角色實際踏入接觸位置，並非畫出遠方分身。接近移動以最多 4 像素步進檢查牆與碰撞，不額外給予無敵。目標死亡、遠離接觸範圍、路線封閉、角色死亡、世界切換及 clearFields 均中止。浮空保存在本招的獨立視覺高度，敵方繪圖透過 liftFor 疊加；完全不修改原生 jumpLift 或跳躍物理。首領不浮空。

官方研究：

- [官方體術示範：木葉旋風](https://naruto-official.com/en/news/01_1489)
- [小李生日專欄：負重、表蓮華、第四／第五門與裏蓮華](https://naruto-official.com/en/news/01_1652)
- [動畫官方：Lee’s Hidden Strength: Forbidden Secret Jutsu!](https://naruto-official.com/en/anime/naruto1/list/01_273)
- [Ninja Council 3 美術研究索引](https://spritedatabase.net/game/55)

G.NarutoLee 提供 supports、canCast、cast、clear、update、liftFor 與 active getter；updateFields 已接線，不需外部重複呼叫 update。active 暴露 owner、world、target、kind、phase、phaseAge、age、visualLift，供唯一玩家本體繪製姿勢與高度。敵方繪圖高度採原生 jumpLift 加上 liftFor(enemy)。
