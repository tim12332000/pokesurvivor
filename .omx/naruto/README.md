# Naruto crossover section

Generation 11 follows Digimon in collection and gacha. The Naruto button appears
in the top navigation and in the first-time Digimon picker. Eight characters are
available: Naruto, Sasuke, Sakura, Kakashi, Hinata, Rock Lee, Gaara and Itachi.
Choosing a ninja uses the existing sandbox save without resetting the collection.
Naruto characters do not use the Digimon evolution system.

Ten adapted skills include eight character signatures and two shared ninja tools.
The in-game skill guide links each character to official Naruto source articles.
Attack names and character identities are source-based; damage, ranges, cooldowns,
type mappings and crowd-control effects are survival-game design choices. In
particular, Lightning Blade's ranged beam and Sand Coffin's slowing sand projectile
are gameplay adaptations rather than literal reproductions of the manga.

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
Set `PAGES_LIVE=1` to check the deployed site instead. Tests require Python
Playwright and the installed Windows Chrome, matching the other sandbox checks.

Deployment remains https://tim12332000.github.io/pokesurvivor/ and uses only the
personal `feat/digimon-sandbox` branch. No upstream PR is created or changed.
