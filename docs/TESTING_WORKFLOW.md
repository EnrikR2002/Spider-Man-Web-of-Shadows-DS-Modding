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

Keep one stable ROM filename/path for everyday testing. Use separate experiment
ROMs for isolated comparisons. A renamed ROM may be associated with a different
save by your emulator; check its configured save location. If Continue disappears,
do not start a new game over your progress: first check which save is being used.
Copy progress between builds using the same emulator/save format, or the emulator's
supported import/export procedure. Never convert a save just by renaming its suffix.
The helper below copies bytes only and does not guess save locations.

Asset-only edits are expected to preserve progress, but broader progression/engine
changes may require special compatibility tests or disposable saves. Back up first.
The automated boot harness does not load your gameplay saves; its opening-game
captures do not mean your normal playthrough must restart.

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

Keep an additional copy on another drive for important progress. Local snapshots
are not protection against disk loss. The emulator must stay closed throughout
restore: this tool cannot lock it out or stop it from overwriting a restored file.

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
Gameplay semantics for BSP, OBJ, GAB, GMB, SCA, save data, and room routing are
not yet decoded. The next high-value milestone is a differential BSP/OBJ room
report followed by save-format mapping, not a blind boss or room injection.
