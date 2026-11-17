/* Firen uses the shared classic LF2 registration and card contracts. */
(() => {
  const dex=30021,kit=G.LF2Bosses.kits.find(row=>row[0]===dex);
  if(!kit||kit[1].length!==4)throw Error('Complete classic Firen kit is missing');
  G.LF2FirenKit={dex,kit,ids:G.LF2Bosses.idsFor(dex),power:G.LF2Firen.specs,source:G.LF2Bosses.source};
})();
