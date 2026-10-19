# Naruto crossover section

Generation 11 follows Digimon in collection and gacha. The Naruto button appears
in the top navigation and in the first-time Digimon picker. Eight characters are
available: Naruto, Sasuke, Sakura, Kakashi, Hinata, Rock Lee, Gaara and Itachi.
Choosing a ninja uses the existing sandbox save without resetting the collection.
Naruto characters do not use the Digimon evolution system.

Twenty-five adapted skills cover three character techniques per ninja, with
Fireball shared only by Sasuke and Itachi, plus two common ninja tools.
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

Naruto now starts with Multi Shadow Clone Jutsu. Eight lightweight actors move,
choose nearby enemies and punch; they share the owner's damage credit and never
become extra players, collect rewards or write saves. Normal pursuers can be
distracted by a closer clone; bosses retain their target. Contact or hostile
projectile hits disperse a clone with smoke. Initial lifetime is six seconds and
cooldown four seconds. Every skill level retains the eight-clone cap. Skill
level three shortens their copied-technique cooldown by 10%; level four extends
lifetime to seven seconds; level five improves their copied-technique damage.
Recasting fills vacancies without refreshing existing
lifetimes. While at the cap, the active skill polls for a vacancy without wasting
a new four-second cooldown or repeatedly replaying Charge. Switching slots keeps
existing clones until they expire.

Character level three guarantees a Rasengan learning choice, and level six a
Rasenshuriken choice. When four slots are full, the card explicitly offers to
replace a shared kunai/shuriken slot rather than removing a character skill.
Players may decline. The original Rasengan move ID is preserved. Switching to
learned Rasengan, Rasenshuriken, Kunai or Shuriken lets existing clones use that
technique autonomously, without waiting for the player's cast. Each maintains a
separate cooldown per technique across slot switches. Each copied cast uses
one eighth of the owner's base damage, so eight clones share one extra cast's
budget (before their explicit skill upgrades and integer rounding). Both the
direct hit and explosion are scaled. Clones cannot recursively summon or borrow
other characters' techniques. While Shadow Clone is selected, they use basic
punches. Pause freezes their simulation time;
death and scene changes clear actors and smoke. A gold chevron marks the owner.

Run `python .omx/check_naruto_clones.py` for caps, lifetime, walls, distributed
attacks, contact/projectile dispersal, aggro, shared combo damage, training choices,
pause and scene cleanup. Original ability reference:
https://naruto-official.com/en/news/01_1423 . Actor counts, automatic behavior,
timing and damage budgets are this game's adaptation. Multiplayer replication of
clone actors is not implemented in this guest-only edition.

## Completed eight-character kits

| Character | Starting technique | Character level 3 choice | Character level 6 choice |
| --- | --- | --- | --- |
| Naruto | Multi Shadow Clone | Rasengan | Rasenshuriken |
| Sasuke | Chidori | Fireball | Sharingan prediction |
| Sakura | Cherry Blossom Impact | Medical ninjutsu | Regeneration |
| Kakashi | Short-range Lightning Blade | Water Dragon | Earth Wall |
| Hinata | Gentle Fist | Twin Lion Fists | Byakugan |
| Rock Lee | Leaf Whirlwind | Forward Lotus | Inner Gates |
| Gaara | Sand Tsunami / burial | Sand Coffin / burial | Sand Shield |
| Itachi | Single-target Tsukuyomi | Fireball | Amaterasu |

Each role retains the four-slot choice system and can decline a learning card.
When full, an explicit card can replace a shared ninja tool in place, retaining
its key binding. Extra-starting-move perks cannot bypass character level gates.
Cooldowns and effect details are available in the source-backed in-game guide.

Healing is capped at maximum health and suppressed when full; regeneration has
five timed ticks. Sharingan provides one dodge and one offensive-cast bonus.
Byakugan marks visible nearby threats and improves close-range precision. Gates
temporarily compose attack/speed multipliers, then fatigue, preserving concurrent
level-up gains. Sand Shield absorbs a finite damage budget and locks on break.
Earth Wall intercepts hostile swept projectiles and repels ordinary enemies;
friendly shots and the player can pass, and no permanent map tile is changed.

Lotus launches ordinary targets and gives other nearby enemies a smaller landing
impact; bosses resist launch. Sand Coffin captures one target, then damages it
once. Tsukuyomi prioritizes one visible elite, with reduced boss control. Amaterasu
creates up to two finite black-flame circles, ticking once per half second for
three seconds. All effects use simulation time and are cleared on run changes.
`naruto-support.js` and `naruto-offense.js` extend the existing engine rather than
replacing core player, room-provider or transport code.

Run `python .omx/check_naruto_roster.py` for eight isolated kits, level gates,
healing, defense, buffs, single-target control, real AoE budgets, wall geometry,
expiry, cleanup and startup. Multiplayer adapter regression is checked with
`node tools/test_multiplayer.js`; replication of these custom techniques remains
a separate verification gap. Extended gameplay balance is still provisional.

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
