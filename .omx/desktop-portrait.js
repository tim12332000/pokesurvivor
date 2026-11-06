/* Give desktop players the same real viewport as the phone portrait game. */
(() => {
  const params = new URLSearchParams(location.search);
  window.PS_PORTRAIT_VIEW = params.get('layout') === 'portrait' ||
    (params.get('layout') !== 'wide' && innerWidth <= 600 && innerHeight > innerWidth);
  if (window.top !== window.self) return;
  if (params.get('layout') === 'wide' || innerWidth <= 600) return;
  if (params.get('layout') !== 'portrait' && !matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  const target = new URL('portrait.html', document.currentScript.src);
  target.search = location.search;
  target.hash = location.hash;
  location.replace(target.href);
})();
