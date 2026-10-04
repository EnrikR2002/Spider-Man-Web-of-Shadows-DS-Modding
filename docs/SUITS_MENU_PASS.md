# Menu readability and suit palette prototypes

Evidence date: 2026-10-03. Private CS5E only. Original ROM, regular mods,
and user battery saves are untouched. Generated assets remain in ignored build/.

## Implemented

- 35 English/American text IDs: shorter ability instructions, explicit suit
  requirements, compact combo sequences, simpler collectible descriptions,
  and Default category renamed Core. Existing button/D-pad glyph codes retained.
- Black-suit texture: negative weighted luminance palette, white/gray body with
  dark eyes/emblem. Anti-Venom-inspired cosmetic prototype, not new abilities.
- Red-suit texture: richer red, deeper blue and gold-tinted light colors/lenses.
  Movie-inspired palette prototype only: original panel shapes, emblem and mesh
  remain unchanged. A faithful first-movie redesign requires UV/model inspection
  and deliberate texture painting. This pass does not claim that result.
- Existing yellow mission-marker recipe included in the combined build.

No costs, combat, unlocks, counts, saves, or executable bytes changed. Labels
still say Red/Black so unchanged tutorials and requirements remain consistent.
Hidden question marks were not located as normal decoded text entries. Do not
claim hidden-item reveal, numeric stats, damage numbers, or an options toggle.

## Reproduce (PowerShell)

```powershell
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\qol_suits_menu.py'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' build --mods 'build/qol-suits-menu/mods' -o 'build/qol-suits-menu/Spider-Man-WoS-qol-suits-menu.nds'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' verify --mods 'build/qol-suits-menu/mods' -o 'build/qol-suits-menu/Spider-Man-WoS-qol-suits-menu.nds'
```

`--inspect` emits the private 1,049-entry text inventory without generating overlays.
The recipe records exact edited IDs/text and hashes. Existing different overlays
are refused. Reverting means opening the clean build or rebuilding an empty isolated
overlay, not deleting other mods. Earlier builds are unchanged.

## Validation and manual acceptance

40 tests pass. All 1,049 clean texts decode and independently re-encode into their
original slots, then decode identically. No-op replacement is byte-exact. Edited
slots retain bounds/tail bytes and cannot exceed their original allocation.
Palette edits preserve pixels, dictionaries, headers, lengths and bit 15.
Both language assets are identical in the clean ROM; both receive matching edits.

The final five-asset build verified all 3,733 resources and completed a
1,800-frame melonDS boot capture. This does not validate the Powers menu or black
suit display. Final ROM SHA256:
`9fbbe8c27a935c23ada0318d07fe39b5ef0472cde0c8af3ce9b72dafa936eb87`.
The preliminary gameplay capture visibly shows the edited red-suit colors.

Cold-boot the combined ROM, using a backed-up/copied battery save if desired;
never use an old emulator state. Inspect every changed Powers page for wrapping,
missing glyphs or clipping. Check combos against original instructions. Switch
suits and inspect movement, walls, shadows and effects. Capture front/back poses
for UV work. Black-suit runtime and faithful movie suit remain unverified.
Do not overwrite a live emulator save. See TESTING_WORKFLOW.md for transfer.

Next meaningful features: locate runtime hidden-label selection; map purchase
status and cost rendering; confirm numeric health/damage before adding stats;
map options input and save semantics before adding a persistent damage toggle.