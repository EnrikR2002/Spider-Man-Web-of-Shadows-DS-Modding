# Current work, backend queue and handoff

Updated 2026-10-05 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.2.0 published (stable `935d486b`, profile tasm-v0.2.0):** all seven Red
slots rewritten as the "never stand still" kit (TASM_ROADMAP, CHANGES): Leapfrog,
Skyjack, Spider Perch, Split Decision, Spin Cycle, Spider Reflex, Spider-Sense,
with nine new authored clips. Prices/ownership unchanged. Agent-tested only:
work/kit/evidence.json 20/20 (training dummy; Spider-Sense also vs live
symbiotes), unowned and Black play match v0.1.1; 149 source tests pass. Real save
`3f65dfac...` owns bits 13-17 (five kit skills live) but not 18/19, and has 4 XP:
Reflex costs 250, Sense 350. Player feel/crowds/bosses not yet confirmed.

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
  `tools/kit_clips.py`; candidate `build/version-0.2.0` (regenerate:
  `python tools/tasm_kit.py`). Research tools in `work/kit/`: trace.py (training
  room, `--bits/--clear-bits/--enemy-state`), arena.py (Sewer room left of save,
  teleport incl. actor copies), qualify.py, clip_preview.py, author_clips.py.
- Prior release: build/version-0.1.1, recipe copy work/kit/prior-gameplay-profile-
  v0.1.1.json, ROM rollback build/releases/bcc6974a.../.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
