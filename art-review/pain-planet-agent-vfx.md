# 地爆天星演出細修

此輪遵循使用者指定的遊戲版本：聚合成月球，整球往下墜，觸地後以大範圍震波往外擴散並造成傷害。既有考據與直接官方來源沿用 [地爆天星演出紀錄](pain-planet-vfx.md)，不宣稱看過完整影片，也不把此落地版本說成已核實的原作完整演出。

`js/systems/pain-vfx/planet.js` 只增加既有繪製的細節：

- 下墜時，完整月球兩側增加隨下落加速伸長的短線；月球本體由原繪製保留。
- 下墜末段，地面接觸影加深，強化月球接近地面的重量。
- 觸地震波的斷裂地表短線與碎屑跟隨 `NarutoPain.planetVisual(e).waveRadius`，塵粒落在波前後方；近中心接觸塵很快消退，保留外擴波的辨識度。

新增接點為 `G.PainSkillVFX.planet.action(ctx,f,s)`、`ground(ctx,f,s)`、`effect(ctx,e,s)`；可在既有月球、地面與崩落特效後疊加。不改任何數值、傷害、時間、狀態或碰撞；所有繪製均使用模擬年齡、固定迴圈與 Canvas save/restore，無隨機數或持久粒子。

驗證：`node --check js/systems/pain-vfx/planet.js`。最終遊戲畫面與視覺評核由整合主代理在所有技能接線後執行。
