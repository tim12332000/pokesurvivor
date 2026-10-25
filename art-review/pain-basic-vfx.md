# 黑棒連射演出

本次只調整 Canvas 演出。5／5／6／7／8 根、傷害、射速、碰撞及命中邏輯由既有戰鬥程式維持。

- 發射：手前短暫出現兩條灰紫壓力線，不使用火光。
- 飛行：不透明黑色實體棒，尖端朝飛行方向，單像素金屬邊及短灰色氣流。氣流最多 24 像素，不畫能量光束。
- 命中：短促交叉打擊痕、固定六枚黑灰碎屑，.18 秒消退。碎屑為本遊戲閱讀性改編，不宣稱原作黑棒必定碎裂。

## 查證範圍

直接讀取官方文章 [S.H.Figuarts PAIN TENDO -Six Path Rinnegan- Arrives!](https://naruto-official.com/en/news/01_1799)（2024-05-24），文章明確介紹天道的黑棒武器配件。本次查閱的是網頁文字，沒有觀看連結影片，也沒有以商品介紹推論連射時間、彈數、命中效果。黑棒實體外形之外的連射及碎屑均屬本遊戲改編。

## 接線

載入 `js/systems/pain-vfx/basic.js` 後：

- 用 `PainSkillVFX.basic.shot(ctx,p)` 取代原有 rod projectile 繪製；`p.x/y` 為世界座標，內部沿用 `y - 12` 高度。
- 每根棒發射新增 `{kind:'rod-launch',x,y,angle,age:0,life:.12}`，命中／撞牆新增 `{kind:'rod-hit',x,y,angle,age:0,life:.18}`；由共用效果生命週期更新，呼叫 `basic.effect(ctx,e)`。
- 方法不修改輸入、遊戲狀態或效果生命週期；無隨機、時鐘、資產、依賴或事件監聽，所有 Canvas 狀態 save/restore，固定迴圈上限六。

## 驗證

`node --check js/systems/pain-vfx/basic.js` 通過。整合後的實際桌機／手機截圖與 visual-verdict 由主代理統一驗收；本子任務未宣稱完成遊戲內視覺驗證。
