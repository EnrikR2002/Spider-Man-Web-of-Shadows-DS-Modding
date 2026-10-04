# Spider-Man: Web of Shadows DS — personal mod workflow

USA `CS5E`, title `SPIDERMANWOS`. Python 3.10+; the archive/build workflow uses only
the standard library. Commands below run from this project directory in PowerShell.

Resume work from [project tasks and session handoff](docs/TASKS.md). It records the
last release, active task, pending checks and the next action between sessions.

Keep your untouched ROM at:

`original/Spider-Man - Web of Shadows (USA) (En,Fr).nds`

The workflow checks it against the tested SHA256 baseline before every operation.
`original/` is read only to the tooling. Builds stay in `build/`; extracted assets,
overlays, emulator files and captures are private and ignored by `.gitignore`.
This project must not be distributed with the ROM or extracted copyrighted assets.

## Set up on another computer

Install Git and Python 3.10+ on the other computer, and make sure `git --version`
and `python --version` work in PowerShell. Sign in to GitHub as an account with
access to this private repository when Git asks. Your existing DeSmuME 0.9.11
installation can be used for the manual boot check below.

GitHub contains the complete source workflow: `mod.py`, all `tools/` modules,
tests, documentation, the Glob manifest, metadata reports, and the placeholder
files that create `original/` and `mods/`. There are no Python packages to install
with pip. No files from the temporary clone check are needed.

Clone the repository, then copy your own untouched ROM to the path above. The ROM,
extracted assets, builds, and active overlay are excluded from GitHub;
`python mod.py experiment green-suit` regenerates the reversible example from
your clean ROM. `extract` creates `work/`, and `build` creates `build/` automatically.

```powershell
git clone https://github.com/EnrikR2002/Spider-Man-Web-of-Shadows-DS-Modding.git
cd Spider-Man-Web-of-Shadows-DS-Modding
# Copy your clean ROM to original/Spider-Man - Web of Shadows (USA) (En,Fr).nds
python mod.py extract
python mod.py verify --round-trip
python -m unittest discover -s tests -v
python mod.py experiment green-suit
python mod.py build --gameplay-profile original
python mod.py verify --gameplay-profile original
```

The clean ROM must be 67,108,864 bytes with SHA256
`61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`.
The tools check this automatically. Copy the ROM as a separate local transfer;
it is the only game-data input required to reproduce the example and full tests.

In DeSmuME, choose **File > Open ROM**, select
`build/Spider-Man-WoS-modded.nds` inside your new clone. Start a new game only if
you have no existing progress; otherwise associate your battery save and Continue.
Spider-Man's red suit sections should be green in the opening Residential area.
After each rebuild, close and reopen the ROM so it loads the new asset. See
[the DeSmuME procedure](docs/VISIBLE_MOD.md#desmume-0911-on-the-other-computer)
for the baseline comparison. Gameplay was verified here in melonDS DS 1.1.5;
DeSmuME 0.9.11 still needs this manual check on your other computer.

When switching computers, push source changes with `git add`, `git commit`, and
`git push`, then run `git pull --ff-only` in the other clone before working.
Copy any custom private overlays you want to preserve separately; they are not
synchronized through Git. The clean ROM only needs to be copied once per computer.

## Daily edit/build/boot loop

```powershell
python mod.py extract
python mod.py find spd --ext nsbtx
# Copy only an asset you intend to change from work/glob/ into mods/, then edit it.
python mod.py build
python mod.py verify
```

Open `build/Spider-Man-WoS-modded.nds` in your DS emulator. Start a fresh boot after
rebuilding so the game reloads the changed asset. The green-suit commands above
create the proven example overlay, `mods/spd.nsbtx`.

**Fresh boot does not mean New Game.** Save in-game, close the emulator, back up
its separate battery-save file, rebuild/verify, reopen the ROM, and choose Continue.
Keep a stable everyday ROM filename; isolated builds may need a copy of the save
associated with their filename. Do not load old emulator save states to test new
assets. See `docs/TESTING_WORKFLOW.md` for the plain-language explanation and
`tools/save_backups.py` for opaque named `.sav`/`.dsv` backups and guarded restores.

The current local regular overlay contains the cleaned movie-inspired red suit
(solid panels, black lenses), the white alternate suit, menu readability changes,
and yellow mission marker. TASM 1 stage one adds **Snap Sweep**, a compact opening
low kick in the red form: measured completion in 24 versus 44 emulator frames,
with the native follow-up string retained. Stage one used seven overlay assets.
See [the cleanup evidence](docs/MOVIE_SUIT_EXPERIMENT.md#clean-panels-and-black-lenses--2026-10-04).

The current incremental release adds **Rebound**, replacing the native **Web Kick**
purchase at **100 XP**. Grapple with A, then attack with Y: the kick ends with a
short player recoil and an authored recovery pose, exchanging half the enemy's
horizontal knockback for player separation. Existing Web Kick ownership carries
over; unowned and refunded slots remain locked. The other six Red upgrades keep
their native behavior until their replacements are tested. The regular overlay
now has nine assets and two bounded ARM9 data-word changes; no instructions change.
See [Rebound acceptance](docs/TASM1_REBOUND.md).

**Player flow:** double-click `Play Spider-Man.cmd`, choose Continue, play, save
in-game, close DeSmuME. The launcher opens the stable ROM and backs up progress.
The agent handles feature releases/checkpoints; the commands below are agent tools.

```powershell
python tools/playtest.py build
# Open build/Spider-Man-WoS-modded.nds in DeSmuME and choose Continue.
# Save in-game and close DeSmuME before each command that copies saves.
python tools/playtest.py checkpoint early-game
python tools/playtest.py checkpoint before-boss
python tools/playtest.py list
python tools/playtest.py restore early-game
```

The local Battery folder is already configured and the most recently played
movie-suit `.dsv` has been copied to this ROM's save association, retaining backups
of all five earlier Spider-Man saves. `before-suit-cleanup`, `before-tasm1`,
`opening-save-room`, `before-rebound` and `before-web-vault` are available locally.
Checkpoint names must be unique. A checkpoint returns to an in-game save you have
recorded; it does not jump to an arbitrary room. An isolated copy of current progress
successfully loaded/resumed in melonDS; native DeSmuME acceptance is still a player
check. [Setup on another machine](docs/TESTING_WORKFLOW.md#stable-playtest-command--2026-10-04)
uses that machine's actual Battery folder. Configuration, saves and overlays stay
private and do not come from Git.

See the [active TASM 1 kit and selected backlog](docs/NEW_SUIT_DESIGN.md),
[exact implementation/evidence](docs/TASM1_IMPLEMENTATION.md), and
[66-option catalog](docs/SUIT_CATALOG.md). A third selectable slot and custom
conditional abilities remain research milestones.

The [original gameplay map](docs/ORIGINAL_GAMEPLAY.md) explains both suit identities,
all 21 purchased skills, controls, costs and dependencies. The [combo investigation](docs/COMBO_ENGINE.md)
records why Snap Sweep earns credit before the HUD appears: its contacts can leave
the gauge below the native visibility threshold. The meter increases XP rewards;
exact multipliers remain unknown. No credit boost is applied.

Regular builds and verification load `reference/gameplay_profile.json`, which pins
the complete Rebound + Web Vault overlay recipe. Web Vault replaces Web Launch at
200 XP: grapple with A (keyboard W), then Up to launch and follow with a short vault.
See [release evidence](docs/TASM1_WEB_VAULT.md). A new clone has source tools but no private
assets. The suit painter also needs the private `build/suit-model-inspect/spd.dae`
export from your clean model; follow the Apicula export procedure in
[MOVIE_SUIT_EXPERIMENT.md](docs/MOVIE_SUIT_EXPERIMENT.md) first. Then generate a
complete isolated candidate from your own clean ROM with:

```powershell
python tools/qol_suits_menu.py
python tools/movie_suit.py --combined
python tools/tasm_suit.py --mods build/movie-suit-clean/combined/mods
python tools/tasm_web_vault.py --mods build/tasm1-stage1/mods --out build/tasm-web-vault
python mod.py verify --mods build/tasm-web-vault/mods -o build/tasm-web-vault/WebVault.nds --gameplay-profile build/tasm-web-vault/gameplay_profile.json
```

An agent promotes the tested overlays and recipe before using the stable publisher.
Use `--gameplay-profile original` explicitly for earlier asset-only experiments
and native engine-data controls. It leaves the selected overlay intact.

`build` reads unchanged content directly from the clean ROM, so extraction is optional
for a build. Only exact manifest filenames are accepted in `mods/`. File sizes may
grow or shrink; builds are deterministic, capacity-bounded, and verified before writing.
Unknown names, case mismatches, `GlobFiles.txt` changes, and path escapes fail clearly.
The current workflow replaces existing assets; it does not add archive IDs/resources.

Each build emits:

- `build/Spider-Man-WoS-modded.nds` — rebuilt 64 MiB ROM.
- `build/Spider-Man-WoS-modded.Glob.bin` — rebuilt archive.
- `build/Spider-Man-WoS-modded.build.json` — replaced asset IDs, old/new sizes and SHA256s,
  source/output hashes, FAT boundaries, header CRC and verified-resource counts.

There are no timestamps in the build log. Repeating the same command with the same
inputs yields the same ROM, archive and log. ROM publication uses an atomic file replacement.

## Commands

```powershell
python mod.py list
python mod.py list --ext xbd
python mod.py find 'spd_GroundAttack*' --json
python mod.py extract                       # clean NitroFS + 3,733 assets -> work/
python mod.py build                         # mods/ -> default build
python mod.py build --mods work/my-overlay -o build/my-test.nds
python mod.py verify                        # compares build to clean + current mods
python mod.py verify --mods work/my-overlay -o build/my-test.nds
python mod.py verify --round-trip           # checks clean work/glob/, emits exact no-op build/report
python mod.py build --gameplay-profile original # explicit native ARM9 control
python -m unittest discover -s tests -v
```

Paths passed to `mod.py` are relative to the project, regardless of your working directory.
`--rom` can point to another location containing the identical validated clean dump.
Extraction refuses to overwrite edited resources; keep edits in an overlay or choose
another extraction directory with `extract -o work/another-clean-extraction`.
`verify` detects stale builds, unknown overlay assets, and any byte differing from the
expected rebuild. `verify --round-trip` separately validates the clean extraction;
active mods are not used for that command.

## Proven visible experiment

```powershell
python mod.py experiment green-suit
python mod.py build --gameplay-profile original
python mod.py verify --gameplay-profile original
```

This changes only red-dominant palette colors in `spd.nsbtx`. Both original and
modified builds have been cold-booted in melonDS DS 1.1.5 through Residential gameplay;
the player's red suit becomes green. See [the exact procedure and evidence](docs/VISIBLE_MOD.md).

To undo it:

```powershell
python mod.py experiment revert
python mod.py build --gameplay-profile original
python mod.py verify --gameplay-profile original
```

With no other overlays, the reverted build is byte-identical to the clean ROM.
Revert refuses to remove a texture that differs from the generated experiment.

## Optional automated emulator captures

No emulator is needed to build. The optional Windows x64 harness downloads a pinned,
hash-checked official melonDS DS core into `work/`, uses built-in BIOS, executes a
bounded Start/A sequence, and writes private captures/metadata under `build/boot-tests/`.

```powershell
python tools/emulator_smoke.py --fetch-core > build/emulator-modded.log 2>&1
python tools/emulator_smoke.py build/roundtrip/Spider-Man-WoS-unmodified.nds > build/emulator-unmodified.log 2>&1
```

`--fetch-core` is needed only once. The captured images need visual inspection;
the harness does not automatically claim gameplay correctness. Optional `--save`
loads a read-only battery copy, `--script` replays explicit DS button ranges and
`--player-trace START:END` records bounded, read-only CS5E player telemetry.

## Reverse-engineering tools and notes

```powershell
python tools/analyze_formats.py
python tools/analyze_formats.py --decoded work/decoded
```

These regenerate a deterministic metadata survey and optionally decode supported
GMB/2LZ streams into a private work directory. **Decoded files are inspection data;
do not copy them directly into mods/**. A changed compressed asset needs re-encoding,
and its gameplay fields still need to be understood.

The low-level `tools/wos_tool.py` commands remain available: `inspect-rom`,
`extract-rom`, `unpack-glob`, `repack-glob`, `repack-rom`, and `manifest`.
Use `mod.py` for the normal workflow; it adds clean-source/manifest/overlay validation.

Read [validation results](docs/VALIDATION.md), [format evidence](docs/FORMAT_NOTES.md),
[editing status/priorities](docs/MODDABILITY_MATRIX.md), and the
[modding/testing and room-research workflow](docs/TESTING_WORKFLOW.md). The next work
is the next approved purchased replacement, Web Vault, using the native gameplay,
purchase and animation maps. Room geometry, save payloads, full decompilation and
a general animation GUI remain research.
