# Combat feedback and Rebound juggle revision

2026-10-04. Web Vault is now **player-confirmed**. Its brief aerial window remains
an early setup; reliable paid pursuit/control belongs in the expanded kit roadmap.
This release adds readable combat numbers and the requested Rebound trajectory.
Sling Strike remains the next approved move after this feedback pass.

## Player-visible behavior

- Rebound's enemy horizontal impulse changes from -4506 to -2253 Q12 in the two
  non-immune kind-32 response records. Vertical changes from 6554 to 11469. This
  halves the previous horizontal impulse and increases vertical impulse about
  75%. Player recoil, contact windows, damage, costs and purchase gates stay exact.
  The target has more airtime and lands closer. More airtime can delay landing;
  this is not a promise of a shorter total recovery time.
- **DEALT** and **TAKEN** each show the three most recent positive health-loss
  instances and **SUM** for the current sequence. Instances last 60 active HUD
  updates; totals last 120 updates after the last loss. A longer gap starts a new
  sequence. Room/HUD construction clears the buckets. Pause freezes that clock.
- These are compact fixed HUD readouts, not labels anchored over actors. Position,
  colour and larger accumulated-number styling remain a later visual pass. No
  native options flag or save field is commandeered; the current recipe enables
  feedback. A proper native feedback setting is backlog work.
- The numeric combo label is `75*tier + floor(gauge_q12/4096)`. It shows zero and
  the first Snap Sweep gain even while the bar is hidden below 30. Native tier
  advancement subtracts 75 from gauge, making this a continuous meter value.
  It is **not a hit count** and does not alter the gauge, decay, XP or damage.
- Damage uses **100 displayed HP per native health unit**, rounded to two decimal
  places. The observed three-unit player health budget therefore displays as
  300 HP. This is a display scale, not a damage/stat multiplier. SUM rounds the
  accumulated raw loss, rather than adding individually rounded strings.

## Health paths and limits

Player damage `0205F3F0` subtracts requested Q12 loss from stats `actor+E4 -> +84`,
clamping at zero. Enemy damage `020492A8` subtracts requested Q12 loss from
`actor+44`, clamps it, and dispatches setter `02049304`. Both hooks record
`min(max(old_hp,0), max(requested,0))` immediately before the unchanged native
function. Zero/healing requests and already-dead targets do not produce numbers.
Overkill shows actual available HP lost, not the larger attack request.

The native Test Upgrades dummy starts with 4096 Q12 HP (100 displayed), then
setter logic with its training flag refills it to **40 Q12** after defeat. Further
overkill hits correctly show 0.98. This is native training behavior, not the move
becoming weaker or the feedback synthesizing damage. A better training health
budget is an independent future improvement.

DEALT aggregates the observed common enemy health-loss path, including losses
from other callers of that path. It is not an attacker-credit system: incidental
environmental enemy loss could join the total. Separate damage paths used by
special bosses or scripted destruction are not yet audited. TAKEN covers the
observed common player subtraction path; direct set-health/healing scripts are
not fabricated into hits. There is no new bleed/DOT mechanic. Repeated native
damage calls already stack with the same per-instance/total behavior.

Player-path validation includes controlled calls of the actual native subtraction
function in a **test-only ROM**, producing three 1024-Q12 losses, 25.00 each and
SUM 75.00. That test fixture calls damage automatically and is absent from the
release, whose six hook targets and code hash are pinned. Normal incoming enemy
contact and broader boss/environment coverage remain player/runtime checks; the
controlled test does not claim to simulate enemy AI.

## Code and rendering

All original runtime addresses remain unchanged. The clean ARM9 has a 24-byte
SDK autoload table at offset 1439A0 and main BSS end 0214F420. A third autoload
record copies our own code to **0214F420** before clearing main BSS. Main BSS
bounds and existing ITCM/DTCM entries remain exact. Main arena lower-bound literal
at FF374 moves from 0214F420 to 02153420, reserving **16 KiB** from the heap.
The extension's source and autoload table fit below its destination.

ARM9 file growth relocates ARM7/FNT/FAT/banner and both NitroFS files by a fixed
aligned delta. Their runtime addresses and byte payloads stay exact. Header
capacity/used-size/CRC are checked and only verified zero/FF tail padding may be
consumed. Unsupported module parameters, overlay layouts, hashes, hook words or
sizes fail before publication. Reversing declared edits and removing the new
autoload entry reconstructs the exact accepted ARM9.

Hook sites: HUDComboMeter update E7D48; HUDTextBG constructor return E8F30;
its two destructor paths E8F38/E8F90; player subtraction 5F3F0; enemy subtraction
492A8. Stubs preserve live registers, CPSR flags and stack alignment, replay the
displaced instruction, and return to the unchanged native body. Font ownership
ends with HUDTextBG destruction. Construction clears both loss buckets and
telemetry, preventing totals from leaking across rooms.

HUDTextBG `+1C` is the main-engine BG2 descriptor; `+4` is the atlas layer and
must not be used for font glyphs. Native font constructor B1DC, text draw B3A4,
canvas constructor 9328 and destructors are reused. Canvas includes a 512-byte
cache at +38, requiring roughly **0x238 bytes**, not merely its small header.
The hook reserves 0x300 stack bytes, begins glyph tiles at 0x200, clears only its
top readout rows and lower-right combo rectangle, and retains central messages.
The bounded three-hit columns fit the reserved text area.

`tools/combat_feedback.s` and `assemble_combat_feedback.py` contain our source.
Optional developer reassembly uses Keystone; ordinary builds read guarded own
code in `combat_feedback.hex` and require only Python's standard library. No game
assets, executable dump, RAM, save or ROM are committed.

## Validation and release

**86 tests pass (86.976 seconds)**. Added checks cover extension integrity,
reversible ARM9 edits, autoload/BSS/source separation, heap reservation, original
ARM7/banner/FNT/NitroFS byte preservation, strict bad-input rejection, native
purchase records/input/damage/accumulator bodies, and branch destinations.
Every complete build rereads all **3,733 resources**; the existing eleven asset
overlays remain exact.

Isolated replay evidence (private `build/boot-tests/`):

| Check | Evidence / result |
|---|---|
| First Snap Sweep | `Spider-Man-WoS-modded-fe2be48f/feedback-snap-menu`, frame3110: DEALT75.00/SUM75.00, **COMBO12** with the native bar hidden |
| Multiple actual losses | Same run frame3190; previous development `CombatFeedback-cbb04bff/snap-close`: 3072,1024,40-Q12 losses, overkill capped; instance list and raw accumulated total agree |
| Menus | Save Options and native pause/options screens remain readable; feedback ceases with inactive gameplay HUD |
| Web Vault regression | `feedback-vault`: paid launch/hop still works; native damage loss3072 Q12, player hop/landing and purchase checks retained |
| Player path | `ControlledHealthLater-8341e2b7/player-health`: native HP subtraction and 25/25/25 ->75 rendering; isolated test-only fixture |
| Rebound facing/ownership | `feedback-left-owned`: bit13 true, paid action50, recoil and higher target launch; `feedback-rebound-left`: actual refund clears bit13 and prevents the paid chain |
| Current progress resume | A fresh read-only real battery copy loads the current Residential roof/save progression normally |

Final ROM SHA256:
`fe2be48f62999321edc4b67e3705268c21108e21b1d21efaeb6a07eaa1e7b432`.
Final ARM9 SHA256:
`0cb23de19e5541393bbbe161b98c5104fc06570ba3c149c0f36ec4b2712903cb`.
Own extension SHA256:
`4cfb1099ca1dd86dfc28d87ecce51fed6a9d7495775eb5a7b8dd146d18d1426d`.

Published through `python tools/playtest.py build` with a closed emulator and
checkpoint `before-combat-feedback`. Real battery SHA256
`9336ca4a3cbb3679ebf2fed31f796d6f8b9a93c9bb7d1faef8c8dd7f61b7861e`
remains identical before/after; prior Web Vault ROM is retained for rollback.
`feedback-resume-long` returns from training to Save Options, continues into
gameplay, clears old totals/font ownership, and runs through frame 9999 with
tick 2739, no stale damage entries and a readable COMBO 0. Stable filename and
the real battery association stay
the same. Broader player checks: readability during busy fights, ordinary incoming
damage, Rebound pursuit near walls/ceilings, unusual bosses, and long play.
