# Spider-Man: Web of Shadows DS — personal mod workflow

USA `CS5E`, title `SPIDERMANWOS`. Python 3.10+; the archive/build workflow uses only
the standard library. Commands below run from this project directory in PowerShell.

Keep your untouched ROM at:

`original/Spider-Man - Web of Shadows (USA) (En,Fr).nds`

The workflow checks it against the tested SHA256 baseline before every operation.
`original/` is read only to the tooling. Builds stay in `build/`; extracted assets,
overlays, emulator files and captures are private and ignored by `.gitignore`.
This project must not be distributed with the ROM or extracted copyrighted assets.

## Set up on another computer

Clone the private source repository, then place your own clean ROM dump at the path
above. The ROM, extracted assets, builds, and active overlay are deliberately excluded
from GitHub; `python mod.py experiment green-suit` regenerates the reversible example.

```powershell
git clone https://github.com/EnrikR2002/Spider-Man-Web-of-Shadows-DS-Modding.git
cd Spider-Man-Web-of-Shadows-DS-Modding
# Copy your clean ROM to original/Spider-Man - Web of Shadows (USA) (En,Fr).nds
python mod.py extract
python -m unittest discover -s tests -v
python mod.py experiment green-suit
python mod.py build
python mod.py verify
```

When switching computers, push source changes with `git add`, `git commit`, and
`git push`. Copy the clean ROM and any private overlay you want to preserve separately;
they are not synchronized through Git.

## Daily edit/build/boot loop

```powershell
python mod.py extract
python mod.py find spd --ext nsbtx
# Copy only an asset you intend to change from work/glob/ into mods/, then edit it.
python mod.py build
python mod.py verify
```

Open `build/Spider-Man-WoS-modded.nds` in your DS emulator. Start a fresh boot after
rebuilding so the game reloads the changed asset. The currently active overlay is
the proven green-suit experiment, `mods/spd.nsbtx`.

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
python mod.py build
python mod.py verify
```

This changes only red-dominant palette colors in `spd.nsbtx`. Both original and
modified builds have been cold-booted in melonDS DS 1.1.5 through Residential gameplay;
the player's red suit becomes green. See [the exact procedure and evidence](docs/VISIBLE_MOD.md).

To undo it:

```powershell
python mod.py experiment revert
python mod.py build
python mod.py verify
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
the harness does not automatically claim gameplay correctness or load your saves.

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
and [editing status/priorities](docs/MODDABILITY_MATRIX.md). The next work is actor
bindings and decoded move triplets, followed by controlled room comparisons and text/UI
formats. A full game decompilation and GUI are deliberately deferred.
