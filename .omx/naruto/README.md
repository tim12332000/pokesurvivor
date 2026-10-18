# Naruto crossover section

Generation 11 follows Digimon in collection and gacha. The Naruto button appears
in the top navigation and in the first-time Digimon picker. Eight characters are
available: Naruto, Sasuke, Sakura, Kakashi, Hinata, Rock Lee, Gaara and Itachi.
Choosing a ninja uses the existing sandbox save without resetting the collection.
Naruto characters do not use the Digimon evolution system.

Fourteen adapted skills include eight character signatures, two shared ninja tools
and four additional character skills restricted to their respective characters.
The in-game skill guide links each character to official Naruto source articles.
Attack names and character identities are source-based; damage, ranges, cooldowns,
type mappings and crowd-control effects are survival-game design choices. In
particular, Lightning Blade's ranged beam and automated combo timings are gameplay
adaptations rather than literal reproductions of the manga.

Gaara's primary now sweeps a widening sand wave across enemies, briefly binds
ordinary enemies (bosses resist), and erupts across the swept area once. It no
longer fires a sand orb. Naruto can learn Rasenshuriken, Sasuke and Itachi can
learn Fireball Jutsu, and Kakashi can learn Water Dragon. The latter three use
area impacts, with real multi-target damage checks and character-specific pools.
The [AoE audit](aoe-audit.md) records references and separates canon ability from
the crossover's area, timeline and balance choices. Existing Sakura, Hinata and
Rock Lee close-range attacks also have tested multi-target areas.

## Naruto shadow clones

Naruto now starts with Multi Shadow Clone Jutsu. Three lightweight actors move,
choose nearby enemies and punch; they share the owner's damage credit and never
become extra players, collect rewards or write saves. Normal pursuers can be
distracted by a closer clone; bosses retain their target. Contact or hostile
projectile hits disperse a clone with smoke. Initial lifetime is six seconds and
cooldown ten seconds. Skill level three raises the cap to four and enables the
Rasengan follow-up; level four extends lifetime to seven seconds; level five
raises the cap to five. Recasting fills vacancies without refreshing existing
lifetimes. Switching slots keeps existing clones until they expire.

Character level three guarantees a Rasengan learning choice, and level six a
Rasenshuriken choice. When four slots are full, the card explicitly offers to
replace a shared kunai/shuriken slot rather than removing a character skill.
Players may decline. The original Rasengan move ID is preserved. With the clone
skill at level three or higher, casting Rasengan lets at most two eligible
clones share a follow-up worth 40% of that cast's damage budget. Clones do not
recursively summon or copy Rasenshuriken. Pause freezes their simulation time;
death and scene changes clear actors and smoke. A gold chevron marks the owner.

Run `python .omx/check_naruto_clones.py` for caps, lifetime, walls, distributed
attacks, contact/projectile dispersal, aggro, shared combo damage, training choices,
pause and scene cleanup. Original ability reference:
https://naruto-official.com/en/news/01_1423 . Actor counts, automatic behavior,
timing and damage budgets are this game's adaptation. Multiplayer replication of
clone actors is not implemented in this guest-only edition.

## Original artwork

The sprites are original downloaded sheets from *Naruto: Path of the Ninja 2*
(Nintendo DS), mirrored by Sprite Database. Sources, download hashes and sheet
credits are recorded in `sources.json`; the original PNGs retain their credits.
Sheet ripping is credited to **Hwdphg**. Character/game artwork remains the
property of its original rights holders; a public sprite download is not a new
license for that artwork. This is a free, unofficial fan crossover.

`sprites.json` records source frame rectangles. Six characters use overworld walk
frames. Sasuke and Itachi use side-facing battle poses with runtime mirroring;
these two do not have four-direction walking animation in this version. Runtime
Canvas removes the exact flat sheet background and draws with nearest-neighbor
scaling; downloaded PNGs are unchanged. Rendering keeps characters around 64
world pixels high, separate from menu-preview fitting.

Horizontal field rows are audited against the original face direction. The six
field sheets have right-facing frames above left-facing frames; the two battle
sheets face right in the original, so only left views are mirrored.

The renderer now plays available original attack/jutsu sequences for all eight
characters, Naruto's casting sequence, and the battle sheets' hurt/faint rows.
Attack and Shoot share the field combat sequences; missing action directions use
the documented default view or an explicit mirror. Field sheets without verified
hurt/faint art retain fallback flash/flatten presentation. Those fallbacks are not
claimed to be newly sourced animations. Scaling uses standing height, so extended
attacks and fallen poses retain their original proportions.

Regenerate metadata and the shared entry with `python .omx/make_digimon.py`.
Run `python .omx/check_naruto.py` for browser checks without a local HTTP server.
Run `python .omx/check_naruto_animations.py` for source direction, frame timing,
signature-animation checks and a labeled screenshot of all eight characters.
Run `python .omx/check_gaara.py` for sand-wave phases, three spread targets plus
outside controls, boss resistance, walls, cleanup, extra AoE ownership and range
upgrades. The reusable `$naruto-survivor-skills` policy is tracked under
`.codex/skills/naruto-survivor-skills/SKILL.md` and installed in the local Codex
skills directory for future character work.
Set `PAGES_LIVE=1` to check the deployed site instead. Tests require Python
Playwright and the installed Windows Chrome, matching the other sandbox checks.

Deployment remains https://tim12332000.github.io/pokesurvivor/ and uses only the
personal `feat/digimon-sandbox` branch. No upstream PR is created or changed.
