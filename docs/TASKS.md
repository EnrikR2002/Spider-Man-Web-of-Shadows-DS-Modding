# Current work, backend queue and handoff

Updated 2026-10-05 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.2.1 published (stable `00ca471c`, profile tasm-v0.2.1):** the player called
the v0.2.0 kit "very good"; fixed their two complaints. Spin Cycle now aims each
contact, glides into reach, keeps spinning while steered, stops sliding on exit,
and uses straight blade legs instead of a breakdance V (CHANGES v0.2.1).
Agent-tested only: work/kit/evidence.json 23/23. Real save `75bb8efc...`
checkpointed. Next: the queued roadmap iterations below.

## Ordered next development

1. **Player playtest of v0.2.0** (Test Upgrades + real fights): feel of each
   skill, animation quality, crowd/boss behaviour. Ask whether Reflex/Sense should
   be cheaper (patch release; never grant them free).
2. **Iterate per TASM_ROADMAP "Status and next iterations"**: Spider-Sense timing,
   slow-mo and tingle; Perch exits/head-hopping/bosses; Reflex neutral flip and
   Enhanced Dodge interplay; Skyjack landing impact.
3. Measure heap headroom in dense rooms (reserve now 24 KiB) and other enemy
   attack states for Spider-Sense; record in TECHNICAL.
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
  `tools/kit_clips.py`; candidate `build/version-0.2.1` (regenerate:
  `python tools/tasm_kit.py`). Research/qualification: `tools/kit_lab.py`
  (inputs `reference/combat-inputs/kit/`; last evidence work/kit/evidence.json,
  23/23). Workflow and pitfalls: TECHNICAL "Research workflow and pitfalls".
  work/kit/ holds only old scratch from the first session; do not depend on it.
- Prior releases: v0.2.0 candidate build/version-0.2.0 (mods + recipe), ROM
  rollback build/releases/935d486b.../; v0.1.1 rollback build/releases/bcc6974a.../.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
