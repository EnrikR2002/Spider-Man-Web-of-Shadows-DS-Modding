# Spider-Man: Web of Shadows DS modding

Private USA CS5E research. ROMs/extracted assets/builds/saves stay private.

**Play:** `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
The agent handles the stable ROM, releases and progress backups.
Current release: **v0.39.0**. **Crane Row** is rebuilt: the Long Arm is a
three-act fight with a boss meter, crews arrive by crane cargo drop, the map is
one connected ring and the harbour opens behind the boss. Agent-tested; your
verdict is open. **Boarding** (v0.38.0) costs 275 XP in Black upgrades.
Jump into a supported boss while holding toward it, or hold toward during a
heavy Web Yank zip. Y rakes; A tears and kicks off; R releases.
Boss attacks shake Miguel off. The Conductor and four native mini-boss types
are qualified. Existing purchases remain; twelve Black rows total 1,925 XP.
GPT-6.1 Terra rated every metric **8/10 or higher**. The player likes the
preview motion; in-game feel, hardware pacing and full-route balance remain open.
The existing Conductor sound issue is deferred at the player's request.
Details: [Changes](docs/CHANGES.md). What comes next: [Roadmap](docs/ROADMAP.md#now).

## Find what you need

Start with [instructions](AGENTS.md) and the [current handoff](docs/TASKS.md).
Then read the relevant section; routine startup does not require every document.

```powershell
python tools/run_tests.py          # tests; a fresh clone skips private-input cases
python tools/tool_index.py vortex  # find a tool by name or purpose
python tools/doc_contract.py check # every documentation rule, links included
```

| Need | Document |
|---|---|
| Build stack, adding a feature, qualification and publishing | [Development guide](docs/DEVELOPMENT.md) |
| Engine/format knowledge and task-to-topic map | [Technical notebook](docs/TECHNICAL.md) |
| Original gameplay | [Native behavior](docs/OG_GAMEPLAY.md) |
| Shipped behavior and release history | [Changes](docs/CHANGES.md) |
| Plans, designs, player feedback and ideas | [Roadmap](docs/ROADMAP.md) |

TASKS describes current work; source recipes, release pins and verified build
metadata establish exact build identity. Dated sections retain historical facts;
they are not current instructions. Keep the approved document roles instead of
adding session logs. Machine receipts/catalogs belong in reference/; scratch
scripts, captures and large reports belong in ignored work/ or build/.

## Local setup

Python 3.10+ and Windows PowerShell; production art/ARM tools have additional
[local dependencies](docs/DEVELOPMENT.md#local-runtime-dependencies). A new clone
contains source/metadata, not private ROMs, overlays, batteries or local research
dependencies: see [Know your environment](docs/DEVELOPMENT.md#know-your-environment).
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
