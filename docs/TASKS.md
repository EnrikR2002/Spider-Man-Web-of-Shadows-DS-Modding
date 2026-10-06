# Current work, backend queue and handoff

Updated 2026-10-06 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.5.0 (profile tasm-v0.5.0): Test Upgrades sparring room.** Player asked
(2026-10-06) for several enemies in training that hit back, with auto-heal.
Three Brutes added to `Test_Combat01_app.obj` (`tools/training_room.py`); kit
training logic (TECHNICAL "Training room (Test Upgrades, v0.5.0)"): Brutes get
the native training flag (defeat refills them, 8 HP units), Spidey heals every
30 s or on SELECT+Down and cannot die there. Red kit unchanged otherwise.
Published stable `fd7e4420`; agent-tested (qualification 31/31, crash hunt
12/12, sparring idle/fight runs in work/training/), not yet player-confirmed.
Real save `80c3ed12...` checkpointed before publication.
v0.4.1 (`da324b3c`) remains the previous stable: freeze fix, Sense dash,
continuous Leapfrog vault (CHANGES v0.4.1); its player playtest is still open.

## Ordered next development

1. **Player playtest of v0.5.0 sparring:** heal interval (30 s), Brute count
   and spacing, whether the passive dummy should also fight; offer the other
   training ideas below.
2. **Player playtest of v0.4.1 moves:** long crowd fights with Y/R/held-R spam (no
   freeze?), Sense dash feel and guard window, Leapfrog vault feel, Perch near
   walls; still open from v0.4.0: Skyjack bowling radius, Perch hop on real
   crowds, bosses.
3. Crowd play with the hit replay (TECHNICAL "Hit pipeline"): Spin Cycle hits
   enemies it passes through; Leapfrog kick-through (the popped enemy bowls the
   one behind him); *Stop Hitting Yourself*. Keep the pace fast.
4. Spider-Sense tingle: a marker over an enemy starting an attack behind or
   off-screen (no slow-motion). Needs a sprite/HUD hook (TECHNICAL HUD notes).
5. Remaining TASM_ROADMAP iterations: Perch boss shake-off and entry from
   jumps/walls; Leapfrog vault before the kick; Spin Cycle exit flourish and
   spin-to-launch; Split Decision two-sided contacts.
6. Confirm enemy state 24 (action 41) as an attack; measure heap in a boss room;
   run `tools/crash_hunt.py batch` in a boss room and a second level.

## New ideas to discuss with the player (2026-10-06)

Within the 7 Red slots (extensions, no new shop rows): air Reflex toward an enemy
becomes a web-zip hop to him (chain aerial hops between enemies, Lizard-fight
style); wall bounce: Reflex into a nearby wall rebounds into a flying kick;
Split Decision sweep launches into a short juggle; Skyjack finisher can be
steered into a chosen enemy; Perch spring lands into a dive kick. Needing shop
rows (research): web tags (tag now, yank later), web spray crowd stun, yank
objects/crates into enemies, Clap, Reel, Cocoon.

## Training room ideas offered to the player (2026-10-06)

Mixed enemy types (needs character-type ids and loaded assets), a wave
counter or timer challenge, a toggle for the passive dummy, enemy aggression
or count presets, a combo/damage readout, quick reset of positions.

## Backend ideas retained

Independent shop rows/ownership/refund/save migration; third suit selector;
native HUD/accessibility settings; training timing/reset/quick retry; camera
tracking; enemy windups/fair anti-loop AI; room/encounter/BSP/OBJ editing; same-size
texture work, models/rigs and SDAT sound tools. Selected Ben Reilly/2099/Kaine/
Raimi/symbiote backlog is in reference/suit_roadmap.json, after the combined TASM
kit. Shared progression/traversal remain intact. Research/ideas are not releases.

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}`, `tools/kit_choreography.py`,
  `tools/kit_clips.py`, `tools/training_room.py`; candidate
  `build/version-0.5.0` (regenerate: `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
  pitfalls); `assemble_tasm_kit.py` checks literals and native branches. Kit code
  never writes positions and checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs `reference/combat-inputs/kit/`;
  evidence work/kit/evidence.json, 31/31). Fixtures: `--near U`, `--at X`,
  `--phantom DX`, `--place DX:DY|skip` (training and arena; arena is
  non-deterministic). Lab teleports now use `kit_lab.teleport` (motion base and
  probes); older lab runs corrupted the heap. Freeze/crash hunting:
  `python tools/crash_hunt.py batch FIRST LAST --rom R` (outputs work/crash/),
  `regs STATE --ram RAM` decodes aborts. Workflow: TECHNICAL "Research workflow".
- Prior releases (candidate mods + recipe in build/version-X, ROM rollback in
  build/releases/<sha>/): v0.4.1 `da324b3c`, v0.4.0 `5e6465d8` (freeze bug), v0.3.0 `34736eeb`,
  v0.2.1 `00ca471c`, v0.2.0 `935d486b`, v0.1.1 `bcc6974a`. All kit releases before
  v0.4.1 carry the Sense heap bug; do not roll back to them.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
