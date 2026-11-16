# Freeze acceptance evidence

The acceptance harness is `tools/test_lf2_freeze.py`. Each top-level JSON records before/after SHA-256 snapshots of the combat, registration, renderer, entry, enemy integration, and every LF2 runtime asset. The reports distinguish controlled fixtures from native progression.

| Evidence | Result and scope |
| --- | --- |
| `report.json` | All five controlled suites pass; no page errors; sources stable. Real delayed projectile flight, walls, exact advertised reach, three in/one out targets, independent cyclone contacts, all four no-enemy destructible interactions, true frozen AI/contact suppression, original sword active-window timing, persistent summoned blade, unarmed non-freezing punches, actual giant-card reach, pool/level ownership, lifecycle and same-wave callback cancellation, independent clone attribution/death. |
| `natural-desktop/report.json` and `natural-report.json` | Fresh save, zero permanent upgrades, real keyboard and visible card/item UI only. Native Lv1 to Lv9; all four specials actually damage main-player targets. First complete set at game time86.50; continued through93.21 with first cyclone fully expired and subsequent normal attacks. Alive232.14/240HP. Original card ledger and native video retained. |
| `natural-mobile390/report.json` and `natural-mobile-report.json` | Fresh save, zero permanent upgrades, actual native joystick touchStart/move/end events and visible card/item UI only. Native Lv1 to Lv9; all four actual main-player damage sources, first complete set90.34, continued through95.74 after cyclone expiry. Alive217.31/240HP. `inputs[].input` is `touch`. Sources stable during this run. |
| `blade-current-source.json` and `blade-current/` | Stable-source seven-second controlled native RAF clip of original sword contact/recovery. Active left/right screenshots at action age0.1334, no player damage flash, visible source blade attached at the hand; not natural progression. |
| `final-cycles-source.json` and `final-cycles/` | Stable final-source controlled native RAF playback after transparent sprite-gutter correction. All four skills, original body phases, a freely flying iceball, three rising columns, persistent blade, independent whirlwind and full fade. No manual combat-clock stepping; not natural progression. |

## Source differences

The desktop natural run bracketed a change only to `.omx/lf2-art.js`: original sword animation-frame selection was corrected while the run was recording. Its combat source stayed exactly SHA-256 `18bcfcc59722fda02b44972cee4b01199e3eac6e39edce418297844d2c0b87c1`. The desktop footage therefore establishes legal native growth and the full combat loop, not byte-identical final renderer visuals. The final sword clip and final all-special clip supply current visual evidence.

The mobile natural run was source-stable. After both natural runs, opaque one-pixel dividers outside the original LF2 sprite cells were made transparent to prevent GPU green-edge bleed; the original sprite-cell pixels and combat remained intact. Those earlier natural videos are not labeled as final PNG-byte evidence. `final-cycles-source.json` records the corrected PNG/manifest hashes, and its new native images show the current result.

`first-contact-report.json` and `first-contact.webm` under each natural folder preserve the earlier checkpoint that stopped when the fourth special first hit. They are historical checkpoints; the unsuffixed final natural files include complete cyclone wind-down.

## Limits

The mobile test uses a 390×844 browser viewport and real browser touch events, not physical-phone long play. Native videos were recorded by Playwright; this evidence does not claim audio listening acceptance or a human judgment of fun. Controlled rank/level/terrain/target fixtures are explicitly separate from natural runs; no HP, XP, AI, permanent-upgrade or combat-clock changes were used in the natural runs. The default visible game speed was retained.
