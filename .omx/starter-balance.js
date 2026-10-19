/* Personal edition: begin each run with the existing permanent upgrades maxed.
 * Purchased levels and currency remain save data, never modified here.
 */
(() => {
  'use strict';
  const originalPerks = G.Upgrades.perks;
  const maxLevels = Object.freeze(Object.fromEntries(G.Upgrades.LIST.map(u => [u.id, u.max])));
  const balance = G.StarterBalance = {
    enabled: true, // Set false to restore purchased-level starting stats.
    maxLevels,
    perks: () => originalPerks(maxLevels)
  };

  function updateNotice() {
    const existing = document.getElementById('starter-balance-notice');
    if (!balance.enabled) { existing?.remove(); return; }
    const host = document.getElementById('free-project-notice');
    if (!host || existing) return;
    const note = document.createElement('span');
    note.id = 'starter-balance-notice';
    note.setAttribute('translate', 'no');
    note.style.display = 'block';
    note.textContent = '開局已套用永久強化全滿的基礎能力，無需先購買強化。';
    host.append(note);
  }

  G.Upgrades.perks = function (levels = {}) {
    updateNotice();
    return originalPerks.call(this, balance.enabled ? maxLevels : levels);
  };
  updateNotice();
})();
