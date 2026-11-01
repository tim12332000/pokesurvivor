// Personal sandbox: normal currency consumption, separate save key, no cloud services.
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
    const initialCoins = save.coins;
    try {
      const stored = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (stored && typeof stored === 'object') Object.assign(save, stored);
    } catch (_) { /* Start fresh if sandbox storage is unavailable or corrupt. */ }
    // Migrate only the exact balances written by the former unlimited mode.
    // Keep all collection/progression fields and any ordinary currency balances.
    if (save.coins === 1000000000) save.coins = initialCoins;
    save.tickets = save.tickets || { t1: 0, t10: 0 };
    for (const ticket of ['t1', 't10']) {
      if (save.tickets[ticket] === 1000000000) save.tickets[ticket] = 0;
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
})();
