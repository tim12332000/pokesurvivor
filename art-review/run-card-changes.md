# Run selection card changes

- Removed the `hp` (活力) and `rgn` (光合作用) cards from the global level-up selection pool. Base character health, regeneration, permanent upgrades and legacy HUD history remain unchanged.
- Renamed `heal` to 軍糧丸 and gave it a distinct 12×12 pixel ration-pill icon. The existing berry icon remains available elsewhere. It still restores 45% of maximum HP.
- Renamed `giant` to 倍化之術 in its card and run HUD. Its multiplicative size, collision, maximum health, speed and attack interval effects remain unchanged.
- Added an optional card eligibility predicate and the 忍具連彈 count label for the separately implemented bounce card.
- Root handles old Pokémon evolution dependencies: removed health and regeneration requirements accept 生命成長 and 吸血 respectively, while retaining old pick histories.

Validation: `python tools/test_run_card_changes.py` uses the real game, selection UI and player methods at desktop 1200×900 and mobile 390×844. It checks removed cards cannot be offered, renamed titles and distinct icon, native 45% recovery, all size-card multipliers, HUD text, optional eligibility and actual clicking. No page errors or horizontal overflow were observed. Node syntax checks passed for the four runtime files.

Evidence: `.omx/state/run-card-changes/report.json`, desktop/mobile `selection.png` screenshots and `ralph-progress.json`. The brown pill cluster follows the existing indexed-palette icon grid without introducing assets or dependencies. No remaining card-specific risk identified; release and broader bounce integration validation are owned by root.
