# Mod and reverse-engineering test workflow

This is the repeatable private workflow for testing changes without modifying the
clean ROM or losing emulator progress.

## The simple version: rebuilding does not erase your progress

**Fresh boot means reopen the ROM, then choose Continue. It does not mean New Game.**

- The `.nds` file is the game program/assets. We rebuild this file.
- Your normal in-game save is a separate battery-save file. We do not rebuild it.
- An emulator save state is a snapshot of the running machine. Avoid old states
  when checking a new build: they can restore old assets and memory.

The everyday loop is:

**Save inside the game -> close emulator -> back up save -> build and verify ->
reopen ROM -> Continue -> test one change.**

The user delegates backup/build/checkpoint operations to the agent. On this
machine, their only steps are **double-click Play Spider-Man.cmd -> Continue ->
play -> save in-game -> close DeSmuME**. The agent-facing commands below explain
maintenance and setup; the player does not need to run them.

Keep one stable ROM filename/path for everyday testing. Use separate experiment
ROMs for isolated comparisons. A renamed ROM may be associated with a different
save by your emulator; check its configured save location. If Continue disappears,
do not start a new game over your progress: first check which save is being used.
Copy progress between builds using the same emulator/save format, or the emulator's
supported import/export procedure. Never convert a save just by renaming its suffix.
The helper below copies bytes only and does not guess save locations.

Asset-only edits are expected to preserve progress, but broader progression/engine
changes may require special compatibility tests or disposable saves. Back up first.
The automated harness can load an isolated battery copy with `--save`; it never
writes back to that file. Fresh-game captures do not require restarting progress.

### Current release workflow: TASM 1 Rebound

`playtest.py build` validates the current DSV wrapper, snapshots it, builds to a
candidate path, rechecks that DeSmuME is closed and the save is unchanged, retains
the previous stable ROM by SHA256 in `build/releases/`, then atomically publishes
the same everyday ROM. `launch` checks the ROM/save and makes a pre-play snapshot.
The process check is not a lock: keep the emulator closed throughout publication.

The configured executable is the actual DeSmuME 0.9.13 installation; local paths
stay in ignored `work/playtest.json`. On another machine add `--emulator FULL_EXE`
to configuration. `Play Spider-Man.cmd` changes into its own project directory.

Current named checkpoints: `before-suit-cleanup`, `before-tasm1`, and
`opening-save-room`, plus the latest `before-rebound`. Ask the agent to return to a named point; restoration retains
displaced progress first. More points become available as real in-game saves are
recorded. No arbitrary room warping or save-field editing is implemented.

The adopted progress successfully resumed in the early Residential save room in
melonDS DS using a read-only payload copy. Native DeSmuME Continue remains the
player's final acceptance check. The current nine-asset regular overlay includes
Snap Sweep and purchased Rebound, plus two bounded ARM9 impulse data edits.
The exact recipe is `reference/gameplay_profile.json`; missing or changed required
overlays block a build rather than silently dropping part of the move. See
`TASM1_REBOUND.md`. Earlier six/seven-asset and 47/55-test statements are historical;
the current full suite passes 76 tests. Original Web Kick ownership carries over
through native saving; refund relocks Rebound. The live battery is never edited.

### Where features live

Every build starts from **clean original + selected overlay**, not the last modded
ROM. An isolated experiment contains just its own edits. Accepted features must
be deliberately combined into the regular overlay to appear together. If two
features edit the same asset, their edits need merging; copying one over the other
would lose a feature. Preserve the clean ROM, test one change, validate, observe,
then promote or revert. Replacing a built ROM does not replace its separate save.

## Save backup/restore helper

`F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\save_backups.py`
copies opaque `.sav` or `.dsv` files. **Save in-game and close the emulator first.**
It does not inspect slots, edit progress, convert formats, or know your emulator's
save folder. Give it the actual absolute save path. Do not select a save state.

Snapshots are private under
`F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\work\save-backups\`.
Each has exact save bytes and a size/SHA256 metadata record. Named snapshots are
immutable: use another name for a new checkpoint. Restore validates the snapshot;
before replacing an existing different save, it preserves that file in a verified
`before-restore-<format>-<SHA256>` snapshot. Corrupt snapshots, cross-format restores,
ROM files, and writes into the protected original folder are rejected.

Example: locate your save, then supply its path when prompted (no guessed filename):

```powershell
$SaveFile = Read-Host 'Paste the full path of your CLOSED emulator battery save (.sav or .dsv)'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\save_backups.py' backup "$SaveFile" before-marker-test
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\save_backups.py' list
# Only when you want to return to that checkpoint, with emulator closed:
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\save_backups.py' restore before-marker-test "$SaveFile"
```

To associate a copy with another ROM in the SAME save format, restore to the exact
save filename/path that your emulator expects for that ROM. The helper permits a
new filename with the same suffix and retains the source snapshot. It refuses
`.dsv` -> `.sav` or `.sav` -> `.dsv`; use supported emulator conversion instead.
No actual gameplay save has been located or transferred by this implementation.
Emulator-specific path/import instructions require confirming your setup first.

### Confirmed local DeSmuME setup for this experiment

The user's screenshot identifies DeSmuME 0.9.13. Local inspection found the running
executable at `F:\Enrik Desktop Files\PROJECTS\DsSmuMe\DeSmuME_0.9.13_x64.exe`
and the mission-icon save at
`F:\Enrik Desktop Files\PROJECTS\DsSmuMe\Battery\Spider-Man-WoS-qol-mission-icon.dsv`.
It was zero bytes while the emulator was running despite a reported in-game save.
Do not back up that empty file or assume it contains progress. Close the emulator
normally after saving, verify that this file is nonempty, back it up, and reopen
the SAME ROM to check Continue. If it stays empty, stop and investigate output
paths/export; do not replace it with an older save or rebuild over an uncertain
checkpoint. A subsequent check found this file had grown to 634 bytes while
DeSmuME was still running. Wait for normal closure, then back up and test Continue.
This documents observations, not a confirmed emulator flushing rule or save validity.
The 2026-10-04 migration below subsequently preserved the nonempty files while
DeSmuME was closed; the earlier warning is historical evidence.

Keep an additional copy on another drive for important progress. Local snapshots
are not protection against disk loss. The emulator must stay closed throughout
restore: this tool cannot lock it out or stop it from overwriting a restored file.

## Stable playtest command — 2026-10-04

Use **one everyday filename**, `build/Spider-Man-WoS-modded.nds`. You may retain
isolated experiment ROMs for comparison, but normal accepted features go into
`mods/` and every daily rebuild replaces this same ROM atomically.

`tools/playtest.py` remembers the actual absolute Battery directory in ignored
`work/playtest.json`. It associates the stable ROM basename with
`Spider-Man-WoS-modded.dsv` in that directory. It uses the existing opaque snapshot
helper: no save parser, format conversion, room editor, or save-state loading.

This machine is configured for
`F:\Enrik Desktop Files\PROJECTS\DsSmuMe\Battery`.
Inspection found five 634-byte Spider-Man `.dsv` files matching the five played ROM
names. DeSmuME was not running. Each was preserved in a named `legacy-<ROM-stem>`
snapshot. The movie-suit file was the latest by modification time and matched the
first recent-ROM entry in `desmume.ini`; it was copied byte-for-byte into the stable
ROM's `.dsv` association. Its SHA256 is
`548d4d8e6d7044b2299067de92c3d48c66896cd872abcb7f370b88d024938484`.
The prior stable `.dsv` was preserved by the restore helper before replacement;
all other source files were retained. Named checkpoint `before-suit-cleanup`
contains the adopted bytes. These facts establish association/copy integrity,
not interpretation of save slots or a successful Continue reload.

Every `playtest.py build` checks for running DeSmuME processes on Windows, snapshots
the current nonempty stable battery save under a content-addressed `before-build`
name, builds the stable ROM from clean input plus selected overlay, and checks that
the save bytes remain identical. Running DeSmuME causes build, adoption, checkpoint,
restore and configuration commands to fail before their mutations. Keep it closed
throughout the operation: the process check is not a lock against relaunching.

Daily use, from this project's PowerShell directory:

```powershell
# Save in-game, then close DeSmuME.
python tools/playtest.py build
python mod.py verify
# Open build/Spider-Man-WoS-modded.nds; Continue, then test the changed feature.

# At a useful IN-GAME SAVE point, save normally and close DeSmuME:
python tools/playtest.py checkpoint early-game
python tools/playtest.py checkpoint before-boss
python tools/playtest.py list

# With DeSmuME closed, return to a previously recorded checkpoint:
python tools/playtest.py restore early-game
# Reopen the SAME stable ROM and choose Continue.
```

The sample checkpoint names do not exist until recorded; `before-suit-cleanup`
does exist locally. Use a different name to save a new version. Restoring keeps a
verified copy of displaced progress. Battery checkpoints resume where the game
saved, not at arbitrary animation frames, and cannot reach progress never recorded.
Avoid loading old emulator states after rebuilding: they restore old running memory
and can obscure whether changed assets or code loaded. Saves/states are distinct in
the [official DeSmuME manual](https://wiki.desmume.org/index.php?title=DeSmuME_Manual_for_the_Windows_port).

On a new computer, configure its actual Battery directory and adopt an existing
same-emulator `.dsv` before relying on Continue:

```powershell
$BatteryFolder = Read-Host 'Full path of the DeSmuME Battery folder'
python tools/playtest.py configure --battery-dir "$BatteryFolder"
$ExistingSave = Read-Host 'Full path of your existing nonempty Spider-Man .dsv'
python tools/playtest.py adopt "$ExistingSave"
python tools/playtest.py status
python tools/playtest.py build
```

For a different isolated overlay, `python tools/playtest.py build --mods
build/my-experiment/mods` still publishes the same stable ROM and preserves its
save association. That command includes only the chosen overlay; merge accepted
features deliberately when you want them together. The current six-asset movie/QoL
overlay has been promoted into regular `mods/`; Git excludes those private assets.

Four new synthetic playtest tests cover configuration/adoption/checkpoint restore,
both previous saves retained, repeated stable filename builds with unchanged save
bytes, idempotent safety snapshots, live-process rejection, invalid paths/formats,
and corrupt snapshots. Full suite: 47 passing; final helper checks rerun after small
guard adjustments. Actual save copying/hash verification is complete; user DeSmuME
Continue and named-checkpoint reload remain manual acceptance checks.

## Build and test a content change

1. Keep the clean input at `original/Spider-Man - Web of Shadows (USA) (En,Fr).nds`.
   The tool verifies its SHA256 before every operation.
2. Put only changed, manifest-approved resources in `mods/`. Extracted files in
   `work/` are inspection data; do not edit them in place.
3. Build to a descriptive output inside `build/`:

   ```powershell
   python mod.py build -o build/my-test.nds
   python mod.py verify -o build/my-test.nds
   ```

4. Reopen the newly built ROM from a fresh boot and choose Continue using your
   normal in-game save. New Game is needed only for explicitly fresh-game tests.
   Do not use an old save state: it can restore cached assets and stale RAM.
5. Keep a copy of the emulator battery save before experiments. Battery saves are
   separate from the ROM; save states are not a replacement for battery-save
   backups.
6. Record the output hash, changed asset, exact test steps, and observed result.
   A build report is emitted beside every ROM.

The clean ROM is read-only to the workflow. Builds are separate files, and the
writer refuses to overwrite the input. To prove the extraction/repacker path
without active mods:

```powershell
python mod.py extract
python mod.py verify --round-trip
python -m unittest discover -s tests -v
```

## Room and progression investigation

The objective is a private, deterministic test harness rather than blind room
swapping. Work from the existing inventory and change one input at a time.

### Phase 1: establish room identities

- Use `python mod.py find 'Downtown*'`, `python mod.py find 'Residential*'`, and
  the other map prefixes to make a room table.
- Pair each `.bsp` with its room `.obj` and record size, hashes, magic, envelope
  fields, and neighboring resources.
- Treat names as labels, not proof of runtime routing. The current BSP/OBJ
  envelope is parsed, but node, coordinate, entrance, trigger, and object fields
  remain hypotheses.

### Phase 2: differential room analysis

- Compare closely related rooms, starting with `Downtown_Save02` versus
  `Downtown_Save03`, where only 104 OBJ bytes differ.
- Compare one room against itself after a controlled in-game action when a save
  or runtime capture can identify the changed object.
- Classify each differing region as header, table, coordinate, ID, flag, or
  unknown. Do not assign meaning from a single example.
- Preserve unknown bytes and add confirmed observations to
  `docs/FORMAT_NOTES.md`; update confidence and editability in
  `docs/MODDABILITY_MATRIX.md`.

### Phase 3: safe runtime experiments

- Make a byte-identical clean round-trip first.
- Test a same-size replacement before testing a resized resource.
- Use a disposable build and a backed-up battery save.
- Test boot, room entry, collision, camera, exits, enemies, saving, and reload.
- Revert after each experiment. A room replacement that boots is not necessarily
  semantically correct.

### Phase 4: create private testing tools

The first useful tools should be small and evidence-driven:

1. A room inventory/diff report for BSP/OBJ pairs.
2. A lossless BSP/OBJ parser that exposes only confirmed fields and retains an
   opaque tail.
3. A save-file differ that compares two saves and detects checksums, slots, room
   IDs, flags, and inventory candidates.
4. Opaque named save backups/restores are now available in `tools/save_backups.py`;
   save decoding, checksum mapping, and save editing remain unimplemented.
5. An emulator test manifest recording ROM hash, overlay hashes, save snapshot,
   room, inputs, frame count, and observations.
6. Later, a save editor or debug warp only after room IDs and progression flags
   have been confirmed by multiple controlled comparisons.

Shipped test maps (`Test_Combat01`, `Test_Collision01`, and
`Test_Challenge01`) are good candidates for early experiments, but they should
not be routed into normal gameplay until the loader and entrance conventions are
understood. Adding new Glob IDs, renaming resources, and arbitrary engine code
patches are outside the current safe workflow.

## Current limits and priorities

The archive and ROM builder are validated. NSBTX palette editing, compression
round trips, XBD binding replacement, and room envelopes have different levels
of support, documented in [the moddability matrix](MODDABILITY_MATRIX.md).
BSP/OBJ geometry, save payloads and arbitrary room routing remain unknown.
GMB channels/root movement, SCA pools/joint matrices, purchase records and combo
credit now have tested mappings. Read ORIGINAL_GAMEPLAY.md, COMBO_ENGINE.md,
UPGRADE_ENGINE.md and ANIMATION_RESEARCH.md before changing another paid move.
The next approved incremental gameplay replacement is Web Vault; controlled
collision/launch tests must precede its release.
