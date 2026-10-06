# Current work, backend queue and handoff

Updated 2026-10-05 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.3.0 published (stable `34736eeb`, profile tasm-v0.3.0).** Player said the
v0.2.0 kit was "very good" but the helicopter spin missed every other hit and
looked like breakdancing: fixed in v0.2.1 (aimed contacts, glide into reach,
any-direction repeats, blade legs). v0.3.0 then did the queued iterations: Perch
B flip-spring and A head-hop, neutral-R Reflex back tuck, Spider-Sense vs ranged
state 16; heap headroom measured (TECHNICAL). Agent-tested only:
work/kit/evidence.json 27/27. Real save `75bb8efc...` checkpointed (unchanged
since v0.2.1 publish).

## Ordered next development

1. **Player playtest of v0.2.1/v0.3.0:** does the spin now land every hit and read
   as a helicopter kick? Perch hop/spring on real crowds (head-hop was tested only
   against a lab phantom, so Y-chaining after a hop on a real enemy is unverified),
   back tuck feel, Sense against spitters. Ask if Reflex/Sense should be cheaper
   (patch; never free).
2. Remaining TASM_ROADMAP iterations: Spider-Sense timing/slow-mo/tingle; Perch boss
   shake-off and entry from jumps/walls; Skyjack landing impact/bowling (needs a
   way to hit other enemies: find the contact-damage call); Leapfrog vault before
   the kick; Spin Cycle exit flourish; Split Decision two-sided contacts (GMB).
3. Confirm enemy state 24 (action 41) as an attack; measure heap in a boss room.
4. Player feedback on incoming hits, walls/ceilings, HUD crowding and long play.
5. DeSmuME JIT/preload/renderer settings for reported hitches.

## Backend ideas retained

Independent shop rows/ownership/refund/save migration; third suit selector;
native HUD/accessibility settings; training timing/reset/quick retry; camera
tracking; enemy windups/fair anti-loop AI; room/encounter/BSP/OBJ editing; same-size
texture work, models/rigs and SDAT sound tools. Selected Ben Reilly/2099/Kaine/
Raimi/symbiote backlog is in reference/suit_roadmap.json, after the combined TASM
kit. Shared progression/traversal remain intact. Research/ideas are not releases.

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}`, `tools/kit_choreography.py`,
  `tools/kit_clips.py`; candidate `build/version-0.3.0` (regenerate:
  `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
  pitfalls); `assemble_tasm_kit.py` checks literals and native branches. Research/qualification: `tools/kit_lab.py`
  (inputs `reference/combat-inputs/kit/`; last evidence work/kit/evidence.json,
  27/27). Fixtures: `--near U`, `--phantom DX` (training), `--place` (arena). Workflow and pitfalls: TECHNICAL "Research workflow and pitfalls".
  work/kit/ holds only old scratch from the first session; do not depend on it.
- Prior releases (candidate mods + recipe in build/version-X, ROM rollback in
  build/releases/<sha>/): v0.2.1 `00ca471c`, v0.2.0 `935d486b`, v0.1.1 `bcc6974a`.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
