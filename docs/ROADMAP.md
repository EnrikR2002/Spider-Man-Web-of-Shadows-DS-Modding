# Roadmap

The whole-game list of what the player wants to add and why it should be fun,
reviewed 2026-10-24 (America/Edmonton). Renamed from `docs/TASM_ROADMAP.md`
on 2026-10-24: the project is no longer only a TASM kit. [TASKS](TASKS.md) owns
the live build and next action; [CHANGES](CHANGES.md) owns shipped behavior;
[TECHNICAL](TECHNICAL.md) owns engine facts; [DEVELOPMENT](DEVELOPMENT.md) owns
how to build and qualify.

**Status words used below.** *Shipped* means in a published release.
*Agent-tested* means qualified by tools, not by the player. *Player-confirmed*
means the player said so. *Designed* means a spec exists and nothing is built.
*Idea* means a direction, not a plan. Only start a Designed item when the player
says go; record every verdict in the [feedback log](#player-feedback-log).

## Now

| # | Item | Status | Next step |
|---|---|---|---|
| 1 | [Spider-Man 2099 Black kit](#spider-man-2099-black-kit-the-hunter) | Refined Web Yank shipped in v0.34.1; rest of revision 3 designed | Player reviews the firm reel before any further slice |
| 2 | Taller 2099, scarlet webs, Hunter's Return and Talon Lift; retained Vortex/Conductor/Vitality | Shipped, agent-tested | Player plays and gives a verdict |
| 3 | [Midnight Line](#midnight-line) full-route verdict | Shipped, agent-tested | Player replays the full route |
| 4 | [Crane Row](#crane-row) full vertical route | Shipped, agent-tested | Player replays the full route |
| 5 | [Creature presentation](#creature-presentation) beyond Rail Skitter | Waiting on the Skitter verdict | Expand one species at a time only after it passes |

## Player direction

Fun and spectacle come first. The game is a 2D side-view brawler against mobs
and bosses; every feature has to work inside that. The two forms play
differently on purpose:

- **Red (Amazing Spider-Man, TASM1/2 combined):** fast and acrobatic. Strike,
  cancel with R, reposition, resume. Its skill list is final.
- **Black (Spider-Man 2099):** a relentless hunter who takes targets where he
  wants them and climbs what he cannot move. Add the rows its kit needs.

Preserve native controls, purchases, ownership/dependencies, Both Suits
traversal, story barriers and earned rewards. Prices/balance, a third suit,
save expansion and new campaign branches wait until the player asks.

## Spider-Man 2099 Black kit: the Hunter

**Status:** Designed and approved by the player, revision 3 (2026-10-24).
The player explicitly made `claude/zen-clarke-p0wo8j` authoritative over
conflicting local plans on 2026-10-23.
Implementation requested locally on 2026-10-23 after importing the remote
revision-3 design. The appearance/earlier-move baseline is v0.33.1: taller cape-free appearance,
scarlet webs, Hunter's Return and manual-jump Talon Lift already ship; receipts
are `reference/spider2099_presence.json`, `reference/hunters_return.json` and
`reference/talon_lift.json`. Web Yank now ships as the first revision-3 slice in
v0.34.0; v0.34.1 replaces its rejected pull/placement with an upright reel and
arrival-timed rake (300 XP; X/Up+X, native prompt priority, close rake, heavy zip
and native R exit). Receipts are `reference/hunter_kit.json` and
`reference/web_yank_fix.json`; refined feel is player-unconfirmed.
Remaining revision-3 behavior below is designed; retain baseline
mechanics until each replacement qualifies.
The remote design's 2026-10-24 dates are retained as source provenance. Machine-readable rows are in
[suit metadata](../reference/suit_roadmap.json) under `2099-classic`.

**History:** 2026-10-22 catch/carry/crash/chase proposal -> 2026-10-23
revision 1 (too pin-centred) -> revision 2 (talon/web/air/boss pillars, 15
rows) -> revision 3: the player approved X for webs and the overall kit, cut
Collar Toss and Lariat, and asked for one skill that rewards a full combo meter
the way Red's Momentum and Overclock do. The player approved revision 3, moving
Shockwave Talons to tier 3, adding tier-5 life steal and a visual for each
tier. Earlier drafts are archived as
`RETIRED_2099_DESIGNS.md` and `docs/TASM_ROADMAP-2026-10-24.md`. The local
seven-row air/guard proposal is separately preserved as
`docs/TASM_ROADMAP-local-2026-10-23.md`; revision 3 supersedes it.

### Identity

In *Across the Spider-Verse* Miguel O'Hara is big, serious and relentless. He
leads the Spider Society's hunt for Miles and ends it by pinning him to a
speeding train's roof. Against the Vulture he climbs onto the villain's back,
tears off a wing and hangs on as the Vulture rockets upward. His web lines are
heavy and glowing. He is reportedly animated on ones, so his weight comes from
fluid motion, not stiffness
([film](https://en.wikipedia.org/wiki/Spider-Man:_Across_the_Spider-Verse),
[chase](https://intothespiderverse.fandom.com/wiki/Hunt_for_Miles_Morales),
[Vulture](https://intothespiderverse.fandom.com/wiki/Spider-Man:_Across_the_Spider-Verse)).

**Red never stands still; 2099 never lets go.** Red slips around a crowd. 2099
takes a target where he wants it (into the air, into the crowd, into the
floor) and uses it against the rest. What he cannot move, he climbs.

| Pillar | Verbs | Skills |
|---|---|---|
| Talons | slash, hook, shred, tackle, pin | Rundown, Talon Line, Shredder, Roof Pin |
| Webs | yank, reel, zip | Web Yank, Reel In |
| Air | lift, rake, catch, dive, pounce | Talon Lift, Sky Rake, Meteor Catch, Freefall, Talon Pounce |
| Boss | board, ride, rip | Boarding (Wing Ripper) |
| Meter | escalate | Relentless, Apex Predator |

Mobs already support this vocabulary in the engine: stagger, knockdown, launch,
air juggle, web yank and hold, floor drag and far throw (TECHNICAL
[Hit pipeline](TECHNICAL.md#hit-pipeline-v040-runtime-probed)). Bosses only
stagger: the Conductor turns knockdowns into standing staggers, and native
mini-bosses sit outside the kit's enemy registry. So against bosses Miguel
moves, not the boss. The native combo meter pays less for repeated contacts, so
a varied kit also scores better.

### Rules every 2099 move obeys

1. **Form and ownership gates.** Only in Black form (`actor+0x34 == 1`) and
   only when the move's row is owned. Otherwise the native path runs unchanged.
   Red form, Red rows and Both Suits rows are untouched.
2. **Native foundation stays exact.** Ground A Power Dash, air A Hammer Spike
   and air Down+A Hammer Slam keep their input, movement and Bulldozer
   Dash/Sledgehammer Slam story use, and never need a target. Ordinary B, base
   Y strings, R evade, wall crawl and swinging stay native.
3. **Movement is velocity only.** Write actor velocity and let native
   collision resolve walls and floors. Never write player or enemy positions.
4. **The heavy rule.** A target is *heavy* when it is a boss, or when a built
   yank/launch comes back ignored (ReceiveHit result 1). Heavy targets pull
   Miguel to them; they are never yanked, launched, thrown or pinned.
5. **R always lets go.** R, getting hurt, death, a room change or a form switch
   ends any 2099 move, releases its web line and clears its state.
6. **No chains from built hits.** Hits the kit builds never trigger further kit
   hits (the Overclock rule); Feeding Frenzy's healing is the only effect they
   feed. No freezes, slow motion, timers that stop the game or permanent stun.
7. **Original motion.** Every move gets its own continuous authored clip; never
   rename a stock attack as a new move.

### Controls in Black form (all rows owned)

| Input | Action |
|---|---|
| Y, Y, Y... | Native Black string; late-pause branches become Talon Line and Shredder |
| Hold Y, release | Talon Pounce (Up held at release aims high) |
| Air Y | Sky Rake |
| Down+Y next to a downed enemy | Roof Pin (otherwise native Down+Y) |
| A on the ground | Native Power Dash; A again after a dash hit = Rundown |
| Up+A on the ground | Talon Lift |
| Air A | Native Hammer Spike; Meteor Catch when an airborne enemy is in reach |
| Air Down+A | Native Hammer Slam with Freefall's height bonus |
| X, no lift/lever/grate prompt in reach | Web Yank (Up+X yanks upward) |
| Air X | Reel In |
| Web Yank zip, Up-pounce or jump into a boss while holding toward it | Boarding; while riding, Y rakes and A is Wing Ripper |
| R | Native evade; lets go of any 2099 move |
| B | Native jump, swing and Enemy Kick-Off |

Native X prompts (lift, lever, grate) always win over Web Yank.

### The fourteen skills

The seven native Black rows keep their ability bits 20..26, events 329..335 and
native dependencies. Seven new rows use free saved bits 83..89 (events
392..398; third ability word masks `1 << (bit - 64)`). Bits 90..95 stay spare.
Distances and timings below are starting values for tuning, not measurements.

| # | Row (bit) | Skill | Requires | Pillar |
|---|---|---|---|---|
| 1 | Webbed Fury (20) | Rundown | - | Talons |
| 2 | Power Launch (21) | Talon Lift | - | Air |
| 3 | Ground Rebound (22) | Freefall | - | Air |
| 4 | Black Widowmaker (23) | Talon Line | - | Talons |
| 5 | Poison Pummel (24) | Shredder | Black Widowmaker | Talons |
| 6 | Super Charge (25) | Talon Pounce | - | Air |
| 7 | Quick Charge (26) | Relentless | Super Charge | Meter |
| 8 | New (83) | Web Yank | - | Webs |
| 9 | New (84) | Reel In | Web Yank | Webs |
| 10 | New (85) | Sky Rake | - | Air |
| 11 | New (86) | Meteor Catch | Sky Rake | Air |
| 12 | New (87) | Roof Pin | - | Talons |
| 13 | New (88) | Boarding | - | Boss |
| 14 | New (89) | Apex Predator | - | Meter |

Shop rows are one level each with at most one parent and one dependent, the
native rule. Every pillar has a row without a parent. Prices stay deferred.

**1. Rundown (Webbed Fury).** After a Power Dash hit, press A again within the
native Webbed Fury window to dash again at the still-tumbling target or the
nearest enemy ahead (about 40 units); up to two extra links. Links hit as
knockbacks, the last as a knockdown (kind 0x1F). Heavy: the link becomes a
shoulder check that stops on contact (one stagger). No target: native recovery.

**2. Talon Lift (Power Launch).** Grounded Up+A: a rising claw launch (kind
0x25) on the enemy in front. Keep holding Up and Miguel rises with it on jump
velocity, ready for Sky Rake; let go and he stays grounded. Heavy: no launch,
Miguel rises to head height and the claw lands as a stagger.

**3. Freefall (Ground Rebound).** The native air Down+A slam becomes a
head-first, talons-first dive. Record the height where the slam starts; at the
native slam contact, scale hit strength and the impact radius by drop height.
No bonus below a held jump (about 27 units); cap near three jump heights. The
native rebound bounce stays for bystanders, and bounced enemies can be
juggled. Heavy: a height-scaled stagger hit. Floor breaking stays native.

**4. Talon Line (Black Widowmaker).** The native late-pause branch
(Y,Y,Y, pause, Y,Y) plays three advancing slashes (stagger kind 0x04), then a
hook that drags the target across Miguel's body (floor drag kind 0x26 aimed
behind him) and leaves him facing the next enemy. Back on the last press hooks
the enemy behind instead. Heavy: two close slashes, no drag.

**5. Shredder (Poison Pummel).** The native late barrage (Y,Y,Y, pause,
repeated Y) becomes a forward-walking talon flurry, steerable with the D-pad
and capped like the native Scissor repeat limit. The last press's direction
picks the ender: Up launches (0x25), Forward blasts back (0x1F), Down smashes
the enemy to the floor (knockdown plus one small bounce). Heavy: flurry
staggers, then a heavy rip.

**6. Talon Pounce (Super Charge).** Hold Y to coil (the native Super Charge
hold and charge time), release to leap talons-first at the enemy ahead, or
above with Up held, up to about 25 units in under half a second. A grounded
target takes a knockdown; an airborne one takes an air-juggle hit (0x14) and
Miguel stays airborne for Sky Rake. Heavy: a strike; an Up-pounce into a boss
while holding toward it starts Boarding. Never passes through walls.

**7. Relentless (Quick Charge).** Passive. Halves the Pounce coil. During any
2099 ender's recovery, holding Y fires Pounce and pressing X fires Web Yank the
moment the ender ends, so the hunt moves to the next target without a reset.
One stored cancel; hurt, R, a form switch or a room change clears it.

**8. Web Yank (new; pull refined after the 2026-10-24 rejection).** Ground X
with no native prompt ties a scarlet line to the nearest enemy ahead within
about 45 units. A firm grounded reel keeps it upright and brings it six units
in front of Miguel; actual arrival starts the authored talon rake. Up+X launches
at that strike. Within eight units, skip the pull and rake immediately. Let the
player flow into a normal follow-up without waiting through a floor bounce.
Heavy: Miguel zips to the target by native velocity and strikes; holding toward
it with Boarding owned starts Boarding once that later skill ships. The original
pipeline-proof pull design is archived before replacement.

**9. Reel In (new, requires Web Yank).** X in the air: tie the nearest enemy
below or ahead and pull it up to Miguel's height to extend or restart an air
combo. Heavy: Miguel zips to it. Lab question: whether a built yank toward an
airborne player lifts the enemy, or a timed launch is needed instead.

**10. Sky Rake (new).** Black's air Y string plays four talon rakes (air
juggle 0x14) and a flip kick that pops the target higher. The native air-chain
rules still decide whether the next press chains. Red's air string stays exact,
so this needs Black-only clips. Heavy: the same hits land as staggers.

**11. Meteor Catch (new, requires Sky Rake).** Air A with an airborne enemy
within about 10 units in front: grab it, flip and fall together (both by
bounded velocity, as Vortex steers bodies), and slam it into the floor
(knockdown) with one small bounce, ready for Talon Lift or Roof Pin. Otherwise,
and against heavy targets, the native Hammer Spike runs.

**12. Roof Pin (new).** Down+Y on the ground with a downed enemy within about 10
units in front: the train-roof moment as one short fixed finisher. Pin it with a
knee and talons, three tearing hits (each re-bounces it in place), then kick it
away (0x1F). About a second, no mashing, no repeat. Otherwise native Down+Y.
Not available on heavy targets.

**13. Boarding (new).** Reaching a boss or heavy enemy by Web Yank zip,
Up-pounce or jump while holding toward it makes Miguel cling to its back or
shoulder: each update a bounded velocity steers him to an anchor on the boss, as
Spider Perch follows an enemy. Y rakes (stagger hits from behind). A is **Wing
Ripper**: a heavy tear that forces a stagger, then a kick-off jump that throws
Miguel clear into the air. When the boss starts an attack it throws a rider off;
R leaves at any time. Riding ends when the boss shakes him or he rips, not on
a timer.

**14. Apex Predator (new).** Passive. 2099 scraps instead of evading, so the
meter both raises his power and keeps him in the fight, the way Red's Momentum
(speed by tier) and Overclock (tier-5 web shot) reward Red. It reads the native
combo tier every update; effects and visuals stack by tier and vanish the moment
the tier drops. It never spends the meter and adds no damage beyond native tier
scaling.

| Tier | Effect | Visual (must read at native scale) |
|---|---|---|
| 0-1 | None | Normal navy/red suit |
| 2+ | **Fast Hunt:** Black attacks and 2099 moves play at 1.10x | Eye lenses and talon tips light up red |
| 3+ | **Heavy Line:** Web Yank and Reel In also catch up to two more enemies in a narrow lane along the line and drag them in together; each arrival takes one light knockdown. **Shockwave Talons:** every 2099 ender (Rundown's last link, Talon Lift, Freefall, Talon Line's hook, Shredder's ender, Meteor Catch, Roof Pin's kick, Wing Ripper) also knocks down every other standing enemy within about 14 units; heavy targets take one stagger | Web lines turn red; chest spider and shoulder panels brighten red |
| 4+ | Fast Hunt rises to 1.20x | Red accents pulse slowly |
| 5 | **Feeding Frenzy:** a little life steal (below) | The whole suit glows red with a slow pulse; the HUD health bar flashes on each heal |

**Feeding Frenzy.** At tier 5, every point of HP Miguel removes from an enemy or
boss (native and kit-built hits alike) adds 5% of it to a hidden heal bank.
Each time the bank holds a quarter health unit (1024 of a unit's 4096), restore
it through the native clamped health setter. About 13 to 20 ordinary hits
restore one segment of the roughly six-segment bar. Caps: at most one health unit per 300
updates; no healing at zero HP, during the near-death minigame or above max.
The bank keeps its contents when the tier drops but fills only at tier 5.
Healing is not a hit, so it does not break rule 6. Life steal was chosen over
heal-on-kill (no sustain in boss fights) and damage reduction (rewards
passivity): it pays for aggression against mobs and bosses alike.

Open questions for the capstone lab:

- Does the HUD draw partial segments? If not, restore whole units so every heal
  is visible.
- Does taking a hit drop combo tiers (TECHNICAL notes a native penalty path
  that subtracts two tiers, trigger unconfirmed)? If so, tier 5 may vanish just
  when healing matters: move Feeding Frenzy to tier 4 before raising its rate.
- In Black form the purple HUD bar shares palette colours 29..31 with the combo
  meter, so a heal flash tints both; that is acceptable.
- Suit glow: pre-bake one palette per tier into the 2099 texture and let the
  existing player draw adapter (`spider2099_visual`) select it. If no material
  palette field can be switched, fall back to red web lines plus HUD tint.

### What fights should look like

- **Hunt:** Web Yank the enemy at the back -> Talon Line through it -> hook it
  behind -> Relentless pounce onto the next.
- **Sky:** Talon Lift holding Up -> Sky Rake -> Meteor Catch into the floor ->
  Talon Lift the bounce, or Reel In a fresh victim from the air.
- **Crowd:** Shredder's Forward ender into a group -> Rundown through the
  falling bodies -> wall climb -> Freefall onto the pile -> Sky Rake a bounced
  one -> Roof Pin whoever lands nearest.
- **Meter:** vary the string to reach tier 3 and every ender knocks the room
  flat while Heavy Line drags three at a time; hold tier 5 and every hit feeds
  health back while the suit glows red.
- **Boss (the Vulture plan):** Web Yank or Up-pounce to close in -> Boarding,
  raking from behind -> Wing Ripper forces a stagger and throws Miguel clear ->
  Sky Rake at head height -> Freefall from above -> the next boss attack throws
  a rider off -> R or Kick-Off out -> board again. No forced boss movement,
  permanent stun or invented armor breaks.

### Implementation guide

Follow DEVELOPMENT's [add a feature](DEVELOPMENT.md#add-a-feature-as-a-new-post-pass)
recipe. Proposed files, mirroring the latest feature (`tools/vortex_forge*`):

| Piece | File |
|---|---|
| Post-pass generator over the exact published parent | `tools/hunter_kit.py` |
| ARM code in its own guarded block | `tools/hunter_kit.s` |
| Authored clips (`kit_choreography.Clip`) | `tools/hunter_kit_art.py` |
| Lab cases (copied saves, disposable RAM) | `tools/hunter_kit_lab.py` |
| Tests | `tests/test_hunter_kit.py` |
| Receipt for the published slice | `reference/hunter_kit.json` |

Engine facts to reuse, all in TECHNICAL:

| Need | Section |
|---|---|
| States, input queue (X is command 6; L is command 4), ability query, Black form, string nodes 5..10 and late branches | [Player state machine](TECHNICAL.md#player-state-machine-and-red-kit-hooks-v020) |
| Built hits, reaction kinds, ReceiveHit result and health argument | [Hit pipeline](TECHNICAL.md#hit-pipeline-v040-runtime-probed) |
| WebLine spawn/tie/release and colour | [Web lines](TECHNICAL.md#web-lines-built-hits-and-the-web-skills-v0130) |
| Moving enemy bodies with bounded velocity | [Tether Vortex](TECHNICAL.md#conditional-tether-vortex-and-conductor-armor-v031-research) |
| Kit blocks, registry, `kit_alive`, held/new keys | [Kit extension contract](TECHNICAL.md#kit-extension-contract) |
| Momentum's tier-scaled speed and Overclock's tier-5 trigger | [Second kit block](TECHNICAL.md#second-kit-block-web-rush-ricochet-momentum-v0100), [Web lines](TECHNICAL.md#web-lines-built-hits-and-the-web-skills-v0130) |
| Combo tier and gauge | [Combo resource](TECHNICAL.md#combo-resource-and-hp-are-different) |
| Shop tables, rows, free bits and strings | [Purchase records](TECHNICAL.md#purchase-records-and-native-ownership), [Shop tables](TECHNICAL.md#shop-tables-menu-and-free-ownership-bits-v0100) |
| Clip authoring, sample counts and contact clocks | [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) |
| Mini-boss class, registry exclusion and boss meter | [Character route](TECHNICAL.md#character-route-concrete-engine-starting-points) |
| Player health setter, health units and HUD bar colours | [Player health](TECHNICAL.md#player-health-and-the-top-screen-hud-v0110) |
| Player draw adapter, 2099 mesh and texture | [SCA / model / textures](TECHNICAL.md#sca--model--textures) |

**Gates before the first slice** (lab only, no release):

1. **Code space:** the 32 KiB kit stays exact. Give 2099 its own guarded
   code/state block, as v0.31.0's autoload extension page did; this deliberately
   extends the kit contract.
2. **Shop:** move the native Black list into the new block (as v0.10.0 moved
   Red's), append the seven rows with appended strings, and keep the native
   rows' bits, events and dependencies exact.
3. **Inputs:** X shared safely with native prompts; held X/Y readable from the
   kit's key words; Down+Y next to a downed enemy distinguished from native
   Down+Y; air X free.
4. **Black-only animation:** route Black-form actions to appended clips. Air
   string actions are shared with Red; GroundAttack15 is shared; G11/16/17 have
   m6.xbd users and are not spare.
5. **Bosses:** a Perch-style velocity follow for Boarding, plus a class-specific
   target adapter for native mini-bosses. Start on the Conductor.
6. **Tier visuals and healing** (before the capstone): a switchable material
   palette in the player draw adapter, partial-segment HUD drawing, and whether
   damage drops combo tiers.

**Acceptance for every slice:**

- Owned vs unowned (row bit cleared in disposable RAM) and Red form behave as
  specified; Red's kit checks still pass.
- Black traversal is unchanged: Bulldozer Dash barriers, Sledgehammer floors,
  wall crawl and swing.
- Real enemies lose HP; R, hurt, death, room and form changes clean up; no
  stale pointers after kills.
- Each slice's moves work on the Conductor under the heavy rule.
- Bought rows survive save and fresh Continue on a copied latest battery.
- Native-scale, normal-speed footage goes to the player before the next slice.

**Build order**, one published slice at a time with a player verdict between:

1. **Pipeline proof:** Web Yank alone (X input, web line, Black-only clip
   routing, heavy rule, one new shop row).
2. **Sky slice:** Talon Lift, Sky Rake, Reel In, Meteor Catch.
3. **Boss slice:** Boarding with Wing Ripper, Freefall, Talon Pounce,
   Relentless.
4. **Ground slice:** Rundown, Talon Line, Shredder, Roof Pin.
5. **Meter capstone:** Apex Predator, last because it modifies the others.
   Tiers 2..5 must be distinguishable side by side in native-scale footage.

**Web Yank slice progress:** Web Yank's own code/state, first appended Black row,
native X priority and Black-only clips are qualified. Conductor heavy behavior
is qualified; the native mini-boss adapter, Boarding follow and capstone gates
remain open. The first slice's pull/placement was rejected on 2026-10-24;
v0.34.1's firm reel and arrival rake are agent-tested and published. Wait for the
player's refined-move verdict before starting the Sky slice.

## Red kit: the Amazing Spider-Man

**Status:** Shipped. Snap Sweep and the original Web Vault are
player-confirmed; later revisions need their own verdict. The skill list is
final: iterate these rows, add none.

| Native slot | Move | Input / purpose |
|---|---|---|
| Web Kick | Leapfrog | Y during grapple; cross-up vault/kick |
| Web Launch | Skyjack | Up during grapple; rise, aerial pressure and spike |
| Mid-Air Snare | Spider Perch | Air A toward an enemy; perched attacks, hop/spring exits |
| Spider Dance | Split Decision | Y, pause, Y; crowd-facing string |
| Scissor-Kick Special | Spin Cycle | Split Decision extension/repeated Y; steerable spin |
| Amazing Speed Boost | Spider Reflex | R during Red attacks; cancel, reposition, resume |
| Ultimate Speed Boost | Spider-Sense | Timed R against supported threats; reversal |

Added Red rows: Web Rush, Ricochet, Momentum, Overclock, Dragnet and Vortex.
Both Suits Vitality I-III also exist. Vortex (v0.31.0) now needs a webbed enemy:
web with A or Dragnet, release A, then Down+Y for a tethered catapult and slam;
its feel needs a player verdict. Catalogs: [suit metadata](../reference/suit_roadmap.json),
[upgrade metadata](../reference/tasm_upgrade_plan.json).

## Chapters

### Midnight Line

**Status:** Shipped, agent-tested; full-route verdict open. Eight active rooms;
Signal House and Pump Refuge are retired; Relay Sanctuary is the main save room.
The player accepted the environment direction, not yet the enemies.

Next, with real purchases and ordinary damage: does the Conductor land fair
attacks, accept combos, counter sustained pressure and leave readable
recovery? Do Terminal, Floodworks, Turbine Rise and Observatory feel like a
rising ramp with quiet travel between fights? Check map order, the return
loop, retries and save/Continue. Then refine encounters: target unfair
overlap, idle gaps, weak pursuit and repetition; teach roles before combining
them; prefer staging and decisions over more HP or bigger crowds.

### Crane Row

**Status:** Shipped, agent-tested; full-route verdict open. Twelve rooms, two
exploration loops, maps, saved power and shortcuts, original enemies and
rewards, a hoist finale and an approach checkpoint. Earlier creature and
presentation rejections still apply. Review the whole vertical route before
deciding whether upper roofs need navigation work or the finale needs pacing.
Two tested roofs do not prove every pursuit path. Moving counterweights stay
scenery above fixed landings.

### Creature presentation

**Status:** One complete example (Rail Skitter) shipped; verdict open. If the
player accepts its normal-speed motion, silhouette and mixed audio, apply the
same approach to Warden, Eye and Conductor one species at a time, each with
distinct patterns, voice and complete hurt, knockdown, get-up and death. If
Skitter fails, fix it first.

## Acceptance for any future release

- **Gameplay:** native movement/collision, fair contacts, meaningful combos and
  R exits, both forms viable, complete enemy lifecycles in mixed terrain.
- **Presentation:** native-scale, normal-speed footage and mixed audio before
  expanding an example. Clearability and counters do not decide fun.
- **Persistence:** purchases, dependencies, rewards, story abilities and earned
  clears survive retries and fresh Continue on copied latest batteries.
- **Composition:** changed-byte scope, real-input doors for changed rooms and
  broad controls on one stable candidate, published through the guarded flow.
- **Player confirmation:** recorded separately from agent results.

## Idea backlog

Ideas the player may want later. None is scheduled; ask before starting one.

| Idea | What it needs first |
|---|---|
| Prices and balance pass | Player request; current prices are retained |
| Third suit (Scarlet Spider Ben/Kaine, Raimi, classic symbiote) | Player request; no suit selector or migration exists |
| Downtown Grid/Lost Lab, Residential Skyline Run, Hive Quarantine Heart | Audit current flags/storage first; Hive stays post-story |
| Midnight Express, gauntlets, timed replays, collectibles | Backlog only; not required by current chapters |
| Moving trains, rideable loads, changing platforms | A complete native collision/ownership prototype |
| Cross-room timers/pursuit, broader music routing | Lifecycle and audio channel-budget evidence |
| More Red skills or extra stat rows | Not planned: Red's list is final |

## Player feedback log

Newest first. Record each new verdict here the day it is given.

| Date / build | Player said | What it decided |
|---|---|---|
| 2026-10-24, v0.34.0 Web Yank | Clunky and buggy; the way it yanks and places enemies feels really bad and limp | Rework the pull, arrival and impact before any further Hunter slice; quality remains player-unconfirmed |
| 2026-10-24, 2099 rev. 3 | Revision 3 is good. Shockwave Talons at tier 3+; tier 5 gets a little life steal because 2099 scraps and takes more damage; give every tier a visible upgrade, maybe a red glow at tier 5 | Approved for a later implementation session; Feeding Frenzy and tier visuals added |
| 2026-10-24, 2099 rev. 2 | X for webs is fine and the kit is liked; remove Collar Toss and Lariat; add a skill that rewards a full combo meter | Revision 3: 14 skills, Apex Predator added |
| 2026-10-23, imported Hunter rev. 3 | Prioritize all changes from claude/zen-clarke-p0wo8j; they may override existing work | That branch's design/policy is authoritative; superseded local proposals stay archived |
| 2026-10-23, v0.33.1 / imported Hunter rev. 3 | Pull GitHub changes and start the new 2099 skills | Merge both histories, retain the verified local build and start Web Yank pipeline proof |
| 2026-10-23, 2099 rev. 1 | Better, but pin/pound dominates; pins fail on bosses; no webbing; no air combos; add as many rows as needed within the 2D mob/boss brawler | Revision 2: four pillars, Boarding, webs on X |
| 2026-10-23 | Make Black play like Across the Spider-Verse's Miguel and make it fun | Hunter direction replaces the comic-style juggle proposal |
| 2026-10-22, v0.30.3 | Vortex is boring; keep it conditional on cocoons. The boss fights well but needs a larger symbiote war-machine body, one boss bar and a low-HP damage fix | v0.31.0 ships all three; verdict open |
| 2026-10-22, v0.30.2 | Terminal enemies render white | v0.30.3 compact atlas fixes the sampled crowd |
| 2026-10-22, v0.30.1 | 2099 liked overall; match the movie reference; remove the red web cape | v0.30.2 cape-free movie look; visual verdict open |
| 2026-10-22, v0.30.0 | Good start; cape and forearm blades look bad; add Spider-Verse muscle | v0.30.1 sculpt and blade placement |
| 2026-10-19, v0.27 | Combos only slightly better; boss too easy and idle; ramp not felt; remove two save rooms; fix map order | v0.28 addresses these; no v0.28 verdict |
| 2026-10-19, v0.26 | Harder mobility welcome; blanket stagger suppression blocked combos | v0.27 restores hurt openings |
| 2026-10-18, v0.25 | Boss lacked pressure responses; monsters seemed silent | v0.26 adds responses and audio evidence |
| 2026-10-18, v0.24 | Keep the environment and enemy direction; rigid motion, poor SFX and a slow, easy boss rejected | v0.25-v0.27 motion, sound and anatomy |
| 2026-10-18, v0.23 | Unconvincing hits, odd animation, recognizable voices, repetitive rooms rejected | v0.24 contact, lifecycle, audio and room fixes |
| v0.2-v0.4 | Keep responsive cancels, continuous movement and crowd play; Snap Sweep and Web Vault work | Early praise does not approve later revisions |

## Historical designs

Retired designs live byte for byte in the verified archive. They are context,
not a second plan; later decisions above win.

```powershell
python tools/doc_archive.py list roadmap
python tools/doc_archive.py read docs/TASM_ROADMAP-2026-10-24.md --toc
python tools/doc_archive.py read RETIRED_2099_DESIGNS.md --toc
python tools/doc_archive.py read docs/TASM_ROADMAP.md --section 'Spider-Man 2099'
```

To retire a section, archive the file first:
`python tools/doc_archive.py add <unique-name> --from <file> --title <title> --date <YYYY-MM-DD>`.
