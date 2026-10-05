# Project instructions

Private modding/research of Nintendo DS Spider-Man: Web of Shadows, USA CS5E.
User instructions override older plans. Never overwrite the original ROM or
publish ROMs/extracted copyrighted assets.

## Fixed document layout

There are six core Markdown documents. Edit these in place; do not create another
feature, release, experiment, session, plan or handoff Markdown file.

| File | Owns |
|---|---|
| AGENTS.md | Startup instructions, guardrails and this document policy |
| docs/TASKS.md | Current work, ordered backend queue/ideas and short handoff |
| docs/TECHNICAL.md | Everything learned about ROM formats/engine/tools; confidence, unknowns and evidence |
| docs/OG_GAMEPLAY.md | How the original game works, before modifications |
| docs/CHANGES.md | Implemented mod behavior, numbered release history and validation limits |
| docs/TASM_ROADMAP.md | TASM identity, combat design, progression and prototype order |

Root README is a short entry point/workflow; mods/README is the overlay-loader
exception. No other active Markdown is permitted. The documentation-layout test
enforces this set and bounds TASKS/AGENTS size. Technical detail may grow in the
single notebook, but must use searchable topic headings, not repeated logs.
Machine-readable catalogs/release records live under reference/. Generated
reports/scripts/captures live in ignored work/ or build/.

Read AGENTS and TASKS at startup. Then search headings with rg and read only the
section relevant to the task. Never bulk-read TECHNICAL, CHANGES, catalogs or the
archive. Older exact notes are in docs/archive/legacy-notes.zip; use
`python tools/doc_archive.py list <topic>` then `read <note> --toc/--section`.
Update TASKS after milestones/before stopping, replacing stale state. Keep it
under 900 words; preserve concrete next actions/evidence paths and backend queue.
Put shipped facts in CHANGES, research in TECHNICAL, proposals in TASM_ROADMAP.
Always distinguish implemented, agent-tested and player-confirmed behavior.

## Tools, testing and release safety

- Read originals from original/, write builds to build/. Keep tools deterministic
  and scriptable in Windows PowerShell; prefer Python standard library.
- Every parser/repacker needs lossless round-trip tests. Preserve unknown bytes;
  call unknown fields unknown. Test one empirical change at a time with a control.
- Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
  Agent manages builds/checkpoints; keep build/Spider-Man-WoS-modded.nds stable.
- Use the actual Battery directory in ignored work/playtest.json. Keep DeSmuME
  closed for save mutations/publication, verify DSV wrapper/snapshot bytes, and
  preserve latest progress/prior ROMs/active compositions. Re-read latest battery.
- Use copied batteries/disposable emulator RAM for research; never write fixtures
  into the real save or load stale emulator states over a changed ROM.
- Qualify isolated candidates, compose all accepted overlays, publish through
  `python tools/playtest.py build`. Do not ask the player to manage filenames,
  backups or build commands. Record the release in CHANGES and reference/releases.json.
- Version is major.minor.patch: minor for new/overhauled mechanics, patch for
  fixes/polish/balance, major for a finished overhaul or incompatible contract.
  A published version identifies one exact ROM; never reuse it for different bytes.
  Show the same version at boot and in Options. Keep release code in existing
  tools/release_info.py rather than creating per-version scripts/modules.

## Current gameplay authority

2026-10-05 latest steering: FUN COMES FIRST. The user rejected the 26-skill
catalog as overwhelming. Build one complete trickster-acrobat kit around bounce,
zip, sling and web burst, with responsive attacks/escapes and a few consistent
inputs. Prove the fun in a crowd with generous tuning and the full kit enabled
in an isolated prototype. Defer prices, cooldowns, damage parity and progression
until the loop earns player acceptance. No target skill count or separate
purchases for basic movement/cancel/targeting usability. Native limits are not
design ceilings. Real mechanics/choreography must make the identity visible.

Develop one combined TASM1/2 kit at a time through red form. Selected later suits
remain in reference/suit_roadmap.json. Preserve native ownership/dependencies,
existing purchases, Both Suits traversal and Reinforced Web unless a deliberate
migration is implemented. Do not grant paid moves at start or steal black bits.
Expanded shop rows/save support and third suit selection remain research;
progression work follows the fun prototype. Fully enabled research uses copied
saves/disposable RAM, never the real save. Public ownership migration stays explicit.

Snap Sweep is player-confirmed. It borrows GroundAttack15 payloads; author paid
routes separately and test locked/owned cases. G11/16/17 also have m6.xbd users,
so they are not spare storage; retain original IDs/other actor bindings.
Original Web Vault is player-confirmed; later refinements/player checks remain
open. Never report attack strength as HP damage or the combo gauge as hit count.
