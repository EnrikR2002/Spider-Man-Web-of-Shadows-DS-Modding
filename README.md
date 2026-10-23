# Spider-Man: Web of Shadows DS modding

Private USA CS5E research. ROMs/extracted assets/builds/saves stay private.

**Play:** `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
The agent handles the stable ROM, releases and progress backups.
Current release: **v0.32.1**. 2099's first skill is Hunter's Return, in the
existing Webbed Fury purchase slot: after a ground dash hits, release A and tap
A again for recall into a rising talon rake; R cancels. Native-resistant targets
get a short physical pursuit attempt. His cape-free model has fuller chest,
shoulders and arms. Earlier Red kit/chapter/boss/Vitality work remains.
The v0.32.1 correction isolates launches per victim and clears a departed
player's move after room reloads. Player feel and appearance preference remain open.
Details: [Changes](docs/CHANGES.md). Next priorities: [Roadmap](docs/TASM_ROADMAP.md#recommended-build-order).

## Find what you need

Start with [instructions](AGENTS.md) and the [current handoff](docs/TASKS.md).
Then read the relevant section; routine startup does not require every document.

| Need | Document |
|---|---|
| Commands, tool selection, qualification, evidence and publishing | [Development guide](docs/DEVELOPMENT.md) |
| Engine/format knowledge and task-to-topic map | [Technical notebook](docs/TECHNICAL.md) |
| Original gameplay | [Native behavior](docs/OG_GAMEPLAY.md) |
| Shipped behavior and release history | [Changes](docs/CHANGES.md) |
| Design, player feedback and deferred work | [TASM roadmap](docs/TASM_ROADMAP.md) |

TASKS describes current work; source recipes, release pins and verified build
metadata establish exact build identity. Dated sections retain historical facts;
they are not current instructions. Keep the approved document roles instead of
adding session logs. Machine receipts/catalogs belong in reference/; scratch
scripts, captures and large reports belong in ignored work/ or build/.

## Local setup

Python 3.10+ and Windows PowerShell; production art/ARM tools have additional
[local dependencies](docs/DEVELOPMENT.md#local-runtime-dependencies). A new clone
contains source/metadata, not private ROMs, overlays, batteries or local research dependencies.
Clean ROM: `original/Spider-Man - Web of Shadows (USA) (En,Fr).nds`, 64 MiB,
SHA256 `61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`.
Never overwrite it. Initial inventory/round-trip setup, when needed:

```powershell
python mod.py extract
python mod.py verify --round-trip
```

Use the development guide's task-specific workflow for changes. Old release
generators reproduce their pinned release; changing their bytes under an already
published version is forbidden. Preserve the accepted composition, qualify a
private candidate, then publish via `python tools/playtest.py build` with DeSmuME
closed. Do not load an old emulator state over a changed ROM.

Historical notes: `python tools/doc_archive.py list <topic>`, then
`read <name> --toc` or `read <name> --section '<heading>'` (80-line default).
The archive retains retired design/catalog snapshots with their own dates;
the live roadmap records current decisions and deferred work.
