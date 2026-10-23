# Project instructions

Private Nintendo DS Spider-Man: Web of Shadows research/modding, USA CS5E.
User instructions override older plans. Never overwrite the clean ROM in
original/ or externally publish ROMs/extracted copyrighted assets.

## Start and find the current truth

Read AGENTS and docs/TASKS first. Inspect the working tree and preserve unrelated
changes. TASKS is the live handoff; verify its current build against
reference/gameplay_profile.json, tools/release_info.py, reference/releases.json
and the stable ROM/build metadata before acting. Past save hashes are observations,
not instructions to restore them. Always read the actual latest battery.

Read only the relevant section of docs/DEVELOPMENT.md for tool selection,
commands, evidence schemas and release procedure. TECHNICAL has a topic map;
search headings and read bounded sections. Never bulk-read the technical notebook,
changelog, catalogs or archive at startup. Historical notes: tools/doc_archive.py
list, then read --toc/--section. Dated designs and old release sections are historical;
check later implementations and current player direction before reusing them.

## Documentation ownership

| File | Owns |
|---|---|
| AGENTS.md | Stable constraints, startup and documentation policy |
| docs/TASKS.md | Current objective/build, evidence, blocker and next exact action |
| docs/DEVELOPMENT.md | Reusable development, validation and release workflow |
| docs/TECHNICAL.md | Engine/format contracts, discoveries, unknowns and evidence |
| docs/OG_GAMEPLAY.md | Original game behavior before modifications |
| docs/CHANGES.md | Shipped behavior, numbered release history and validation limits |
| docs/TASM_ROADMAP.md | Design, player feedback and deferred ideas |

README is the short entry point; mods/README is the overlay-loader exception.
Keep this approved set; add a document only when the user authorizes it and a
new ownership boundary is necessary. No per-session/release/handoff Markdown.
Preserve retired designs in the existing verified archive with dated provenance;
keep current decisions and deferred scope in the live roadmap/catalogs.
Keep AGENTS/TASKS under 900 words. Update TASKS at accepted-candidate/publication
milestones and before stopping; replace stale state. Record discoveries in their
owning technical section immediately, with confidence and source version. Mark
superseded assumptions. Distinguish implemented, agent-tested and player-confirmed.

## Task completion and Git

Before finishing a task, refresh docs/TASKS.md with the current objective, evidence,
blocker and next exact action. Update other owning docs when the task changes their
domain. Commit all and only the task's changes with a concise descriptive message.
Preserve and exclude unrelated pre-existing edits; if changes cannot be safely
scoped, report the commit blocker instead of including or discarding them. Do not
push unless the user asks.

Machine catalogs/recipes/receipts belong in reference/. Scratch scripts, large
traces, captures and temporary assets belong in ignored work/ or build/. A reusable
research tool belongs in tools/ with appropriate tests. Do not duplicate volatile
hashes, runtime addresses or test logs across startup documents.

## Safety and validation

- Read original/, write build/. Prefer deterministic Python tools and PowerShell.
  Parsers/repackers need lossless round trips; preserve unknown bytes.
- Use copied batteries/disposable RAM for research; never put fixtures into the
  actual save or load stale emulator states across changed ROMs.
- Preserve native abilities, ownership/dependencies, purchases, Both Suits
  traversal, Reinforced Web, rewards and the 32 KiB player kit unless deliberately
  changing the contract. Never grant paid skills or steal Black ownership bits.
- Use native velocity/collision for gameplay movement. No player teleports or
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

Fun and spectacle come first. Garfield's Spider-Man is fast, acrobatic and
spider-like: combo strong/web-resistant enemies, hit behind, cancel with R to
reposition and retain the combo. Preserve native A/B/base strings/evade. Develop
one combined TASM1/2 kit through Red purchase slots. Overclock, Dragnet and Vortex
are the final added skills: iterate them, add none. The 2099 Black kit may add
purchased rows on free saved bits as its coherent design needs (2026-10-23).
Prices/balance, third suit, save expansion, other shop growth and campaign
branches remain deferred unless requested.

New moves require fluid authored motion, continuous trajectories and overlap;
per-key eased "dancing" and repackaged stock attacks were rejected. Both chapters
need original enemy silhouettes/patterns/voices, full knockdown/get-up/death,
visible roofs/doors and connected varied spaces. Midnight should avoid repeated
sewer/Hive recolours and excess copy-paste rooms. Accepted map improvement does
not imply acceptance of enemy quality; read the latest player feedback in TASKS.

Snap Sweep and original Web Vault are player-confirmed. GroundAttack15 is shared;
G11/16/17 have m6.xbd users and are not spare storage. Preserve other actor bindings.
Attack strength is not HP damage; the combo gauge is not a hit count.
