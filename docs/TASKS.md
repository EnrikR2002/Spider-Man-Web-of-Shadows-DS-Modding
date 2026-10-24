# Current work and handoff

Updated 2026-10-24 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design and
player feedback.

## Current objective

Two player requests on 2026-10-24, both delivered as documents and tooling; no
game artifacts changed and the published build is still v0.31.0.

1. **2099 Black kit, revision 3 (designed, not built).** The player approved X
   for webs and the revision 2 kit, removed Collar Toss and Lariat, and asked
   for one skill that rewards a full combo meter like Red's Momentum and
   Overclock. ROADMAP "Spider-Man 2099 Black kit: the Hunter" now specifies 14
   skills: the seven native Black rows reworked plus Web Yank, Reel In, Sky Rake,
   Meteor Catch, Roof Pin, Boarding and Apex Predator on free saved bits 83..89.
   Each skill lists input, mob and boss behavior, and fallthrough; the section
   adds a control map, rules, engine-fact links, gates, slice acceptance and a
   build order. `reference/suit_roadmap.json` holds the rows.
2. **Repository sweep for faster agent work.** `docs/TASM_ROADMAP.md` became
   `docs/ROADMAP.md`, a whole-game roadmap (Now table, 2099 spec, Red kit,
   chapters, idea backlog, feedback log). The old file is archived byte for byte
   as `docs/TASM_ROADMAP-2026-10-24.md`. DEVELOPMENT gained "Know your
   environment", "How a release is built" and "Add a feature as a new
   post-pass". New tools: `run_tests.py` (fresh-clone-aware test runner),
   `tool_index.py` (tool finder), `doc_links.py` (link/anchor checker, also run
   by the document test) and `doc_archive.py add`. AGENTS was condensed, the
   duplicated v0.30.3 CHANGES section removed and run-together words fixed.

Evidence: in this ROM-less cloud workspace, `python tools/run_tests.py` passes,
counting tests that need the ROM, build/work files or Keystone as skips;
`--strict` shows the 121 errors that need a full local setup. The archive
verifies and every local doc link and anchor resolves.

## Published build

The stable `build/Spider-Man-WoS-modded.nds` is **v0.31.0**, published on
2026-10-22 through `tools/playtest.py build`. The accepted candidate, a
normal-source rebuild and the installed stable ROM have the same hash. Recipe,
release pins, boot/Options version and full evidence are in
`reference/vortex_forge.json`; the previous ROM and recipe are retained.

At publication the latest actual battery was read before and after; its DSV
wrapper, payload and publication checkpoint matched. A fresh native Continue
kept abilities, XP, initial HP and checkpoint. No research save was adopted.

## v0.31.0 contents (agent-tested, player verdict open)

- **Vortex:** web an enemy with A or Dragnet, release A, then Down+Y. Up to four
  real cocoons are tethered, swung through a two-turn catapult and slammed down.
  R or getting hurt interrupts cleanly; movement uses native velocity and
  collision. Unwebbed, unowned, Black-form and stale-pointer controls pass.
- **Conductor:** larger articulated symbiote war-machine armor at 1.28x scale,
  a boss-only texture and only the native top boss meter. All 39 private motion
  timings and native attacks, AI, HP, audio and collision are unchanged; the
  player liked this fight's behavior.
- **Vitality:** damage is now scaled before the final HP clamp, fixing the
  low-HP case where eleven old-build hits were needed instead of one. 26 tests
  cover 256 damage combinations; a Red boss win, save and fresh Continue pass,
  and a Black control earns a win and save without refills.

## Blockers and next exact action

1. **2099 combat** waits for the player's go on revision 3. Then, in a
   workspace with the ROM and emulator, clear the ROADMAP gates on copied saves
   (own code/state block, Black shop rows, X and held-key inputs, Black-only
   clip routing, boss adapter) and build the Web Yank pipeline proof as the
   first published slice.
2. **v0.31.0 review:** the player plays Vortex and the larger boss through the
   normal launcher. Feel, appearance, full-route balance and DeSmuME pacing are
   open. Earlier environment acceptance does not imply enemy acceptance.
3. This cloud workspace has no ROM or emulator; nothing here was played or
   qualified in-engine.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
