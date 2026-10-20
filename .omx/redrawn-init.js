/* Install reviewed hero art before the standalone sandbox boots. */
(() => {
  const params = new URLSearchParams(location.search);
  // The review wrapper owns installation inside its child game frame.
  if (params.get('animationLab') === '1' || params.get('originalArt') === '1') return;
  window.PS_REDRAWN_READY = Promise.resolve().then(async () => {
    await Promise.all([AnimationAssets.load(), KyuubiForm.load()]);
    CastContinuityLab.install(G, { controls: false });
    AnimationRuntime.install(G);
    KyuubiForm.install(G);
  });
})();
