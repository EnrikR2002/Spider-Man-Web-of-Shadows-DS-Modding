# Project tasks and session handoff

Updated: 2026-10-04 (America/Edmonton).

## Resume here

**Current release:** combat feedback + Rebound juggle revision, published under
`build/Spider-Man-WoS-modded.nds`. The user confirmed Web Vault works well.
Rebound now halves the previous horizontal impulse and increases vertical by
about 75%; damage/gates/player recoil remain native. DEALT/TAKEN show three recent
actual capped HP losses and a running SUM. COMBO shows the continuous native
meter value from zero, including Snap's 12 below the old 30 bar threshold.

ROM SHA256 `fe2be48f62999321edc4b67e3705268c21108e21b1d21efaeb6a07eaa1e7b432`.
ARM9 SHA256 `0cb23de19e5541393bbbe161b98c5104fc06570ba3c149c0f36ec4b2712903cb`.
86 tests pass; all 3,733 resources verified. Source commit title:
`Add combat feedback, Rebound juggle tuning, and expanded TASM roadmap`.
Real DSV before/after publication:
`9336ca4a3cbb3679ebf2fed31f796d6f8b9a93c9bb7d1faef8c8dd7f61b7861e`.
Named checkpoint `before-combat-feedback` preserves current progress; previous
Web Vault ROM retained in build/releases. Its source is 224c06d; Rebound 67caa5a.

**Player checks pending:** readability during real fights, ordinary incoming
hit readouts, Rebound pursuit/walls/ceilings, and special enemies/bosses. Controlled
native player HP calls render 25/25/25 ->75 correctly; do not describe this as an
AI-contact test. Damage panels are fixed HUD readouts. Enemy loss is not a formal
attacker-credit system; specialized health paths remain unaudited. Native training
dummy refills to 40 Q12 after defeat, so further capped hits can show 0.98. Damage
scale is 100 displayed HP per native unit; COMBO is meter amount, not hit count.
Full implementation/validation/limits: `COMBAT_FEEDBACK.md`.

**Next approved development:** Sling Strike, initially replacing Mid-Air Snare at
600 XP / event 324 / bit 15. Trace owned and locked native aerial input/action,
HP-loss budget and approach on a fresh save copy. Preserve free Snap Sweep,
shared traversal and current feedback. Do not run legacy generators over the
new default feedback recipe without explicitly composing it again.

Web Vault remains 200 XP / event 323 / bit 14: grapple with A (keyboard W), then Up.
Keep its early short window; future paid Air Catch/air control should make chains
reliable. Latest design is ONE combined TASM 1/2 kit, with twelve paid tools plus
Snap Sweep proposed in `TASM_EXPANDED_ROADMAP.md`. Additional tools/prices are
ideation, not implemented grants. Other ideas: `IMPROVEMENT_BACKLOG.md`.

## Active TASM 1 task list

- [x] Clean movie suit panels and black lenses; preserve accepted cosmetics/QoL.
- [x] Stable ROM/launcher, battery backups and named checkpoints.
- [x] Snap Sweep base opener; player confirmed working.
- [x] Map original gameplay, all 21 purchases, native combo meter and animation formats.
- [x] Rebound: purchase/refund, save carryover, facing and native credit checked.
- [x] Web Vault: implemented, agent-tested and player-confirmed.
- [ ] Sling Strike: replace Mid-Air Snare, 600 XP.
- [ ] Oscorp Rush: replace Spider Dance, 400 XP.
- [ ] Rebound Barrage: replace Scissor-Kick Special, 600 XP; retain dependency.
- [ ] Slip Counter: replace Amazing Speed Boost, 800 XP; engine research required.
- [ ] Momentum: replace Ultimate Speed Boost, 1,000 XP; retain dependency.
- [x] Player check for Web Vault in normal DeSmuME play; worked well.
- [x] Revised Rebound juggle response implemented; both facing directions/locked case agent-tested.
- [ ] Player check of revised Rebound juggle response.
- [x] Common enemy/player HP capture and recent-hit/running-total HUD; agent-tested with stated limits.
- [ ] Ordinary incoming contact, specialized health paths and display readability player checks.
- [x] Numeric combo readout; Snap COMBO 12 below 30 confirmed onscreen.
- [x] Combined TASM 1/2 expanded kit and impact/effort improvement list drafted for discussion.
- [ ] Agree on Air Catch as a separate purchase versus a Sling Strike extension.
- [ ] Independent additional shop rows/ownership/save migration research before expanding purchases.
- [ ] Proper native feedback toggle, actor-anchored numbers and stronger total styling.
- [ ] Broader walls/ceilings/bosses/interruption/long-play checks as the kit develops.
- [ ] Independent third suit selection; investigate without altering traversal.

## Selected suit backlog

Finish the combined TASM kit first. Then retain Scarlet Spider (Ben Reilly),
classic Spider-Man 2099, Scarlet Spider (Kaine), Raimi Spider-Man and classic
symbiote. TASM 2 identity is merged into the active kit; a cosmetic variant can
be discussed later. Exact selection is in `SUIT_ROADMAP.json`.

## Working rules and evidence

- Player flow: `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
  Agent handles releases and checkpoints. Keep the everyday ROM filename stable.
- Free Snap Sweep is accepted. Use native paid slots/costs/gates for the already
  approved incremental path. The latest user direction permits an expanded kit
  and different future prices; those remain design work until implemented safely.
  Existing ownership carries over. Preserve shared traversal/upgrades.
- Preserve the original ROM. Test isolated candidates with battery copies before
  promotion; never use a stale emulator state over changed assets.
- Approved scope/order: `TASM1_UPGRADE_PLAN.md` / `.json`.
- Original behavior: `ORIGINAL_GAMEPLAY.md`, `UPGRADE_ENGINE.md`, `COMBO_ENGINE.md`.
- Animation data: `ANIMATION_RESEARCH.md`, `FORMAT_NOTES.md`, `MODDABILITY_MATRIX.md`.
- Current release evidence: `COMBAT_FEEDBACK.md`; historical move evidence:
  `TASM1_WEB_VAULT.md` and `TASM1_REBOUND.md`;
  save workflow: `TESTING_WORKFLOW.md`.

## Session log

- 2026-10-04: recovered prior session and confirmed Web Vault is next. Added this
  tracker and an AGENTS.md read/update rule so future sessions have a durable handoff.
- 2026-10-04: released Web Vault. Preserved real battery bytes and previous ROM;
  81 tests plus isolated runtime checks pass. Next approved move: Sling Strike.
- 2026-10-04: player confirmed Web Vault. Released higher/closer Rebound plus
  actual HP recent-hit/SUM and numeric combo HUD. 86 tests pass; both facing and
  refund control, Vault regression, low-meter Snap, native controlled player
  health, menus/return cleanup and 10,000-frame resume pass. Preserved latest real
  save, checkpoint and previous ROM. Combined TASM roadmap and impact/effort
  backlog drafted. Next move stays Sling Strike; feedback player checks pending.
