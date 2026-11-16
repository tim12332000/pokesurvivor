/* Complete records and playable views have independent lifetimes. */
G.Catalog = (() => {
  let restriction = null;

  function isPlayable(dex) {
    return !!G.DEX_BY[+dex] && (restriction === null || restriction.has(+dex));
  }

  function restrictTo(ids) {
    if (ids === null) { restriction = null; return; }
    if (!Array.isArray(ids)) throw new TypeError('Playable character IDs must be an array or null');
    const next = new Set();
    for (const id of ids) {
      const dex = Number(id);
      if (!['number', 'string'].includes(typeof id) || !Number.isInteger(dex) || dex <= 0 || !G.DEX_BY[dex]) {
        throw new Error('Unknown playable character: ' + id);
      }
      next.add(dex);
    }
    restriction = next;
  }

  return Object.freeze({
    all: () => Object.values(G.DEX_BY),
    playable: () => G.DEX.filter(mon => isPlayable(mon.dex)),
    starters: () => G.STARTERS.filter(starter => isPlayable(starter.dex)),
    isPlayable,
    restrictTo
  });
})();
