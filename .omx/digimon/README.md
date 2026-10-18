# Local Digimon Adventure crossover prototype

Open `http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW`.

From the repository root, run `python -m http.server 8002 --bind 127.0.0.1`,
then open that URL. No build or package installation is needed to play.
Browser checks require Python Playwright and an installed Google Chrome.
Use port 8001 for `check_unlimited.py`; the Digimon checks use port 8002.
This variant is maintained on `feat/digimon-sandbox`, separately from the
Traditional Chinese translation pull request.

## Personal website

The personal GitHub Pages site is https://tim12332000.github.io/pokesurvivor/ .
The `digimon-pages.yml` workflow deploys only `feat/digimon-sandbox` on this fork.
`python tools/build_digimon_site.py` builds `dist-digimon/` from tracked runtime
files, omitting local state, development tools and the upstream custom domain.
The sandbox host restriction allows localhost and this specific Pages site.
Public saves remain browser-local and do not connect to original game accounts.

Includes eight Adventure evolution lines (33 forms) after generation nine in collection
and gacha tabs, a staged partner picker, local-only isolated saves, and unlimited
coins and both gacha-ticket types. The normal game and translation PR are unchanged.

Character identities, partner pairings and original English move names reference
Toei's official LAST EVOLUTION KIZUNA character page:
https://www.toei-anim.co.jp/movie/digimon-adventure/last-evolution/eng/character/inc/chara03.php

The game now uses DS-era pixel walk sheets, downloaded unchanged from the pinned
public DigiGame mirror recorded in `pixel-manifest.json`. That manifest records
source URLs, SHA256 hashes and upstream provenance. The source sheets contain
four diagonal directions and three frames per direction. Rendering uses nearest
neighbor scaling and original pixel frames, without smoothing or AI redrawing.

The former full-size Toei portraits are no longer drawn or shipped in this variant.
Chinese names use common Taiwan
translations and are not a comprehensive official terminology audit. Artwork and
Digimon trademarks remain the property of their respective rights holders.
This is an unpublished local fan prototype, not official content or a new artwork license.

Combat now uses dedicated signature-skill definitions and a local combat extension,
while sharing the game's collision, damage and pixel-effect infrastructure.
The original four-way walking frames are reused for the nearest cardinal direction.
This is not a full eight-direction sprite animation set. No external account or
cloud service is initialized.

## Signature skills

All 33 forms have a distinct signature profile, with five additional learnable
skills, for 38 skills total. The picker includes a skill guide with gameplay
descriptions and clickable official references for every form. See
[SKILL_SOURCES.md](SKILL_SOURCES.md) and `skills-reference.json` for the source audit.

Examples include Gomamon's homing fish, MetalGreymon's explosive missiles,
WarGreymon's charged Terra Force, Gatomon's staggered claw combo, MagnaAngemon's
pulling portal, Seraphimon's seven holy spheres and Omnimon's sword/cannon combo.
Garurumon's blue flame remains fire, rather than an ice attack. Delayed casts
snapshot their skill data so evolution cannot change an attack already charging.

Official sources establish attack identities and documented characteristics.
Damage, cooldown, homing, status effects, upgrade levels and portal boss resistance
are local survival-game adaptations. Ophanimon's referenced page establishes skill
names without attack mechanics; its javelin behavior is explicitly an adaptation.
Chinese labels use common translations rather than a complete official-name audit.
The learning pool includes the current form and its ancestors, plus unlocked
secondary skills. Ordinary Pokemon retain their original move pools and combat.

Verify using `python .omx/check_digimon_skills.py` and
`python .omx/check_digimon_evolution.py`.

## Evolution controls

The picker has Initial Partners, Champion, Ultimate, Mega and Fusion tabs. The
local unlimited-resource edition lets you select any form directly.

Automatic evolution is enabled by default: level 5 → Champion, 10 → Ultimate,
15 → Mega. Gatomon already starts at Champion, so its next threshold is level 10.
Disable the checkbox in the picker to use the in-run evolution button instead;
the button requires the same levels. WarGreymon and MetalGarurumon can evolve to
Omnimon at level 20 when both mega forms are in the collection. These thresholds,
combat values and fusion-collection rules are local gameplay choices.

- Agumon → Greymon → MetalGreymon → WarGreymon
- Gabumon → Garurumon → WereGarurumon → MetalGarurumon
- Biyomon → Birdramon → Garudamon → Phoenixmon
- Tentomon → Kabuterimon → MegaKabuterimon (red) → HerculesKabuterimon
- Palmon → Togemon → Lillymon → Rosemon
- Gomamon → Ikkakumon → Zudomon → Vikemon
- Patamon → Angemon → MagnaAngemon → Seraphimon
- Gatomon → Angewomon → Magnadramon; Ophanimon is an optional game branch.

The forms follow the familiar Adventure partner lines, referenced against Toei's
[Adventure character page](https://www.toei-anim.co.jp/tv/digimon/character/) and
[tri. evolution pages](https://www.toei-anim.co.jp/movie/digimon-adventure/tri/evolution/).
This is not an exhaustive roster of every franchise timeline, dark evolution,
armor form, X variant or movie-only transformation.

Evolution preserves position, HP ratio, learned move groups, equipment, run stat
bonuses and the permanent upgrades of the original partner line. The signature
move changes with the form. Evolved partner choice, preferences and history use
the existing isolated `ps.sandbox.digimon.v1` save key; old base-form saves remain
valid and are not copied into normal or cloud saves.

The 25 added source PNG/metadata pairs and hashes are recorded in
`evolution-pixel-manifest.json`. Greymon's source has nine irregular frames and
no source direction metadata: its local JSON records only inferred alpha bounds;
the renderer's front/rear grouping was visually reviewed using
`.omx/greymon-source-preview.png`, with right views mirrored. Other evolution
forms retain their supplied four-direction metadata unchanged.

Regenerate the entry after source changes using `python .omx/make_digimon.py`.

## Visual size

The extra world-size multipliers are initial partner ×1, Champion ×1, Ultimate ×1.3,
Mega ×1.45 and Fusion ×1.6, in addition to each source sprite's native dimensions.
The source evolved sprites are already larger, so these extra multipliers are restrained.
Initial Gatomon retains its small original appearance. These are presentation
choices, not official height measurements. Shadows and damage-label height follow
the visual scale; collision radius keeps its existing size for map traversal.
Previews retain a smaller-to-larger progression while fitting their canvases.
The camera makes room above large actors and zooms out when needed on mobile.
