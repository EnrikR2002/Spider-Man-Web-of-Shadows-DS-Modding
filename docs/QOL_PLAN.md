# Vanilla-plus QoL plan and first experiment

Historical first experiment. The current mission marker is red per player request;
current instruction improvements are documented in [QOL_CLARITY.md](QOL_CLARITY.md).

Updated 2026-10-03. Keep combat balance, progression, saves, and room logic unchanged
in the initial readability pass. All extracted assets, previews, builds, and emulator
captures remain private/ignored. No original ROM or regular overlay is overwritten.

## First experiment: mission marker contrast

Status: **yellow mission marker visible in user gameplay screenshot; animation,
clean comparison, and save/reload still need checking**.

User evidence: a supplied DeSmuME 0.9.13 screenshot shows Residential gameplay
with a yellow exclamation-style map marker and dark edge. Nearby blue S icons
retain their expected appearance. This matches the intended palette edit; it is
not a paired clean/modded comparison or proof of every palette user. The user
reports saving at a save spot. No screenshot file was copied into the repository.

Local follow-up found DeSmuME running and the recent-ROM configuration naming
the mission-icon test ROM. Its corresponding battery file at
`F:\Enrik Desktop Files\PROJECTS\DsSmuMe\Battery\Spider-Man-WoS-qol-mission-icon.dsv`
was zero bytes during inspection. Do not treat this as a usable backup or proof of
lost progress. Close DeSmuME normally after saving, recheck the file, back it up
only once nonempty, then reopen the same ROM and verify Continue loads the checkpoint.
If it stays empty, investigate save output/export before rebuilding or transferring
progress. A later check in the same inspection found the file had grown to 634
bytes while DeSmuME was still running. This establishes nonempty disk output, not
a valid checkpoint or reload. Wait for normal emulator closure before backup.
No real save was copied, overwritten, or restored during this inspection.

### What to look for, and when to stop playing

Use your existing normal in-game save; a new playthrough is not required. Play
only until a mission/objective marker appears on the map. Its exact first room or
story trigger has NOT been identified, so no specific boss or playtime is promised.
The intended change is yellow marker fill with the existing black edge. Spider-Man,
save-point icons, combat, and progression should remain unchanged.

Capture a screenshot when the marker appears. Check its color, edge, animation,
and neighboring icons, and whether it is easier to spot. No visible marker means
the relevant display has not been tested, not that the edit failed. A marker that
stays red is useful evidence: capture it rather than changing more palettes blindly.
Use equivalent progress for clean/edited comparisons, with copied battery saves
and fresh ROM boots, not old emulator save states. See the simple save/build loop
and backup helper in `TESTING_WORKFLOW.md`.

The bounded tool accepts only the two hash-identified clean minimap families.
Its tiled preview yields a coherent player face and mission marker sheet. General
DAT semantics and palette ownership are not decoded. The edit changes one used
MissionMiniMapIcon.pal entry from red to yellow while keeping the black edge,
pixel bytes, metadata, palette size, and every other entry unchanged. Yellow is a
candidate for readability, not a proven accessibility improvement. Palette edits
cannot add shape distinctions; do not claim color-blind accessibility from this alone.

### Reproduce from Windows PowerShell

All commands use absolute paths. Inspection loads the validated original directly;
no full extraction or third-party Python package is required.

```powershell
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\qol_minimap.py' inspect
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\qol_minimap.py' experiment
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' build --mods 'build/qol-mission-icon/mods' -o 'build/qol-mission-icon/Spider-Man-WoS-qol-mission-icon.nds'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' verify --mods 'build/qol-mission-icon/mods' -o 'build/qol-mission-icon/Spider-Man-WoS-qol-mission-icon.nds'
Push-Location 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding'
try { python -m unittest discover -s tests -v } finally { Pop-Location }
```

Output directory: `F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\build\qol-mission-icon\`.
It contains the isolated `mods\` overlay, clean/edited previews, inspection metadata,
ROM, Glob, and build report. `inspect` writes previews/report only, never an overlay.
`experiment` refuses unexpected clean profiles or additional assets in its overlay.

### Revert

```powershell
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\qol_minimap.py' revert
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' build --mods 'build/qol-mission-icon/mods' -o 'build/qol-mission-icon/Spider-Man-WoS-qol-reverted.nds'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' verify --mods 'build/qol-mission-icon/mods' -o 'build/qol-mission-icon/Spider-Man-WoS-qol-reverted.nds'
```

Revert removes only a recognized experiment/clean palette, refuses a different
edit, and does not alter previously built ROMs. Regenerate with `experiment` later.
An empty isolated overlay must reproduce clean SHA256
`61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`.

### Tests and acceptance

- 29 tests passed: 23 existing plus six minimap tests, including real-ROM confinement
  and exact revert. Build verifies all 3,733 resources; only the 32-byte mission palette
  differs, at offsets 2 and 3 within that resource.
- Edited ROM SHA256: `8932a811aa934bb683d2266e22e6c225f8c8da0380c2a4243712ca220b7a80ca`.
- Clean and edited 1,800-frame melonDS DS 1.1.5 captures match at frames
  299, 599, 899, 1199, 1499, and 1799. The last shows Residential gameplay but no
  mission marker. This is a boot smoke check, not proof that the visible edit works.
- Baseline captures: `F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\build\boot-tests\Spider-Man-WoS-unmodified-61a6ed6e\`.
- Edited captures: `F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\build\boot-tests\Spider-Man-WoS-qol-mission-icon-8932a811\`.
- Before promotion: back up the battery save; cold-boot each ROM with equivalent
  progress; reach an actual mission-marker display; capture both; confirm yellow fill,
  unchanged black edge, blinking/animation, and unchanged neighboring icons. Test
  different map backgrounds and check for unintended shared-palette effects.
- Retain only if it is measurably easier to read. If no change appears, investigate
  the runtime asset/palette binding rather than blindly modifying more entries.

## Optional stats and damage numbers — research backlog

Follow-up: user supplied seven pause/Powers & Stats screenshots. They establish
ability descriptions, Red/Black/Both/Default categories, hidden question marks,
XP 21, and collectible counters (health 1/16, life 1/4), not numeric health/damage.
Implemented first menu readability and suit palette prototypes; see
`SUITS_MENU_PASS.md`. Damage numbers/toggle and hidden-label reveal remain research.

Next order: verify/save-backup the new gameplay checkpoint after closing DeSmuME,
check Continue and marker animation, then inspect the existing stats/upgrade screen
using this progress. The screenshot already establishes a visible yellow marker;
avoid another arbitrary color edit unless screenshots reveal a concrete problem.
Stats/menu mapping can proceed as research while the remaining marker checks are
pending; runtime damage numbers still require engine evidence.
The backup helper is implemented; the remaining items are investigation milestones,
not available gameplay features.

Requested final behavior: an in-game toggle, off by default, with no balance change.
Separate test builds are acceptable for prototyping, not a replacement for the toggle.

1. Observe the existing stats screen first. PauseStats.xbd (1,564 bytes),
   PauseStatsTop.xbd (124 bytes), Options.xbd, and PauseOptions.xbd are name-based
   leads only; they do not establish numeric stat fields or setting semantics.
2. Locate and confirm actual applied damage, enemy identity/position, and blocked-hit
   behavior through controlled runtime captures. Do not label unknown XBD/GAB words
   as damage or infer per-hit damage from a health delta with overlapping effects.
3. Prove one hit can display accurately without changing combat. Then bound label
   count/lifetime and check multi-hit attacks, simultaneous targets, poison, bosses,
   positioning, clipping, and performance. Existing text/font drawing is a lead,
   not yet an available overlay API.
4. Add the real menu toggle only after UI/input semantics are mapped; persist it only
   after save-format/checksum behavior is confirmed. Never reuse audio/language flags.
5. Off must bypass label generation/rendering and preserve the original HUD. No
   ARM9, save, or damage-system patch is included in the mission-marker experiment.