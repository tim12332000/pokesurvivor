/* Original classic LF2 samples, emitted only by live simulation events. */
(() => {
  'use strict';
  const voices = new Set();
  function stop(owner) {
    for (const voice of voices) {
      if (owner && voice.owner !== owner) continue;
      voices.delete(voice);
      if (voice.source) { try { voice.source.stop(); } catch {} }
    }
  }
  async function play(id, owner = G.Game.player) {
    if (!G.Audio?.sample || G.Game.state !== 'playing' || !owner || owner.dead || owner.hp <= 0 || voices.size >= 8) return false;
    const entry = G.LF2Art?.metadata?.source.files.find(file => file.runtime?.endsWith('/' + id + '.wav'));
    if (!entry) return false;
    const voice = {owner, world:G.World, epoch:G.CombatPulse?.epoch, source:null};
    voices.add(voice);
    const guard = () => voices.has(voice) && G.Game.state === 'playing' &&
      G.World === voice.world && G.CombatPulse?.epoch === voice.epoch && !owner.dead && owner.hp > 0;
    const source = await G.Audio.sample(entry.runtime + '?v=' + entry.runtime_sha256.slice(0,12), {gain:.5, guard});
    if (!source) { voices.delete(voice); return false; }
    voice.source = source;
    source.addEventListener('ended', () => voices.delete(voice), {once:true});
    return true;
  }
  G.LF2Audio = {play, stop};
})();
