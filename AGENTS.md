# Project instructions

Private modding/research of Nintendo DS Spider-Man: Web of Shadows, USA CS5E.
User instructions override older plans. Never overwrite the original ROM or
publish ROMs/extracted copyrighted assets.

## Shared agent context

The user alternates between different AI assistants (e.g. Claude and GPT). The
repository is the only shared memory: put every durable fact, decision, user
preference and workflow lesson into the documents below, never only into an
assistant's private memory or chat. Read them; do not rely on prior chats.

## Fixed document layout

There are six core Markdown documents. Edit these in place. Do not create another
feature, release, experiment, session, plan, summary or handoff Markdown file,
including at the end of a task: update the owning document instead.

| File | Owns |
|---|---|
| AGENTS.md | Startup instructions, guardrails and this document policy |
| docs/TASKS.md | Current work, ordered backend queue/ideas and short handoff |
| docs/TECHNICAL.md | Everything learned about ROM formats/engine/tools; confidence, unknowns and evidence |
| docs/OG_GAMEPLAY.md | How the original game works, before modifications |
| docs/CHANGES.md | Implemented mod behavior, numbered release history and validation limits |
| docs/TASM_ROADMAP.md | TASM identity, combat design, skill status and next iterations |

Root README is a short entry point/workflow; mods/README is the overlay-loader
exception. No other active Markdown is permitted; a test enforces this set and
the TASKS/AGENTS size. Technical detail may grow in the
single notebook, but must use searchable topic headings, not repeated logs.
Machine-readable catalogs/release records/input scripts live under reference/.
Generated reports/captures and scratch scripts live in ignored work/ or build/;
a research tool worth reusing belongs in tools/ with a test.

Read AGENTS and TASKS at startup. Then list headings (`rg -n "^#" docs/TECHNICAL.md`)
and read only the relevant section. For combat/engine work start with TECHNICAL
"Player state machine and Red kit hooks" and "Research workflow and pitfalls".
Never bulk-read TECHNICAL, CHANGES, catalogs or the archive. Older exact notes are
in docs/archive/legacy-notes.zip; use `python tools/doc_archive.py list <topic>`
then `read <note> --toc/--section`. Update TASKS after milestones/before stopping,
replacing stale state; keep it under 900 words with concrete next actions and
evidence paths. Put shipped facts in CHANGES, research in TECHNICAL, design in
TASM_ROADMAP. Always distinguish implemented, agent-tested and player-confirmed.

## Tools, testing and release safety

- Read originals from original/, write builds to build/. Keep tools deterministic
  and scriptable in Windows PowerShell; prefer Python standard library.
- Every parser/repacker needs lossless round-trip tests. Preserve unknown bytes;
  call unknown fields unknown. Test one empirical change at a time with a control.
- Emulator research: `python tools/kit_lab.py` (training-room traces, story
  arena, qualification, clip previews, disassembly) with copied saves and
  disposable RAM. Check results numerically and look at captured frames.
- Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
  Agent manages builds/checkpoints; keep build/Spider-Man-WoS-modded.nds stable.
- Use the actual Battery directory in ignored work/playtest.json. Keep DeSmuME
  closed for save mutations/publication, verify DSV wrapper/snapshot bytes, and
  preserve latest progress/prior ROMs/active compositions. Re-read latest battery.
- Never write fixtures into the real save or load stale emulator states over a
  changed ROM.
- Qualify isolated candidates, compose all accepted overlays, publish through
  `python tools/playtest.py build`. Do not ask the player to manage filenames,
  backups or build commands. Record the release in CHANGES and reference/releases.json.
- Version is major.minor.patch: minor for new/overhauled mechanics, patch for
  fixes/polish/balance, major for a finished overhaul or incompatible contract.
  A published version identifies one exact ROM; never reuse it for different bytes.
  Show the same version at boot and in Options. Release profiles live in
  tools/release_info.py; the Red kit release generator is tools/tasm_kit.py.

## Current gameplay authority

2026-10-05 latest steering: FUN COMES FIRST. Garfield's Spider-Man is
spider-like, jumpy and acrobatic; the kit must combo strong enemies and
web-resistant bosses, hit behind as well as in front, and let R cancel combos to
reposition without losing them. Leave native abilities (A web, B jump, base
strings/evade) untouched; change behavior only by rewriting the 7 Red purchase
slots, gated on Red form and their ownership bits. v0.2.0 ships first versions of
Leapfrog, Skyjack, Spider Perch, Split Decision, Spin Cycle, Spider Reflex and
Spider-Sense (TASM_ROADMAP); iterate them from player feedback. More Red
skills/web tags later. Defer prices and balance unless the player asks.
2026-10-05: player confirmed v0.2.1/v0.3.0 "looks feels way better". Keep the game
super fast paced: no slow-motion or time-slowing effects (Spider-Sense included).
2026-10-06: no teleports (felt "teleporty", clipped out of the level, froze the
game): moves travel visibly; kit code moves Spidey by velocity only.
2026-10-06: player asked for the Test Upgrades sparring room (CHANGES v0.5.0).

New moves need new, fluid, acrobatic animations (not repackaged native clips).
The player rejected earlier per-key-eased clips as looking like dancing; follow
TECHNICAL "Kit animation authoring".

Develop one combined TASM1/2 kit at a time through red form. Selected later suits
remain in reference/suit_roadmap.json. Preserve native ownership/dependencies,
existing purchases, Both Suits traversal and Reinforced Web unless a deliberate
migration is implemented. Do not grant paid moves at start or steal black bits.
Expanded shop rows/save support and third suit selection remain research.
Fully enabled research uses copied saves/disposable RAM, never the real save.

Snap Sweep is player-confirmed. It borrows GroundAttack15 payloads; G11/16/17
also have m6.xbd users, so they are not spare storage; retain original IDs/other
actor bindings. Original Web Vault is player-confirmed. Never report attack
strength as HP damage or the combo gauge as hit count.
