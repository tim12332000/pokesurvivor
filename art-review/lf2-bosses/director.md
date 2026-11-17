# Classic LF2 bosses — renewed full-kit independent review

Status: **FULL-KIT CANDIDATE READY for authorized commit/build/publication. No unresolved product blocker remains.** Public deployment, byte equality and fresh live desktop/mobile starts remain root's final release gate; publication is not claimed complete here.

## Corrected scope and withdrawal

The user rejected the earlier omission with 「技能都要放不要偷懶」. The previous four-taught-skill Julian candidate approval was explicitly withdrawn and is not used to certify the corrected scope. This renewed decision covers all original named abilities: **Firzen3 and Julian6**, each implemented with real behavior. A written omission is not an acceptance substitute.

| Character | Complete named kit and formal learning |
| --- | --- |
| Firzen30019 | Firzen CannonLv1, Overwhelming DisasterLv3, Arctic VolcanoLv6 |
| Julian30020 | Skull BlastLv1, Soul PunchLv2, UppercutLv3, Mirror ImageLv4, Soul BombLv5, Big BangLv8 |

Original classic LF2 2.0a sprites/dat/audio are retained. Automatic casting, progression, targeting, resistance and projected top-down geometry are documented adaptations. Original manual inputs/full Z-axis are not claimed. No named Julian ability is omitted; Mirror is neither an attacking clone nor a decorative substitute. Freeze and existing Firzen tuning are preserved.

## Current code and source review

Independently read the current six-skill registration/profile/HUD/guide, roster/art/preload/generator/build hooks, complete Julian runtime, native enemy/physical-hit consumers and original manifests/contracts. Source inventory/readme establishes3/6, and the separate authenticity lane independently verified all4,586,787 original in-cell pixels and current source hashes.

- Soul Punch is now a formal learned move with its own damage, CD, rank/count and HUD icon. Source300–305 has actual close contact during0–6/30, full14/30 body; it advances through3px collision-checked steps during the source forward window. Toward input gates casting, retreat stops continued approach/repeats, and ordinary60/65 fallback punches remain separate. It is no longer a hidden fallback counted as a full named skill.
- Mirror plays106→103→104→105, spawns original240 at2/30 and recovers by22/30. Source103 is truly invisible/empty-body for2/30–13/30; native projectile/contact and telegraphed attack-shape collision exemptions are limited to that window, without a blanket Player.hurt override or enemy-shot deletion. Terrain/status damage still applies. Any held input direction is honored; idle input chooses a safe away/side route, with swept wall/prop checks.
- The old-location ghost is stationary, non-damaging, intangible, owner/world/epoch/learned-move bound and uses original240–251 over59/30. Its HP10 only supports native alive-target semantics; it is not a projectile shield. Original striped fade and real body reappearance at the displaced location are visible. Rank benefits consume actual lure range, distance and ghost count; lifetime remains honestly fixed1.97s.
- Native Enemy.update chooses the ghost before direction/pursuit/aim and records the actual chosen proxy. Party membership, rewards, kill ownership and lag/recycling retain real players. Proxies inherit safe owner stats and zero attack/speed; expiry/unlearn/death/clear/world invalidation stops future attraction. Existing missiles are not globally redirected or absorbed.
- All six use actor-owned lifecycle boundaries; physical damage retains CombatPulse per-victim legality so a first-hit callback cannot damage a stale same-pulse second victim. Released projectiles/fields remain independent of the next body move.

Firzen's unchanged complete source identities remain validated: finite original-timed cannon stream, mother-before-child Disaster split, and compound Volcano center blast + six three-column groups + six ground fires + independent seekers. The previous narrow audio-signature, fire-contact timing, impact/flying-art, mother lift and selected-tile defects were fixed and are not open blockers.

## Independently read current verification

The corrected `julian-report.json` is ok=true/sourceStable=true/errors[], with **seven** groups including mirrorUtility and all six legal pool IDs. Current Firzen shared-hook regression is also stable/pass. Tests cover five real offenses, source timing, physical move/count growth, walls/props, pause/death/unlearn/world/epoch, same-wave clear/unlearn and clone ownership.

Mirror's actual native cases show21HP loss at0/.06/.45s and0 loss only at.10s inside103 for contact/projectiles/hazards. Status/terrain still causes11.76 damage and slow remains. Native chase chooses the ghost; actual ranged aim/projectile changes causally: same-scene no-Mirror loss21 versus with-Mirror loss0. The shot passes through the ghost, and a real body behind it still loses21HP. Expiry restores real target selection; wall-separated lure, all input directions, swept wall boundary and clone isolation pass. The initial paused-predicate fixture failure was corrected to query during playing state, without weakening runtime guards.

## Renewed natural full-six formation

Both corrected Julian runs start fresh Lv1/no permanent upgrades, use actual keyboard or touch and visible paid choices. New skills were chosen at2/3/4/5/8; no HP/XP/AI/time edits were used.

| Current run | Formation and real utility | Final |
| --- | --- | --- |
| Julian desktop keyboard |9 real picks; all6 learned; all5 offensive IDs caused main-player HP loss;7 Mirror casts,31 real native enemy target diversions; full Big Bang closure |100.27game seconds, Lv10,268.63/280HP |
| Julian390 actual touch |9 real picks; all6 learned; all5 offensive IDs hit;5 Mirror casts,25 diversions and actual native ranged-aim events; full signature closure |114.41seconds, Lv10,197.42/280HP |

Both reports are ok=true/sourceStable=true/errors[], `allSkillsLearned:true`, `mirrorUseful:true`, `fullSignatureClosed:true`. Utility is judged by real displacement/targeting, not nonexistent Mirror damage. Actual six-icon HUD rectangles fit inside390px; the new learning strip is an intelligible3×2 layout. No old four-skill natural run is presented as the corrected six-skill proof.

Retained Firzen evidence remains valid for its unchanged complete kit: desktop87.84seconds/Lv8 with7 real picks and mobile touch99.86seconds/Lv6 with5 picks, all3 damage and full signature closure. The old desktop's visual-only emitter-lift drift is preserved/documented and bridged by stable mobile/current native proof; it is not falsely labelled byte-identical.

## Independent current visual/native review

Independently viewed the new mobile six-learning-strip and all-six in-game HUD; formal source300 release/recovery; actual natural Mirror103 absence, two separated original bodies, stationary ghost and striped fade. Source103 remains invisible during hurt flashes, while death retains priority. Camera/feet/body/ghost anchors are coherent; routes and controls remain readable.

Independently decoded actual frames47.5/50s from the65.92s corrected touch natural movie, and8/12/17s from the new25.28s six-skill native-cycle movie. The latter is explicitly a controlledLv30/rank1 native-RAF showcase, with all five offensive HP hits, all six formal casts and actual Mirror diversion; it is not labelled natural growth. Current final-cycle report is ok=true/sourceStable=true/errors[], and independently recomputed current runtime/asset hashes match sourceAfter with zero drift (generated entry query-only refresh is documented separately).

Separate art review renewed PASS94 for the **complete six-skill** candidate (`visual-verdict.json`, `art-review.md`), and independent source/authenticity renewed PASS for Firzen3/Julian6 (`authenticity-verdict.json`, `reference.md`). Their older four-skill approvals remain withdrawn. No human sound-listening or subjective fun claim is inferred from original WAV provenance, tests or scores.

## Release gate and limits

Root may now commit/build/publish this corrected complete candidate under the existing authorization. It must still verify the actual live files, all six registered definitions and normal public desktop/mobile starts against the canonical artifact before claiming publication complete. Push/queued is not proof. Stop adding mechanics or broadening QA absent a new concrete defect.

Physical-phone endurance, multiplayer,30-minute performance and human fun/audio listening remain explicitly unverified; none was used to excuse an omitted named ability.
