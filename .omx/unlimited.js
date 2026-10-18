// Personal sandbox: separate save key; never initialize cloud services.
(() => {
  const local = ['127.0.0.1', 'localhost'].includes(location.hostname);
  const personalSite = location.hostname === 'tim12332000.github.io' && location.pathname.startsWith('/pokesurvivor/');
  if (!local && !personalSite) {
    throw new Error('This sandbox is available on localhost or the personal GitHub Pages site.');
  }
  const KEY = window.PS_SANDBOX_KEY || 'ps.sandbox.unlimited.v1';
  G.FIREBASE_CONFIG = null;
  const playAsGuest = G.DB.playAsGuest;
  G.DB.playAsGuest = () => {
    const session = localStorage.getItem('ps.session');
    const result = playAsGuest();
    if (session !== null) localStorage.setItem('ps.session', session);
    const save = G.DB.save;
    try {
      const stored = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (stored && typeof stored === 'object') Object.assign(save, stored);
    } catch (_) { /* Start fresh if sandbox storage is unavailable or corrupt. */ }
    Object.defineProperty(save, 'coins', {
      enumerable: true, configurable: true,
      get: () => 1000000000,
      set: () => {} // Purchases and rewards retain an inexhaustible balance.
    });
    save.tickets = save.tickets || {};
    for (const ticket of ['t1', 't10']) {
      Object.defineProperty(save.tickets, ticket, {
        enumerable: true, configurable: true,
        get: () => 1000000000,
        set: () => {}
      });
    }
    return result;
  };
  G.DB.ready = async () => { G.DB.playAsGuest(); return true; };
  G.DB.commit = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify(G.DB.save));
      return true;
    } catch (_) { return false; }
  };
  addEventListener('pagehide', () => G.DB.commit());
  const coins = document.getElementById('coins');
  const ticketDisplays = ['tickets-pill', 'gacha-tickets'].map(id => document.getElementById(id));
  const showInfinity = () => {
    if (coins.textContent !== '∞') coins.textContent = '∞';
    for (const display of ticketDisplays) {
      const text = document.createTreeWalker(display, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = text.nextNode())) {
        const value = node.nodeValue.replace(/\b1000000000\b/g, '∞');
        if (value !== node.nodeValue) node.nodeValue = value;
      }
    }
  };
  const observer = new MutationObserver(showInfinity);
  for (const display of [coins, ...ticketDisplays]) {
    observer.observe(display, { childList: true, characterData: true, subtree: true });
  }
  showInfinity();
  const badge = document.createElement('div');
  badge.textContent = window.PS_SANDBOX_KEY === 'ps.sandbox.digimon.v1'
    ? '數碼寶貝本地版 · 金幣與抽卡券無限 · 獨立存檔'
    : '本地測試版 · 金幣與抽卡券無限 · 獨立存檔';
  badge.translate = false;
  badge.style.cssText = 'position:fixed;bottom:8px;right:8px;z-index:9999;padding:6px 10px;background:#122342;color:#ffd23f;border:1px solid #ffd23f;border-radius:6px;font:13px sans-serif;pointer-events:none';
  document.body.appendChild(badge);
})();
