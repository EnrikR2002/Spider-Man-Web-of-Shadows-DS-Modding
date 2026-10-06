# Current work, backend queue and handoff

Updated 2026-10-05 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.4.0 published (stable `5e6465d8`, profile tasm-v0.4.0).** Player confirmed
v0.3.0 ("looks feels way better") and set a rule: keep it super fast, no
slow-motion (AGENTS). v0.4.0: the Skyjack spike now bowls enemies near the
landing with a native knockdown hit, using a new hit-capture/replay primitive
(TECHNICAL "Hit pipeline"). Agent-tested: work/kit/evidence.json 28/28 plus arena
runs (bowl fired when an enemy was within 8 units). Real save `75bb8efc...`
checkpointed (unchanged: the player has not saved in-game since v0.2.1).

## Ordered next development

1. **Player playtest of v0.4.0:** Skyjack bowling feel/radius in real crowds;
   Perch hop Y-chaining on real enemies (only lab-phantom tested); bosses.
2. Use the hit replay for more crowd play: Spin Cycle hitting enemies it passes
   through, Leapfrog kick-through, *Stop Hitting Yourself*. Keep the pace fast.
3. Remaining TASM_ROADMAP iterations: Spider-Sense timing and tingle marker (no
   slow-motion); Perch boss shake-off and entry from jumps/walls; Leapfrog vault
   before the kick; Spin Cycle exit flourish; Split Decision two-sided contacts.
4. Confirm enemy state 24 (action 41) as an attack; measure heap in a boss room.
5. Player feedback on incoming hits, walls/ceilings, HUD crowding and long play.

## Backend ideas retained

Independent shop rows/ownership/refund/save migration; third suit selector;
native HUD/accessibility settings; training timing/reset/quick retry; camera
tracking; enemy windups/fair anti-loop AI; room/encounter/BSP/OBJ editing; same-size
texture work, models/rigs and SDAT sound tools. Selected Ben Reilly/2099/Kaine/
Raimi/symbiote backlog is in reference/suit_roadmap.json, after the combined TASM
kit. Shared progression/traversal remain intact. Research/ideas are not releases.

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}`, `tools/kit_choreography.py`,
  `tools/kit_clips.py`; candidate `build/version-0.4.0` (regenerate:
  `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
  pitfalls); `assemble_tasm_kit.py` checks literals and native branches. Research/qualification: `tools/kit_lab.py`
  (inputs `reference/combat-inputs/kit/`; last evidence work/kit/evidence.json,
  28/28). Fixtures: `--near U`, `--phantom DX` (training), `--place DX:DY|skip`
  (arena; non-deterministic, retry until the scenario happens). Workflow and pitfalls: TECHNICAL "Research workflow and pitfalls".
  work/kit/ holds only old scratch from the first session; do not depend on it.
- Prior releases (candidate mods + recipe in build/version-X, ROM rollback in
  build/releases/<sha>/): v0.3.0 `34736eeb`, v0.2.1 `00ca471c`, v0.2.0 `935d486b`,
  v0.1.1 `bcc6974a`.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
