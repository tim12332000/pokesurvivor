# Digimon signature move source notes

## Method

`skills-reference.json` maps all 33 local forms to official signature move names, source URLs, localization aliases where confirmed, and short paraphrases of source-supported mechanics. Names from different languages are aliases only when they identify the same move. Distinct attacks stay separate. The `zh_common_name` values are this game's existing Traditional Chinese labels; they are not presented as official Chinese names.

Primary sources:

- [Digimon Encyclopedia (English)](https://digimon.net/reference_en/) — Bandai's official encyclopedia, with Bandai and Akiyoshi Hongo/Toei credits. Individual entries use `https://digimon.net/reference_en/detail.php?directory_name={slug}`.
- [Toei Digimon Adventure character page](https://www.toei-anim.co.jp/tv/digimon/character/) — official Japanese source fetched and checked locally. It provides primary text for the classic Adventure forms, including Greymon, MetalGreymon, WereGarurumon, HerculesKabuterimon, Seraphimon, and Magnadramon.

The English Encyclopedia notes it is machine translated and names can vary by language. Where it lists a move but does not explain it, the JSON keeps the move name as `official_verified` and sets `mechanism` to null with `mechanism_confidence: unresolved`. No gameplay values such as damage, cooldown, range, area, or status effects are treated as canon.

## Variant and naming notes

- Greymon and MetalGreymon are the classic Adventure Vaccine forms. The English Encyclopedia's generic `greymon` and `metalgreymon` slugs resolve to 2010/Xros Wars Virus variants, so these two records cite Toei instead. Toei describes Mega Flame as superheated breath and Giga Destroyer as organic missiles fired from a chest hatch. The classic MetalGreymon also lists Trident Arm, but Toei gives no mechanism for it.
- `atlurkabuterimon` is specifically **MegaKabuterimon (Red)**, Vaccine. Its official move Horn Buster stabs the target with its giant horn; no projectile or beam is described.
- WereGarurumon's official English slug did not resolve to a profile, so its Kaiser Nail entry cites Toei's Japanese page, which describes it as a slash from the sharp claws on both arms.
- HerculesKabuterimon's English Encyclopedia slug did not resolve to a profile. Toei verifies Giga Blaster as an enhanced Mega Blaster and describes it as obliterating targets it hits.
- Biyomon uses the Encyclopedia slug `piyomon`. The English entry calls its move Spiral Twister; the Japanese profile calls the same move Magical Fire and the English profile describes spectral flames.
- Gatomon's Lightning Paw and Cat's Eye are separate attacks. Cat's Eye manipulates a target into attacking itself.
- Angewomon's Celestial Arrow (also called Heaven's Punishment) and Heaven's Charm are separate moves: a lightning attack versus a beam of beauty and kindness. Rosemon likewise has three separate moves: Thorn Whip, Roses Rapier, and Forbidden Temptation, each with a different described effect.
- WarGreymon's Gaia Force (Terra Force) and Brave Tornado (Great Tornado) are same-move localization pairs. Seraphimon's Seven Heavens (Strike of the Seven Stars) is one move; Testament is separate. Magnadramon's Holy Flame (Fire Tornado) is one move across Toei and English encyclopedia labels.
- Omnimon's official Encyclopedia labels are Transcendent Sword and Supreme Cannon; Grey Sword and Garuru Cannon are localization labels for those same attacks. MagnaAngemon's Heaven's Gate is its listed special move; Excalibur is a sword it carries, not a synonym for the gate attack.
- Garurumon's Fox Fire is a stream of blue flame, not an ice breath. Lillymon's Flower Cannon uses the flowers on its wrists as cannon mouths. Vikemon's Arctic Blizzard drops the surrounding air to absolute zero, then shatters the frozen target with Mjölnir.

## Coverage

All 33 forms have a source-backed attack name. Distinct attacks are represented as separate entries, including secondary signature moves when the official profile lists them. Attack mechanics remain null when official sources only provide a name; all numerical combat balance and additional effects are game design decisions.
