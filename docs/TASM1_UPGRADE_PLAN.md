# TASM 1 purchased-upgrade replacement proposal

2026-10-04. Latest direction: [one expanded TASM 1/2 kit](TASM_EXPANDED_ROADMAP.md)
with 10+ paid tools and flexible prices; additions remain ideation. This document
retains the approved incremental native-slot path. Rebound's new higher/closer
launch and current damage/combo feedback are documented in COMBAT_FEEDBACK.md.

**Approved by the user; Rebound and Web Vault implemented; five entries pending.**
The inventory below was collected before implementation. Current release evidence
is in [TASM1_WEB_VAULT.md](TASM1_WEB_VAULT.md) and [TASM1_REBOUND.md](TASM1_REBOUND.md). Snap Sweep was confirmed working by
the user and remains the free base opener.

## Inventory and proposed replacements

The actual Red upgrade menu has seven purchasable entries. Names/descriptions
were checked against the clean English/American strings and prices observed in
the running, unchanged stage-one ROM using an isolated copy of current progress.
The costs below are native costs, not newly assigned prices. List order matches
the menu. All replacement names fit their existing compressed name slots.

| Original upgrade | Cost | Proposed TASM name | Change and equivalent-role tradeoff |
|---|---:|---|---|
| Web Kick | 100 | **Rebound** | Keep a grapple-to-kick follow-up with the same damage budget. Spider-Man recoils a short distance after contact; the enemy launches closer and higher. Gains a possible juggle window, loses crowd separation. No automatic chase, extra hits or invulnerability. |
| Web Launch | 200 | **Web Vault** | Launch the grappled target and follow with a short vault. Preserve the original enemy launch height/damage ceiling; the follow adds no hit. Gains aerial pursuit, loses the safety of remaining grounded. Air Dodge and other shared upgrades still need their own purchases. |
| Mid-Air Snare | 600 | **Sling Strike** | Replace the aerial zip/combo with a committed fly-by kick that passes to the target's far side when space permits. Match the original total damage budget; trade sustained target control for repositioning. No extra target range, airtime resets or repeated free hits. |
| Spider Dance | 400 | **Oscorp Rush** | Replace the purchased pause-input combo with a compact advancing kick/strike string and a focused finisher. Keep its input family and comparable duration/total damage; narrower coverage is exchanged for forward pressure. It does not grant a free launcher or the Scissor extension. |
| Scissor-Kick Special | 600 | **Rebound Barrage** | Replace the purchased rapid-kick extension with a finite close-range flurry and retreating finish. Staying in earns the comparable native full-string damage; disengaging early sacrifices remaining hits. Preserve the parent-combo relationship. Retreat movement adds no dodge invulnerability. |
| Amazing Speed Boost | 800 | **Slip Counter** | Exchange part of the permanent attack-speed benefit for a manual post-evade counter opportunity. Ordinary attacks gain less speed than the original upgrade; a correctly timed evade enables one quicker normal-damage punish/recovery. No auto-hit, added damage multiplier or larger invulnerability window. Requires actual dodge/hit/timing research. |
| Ultimate Speed Boost | 1,000 | **Momentum** | Replace always-on maximum speed with conditional flow after a clean string, a paid web hit or Slip Counter. Flow briefly reaches the original maximum-speed ceiling and permits one bounded hit-confirmed evade cancel; getting hit or whiffing drops it. Loses permanent speed, gains conditional control. No stacking damage, infinite refresh or new invulnerability. Cancel benefit must be checked against the existing game. |

These are design budgets, not verified damage/speed equivalence. First measure
native hit count, total damage, reach, stagger, recovery and speed tiers against
the same enemy before tuning a replacement. A low-cost web follow-up should not
become a full launch/air-combo package; that package is assembled through several
separate purchases. The expensive speed passives are valuable upgrades, so their
replacements should be implemented last and compared carefully.

Approved incremental build order: **Rebound -> Web Vault -> Sling Strike ->
Oscorp Rush -> Rebound Barrage -> Slip Counter -> Momentum**. Deliver one at a
time with its own locked/unlocked checks and playtest checkpoint.

## What remains outside these seven replacements

- **Both Suits:** Launching Uppercut, Enemy Kick-Off, Drill Kick, Jackhammer Stomp,
  Enhanced Dodge, Air Dodge and Quick Recovery remain shared upgrades. Do not
  repurpose them as red-only skills or grant their functions through Web Vault.
- **Core red tools:** Web Grapple, Web Zip and Web Pull keep their existing roles.
  They are the foundation for using the purchased web follow-ups, not new gifts.
- **Reinforced Web:** retain heavy-object breaking and its existing acquisition
  gate. Clean message 377 confirms it unlocks blocked paths. It must not be traded
  for a combat-only ability; a cosmetic TASM label can be considered separately.
- Black/white-form moves and stat/collectible upgrades are outside this proposal.

## Purchase and save contract

Each move uses the purchase flag of the slot it replaces. Preserve native prices,
story availability and existing prerequisites. Owning Web Kick in an old save
means owning Rebound after the replacement; it does not earn the other six moves.
No save reset, new persistent layout or forced refund. Exact flag/cost/requirement
addresses and native dependencies are now mapped in UPGRADE_ENGINE.md.
Rebound reuses bit 13 and the native 100-XP price; no persistent layout changed.

Descriptions, list titles and tooltip titles all change together when the actual
behavior ships. Rebound and Web Vault descriptions fit and were checked in-game; future entries
still need their own wrapping checks. Keep locked behavior and native button glyphs.

Snap Sweep currently binds the base GroundAttack11 action to GroundAttack15's
SCA/GMB/GAB resources. The original paid action also references those resources.
Do not modify that shared payload to implement an upgraded move. Preserve the
free opener and change the purchased logical route separately. Distinguishing
animation reuse from input/purchase routing is essential to enforcing the gates.

## Acceptance for every approved entry

1. New-game/unowned slot cannot invoke the replacement through its own input or
   an alternate attack, dodge, air, wall or combo route. Base Snap Sweep still works.
2. Correct purchase enables only the replacement for that slot, costs the native
   amount, and respects prerequisite/availability checks.
3. Existing ownership carries over. Save/reload retains ownership and progression;
   returning an upgrade, where supported by the native menu, relocks its behavior.
4. Same-enemy comparisons establish similar total damage/clear-time budgets and
   verify the promised positional/commitment tradeoff. Boss resistance is retained.
5. Shared upgrades, alternate-form behavior, traversal and room exits remain valid.

## Evidence and limits

Historical stage-one inventory ROM hash:
`3c7ec9a5342a80bc20d6b9d058b2b8bfa029ee670d9d42b50a0642122fa9907c`.
This pass's current-save copy hash:
`3367385a2fa73ee66b0c6b601a3e1d0acab04595762a169f5f1c0795f84ad183`.
The ROM is unchanged; the audit never writes to the real save. Its bytes changed
independently during the audit, so the latest closed-emulator version is preserved
separately instead of restoring this earlier research copy. Audit files remain private
in `work/upgrade-research/` and `build/boot-tests/Spider-Man-WoS-modded-3c7ec9a5/`.
Red tab images: `red-skill-inventory/frame-02170.png`, `frame-02490.png`,
`frame-02690.png`. Shared tab audit: `shared-skill-audit/`.

IDs and proposed targets are persisted in `TASM1_UPGRADE_PLAN.json`. Subsequent
research mapped all 21 purchase records, ability bits and dependencies in
UPGRADE_ENGINE.md and ORIGINAL_GAMEPLAY.json. Speed percentages and counter/flow
handlers remain research beyond the existing synchronized action rebind helper.


Rebound and Web Vault release evidence: TASM1_REBOUND.md / TASM1_WEB_VAULT.md. The remaining five
entries keep their original names and behavior until their actual replacements
are implemented and tested. The original damage/speed budgets stay a requirement.
