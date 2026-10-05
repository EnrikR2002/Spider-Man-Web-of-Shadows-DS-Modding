# Sling Strike: purchased aerial zip-and-kick replacement

Historical initial release. Current player-feedback fixes and limits: `COMBAT_FLOW.md`.

2026-10-04. Implemented and agent-tested; player feel/acceptance remains pending.
Replaces Mid-Air Snare at the original 600 XP / event324 / bit15 purchase. Existing
ownership carries over; the latest real save does not own it and is not edited.
Shared air/traversal upgrades and free Snap/normal aerial attacks stay native.

## Use and budget

In mid-air, press A near a valid enemy. The native web approach/target checks
still apply. The paid zip follow-up now uses AirAttack3's existing kick instead
of playing all three aerial clips. The confirmed kick carries Spider-Man a short
distance through the target, then stops horizontal travel for a normal landing.
There is no extra jump, airtime reset, invulnerability or extended targeting range.
Missing the kick gives no passing burst. Native resistance rules still apply.

The tested native string requested 409 + 4096 + 4096 + 4096 Q12 HP loss. Sling keeps
the zip's 409 and consolidates the three follow-ups into a 12288 request on the
single kick: **12697 Q12 total in either case**, before target health capping.
The dummy has only 4096 HP, so its capped losses are not a full damage-budget
measurement; private telemetry distinguishes request from actual available loss.
No player-facing damage number is drawn. Nonstandard reductions/health paths
are deliberately outside the exact 4096->12288 adjustment and need further checks.

## Bounded engine edits

Own code lives at 02150F20/02151120/02151320 inside unused extension space.
The 600-hexadecimal-byte authored stubs are stored as pinned text hex; ordinary
PowerShell/Python builds need no assembler. Optional source reassembly uses
Keystone from the ignored research library directory.

- 020728F0 action queue: only the Spidey vtable, owned bit15, native paid zip
  state31 or state51 entered from31, valid target and requested action1 can
  substitute action3. It marks that actor for this paid follow-up. Ordinary Y
  air attacks are not globally rebound; all GMB/SCA/GAB and XBD assets stay exact.
- 0209515C common enemy contact: match the actual source actor to that marker,
  current action3/state51 and exactly 4096 requested loss, then request12288 and
  arm one bounded movement window. The light zip hit and unrelated contacts stay
  unchanged. This is a contact hook, not automatic damage or a free attack grant.
- 02073B5C after native controller update: use the native actor horizontal
  velocity and existing collision processing for at most three advancing steps
  of 16384 Q12. A fourth step/recovery stops it. Vertical velocity, gravity and
  room coordinates are not overwritten. Normal air recovery stops residual
  travel; other queued actions clear the marker. Null controllers are guarded.
- 02049330: training-only refill instruction reads actor+48 max HP instead of
  assigning40. Its native training-flag/death conditions are unchanged.
- The authored HUD constructor clears through own state+700, including the new
  actor/countdown/confirmation marker at +680. No ownership/save storage is added.

Original input selectors, paid queries, approach/collision helper and all 21
purchase records are byte-identical. The build rejects unknown/double-applied
profiles or changed expected instructions. Edit/revert restores the compact HUD
ARM9 exactly, and the underlying HUD extension round-trips to the accepted Vault.

Final ROM SHA256:
`92f4aa29cddf77e69f986b39a5ac8e181bbc1a0dca66d830055bc046888ae3d3`.
Final ARM9 SHA256:
`761feb4416bb80eb815c3d0d287265ae31b39ed5578dffd86005cce4badc3306`.
Own Sling code SHA256:
`a2f168a4db19363ca25b37c7f91d63e378b5291426d2f878bf2a687a3f1589d9`.

## Private runtime evidence and remaining checks

Replay inputs are under `reference/combat-inputs/sling-*.json`; binary RAM/images,
ROMs and battery captures stay ignored in build/work. Purchase tests use an
isolated RAM-only XP fixture at frame2040 (1000 XP), then the actual native menu
and save routine. It never changes a source battery or grants ownership directly.
Fixture source: `work/hud-sling/fixture_smoke.py`.

- Native purchase: 1000->400 XP sets only bit15; Rebound/Vault remain owned.
- Native refund: captured owned save400->1000 clears bit15; same input no longer
  enters the paid kick/flight. No save editor was used.
- Native Save Complete then fresh reload preserves bit15/400 XP and the move.
  Battery evidence: `SlingStrike-8897a7aa/sling-purchase-save/battery-03100.sav`;
  final `SlingStrike-92f4aa29/balanced-save-reload` boot observes bit15/400 XP,
  paid action3 and requested409/12288 after a fresh load.
- Final movement response in `SlingStrike-617f8068/accepted-right` lands at
  X156.17, beyond the initial target; the left mirror also passes and lands.
  These movement checks used the preceding 8192-kick budget. The final 12288
  budget replay retains the same short movement code and returns to idle.
- Constructor/free-route replays `accepted-right`, `accepted-locked` and
  `accepted-free-air` under617f8068 cover the constructor cleanup and ownership/free-route
  guard. Standard Y remains the normal aerial route.
- Full-health paired test: RAM-only dummy HP/max16384 in both controls. Native
  `CompactHud-5fc6bfd3/native-budget` and final `balanced-budget` both lose12697
  and retain3687, proving the uncapped complete attack budget. Final native save
  reload evidence is `balanced-save-reload`; source fixtures remain in ignored work.
  Final observations are collected in `work/hud-sling/final-evidence.json`.
- 92 tests pass; all 3,733 resources verified; native save wrapper/progress bytes
  preserved by the stable publication workflow.

Actual wall/ceiling/interruption/boss and long-play checks remain open. A disposable
wall-position fixture moved the actors beyond the training floor and fell; it
was invalid for a wall check and is excluded from acceptance. A stronger travel
prototype caused a long landing roll and was rejected. The accepted move uses
the short passing window/recovery above. No player confirmation is claimed.

Next approved replacement: Oscorp Rush / Spider Dance, 400 XP. Air Catch and
Orbit Breaker remain separate proposals in TASM_EXPANDED_ROADMAP, not new grants.
