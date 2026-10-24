# Current work and handoff

Updated 2026-10-24 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design and
player feedback.

## Current objective

Player requests on 2026-10-24, all delivered as documents and tooling; no game
artifacts changed and the published build is still v0.31.0. The player will
implement features in a later session; this session ends with everything
merged to main.

1. **2099 Black kit, revision 3: approved, not built.** ROADMAP "Spider-Man
   2099 Black kit: the Hunter" specifies 14 skills: the seven native Black rows
   reworked plus Web Yank, Reel In, Sky Rake, Meteor Catch, Roof Pin, Boarding
   and Apex Predator on free saved bits 83..89. Final player changes: Shockwave
   Talons at tier 3+, tier-5 Feeding Frenzy life steal (5% of HP dealt, banked,
   capped) and a visible upgrade per tier ending in a red suit glow. The section
   has a control map, rules, per-skill behavior, engine-fact links, gates, slice
   acceptance and build order; `reference/suit_roadmap.json` holds the rows.
2. **Repository sweep.** `docs/TASM_ROADMAP.md` became the whole-game
   `docs/ROADMAP.md` (old file archived). DEVELOPMENT explains the environment,
   how a release is built and how to add a feature as a post-pass. New tools:
   `run_tests.py`, `tool_index.py`, `doc_links.py`, `doc_archive.py add`.
3. **Drift protection.** `reference/doc_contract.json` is the machine-checked
   documentation contract (document set, word limits, required headings,
   routing, forbidden edits, one current version, frozen CHANGES sections,
   newest-first feedback log, 2099 catalog matching the ROADMAP table).
   `python tools/doc_contract.py check` enforces it; `tests.test_document_layout`
   runs one test per rule.

Evidence: in this ROM-less cloud workspace, `python tools/run_tests.py` passes,
counting tests that need the ROM, build/work files or Keystone as skips
(`--strict` shows them as the errors a full local setup would run). The archive
verifies and the documentation contract holds.

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

1. **2099 combat** is approved for a later session. In a workspace with the
   ROM and emulator, clear the ROADMAP gates on copied saves (own code/state
   block, Black shop rows, X and held-key inputs, Black-only clip routing, boss
   adapter) and build the Web Yank pipeline proof as the first published slice.
2. **v0.31.0 review:** the player plays Vortex and the larger boss through the
   normal launcher. Feel, appearance, full-route balance and DeSmuME pacing are
   open. Earlier environment acceptance does not imply enemy acceptance.
3. This cloud workspace has no ROM or emulator; nothing here was played or
   qualified in-engine.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
