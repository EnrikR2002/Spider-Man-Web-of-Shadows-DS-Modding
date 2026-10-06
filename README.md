# Spider-Man: Web of Shadows DS modding

Private USA CS5E research. Python 3.10+, Windows PowerShell, standard-library
archive tools. ROMs/extracted assets/builds/saves stay private.

**Play:** `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
The agent handles releases, backups/checkpoints and the stable everyday ROM.

Six core documents: [instructions](AGENTS.md), [tasks/backend queue](docs/TASKS.md),
[ROM technical knowledge](docs/TECHNICAL.md), [original gameplay](docs/OG_GAMEPLAY.md),
[implemented changes/releases](docs/CHANGES.md), [TASM redesign](docs/TASM_ROADMAP.md).
Start with instructions/tasks; read other sections only as needed. No new
feature/release/session/summary Markdown files. Machine data belongs in
reference/; reports/captures/scratch scripts belong in ignored work/ or build/.
The repo docs are the shared memory for every assistant working here.

## Agent workflow

Clean ROM: `original/Spider-Man - Web of Shadows (USA) (En,Fr).nds`, 64 MiB,
SHA256 `61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`.
Never overwrite it. A new clone has source/metadata, not private overlays/saves.

```powershell
python mod.py extract
python mod.py verify --round-trip
python mod.py build --mods work/my-overlay -o build/my-test.nds
python mod.py verify --mods work/my-overlay -o build/my-test.nds
python -m unittest discover -s tests -v
# After isolated qualification, merge all accepted overlays/profile; emulator closed:
python tools/playtest.py checkpoint before-feature
python tools/playtest.py build
```

Red kit (v0.2.0+) and emulator research:

```powershell
python tools/assemble_tasm_kit.py            # after editing tools/tasm_kit.s (then re-pin hashes)
python tools/tasm_kit.py                     # candidate build/version-<VERSION>
python tools/kit_lab.py qualify build/version-0.2.0/Versioned.nds
python tools/kit_lab.py trace <rom> <label> reflex --frames 300 --cap 30,40
python tools/kit_lab.py preview spin 4,9     # stick-figure clip check
python tools/kit_lab.py disasm 0x020B5C28 20
```

Use the candidate's composed `--gameplay-profile` for new recipes; `original`
means native engine with the selected asset overlay. Never load old emulator
states over changed ROMs. Read the actual Battery directory in work/playtest.json;
use copies for research. Checkpoints/previous ROMs are agent-managed.

Older exact notes: `python tools/doc_archive.py list <topic>`,
`read <name> --toc`, then `read <name> --section '<heading>'` (80-line default).
The archive is excluded from routine searches. Text/tree/asset round trips,
unknown bytes and unresolved gameplay checks belong in TECHNICAL/CHANGES.
