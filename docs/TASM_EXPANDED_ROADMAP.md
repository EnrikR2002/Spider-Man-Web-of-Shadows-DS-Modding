# One Amazing Spider-Man kit: design discussion

2026-10-04. The user's latest direction merges the TASM 1 and TASM 2 fighting
identity into one kit. This is a proposal for discussion, not a grant of new
abilities or a migration of existing purchases. The active appearance remains
the current TASM suit. A later movie appearance can be a cosmetic variant.

## Identity and progression

Build a nimble, improvisational fighter: kicks open an opportunity, webs reconnect
to it, evasions create a punish, and momentum rewards a deliberate sequence.
Progress should make those tools connect reliably, rather than simply making
every attack stronger. The two films can supply the same vocabulary, with later
upgrades expressing greater control and confidence.

Web Vault's matched rise now provides an early aerial setup. The player should
eventually be able to purchase a clear reconnect input and one limited juggle extension. That
creates a meaningful chain: Snap Sweep -> grapple -> Rebound or Web Vault ->
Air Catch -> Sling Strike -> a chosen landing/finisher. It should become reliable
through explicit input buffering and hit confirmation, not through invisible
automatic damage or unlimited resets of gravity.

## Proposed tools

Prices below are discussion ranges in XP. They are not implemented prices. The
existing purchases and saves retain their current contract until we agree on
balance and a safe progression migration. Shared traversal purchases stay shared.

| Tool | Status | Role and connection | Proposed price/tier | Necessary boundary |
|---|---|---|---|---|
| **Snap Sweep** | Player-confirmed base opener | Low, quick opening into normal attacks or a grapple | Free foundation | Preserve its existing route when authoring paid combo assets |
| **Rebound** | Implemented; juggle retune in current feedback pass | Short recoil plus a higher, closer enemy launch; choose to pursue or disengage | Existing 100; early setup | No added damage, automatic chase or dodge invulnerability |
| **Web Vault** | Initial move player-confirmed; matched-height revision pending player check | Approach and rise alongside the launched enemy without backward target drift | Existing 200; early setup | Does not itself grant shared Air Dodge or a complete air chain |
| **Sling Strike** | Revised after player feedback; agent-tested, player check pending | Committed passing kick with clean stop and native turnaround; change sides and choose the next landing | Existing 600 initially; midgame | Finite hit budget; collision stops passage when space is blocked |
| **Air Catch** | New proposal | A paid web reconnect to an airborne target after Vault/Rebound; generous, readable follow-up buffer | 300-500; connection upgrade | One reconnect per launch cycle; consumes the opportunity on use |
| **Oscorp Rush** | Approved, pending | A compact advancing ground string to pressure an enemy after landing | Existing 400 initially; ground branch | Retain deliberate timing; narrowing coverage pays for advance |
| **Rebound Barrage** | Approved, pending | A finite close flurry ending in a retreat; cash out ground pressure | Existing 600 initially; ground extension | Requires its parent purchase; leaving early loses remaining hits |
| **Slip Counter** | Approved, research needed | Manual punish after a successful evade; quick return to offence | Existing 800 initially; defensive branch | One earned opportunity; no automatic attack or extra invulnerability |
| **Momentum** | Approved, research needed | Temporary flow after a clean sequence; one hit-confirmed cancel | Existing 1,000 initially; advanced flow | Drops on a hit/whiff; bounded refresh and original speed ceiling |
| **Threaded Juggle** | New proposal | One airborne web tug that stabilizes a target for a further normal hit | 600-900; air extension | One use per airborne cycle; resistant/boss targets retain exceptions |
| **Wall Rebound** | New proposal | Contextual kick away from a nearby wall into an earned pursuit angle | 400-700; situational movement | Needs a real wall contact and collision-safe exit; no free extra hit |
| **Web Trip** | New proposal | A short web setup into a sweep against a grounded target; trades burst for control | 300-500; control branch | Interruptible setup; heavy/boss resistance; distinct from free Snap |
| **Slingshot Finish** | New proposal | A deliberate descending strike to end the air sequence and return to the ground | 700-1,000; finisher | Ends the chain; spending Momentum may improve control, not stack damage |
| **Orbit Breaker** | New late-game proposal | Web-supported corkscrew kick with a small area finish, earned through a launch and reconnect setup; also cashes out against one target | 1,200-1,800; late finisher discussion | One hit per target, bounded nearby targets, interruptible setup and committed landing; expanded purchase support still required |

That is thirteen paid tools plus the free opener. Not all need independent buttons:
some are contextual follow-ups or modifiers to an existing action. Keep every
new input teachable, with a distinct purpose and clear feedback when available.

Suggested branch choices: Air Catch versus Oscorp Rush first; then air control
versus Barrage; then Slip Counter and Momentum. This offers a choice between air
pursuit, ground pressure and reactive play instead of a mandatory price ladder.

## Implementation path

1. Compact combo/enemy health feedback and Rebound's juggle response are released;
   player checks remain open. These supply subsequent damage/control measurements.
2. Sling Strike is released with the native 600-XP purchase, locked/unlocked checks
   and a paired original damage-budget comparison. Gather player feel feedback.
3. Design Air Catch's input/window alongside Sling Strike. Prototype reliable
   paid pursuit before adding longer strings, and test both facing directions,
   ceilings, walls, heavy enemies, misses and interrupted launches.
4. Implement Oscorp Rush next, finish the ground branch, then the counter/flow branch. Playtest complete
   routes before adding another extension or increasing total damage.
5. Expand purchases only after the menu, availability rules, ability storage and
   native save/checksum path are proved. Existing seven Red rows are an initial
   implementation surface, not a creative ceiling.

Ten actions can be prototyped through purchased bundles in the current seven
rows, but ten **independent purchases** require additional engine/menu/save work.
We have not established that unused-looking ability bits are safe. A permanent
progression expansion must preserve story gates, shared abilities, refund rules
and existing saves. Do not quietly reuse another suit's bits.

## Choices to discuss next

- Should Air Catch be the first new purchase beyond the approved seven, or be
  included as a second stage of Sling Strike? Separate purchase makes the
  progression more expressive; a bundle fits the current menu sooner.
- Should Momentum feel like faster animation/recovery, a once-per-chain cancel,
  or a resource spent by finishers? Begin with one primary benefit so it is legible.
- Should the expanded kit specialize more in airborne improvisation or keep an
  equally strong ground/counter branch? My starting recommendation is an air
  identity with credible ground and defensive alternatives.

No separate TASM 2 combat kit is queued. The older seven-slot proposal remains
the approved incremental implementation reference; these additions are ideas.

## Acrobatic area finisher: Orbit Breaker

The user's new area-attack idea fits a late-game cash-out move. First launch a
target, spend a paid reconnect to establish a web anchor, then deliberately
trigger a tight corkscrew or cartwheel kick around that anchor. A short descending
finish can reach a few nearby enemies and remains useful as a single-target
finisher. Its area should be small enough that positioning and setup matter.

Begin design with a maximum of three targets and one hit per target, a modest
single-target budget, vulnerable preparation and clear landing recovery. A miss
spends the setup; taking a hit breaks it. Heavy targets may permit an anchor
without being launched, subject to later resistance research. It should not
reset airtime, give invulnerability or replenish its own setup. Input, price,
animation and actual target/contact rules are proposals only. No ability, slot
or save bit is allocated in this release; revisit after the core air chain feels
good and expanded progression is proved.
