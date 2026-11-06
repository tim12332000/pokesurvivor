# Uro orbit release

Live: https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=uro&release=f3c3edd7

- Source: `f3c3edd77668d707754c1c675660bd8ff4cb9f4e`.
- Static publication: `c43a6b31cf5860d195c0e694623b824608037092`.
- Existing Pages source preserved: `codex/ryu-ring-topdown-48a22f71`, legacy, `/`; HTTPS retained, no CNAME.
- Public tree changes only `.omx/jjk-uro.js`, `.omx/jujutsu.js`, and generated `.omx/digimon.html` asset hashes. No dependencies added.

Captured bullets now remain in actor-owned sky space for a full 0.8 second revolution. A bright head and short trail show direction while moving with Uro. The completed orbit launches one real projectile toward the surviving shooter; invalid shooters fall back to a nearby enemy or the reversed incoming direction. Captured shots survive screen exhaustion but cancel with owner/skill/run invalidation. This replaces immediate reflection without adding a separate timer system or changing the existing first-intercept counter.

Independent combat and visual reviews passed. Orbit, fracture, deflect, and sky-space VFX checks passed; the VFX harness required its existing test query for reliable boot. Nine standard Node checks passed both before submission and in a canonical source worktree. Syntax and diff whitespace checks passed.

Public verification: all nine selected files matched canonical artifact SHA256. A real browser opened the public normal menu at desktop 1280 and mobile 360/390, started Lv1 Uro, then applied legal level-up cards to learn sky screen at Lv6. Every viewport produced a full `6.283185307179586` radian orbit lasting 0.8 seconds and exactly one friendly returned projectile. No page errors, failed HTTP loads, or horizontal overflow. These controlled levels are not a full natural-XP playthrough.

Evidence: `public-assets.json`, `public-browser.json`, `combat-review.md`, and `visual/visual-review.md`. Raw captures and recordings remain local under this review directory and `.omx/state/uro-orbit/`.

Not tested: physical mobile long sessions, audio, and subjective player preference.
