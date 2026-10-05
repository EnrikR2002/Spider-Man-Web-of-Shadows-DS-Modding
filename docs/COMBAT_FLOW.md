# Combat flow revision: player-feedback fixes

2026-10-04. Implemented and agent-tested; new player feel/lag acceptance pending.
Profile `tasm-combat-flow` composes every accepted overlay and the historical
Sling release. Stable publication uses the same ROM/launcher and preserves saves.

## Player behavior and confirmed cause

The player correctly recalled Mid-Air Snare's native airborne web dash followed
by several attacks. The first Sling release kept that entry and changed its
follow-up, but the short pass did not distinguish the feel enough. The revision
keeps native targeting/purchase rules and gives the confirmed kick a visible
pass to the target's far side, followed by a clean stop and turn back. It is a
repositioning strike, not a new targeting mode. The dash/stock kick assets are
reused; no new animation is claimed. Misses earn no passing burst.

Web Vault now launches Spider-Man alongside the common enemy he successfully
launches. The old hop helper produced a smaller impulse; native response37
provides14336 Q12 vertical and1434 horizontal toward the player in the measured
case. The revision waits for native successful dispatch, invokes the normal hop
helper, copies the target's actual positive vertical impulse and zeros its
horizontal drift. Native gravity/collision remain. Existing ten-unit approach
root, damage, resistance rules and 200-XP bit14 contract remain. Use A grapple,
Up, then press A again in mid-air for the purchased 600-XP Sling follow-up.

The split bar was a confirmed layout bug: the native canvas consumes pixels by
columns, while the earlier bitmap supplied rows. Each bar now has one 22-pixel
interior inside a 24x4 black border: one red run followed by gray remaining
space. Living targets below pixel resolution retain one red pixel. Full/dead
and offscreen targets remain hidden, subject to the bounded snapshot expiry.

## Bounded code and state

- `tools/combat_flow.py/.hex` apply only to the exact historical Sling ARM9.
  All GMB/SCA/GAB, purchase records and shared traversal/input routes stay exact.
  Only English/American188/191 instructions change in this overlay composition.
- The original five Web Launch dispatch words at020C9268 are restored. The new
  post-dispatch hook020C9314 branches to02151520. It accepts Red state40, bit14,
  Spidey's known vtable, native result4 and the common target health ABI. Other
  result codes/health classes are not guessed. Native result4 is an observed
  accepted contact; this does not define the whole result enumeration.
- Sling keeps logical action3, requested409 zip +12288 kick =12697 Q12 total.
  Its marker at state+680 now also stores contact targetX, original direction
  and targetX +/-20 game units. At most seven advancing physics steps supply
  +/-5 units through native collision. Reaching the destination, timeout or
  landing stops residual travel. It turns through native02072860 only after
  actually crossing the contact target position. Other queued actions clear
  the marker; incoming hit behavior stays native. Fall/landing transitions are
  deliberately handled before the motion action finishes changing.
- The cheap observer at02151920 rejects HUD-disabled, unsupported and full/dead
  actors before entering the prior full snapshot observer02150B20. Snapshot
  rendering still dereferences no stored actor pointer. The Sling targetX is
  copied at contact, not followed through an unsafe retained target object.
- Own code/source size remains3600 hexadecimal; reserved heap remains4000.
  HUD ctor clears own state through+700. Rectangle count+6A0, numeral+6A4,
  counters+6B0..6BC, projection cache+6C0..6C8 and nine 8-byte rectangles+700
  remain within the reservation. No game ownership/save storage is introduced.

## HUD work and performance evidence

Rendering runs every second native HUD update (about15 Hz); game logic and
animation timing are unchanged. Expiry still counts every native HUD update.
Empty HUDs return without constructing/flushing a canvas. The stock font is
warmed on the first room HUD update, avoiding first-hit asset initialization.
Only cells in previous owned rectangles are checked/cleared, preserving native
text. Projection cotFOV/aspect is cached once per draw pass.

Native Canvas+18 stores maximum drawn height, used by its final flush. SetXY
flushes the previous shape, but keeps that maximum. Mixing a numeral with a
shorter bar initially allocated tail tiles outside the tracked four-row region;
a moving-camera replay caught fragments. After SetXY, the revision resets the
new bar's height accumulator before its four-row bitmap call. Clean moving bars,
idle clearing and native pause text were visually checked before publication.

A typical clean Snap replay at HUD tick363 uses65 draw passes and1668 cell checks,
versus the old full-screen scan of768 cells every HUD update. The latest real
save's idle Continue replay had637 HUD updates with zero draw passes/projections
and zero cleared cells. These are work counters, not measured FPS gains.

Serial same-core software benchmarks sampled501 retro_run calls (frames3000..3500):
old mean4.098 ms, median4.385, p95 5.299; revised pre-final means4.109/4.131 ms,
medians4.434/4.451, p95 5.269/5.259. This is roughly flat overall; it does not
prove the reported DeSmuME hitches came from bars or are eliminated. Later replay
runs with concurrent tests are excluded from performance claims. Real DeSmuME
settings were inspected but not changed; renderer enum semantics were not guessed.
Dense actual encounters/scene transitions remain the next lag investigation if
player reports it again. Synthetic or training checks are not normal AI coverage.

## Validation and private evidence

96 tests pass (92.162s), including exact edit/revert, native records/input/damage
preservation, SDK layout, reserved-state bounds and unrelated text-slot preservation.
All3733 resources verified. `work/combat-flow/final-evidence.json` records checks.

Final evidence root: `build/boot-tests/CombatFlow-c700f3b5/`:

- `final-chain`: native purchase1000->400 sets bit15; maxHP16384 RAM-only training
  fixture permits uncapped budget measurement. Vault player/enemy height delta
  is205 Q12 (under0.051 units), equal vertical velocities and zero enemy X drift
  through the pre-Sling window. Full Vault/Sling chain leaves615 HP; Sling itself
  requests12697. Passing stops and faces back at frame3271; final X165.242.
- `final-sling-left`: same409/12288 requests, mirrored pass, stops/turns right,
  lands at X120.303. No long residual landing roll.
- `final-locked`: no bit15, no enemy loss or passing marker. `final-vault-left`
  confirms owned bit14 launch on the opposite side; earlier unchanged Vault code
  negative control is `CombatFlow-79882e1d/vault-locked` (native refund clears14).
- `final-owned-free`: fresh boot of the isolated native purchased battery retains
  bit15/400 XP; ordinary Y stays action1/request4096 with no Sling marker.
- `CombatFlow-3871e3d9/clean-hud` and `clean-chain`: continuous bar, camera-motion
  cleanup, idle zero-rectangle return and native pause; final-chain inspects the
  added one-pixel low-health indication. Earlier invalid wall-position fixture
  remains excluded. Actual walls/ceilings/bosses/interruption/density remain open.
- `CombatFlow-d160f66d/latest-continue`: actual latest progress copy resumes Sewer,
  owns the three Red replacements,417 XP and red mission marker; idle draw work0.
  No artificial progress is put into the real battery. No normal AI hit is claimed.

ROM SHA256 `c700f3b5bbf1d05d2c4d1b61da6256129c3a2e91648068b4f6a237aea99e09cf`.
ARM9 SHA256 `b43630d4f0bf0ea3530a6330f7c80482d6ba1f70ba194a447eb93e8a738d77ea`.
Own code SHA256 `0a53f65237b0c7f1b523c5b31694b9d09d9bf29559300275c898b628d314c2ea`.

Latest real save: 634-byte DSV v0/512 payload, SHA256
`a22cdc22490db27af413520d4a7aa09e7decdec3ab5d41636c575bc6bd19ce46`.
Checkpoint `before-combat-flow` preserves it; prior stable ROM92f4aa29 is retained.
Next queued paid move remains Oscorp Rush/Spider Dance400. Orbit Breaker is still
an area-finisher proposal; extra progression and third suit research stay queued.
