# Project tasks and session handoff

Updated: 2026-10-04 (America/Edmonton).

## Resume here

**Current state:** Web Vault is implemented, agent-tested and published. Player
acceptance is pending. It replaces Web Launch at native 200 XP / event 323 / bit 14.
Grapple with A (keyboard W), then Up: launch the enemy and follow with a short vault.

**Last completed release:** Web Vault + Rebound in `build/Spider-Man-WoS-modded.nds`.
ROM SHA256 `bd94b6f9f8a8a1d8566aca4da284ba4c150ac675cd62ce6afb405a6e9be8c092`.
81 tests pass; owned/refund/repurchase/native-save-reload/facing/miss/air follow,
Rebound regression, alternate-form control and
paired native launch checks pass. Checkpoint `before-web-vault` retains the real save.
Earlier Rebound source commit: `67caa5a`. Player-confirmed move: Snap Sweep only.

**Immediate next development:** Sling Strike, replacing Mid-Air Snare at 600 XP /
event 324 / bit 15. First trace its owned and locked native aerial input/action,
hit budget and approach on a current save copy. Keep free Snap Sweep and shared
skills intact. Read `TASM1_WEB_VAULT.md` before any further engine-profile edit.

## Active TASM 1 task list

- [x] Clean movie suit panels and black lenses; preserve accepted cosmetics/QoL.
- [x] Stable ROM/launcher, battery backups and named checkpoints.
- [x] Snap Sweep base opener; player confirmed working.
- [x] Map original gameplay, all 21 purchases, native combo meter and animation formats.
- [x] Rebound: purchase/refund, save carryover, facing and native credit checked.
- [x] Web Vault: research/build/test/publish; player acceptance remains below.
- [ ] Sling Strike: replace Mid-Air Snare, 600 XP.
- [ ] Oscorp Rush: replace Spider Dance, 400 XP.
- [ ] Rebound Barrage: replace Scissor-Kick Special, 600 XP; retain dependency.
- [ ] Slip Counter: replace Amazing Speed Boost, 800 XP; engine research required.
- [ ] Momentum: replace Ultimate Speed Boost, 1,000 XP; retain dependency.
- [ ] Player checks for Rebound and Web Vault in normal DeSmuME play.
- [ ] Broader walls/ceilings/bosses/interruption/long-play checks as the kit develops.
- [ ] Independent third suit selection; investigate without altering traversal.

## Selected suit backlog

Finish TASM 1 first. Then retain Scarlet Spider (Ben Reilly), classic Spider-Man
2099, Scarlet Spider (Kaine), Raimi Spider-Man and classic symbiote. TASM 2 is a
secondary interest. Exact selection is in `SUIT_ROADMAP.json`.

## Working rules and evidence

- Player flow: `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
  Agent handles releases and checkpoints. Keep the everyday ROM filename stable.
- Free Snap Sweep is accepted. Every new move replaces a paid Red slot at its
  original cost/gates; owned native skills carry over. Preserve shared upgrades.
- Preserve the original ROM. Test isolated candidates with battery copies before
  promotion; never use a stale emulator state over changed assets.
- Approved scope/order: `TASM1_UPGRADE_PLAN.md` / `.json`.
- Original behavior: `ORIGINAL_GAMEPLAY.md`, `UPGRADE_ENGINE.md`, `COMBO_ENGINE.md`.
- Animation data: `ANIMATION_RESEARCH.md`, `FORMAT_NOTES.md`, `MODDABILITY_MATRIX.md`.
- Current release evidence: `TASM1_WEB_VAULT.md` and `TASM1_REBOUND.md`;
  save workflow: `TESTING_WORKFLOW.md`.

## Session log

- 2026-10-04: recovered prior session and confirmed Web Vault is next. Added this
  tracker and an AGENTS.md read/update rule so future sessions have a durable handoff.
- 2026-10-04: released Web Vault. Preserved real battery bytes and previous ROM;
  81 tests plus isolated runtime checks pass. Next approved move: Sling Strike.
