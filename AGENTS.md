# Project instructions

Private Nintendo DS Spider-Man: Web of Shadows research/modding, USA CS5E.
User instructions override older plans. Never overwrite the clean ROM in
original/ or externally publish ROMs/extracted copyrighted assets.

## Start and find the current truth

1. Read AGENTS, then docs/TASKS (the live handoff). Inspect the working
   tree; preserve unrelated changes.
2. Check the workspace (DEVELOPMENT "Know your environment"). If original/ holds
   only PUT_ROM_HERE.txt, edit docs, design and Python and run
   `python tools/run_tests.py`; you cannot build, run labs, read batteries or
   claim in-game results.
3. On a full setup, verify TASKS' build against reference/gameplay_profile.json,
   tools/release_info.py, reference/releases.json and the stable ROM metadata.
   Past save hashes are observations, not instructions; always read the actual
   latest battery.
4. Read only the sections you need. DEVELOPMENT covers the build stack, new
   features, qualification and publishing. TECHNICAL has a topic map; search
   headings and read bounded sections. Find tools with
   `python tools/tool_index.py <word>`; read `--help` before use.
   Never bulk-read TECHNICAL, CHANGES, catalogs or the archive.
5. Dated designs and old release sections are history; check later work
   before reusing them. Archive: `tools/doc_archive.py list`, then `read`.

## Documentation ownership

| File | Owns |
|---|---|
| AGENTS.md | Stable constraints, startup and documentation policy |
| docs/TASKS.md | Current objective/build, evidence, blocker and next exact action |
| docs/DEVELOPMENT.md | Build stack, feature recipe, validation and release workflow |
| docs/TECHNICAL.md | Engine/format contracts, discoveries, unknowns and evidence |
| docs/OG_GAMEPLAY.md | Original game behavior before modifications |
| docs/CHANGES.md | Shipped behavior, numbered release history and validation limits |
| docs/ROADMAP.md | Whole-game design, player feedback log and idea backlog |

README is the short entry point; mods/README is the overlay-loader exception.
`reference/doc_contract.json` is the machine-checked documentation contract:
document set, word limits, required headings, routing (what goes where),
forbidden edits, one current version and frozen CHANGES sections.
`python tools/doc_contract.py check` (run by tests.test_document_layout) must
pass before every commit. Change the contract only when the user changes
documentation policy, never to make a check pass. Archive a retired design with
`tools/doc_archive.py add` before removing it. Record discoveries in their
owning TECHNICAL section immediately, with confidence and source version; mark
superseded assumptions. Distinguish implemented, agent-tested and
player-confirmed. Record player verdicts in ROADMAP's feedback log.

## Task completion and Git

Before finishing, refresh TASKS with the current objective, evidence, blocker
and next exact action, and update other owning docs the task touched. Commit
all and only the task's changes with a concise message; exclude unrelated
pre-existing edits, or report the blocker if they cannot be separated. Do not
push unless the user asks; in an ephemeral cloud session, push only to the
branch that session designates.

Receipts/catalogs go in reference/; scratch, traces and captures in ignored
work/ or build/. A reusable research tool belongs in tools/ with a docstring
and tests.

## Safety and validation

- Read original/, write build/. Prefer deterministic Python tools and PowerShell.
  Parsers/repackers need lossless round trips; preserve unknown bytes.
- Use copied batteries/disposable RAM for research; never put fixtures into the
  actual save or load stale emulator states across changed ROMs.
- Preserve native abilities, ownership/dependencies, purchases, Both Suits
  traversal, Reinforced Web, rewards and the 32 KiB player kit unless deliberately
  changing the contract. Never grant paid skills or steal Black ownership bits.
- Use native velocity/collision for gameplay movement; no player teleports or
  time-slowing effects. Check pointer ownership, stale actors, flags and hook ABI.
- Unfamiliar visual/combat pipelines need one complete in-engine example before
  roster-wide expansion. Review native-scale motion, textures and mixed audio
  early. Counters/clearability do not establish presentation quality or fun.
- Changed chapter rooms require real-input door qualification through
  tools/midnight_walk.py all with an explicit candidate ROM. Teleport tours prove
  links only. Run focused checks, then relevant broad controls on a stable candidate.
- Qualify the final composition before publishing through tools/playtest.py build.
  Use actual Battery paths in work/playtest.json; keep DeSmuME closed, verify latest
  DSV wrapper/checkpoint bytes, preserve prior ROM/recipe and compare final hashes.
  A published version identifies one exact ROM; fixes require a new version.
  Version boot and Options identically. Record publication in CHANGES/releases.json.
- Player flow stays Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
  Agent manages the stable build/Spider-Man-WoS-modded.nds and all backups/releases.

## Player direction

Fun and spectacle come first, inside the base game's 2D side-view brawler
against mobs and bosses. Red (Garfield's Spider-Man) is fast, acrobatic and
spider-like: combo strong/web-resistant enemies, hit behind, cancel with R to
reposition and retain the combo. Preserve native A/B/base strings/evade. Red is
one combined TASM1/2 kit through Red purchase slots; Overclock, Dragnet and
Vortex are its final added skills: iterate them, add none. Black is Spider-Man
2099 (ROADMAP "the Hunter"); its kit may add rows on free saved bits as
needed. Prices/balance, third suit, save expansion, other
shop growth and campaign branches wait until requested.

New moves require fluid authored motion, continuous trajectories and overlap;
per-key eased "dancing" and repackaged stock attacks were rejected. Both chapters
need original enemy silhouettes/patterns/voices, full knockdown/get-up/death,
visible roofs/doors and connected varied spaces. Midnight should avoid repeated
sewer/Hive recolours and excess copy-paste rooms. Accepted map improvement does
not imply acceptance of enemy quality; read the latest player feedback in ROADMAP.

Snap Sweep and original Web Vault are player-confirmed. GroundAttack15 is shared;
G11/16/17 have m6.xbd users and are not spare storage. Preserve other actor bindings.
Attack strength is not HP damage; the combo gauge is not a hit count.
