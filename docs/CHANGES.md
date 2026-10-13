# Implemented changes and releases

Current stable release status is in [TASKS](TASKS.md). Mechanics proposed for the
TASM rebuild are in [TASM_ROADMAP](TASM_ROADMAP.md); a proposal is not shipped
behavior. Historical exact evidence is preserved in the archive.

## Version policy

Use **major.minor.patch**, displayed identically at boot and in Options. Minor
versions introduce/overhaul mechanics; patch versions fix/polish/rebalance them.
Major marks a finished overhaul or incompatible progression/save contract.
During development we start at 0.1.0. Each published number identifies one exact
ROM; the publisher rejects a reused version with a different hash. Build logs,
`reference/releases.json` and per-ROM release metadata record what shipped when.
This file is the only human-readable release/change log. No per-release Markdown.

## v0.12.0 - 2026-10-12 - The Substation: three rooms built from nothing

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed; the build does not touch the battery). SHA256
`0ede04222aa250e97c4348551ae61fdc5c4b586072088768bef8c8d7692dc812`
(ARM9 `a212585a...`, kit ARM9 `3c6a34e0...`: the combat kit is unchanged).
Title and Options show v0.12.0. Player (2026-10-11): the Midnight Line was
"basically just the sewers with different colors", wanted "new map assets"
and more places; (2026-10-12): go ahead with the planned changes.

- **A new door at the far left of the Yard.** From the Refuge take the left
  door into the Yard and cross it to its left wall: a grey door leads to the
  Substation, three rooms that are not copies of any room in the game. Their
  walls, floors, platforms, collision and camera are built from a box plan
  by a new room compiler; the pictures on them are borrowed from Pier,
  Downtown and Residential rooms you have already seen.
- **Switchyard.** An open yard at dusk with the skyline behind a fence: a
  loading dock, two stacked containers, a transformer, a steel gantry
  overhead, a fire escape on each building, pylons and wires. A crew appears
  once you walk in. Two barrels and a trash can to throw. Doors at both ends.
- **Relay Hall.** A tall machine hall. Its outer walls are smooth steel that
  Spidey cannot hold on to, so the way up is five catwalks: a held jump
  (keep B down) reaches the next one, a tap does not. Electric arcs run along
  four of them, the two on the left and the two on the right in turn: 1.5 s
  live, then just under a second with nothing live. The lowest catwalk and
  the ledge by the upper door are never live. A small crew waits on the
  floor. The door out is at the top left.
- **Control Roof.** A roof at night. Three waves, each from another district
  (Pier, Sewer, Residential enemies): the next starts when the one before is
  beaten, or after 90 seconds at the latest. Beating the third shows a
  line. Leave and come back and it starts over: it is meant as a sparring
  arena with real enemies. Two barrels.
- **Map.** The three rooms are drawn in the lower left of the Midnight Line
  screen; the Yard door and the Switchyard door are a pair of arrows.
- **Yard.** The metal barrel by its left wall now stands further along the
  floor (it stood where you arrive from the Switchyard).

How: `tools/nitro_build.py`, `tools/room_compiler.py`, `tools/room_author.py`
and `tools/midnight_rooms.py` (TECHNICAL "Room compiler", "The Substation").
Rooms 91..93; visited flags 267, 165, 164 and flag 150 for the cleared roof;
one instruction of the map's visited test now calls a stub so that rooms
above 91 can have a visited flag. Two things the original game needs in a
room were found on the way: camera regions and anchor points for spawners.

Agent-tested on this ROM, not player-confirmed:
279 unit tests; kit qualification 48/48; crash hunt 12/12; 10/10 walk
routes on the first try (four new ones: real doors both ways between the
Yard and all three rooms, a real held jump onto the first catwalk, a live
catwalk shocks, all three waves beaten sets the flag); eight further roof
fights started seconds apart all cleared; the door tour (every link, the
visited flags, no other chapter flag), the power puzzle, save and Continue
in the Refuge, the Vitality shop run. Evidence: `work/kit/v0.12.0/`,
`work/midnight-line/walk-*-0ede0422.json`, frames under
`build/boot-tests/Versioned-0ede0422/`.
Limits: the climb is scripted for the first hop only (the rest is placed;
a human climb follows from the measured jump heights); in the lab one roof
fight in about a dozen never reported its second wave beaten (cause not
found), which is why a wave also starts after 90 s; enemies have native
strength (no dial); the zoom's third step shows the debug placeholder in
these rooms; the nearest save point is the Refuge, two rooms back; a fall
from the catwalks only costs the climb.

## v0.11.0 - 2026-10-12 - Feedback pass: speed, Vitality, a chapter map, closed hatches, a gentler Nest

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed; the build
does not touch the battery). SHA256
`4f387a21821cf071c08a797d0daa997814b50b335c9da4e6e088c24610163ca5`
(ARM9 `caa84033...`, kit ARM9 `3c6a34e0...`). Title and Options show v0.11.0.
Player (2026-10-11, after finishing the Midnight Line on v0.10.0; verdict
under v0.10.0 below): do the quick fixes before bigger work, and of the
proposed stat upgrades "just vitality for now".

- **Speed rebalance.** Spider Reflex now speeds Red attacks by 10% (was 15%)
  and Spider-Sense by 20% (was 30%). Momentum starts a tier earlier (tier 1
  shortens two of five free steps, tier 4 all of them; still nothing at tier
  0) and from combo tier 3 up gives the old 15% / 30% back. Measured Y,Y,Y,Y
  with Sense and Momentum: 122, 106, 100, 88, 86, 86 frames at tiers 0..5
  (v0.10.0: 113, 105, 99, 93, 91, 87), the same hits at every tier. With no
  combo you are a little slower than before, from tier 3 a little faster, and
  Momentum's swing is 36 frames instead of 26.
- **Vitality I, II, III.** Buy Upgrades, Both Suits list, below Quick
  Recovery: 500, 750 and 1000 XP. Each needs the one before; refund them in
  reverse order. Your health bar holds 25%, 50%, 75% more: every hit takes
  that much less of it. The bar keeps its length; in the Red suit the bar
  and the spider emblem turn orange, gold, green. Healing is unchanged.
- **The Midnight Line has its own map.** In chapter rooms the touch screen
  shows a screen titled "Midnight Line": rooms drawn by their shape and
  joined on the side their doors are on, save rooms with a dot, the boss
  with a cross, an arrow back to the Sewer. The Gate's climb into the
  Stairs' floor grate is two dotted arrows (those rooms cannot sit next to
  each other on a flat plan). The zoom button's third step now shows the
  detailed room map in chapter rooms. The Sewer map is the original again.
- **Dead hatches closed.** The Entry's first ceiling grate and the
  Platform's top trapdoor are locked shut: nothing to crawl into.
- **A gentler Nest.** Enemy health / the damage they deal, as a share of
  native: Shaft 59% / 55%, Throat 66% / 59%, Span 70% / 66%, Hollow 75% /
  70%, Gate 80% / 75%. The boss room is unchanged. Measured before, in the
  lab's save: chapter sewer enemies 22k..37k health and 4,096 per hit, Nest
  enemies 74k..106k and 8,192..9,554.

How: the second kit block and the chapter build (TECHNICAL "Second kit
block", "Player health and the top-screen HUD", "Chapter map, closed hatches
and the strength dial"). Vitality is three chained rows on free ownership
bits 77..79 and scales the health Spidey loses, not his maximum, so the HUD
needs no change. The map uses the game's spare sixth area.

Found by the lab before release, never shipped: with the new speeds
Momentum jumped over the last sample of the Spin Cycle loop, so the spin
never ended (it now never skips an attack's last sample); the first map
build stayed locked on the objectives page (the game gives its sixth area
no map: three small patches) and a later one drew two rooms magenta and
black (three of the screen's palettes cannot hold rooms); a scaled enemy at
full health now stays exactly full.

Known limits: the Vitality colours show in the Red suit only (the Black
suit's purple is shared with the combo meter) and were seen in the lab's
emulator, not in DeSmuME; the shop shows no level number; rooms appear on
the map as you visit them, like native ones; the world view (zoom x2) has no
"you are here" for the chapter; the Yard's detailed map is a placeholder; a
chapter message covers the map until you change rooms (as before); B pressed
in the two updates between Perch stomp cycles still fires the native web
swing (older than this release); only chapter rooms have a strength dial;
Momentum does not show its tier.

Agent-tested on `4f387a21`: kit qualification 48/48 (the Perch spring check
now presses B ten frames earlier, off the gap between stomp cycles); the
three Vitality rows bought in order in the real menu, level I not refundable
under level II, level III refunded (XP 3000 -> 2500 -> 1750 -> 750 -> 1750);
a sparring Brute's hit 4,096 -> 3,280 / 2,736 / 2,336 with levels I..III; bar
colours and the map views x1, x2, x3 reviewed in frames (the whole map with
every room marked visited, from Gate, Hollow and Yard); crash hunt 12/12
with every new skill and Vitality III owned; chapter walk routes 6/6 on the
first try (75 checks); door tour 32/32 in two runs (links 0..16, then from
17: the tour's teleport dropped a knocked-back Spidey out of bounds in the
Throat, a lab artifact); power puzzle; save and Continue in Refuge, Rest and
Shrine; neither hatch can be crawled into; Span enemies 90,112 -> 63,361
(x 45/64), Hollow 81,108 -> 60,831 (x 48/64); 260 unit tests. Feel, prices,
colours and the Nest's new strength are untested by the player. Evidence:
`work/kit/v0.11.0/`, `work/kit/evidence.json`, `work/midnight-line/walk-*.json`.

## v0.10.0 - 2026-10-11 - Three new Red skills: Web Rush, Ricochet, Momentum

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed, battery
unchanged since 2026-10-07). SHA256
`a928843cb520d82568e703b3710f4177da4160addab5f8a61dbddd78ca7ae271`
(ARM9 `c6e2992a...`, kit ARM9 `7200e357...`). Title and Options show v0.10.0.
Player (2026-10-11): has mastered the seven skills, "everything feels very
bread and butter basic", wants "a bit more spice"; picked these three from
eight ideas and asked for real new Red shop slots. The Midnight Line is the
same as in v0.9.0.

- **Three new rows in the Red upgrade list**, below Spider-Sense (scroll
  down): Web Rush 300 XP, Ricochet 300, Momentum 400. They are bought and
  refunded like the others. Nothing is given for free and your purchases, XP
  and prices are untouched. Prices are placeholders.
- **Web Rush.** In a ground combo press A. Spidey fires a line and flies to
  the nearest enemy he cannot already reach (hold Left or Right to choose a
  side), runs three bicycle kicks up his chest and back-flips off. Y then
  carries the combo on where you left it; after the first hit that is Split
  Decision if you own it. A again after the kicks zips to the next enemy. It
  works out of Split Decision and Spin Cycle (the spin restarts with Y), R
  still cancels it, and with an enemy already in reach A does what it always
  did. Up to 56 units away (about two thirds of the screen), same floor.
- **Ricochet** (passive). An enemy you send flying knocks down and hurts
  everyone standing in his path, and they go flying too. It needs a real
  throw (1 unit per update sideways or more): the string finisher and the
  Sense counter throw at 1.5. Leapfrog's kick only pops him at 0.75 and a
  Skyjack spike goes straight down, so those do not count yet.
- **Momentum** (passive). Each combo meter tier shortens the wind-up and
  recovery of your ground combo attacks. Hits land exactly when they did
  before, so nothing whiffs: a Y,Y,Y,Y string that takes 113 frames at tier 0
  takes 99 at tier 2 and 87 at tier 5 with fixed button timing.

How: a second kit code block (the first was nearly full), a Red purchase
table of ten rows, and three ownership bits in unused space the game already
saves (TECHNICAL "Shop tables, menu and free ownership bits", "Second kit
block"). Unowned, Black-suit and native behavior are unchanged.

Known limits: Web Rush has no invulnerability and only targets enemies on
about the same level; R during the dash always rolls forward; Ricochet hits
with the strength of your last hit; Momentum leaves air strings, Perch and
the Spider-Sense counter at native speed.

Agent-tested on `a928843c`: kit qualification 48/48 (the 31 earlier
checks plus Web Rush near/far/chain/unowned/in-reach, Ricochet with a fixed
bystander and with four real Brutes, Momentum hit counts and speed at tier 0
and 5, with Spin Cycle and the Sense counter); the three rows bought, refunded,
re-bought and cleared in the real menu, and kept across save and Continue;
crash hunt 12/12 with the three skills owned; chapter walk routes 6/6 on the
first try (75 checks), power puzzle, save/Continue in Refuge, Rest and Shrine;
door tour 32/32 on a second run (the first, run beside six other emulator
jobs, missed one Nest door; alone it passes); 252 unit tests; frames reviewed
(shop rows and texts, the rush near and far). Rush out of the spin and a
Reflex cancel during the dash were traced once each. Not measured: bosses,
walls between Spidey and the target, enemies above or below him. Feel,
prices and whether tier 5 is too fast are untested by the player. Evidence:
`work/kit/v0.10.0/`, `work/kit/evidence.json`.

Player verdict (2026-10-11, after playing `a928843c`): Web Rush "was cool",
the passives "nice". Spider Reflex and Spider-Sense still carry the native
speed bonuses, so total speed is high and Momentum is hard to notice: the
player wants those two slightly slower and Momentum slightly stronger. The
chapter (v0.9.0 content) was finished on foot, boss included: that it can be
completed is player-confirmed. Complaints: the boss is one of the game's own;
the diagram does not show how rooms connect; some hatches can be crawled into
and lead nowhere; the terrain reads as recoloured sewers plus a hive section;
Nest enemies are far stronger than the sewer ones. The Yard was not
mentioned. Follow-up proposals: TASM_ROADMAP "Round two (2026-10-11)".

## v0.9.0 - 2026-10-11 - Midnight Line: the Yard

Published through Play Spider-Man.cmd's stable ROM. SHA256
`f109a5255b82f57e5290795e566a8f16ec1fbd8711b7c4b6a142a090dbd7432f`
(ARM9 `e54fa1aa...`; kit code unchanged). Title and Options show v0.9.0.
Player (2026-10-11): "keep advancing the map as much as you can and make sure
everything works well". Includes every v0.8.1 fix.

- **New room: the Yard.** The Refuge has a grey door in its left wall. Behind
  it is a freight yard above the line: a warehouse front with shutters, a
  wooden dock, a roof walkway with crates and boilers to throw, and a gang
  that has made camp there (the Pier's thugs). This is a room the game ships
  but never uses, so you have not seen it anywhere. You arrive in a rock
  tunnel at its right end; walk down into the yard. The same tunnel leads
  back. It is right next to the Refuge's save point, with no boss or puzzle
  in the way: a place to fight and use the kit.
- The Yard is on the touch-screen diagram under the Refuge.
- Its test leftovers are gone (ability orbs, red ichor floor and wall, ichor
  gates, hazards), so nothing in it gives or needs a story ability.

Agent-tested on `f109a525`: walk routes 6/6 on the first try, 75 checks (the
five v0.8.1 routes plus the Yard: Refuge door, tunnel arrival, down into the
yard, gang appears, back out, on to the Stairs), door tour 32/32, power
puzzle, save/Continue in Refuge, Rest and Shrine, kit qualification 31/31,
crash hunt 12/12, 248 unit tests; frames reviewed (door in the Refuge, Yard
at night, diagram). Gang strength and count were not balance-tested; not
player-confirmed. Evidence: `work/midnight-line/walk-*`, `work/kit/v0.9.0/`.

## v0.8.1 - 2026-10-11 - Midnight Line: a Nest you can actually walk through

Published through Play Spider-Man.cmd's stable ROM. SHA256
`f68a082e1829a97d2b2d0b4238050918e7c875d80e745c9569b615232385ce1b`
(ARM9 `4bdceb45...`; kit code unchanged). Title and Options show v0.8.1.
Player report (2026-10-11, v0.8.0): went down "this hive section", the top
entrance was sealed by goo, could not break "the red platform thing" without
the power-up, had to quit and lost a little progress. That was the Gate,
entered backwards through the Stairs grate. Walking the chapter with real
inputs showed the Nest could not be finished at all in v0.7.0/v0.8.0.

- **Fix: no room needs Sledgehammer Slam.** The red ichor floors in the Gate,
  the Hollow and the boss room only break to Sledgehammer Slam, the story
  ability of the very boss this chapter borrows and never grants. They are
  gone (the rooms' own "already smashed" state).
- **Fix: Nest fights no longer seal the doors.** Shaft, Throat, Span, Hollow
  and Gate keep their enemies, but the purple crystals never close the exits.
  With the rooms run against their native direction a seal could leave you
  with enemies you cannot reach (the lab reproduced it in the Throat and
  in the Gate). Fight or run; the boss arena is the one sealed fight.
- **Fix: the boss can be reached and fought.** You arrive in the arena's
  lower-right exit corridor. Climb the alcove and step into the arena: the
  ichor walls rise behind you and the fight starts. Before, the walls and a
  hidden timer locked you in the corridor with the boss on the other side.
  When the boss falls the walls and both lower doors open; the touch screen
  says to take the left passage, whose shaft (the Gate) climbs to the Stairs.
- **The Stairs grate is the way out, then a shortcut.** It is locked until
  you have reached the Gate from below; standing on it says so. After the
  loop it drops you straight back to the Gate.
- **Grate hint.** Breaking the boiler now also says how the grate works: stand
  on it, X opens it, Down drops in (the pit is barely wider than Spidey, so X
  alone only drops you when you stand dead centre).
- Needs from your save: Bulldozer Dash for the Span's two red walls (black
  suit, A); you own it.

Agent-tested on `f68a082e` with the new walk routes (`tools/midnight_walk.py`:
real inputs and real doors; lab fixtures: warp into the first room, enemies at
1 HP or parked, boss at 1 HP, health refilled, your ability bits): way in
(sealed grate and hint, breaker, boiler, grate), descent on foot through Shaft,
Rest and Throat into the Span, both red walls dashed, Hollow open where the red
floor was, Gallery, Shrine, boss room (500 frames in the corridor change
nothing; walls rise with the fight; boss; walls gone; left alcove open), Gate
(gap open, top never seals, out through the neck by wall crawl), Stairs,
grate back down: 5/5 routes, 67 checks. Door tour 30/30, power puzzle,
save/Continue in Refuge, Rest and Shrine, kit qualification 31/31, crash
hunt 12/12, 246 unit tests. The two dead
hatches (Entry chimney, Platform trapdoor) cannot trap Spidey. Fights were
not balance-tested; not player-confirmed. Evidence:
`work/midnight-line/walk-*`, `work/kit/v0.8.1/`.

## v0.8.0 - 2026-10-08 - Midnight Line: the power puzzle, hints and an objective board

*Superseded by v0.8.1: the "way into the Nest works" claim below held, but the
Nest itself could not be crossed on foot (red floors, door seals, boss room).*

Published through Play Spider-Man.cmd's stable ROM. SHA256
`d84ae5393d2e3f5cf0c82c3aaa346e087f7804b31f2b6e4a0b67bb8098f2557b`
(ARM9 `dc4911d7...`; kit code unchanged). Title and Options show v0.8.0.
Player (2026-10-08) was about to playtest v0.7.0 and asked the agent to work
on whatever it found worthwhile; the lab then found the Nest blocker below.
The player's battery was last saved before v0.7.0 shipped.

- **Fix: the way into the Nest works.** In v0.7.0 the boiler sitting on the
  Last Platform's floor grate stayed electrified forever (it shocks and knocks
  Spidey back), so the grate never opened and the Nest could only be entered
  backwards through the Stairs' floor grate, reaching the boss first.
- **Power puzzle.** The Platform's tracks are live. On the Stairs landing
  (left of the trash can) there is now a wall breaker: stand at it and press
  X to pull the lever and cut the track power for good. Back on the tracks,
  X lifts the boiler, throw it to smash it, then X on the striped grate drops
  into the Nest. This is the game's own switch/boiler/grate chain, rebuilt
  across chapter rooms; after the breaker is thrown the lever stays down.
- **Hints and objective board.** Short lines on the touch screen (play keeps
  going): entering the Platform while the power is on, pulling the breaker,
  and on entering the Refuge the current objective (cut the power -> go down
  into the Nest -> "The Midnight Line is quiet. For now." after the boss).
  The board checks completion first, so a v0.7.0 player who beat the boss
  through the back way sees "quiet", not "cut the power".

Agent-tested on `d84ae539` (and candidate `bc3aa3a1`, identical except the
Refuge OBJ): `midnight_line.py puzzle` (breaker -> Platform -> lift, throw ->
grate -> Nest Shaft, real presses) passes; v0.7.0 control shocks and never
lifts; thrown-lever pose and no prompt on re-entry; hint, breaker and the
objective lines (incl. completed-without-power) render; native training
message unchanged; door tour steps 0..22 on `bc3aa3a1` (step 23 hit the
Gate's ambush seal mid-run) plus `tour --start 24` on `d84ae539`, and the
Gate -> Stairs exit after fights (seeds 11, 12), i.e. all 30 links;
save/Continue in Refuge, Rest and Shrine; kit qualification 31/31; crash hunt
12/12 (`work/kit/v0.8.0/`); 230 unit tests. Not player-confirmed.

## v0.7.0 - 2026-10-07 - Midnight Line: The Nest, a boss, and the chapter on the map

Published through Play Spider-Man.cmd's stable ROM. SHA256
`c56095be2dfd999adb475c93f5238bd916289dbfe9dce1eb9b3cf4f8563d43b8`
(ARM9 `a19896db...`; kit code unchanged). Title and Options show v0.7.0.
Player asked (2026-10-07, before testing v0.6.1) for as much new content as
possible. v0.6.1 changes are included.

- **The Nest (8 rooms).** The floor grate on the Last Platform's tracks now
  drops into a symbiote nest under the line: Shaft, Rest (save), Throat,
  Span, Hollow, Gallery, Shrine (save), Gate. These are the game's Hive rooms
  (you have only seen Hive_Map01), recoloured and cloned with their own
  encounters: symbiote crowds and fliers (about twice the health of sewer
  thugs), ambushes that seal the doors with purple ichor crystals you smash
  to get out, and two save spheres. All Nest doors are the game's own pairs.
  The Gate's ceiling exit climbs back out through the Stairs' floor grate,
  next to the Refuge, so the chapter is a loop.
- **Boss: the rooftop arena.** Between the Shrine and the Gate is the
  Downtown_Map14 arena (a room you have not visited): an orange symbiote
  mini-boss with its own health bar, ichor gates and timed platforms. Beating
  it marks the chapter completed. Its native reward (Sledgehammer Slam and a
  story collectible) is *not* given, so the main story is untouched.
- **The chapter is on the map.** The Sewer touch-screen map now has a
  subway-style diagram in its empty lower-left corner: the line from the
  arrow (back to the Sewer) through Entry, Station, Platform, Stairs and
  Refuge, with the Nest loop below and the boss marked with a cross; save
  rooms have a dot. Rooms appear as you visit them; the current room is lit.
- Sealed: the Entry's second ceiling hatch and the Platform's top trapdoor
  (their floor-grate partners now lead into the Nest). Entry -> Station ->
  Platform is the way in.
- Dialogue removed from cloned rooms no longer cuts off the script steps
  that followed it (the follow-up group still runs).
- Version text needed the digit 7, which the game's compressed text table
  lacked; the table now gains that symbol (all 1049 strings re-encoded).

Agent-tested on `c56095be`: door tour 30/30 (rooms, arrival points, 14
visited flags, no other flags), save/Continue in the Refuge, Rest and Shrine,
fights end with working exits in Station, Shaft, Throat, Span, Hollow and
Gate (enemies capped at 1 HP), boss fight starts, boss death (HP capped)
sets the completed flag without the native reward and the exit opens, map
diagram drawn and highlighted in game, title shows v0.7.0, kit
qualification 31/31, crash hunt 12/12 (`work/kit/v0.7.0/`), Station ambush
seeds 11/12. Not player-confirmed. Still
missing: power puzzle, Signal Leech (original enemy), Conductor teaser.

## v0.6.1 - 2026-10-07 - Midnight Line: doors that make sense, a visible way in

Published through Play Spider-Man.cmd's stable ROM. SHA256
`c3010cba9255a30645ad9f020d3af284550f42da26b98f728e93b4c94f8ef590`
(ARM9 `817c23a4...`; kit ARM9 unchanged). Title and Options show v0.6.1.
Player feedback on v0.6.0 (2026-10-07): "really cool"; but the entrance was
hard to find (no visible door, "Sewer Map 7" meant nothing in game), doors led
to unexpected places (a ceiling trapdoor came out of a side door and vice
versa), fights were low-level sewer enemies, rooms are recognisably recoloured
sewer rooms, and having no working map was unnerving.

- **Doors now match.** Every chapter door pairs left with right and ceiling
  with floor: climb out through a ceiling hatch and you come up through the
  next room's floor grate. Three of the six links are the game's own
  connections. New layout: Maintenance Entry (arrival) -> up to the Station or
  up to the Last Platform; Station -> right -> Platform; Platform <-> Stairs
  (side door and top trapdoor); Stairs -> left -> Refuge (save sphere).
- **Visible entrance.** A grey doorway now stands at the right wall of the
  sewer save room behind the desk (Sewer_Save02: the save point in the lower
  middle of the Sewer map). Walk through it.
- **Last Platform fight.** The tracks room now runs its native encounter
  record: a crowd including red suits on the roof of a parked subway car.
  Station ambush and the Stairs' three groups remain.
- **Map.** Chapter rooms show the real Sewer map (your explored sewer and its
  save points) instead of an empty "Pier" map. The chapter's own rooms and
  your position are not drawn on it yet.
- Rooms renamed for what they are (Entry, Station, Platform, Stairs, Refuge);
  saves made in the v0.6.0 Refuge still Continue into the Refuge.

Agent-tested: all 14 doors (door kinds checked from trigger/spawn geometry
against 175 native pairs), Refuge save -> Continue, Station fights end with a
working exit (seed 11 also completed the ambush), Platform spawns up to 6
enemies on the train roof, kit qualification 31/31, crash hunt 12/12, native
Sewer_Save02 exit unchanged. Not player-confirmed. Still missing: chapter
rooms on the map, puzzle, Signal Leech, teaser; enemies are native sewer types.

## v0.6.0 - 2026-10-07 - Midnight Line: first station (exploration slice)

Published through Play Spider-Man.cmd's stable ROM. SHA256
`36aa52f8e5aef674d12f18f31aac1ac98aa874c9fed7d7b0d63264cfd9216021`
(ARM9 `efab33e0...` = v0.5.0 kit ARM9 `88328d56...` plus the chapter stage).
Title and Options show v0.6.0. Kit, prices and all native rooms' behaviour
are unchanged except Sewer_Save02, which gains one doorway.

- **Finding it.** In the sewer save room off Sewer Map 7 (Sewer_Save02, the
  one with the save sphere and the man at the desk), walk into the far right
  wall past the desk. Walking back out the Platform's left door returns you
  beside the desk.
- **Five new rooms** of an abandoned, cold-lit subway line (rooms 76-80, built
  from the native sewer subway section with a midnight colour grade):
  Last Platform (tracks; quiet arrival), Service Passage (station with the
  timetable; enemies and a one-time ambush), Switching House (station stairs;
  three enemy groups), Overhead Gallery (upper return route) and the
  Maintenance Refuge (amber emergency light, up the Platform's top-right
  stairs, no enemies, **save sphere**). The rooms form a loop: Platform ->
  Service -> Switching -> Gallery -> back to the Platform.
- **Saving inside the chapter works**: save at the Refuge sphere and Continue
  returns you to the Refuge. Visits and the Service ambush are remembered.
- Not in this slice yet: the power puzzle, the Signal Leech, the Conductor
  teaser and a chapter map (the bottom screen shows the source rooms' map).

Agent-tested (copied saves, lab warps/teleports): all 14 doors in one tour
with correct arrivals; Refuge save -> fresh boot -> Continue restores room 77
(control build without the room guard patch fails); death in the chapter runs
the native health-orb minigame and resumes there; Switching spawns the same 4
enemies as its native room; Service fights end with a working exit (seeds 11,
12; seed 13 inconclusive); native Sewer_Save02 exit unchanged; kit
qualification 31/31; crash hunt 12/12 clean. Not player-confirmed: route feel,
discoverability, encounter difficulty, lighting.
Rollback caveat: a save made inside the chapter is ignored by v0.5.0 and older
ROMs (the battery itself stays intact). Details: TECHNICAL "Midnight Line
chapter build (v0.6.0)".

## v0.5.0 - 2026-10-06 - Test Upgrades sparring room

Published through Play Spider-Man.cmd's stable ROM. SHA256
`fd7e4420f97645dd55011504843ce62f068d1276234c3cd781931c85bb1eb193`
(ARM9 `88328d56...`, kit code `395e9bfa...`). Title and Options show v0.5.0.
Player request (2026-10-06): several enemies in the training room that hit
back, with automatic healing so Spidey does not die. Applies to every suit
(training room only); the Red kit is unchanged.

- **Three sparring Brutes** join Test Upgrades: one left of Spidey's start,
  two at the far right. They use the native Brute AI (walk in, swing, hit
  for one health unit). The original practice dummy stays as a passive
  punching bag.
- **Enemies get back up.** Training enemies have 8 health units instead of 1;
  "defeating" one refills it to full instead of killing it, so the fight
  never empties.
- **Spidey cannot die in training.** He heals to full every 30 seconds, and
  holding SELECT+Down now refills him as well as the enemies. A hit that
  would kill him leaves him on an empty bar instead.
- Help text: "Sparring: you heal every 30 s. SELECT and Down: refill all.
  Pause: Return to Save Point."

Agent-tested: qualification 31/31 (solo-dummy room, unchanged checks), crash
hunt 12/12 sewer fights clean, 163 unit tests. Training room (copied save,
`--sparring`):
idle 3000 frames among the Brutes (healed at 30 s, lethal hits leave him
alive), three 4000-frame random Y/R fights (no stall, all four enemies alive
with 9-12 defeat refills each, SELECT+Down healed him); sewer arena: training
logic never active. Frames reviewed. Not yet player-confirmed: sparring feel,
heal interval, Brute count and spacing.

Launcher-only player performance trial (2026-10-06): `Play Spider-Man.cmd` now
selects `jit-preview` (DeSmuME JIT enabled, block size 12) so the normal play flow
uses the trial. Same v0.5.0 ROM and save; no renderer/resolution/timing overrides.
Launch arguments verified. Player confirmed overall performance was better,
with occasional dips that "weren't bad"; keep JIT12 in the normal launcher.
Broader gameplay/save compatibility was not separately confirmed. Details and
settings/launcher rollback baselines: TECHNICAL "Crowd combat performance".

Next renderer trial launched on 2026-10-06: normal shortcut now selects AUTOGL
at 1x while retaining accepted JIT12, the same v0.5.0 ROM and latest progress.
Prior software/JIT launcher and INI preserved; arguments and renderer setting
change verified. Renderer performance/visual acceptance pending.

## v0.4.1 - 2026-10-06 - Freeze and clip fix; smoother Sense and Leapfrog

Published through Play Spider-Man.cmd's stable ROM. SHA256
`da324b3c5b812fc941f58179386f0489ea151091518c350a5df1bbaf662fed29`
(ARM9 `b806e508...`, kit code `3826b452...`). Title and Options show v0.4.1.
Player report on v0.4.0 (2026-10-06): loving the kit, smooth overall, but
Spider-Sense and Leapfrog feel "teleporty"; a Sense flip clipped Spidey down
into an unreachable area; and the game froze for good during Y/R spam in a
crowd with Enhanced Dodge held.

- **Freeze fixed.** Every Spider-Sense teleport since v0.2.0 wrote Spidey's
  position past the end of his actor object, corrupting nearby heap memory; a
  later allocation then crashed the game (a data abort, which looks like a
  freeze). Spider-Sense no longer writes positions. The kit also checks every
  other enemy's pointers before reading them (a second crash in the Sense scan).
  Details: TECHNICAL "Freeze root cause and crash hunting".
- **Spider-Sense is a dash, not a teleport.** R as an enemy attacks: Spidey
  springs into a tucked front flip over the attacker (4 updates, top speed
  about 3 units per update), turns in the air and whips a roundhouse into his
  back. Walls stop the dash (he counters from the front instead of going
  through the wall). He ignores hits for 7 updates (about 0.23 s) from the
  press, like the old instant teleport did. New counter animation.
- **Leapfrog vault is continuous.** After the kick's hit-stop he moves forward
  every update (6 updates, about 2 units each, cancelling the kick's built-in
  recoil step) and lands about 3 units past the target, facing him; no more
  overshoot, snap back and drop. The flip goes higher in the animation.
- **Spider Perch** rides and head-hops by steering velocity instead of
  writing positions, so walls and ceilings can no longer be passed through.
- **Neutral Spider Reflex** (R with no direction) now consumes the R press; it
  used to consume a queued Y and leave the R queued.

Agent-tested: qualification 31/31 (new: Sense never moves more than 6 units in
one update, Sense next to the training wall stops at the wall where v0.4.0 put
Spidey 2 units inside it, Leapfrog vault continuous). Crash hunt
(`tools/crash_hunt.py`, sewer arena, random Y/R/held-R crowd fights of 4,000
frames with endless enemies, same setup for both): v0.4.1 0 crashes and 0 heap
corruption in 48 fights; v0.4.0 showed fresh heap corruption in 9 of 48 and
crashed in 2 (plus 4 freezes in about 90 earlier fights), every crash the same
abort in a heap pool whose node sits right after Spidey's actor. Frames reviewed for the Sense flip and
the Leapfrog vault. Not yet player-confirmed: Sense and Leapfrog feel, the
guard window, freeze-free long play.

## v0.4.0 - 2026-10-05 - Skyjack spike bowls the crowd

Published through Play Spider-Man.cmd's stable ROM. SHA256
`5e6465d824ef0a27c9372363806deb669703f1d8cbee2e26d2c54402f1d51207`
(ARM9 `b4e91fdd...`, kit code `68b1129e...`). Title and Options show v0.4.0.
Player confirmed v0.3.0 ("looks feels way better") and asked to keep the game
fast: no slow-motion anywhere.

- **Skyjack bowling.** When the spiked enemy hits the ground (it stops falling,
  within 40 updates of the spike), every other enemy within 8 units across and
  6 up/down of the impact takes a native heavy-kick hit: damage (4096 observed)
  and a full knockdown (launched, down, get-up). One impact per spike.
- How: a new hook on the native hit dispatcher keeps a copy of the latest hit
  Spidey deals; the kit replays it (as attack kind 0x1F, the heavy kick's
  knockdown) through each bystander's own ReceiveHit. Enemies in their get-up
  ignore it, as natively. Pointers are range-checked before use.

Agent-tested: qualification 28/28 (new check: hits captured and the landing
detected, nobody bowled with a lone dummy; native/Black parity unchanged with the
always-on capture hook). Sewer arena with live symbiotes (non-deterministic, a
second enemy placed near the landing; most runs have nobody within 8 units of
the landing): on the final bytes the bowl fired in run 2 of 2 (result "taken",
bystander HP -4096, states 41 -> 48 -> 49; frames show the impact spark and the
bystander launched); two earlier candidate builds showed the same. All 153 source tests
pass. Real DSV `75bb8efc...` checkpointed (unchanged). Not yet player-confirmed:
feel, bowling radius, bosses (not tested).

## v0.3.0 - 2026-10-05 - Perch exits, Reflex back tuck, Sense vs ranged

Published through Play Spider-Man.cmd's stable ROM. SHA256
`34736eeb50ae36dfb427ce16e232c3055a87589a9a0d2165a7e241c1880c1647`
(ARM9 `0483dc40...`, kit code `d2c1d4df...` + text). Title and Options show
v0.3.0. Queued roadmap iterations after the v0.2.1 fix; prices/ownership unchanged.

- **Spider Perch: B springs off.** While riding (air attack state 51), B launches
  him high off the head (initial 4.75 units/update up, Left/Right drift) in the Reflex front
  flip. That B is used up, so a second B is needed to web-swing.
- **Spider Perch: A hops to the next head.** A while riding picks the nearest other
  enemy within 24 units (held Left/Right picks the side), faces it and arcs onto
  its head over 8 updates (6-unit peak) in the front flip, landing straight into a
  pound. The perch lets go without a spring if he is hit, Snares or swings; in the
  short falls between pounds native A/B work as before.
- **Spider Reflex: neutral R back tuck.** With no direction held, the in-place
  dodge plays a new 7-sample back tuck (route kind 8 on action 139) instead of
  the native side-step; directional R still rolls with the front flip.
- **Spider-Sense reads ranged attacks.** Besides melee state 15 (within 12
  units), an enemy in state 16 (the ranged attack, see TECHNICAL) within 16 units
  now triggers the flip-behind counter.
- Perch shop text: "Y pound, A next head, B spring."

Agent-tested (training room, copied save): qualification 27/27
(`work/kit/evidence.json`), four new checks that fail on v0.2.1 (Sense vs forced
state 16, B spring height without a swing, head-hop onto a phantom enemy,
back-tuck routing flag). The head-hop target is a lab phantom (fake registry
enemy without AI or hitbox) because arena placements were unreliable; its landing
pound therefore whiffs, and chaining Y after a hop on a real enemy is untested.
Frames checked: spring flip, hop arc, back tuck, Perch text in Powers & Stats,
Options v0.3.0. All 153 source tests pass. Real DSV `75bb8efc...` checkpointed;
v0.2.1 ROM retained for rollback. **Player-confirmed (2026-10-05):** overall
"looks feels way better" after playing v0.3.0; no specific skill was singled out,
so head-hop on bosses and Sense vs spitters remain individually unconfirmed.

## v0.2.1 - 2026-10-05 - Spin Cycle reach and blade legs

Published through Play Spider-Man.cmd's stable ROM. SHA256
`00ca471c9627cf389cce4850423a7dc6a91938f6cc315ad9fbecbe9f72f03bc1`
(ARM9 `e0f1c3d3...`, kit code `d3851f52...`). Title and Options show v0.2.1.
Player feedback on v0.2.0: kit "very good"; the helicopter spin hit only every
other time and looked like breakdancing.

- **Spin Cycle aims every contact.** v0.2.0 flipped facing once per loop, so
  against one enemy every second contact kicked empty air (measured: 7 of 14
  contacts landed). Now, before each of the loop's two contacts, Spidey faces an
  enemy on the other side within 7 units (crowds still get both sides), else the
  nearest within 16 units.
- **Longer reach.** With no direction held, he glides (2 units/update) toward the
  enemy he faces until it is within 4.5 units, from up to 16 units away.
- **Steering no longer ends the spin.** Native Scissor repeats rejected Y with a
  back (or up/down) direction and fell into the sweep; during an owned spin any
  direction now repeats (new hook `0x020B5508`).
- **No slide after the spin.** Steering/glide velocity is cleared when the spin
  ends (v0.2.0 kept drifting ~9 units into the sweep, which then missed).
- **Split Decision never turns off a close target.** Hits 1-2 prefer an enemy
  behind only within 12 units (was 40); otherwise they face the nearest.
- **Blade legs.** New spin clip: legs locked straight (96-99% extension) in a wide
  near-horizontal split (9.5-unit span, 3-33 degrees above horizontal, was 80% and
  45-60 degrees, a V); the forward leg flattens through each contact.

Agent-tested (training dummy, copied save): qualification 23/23
(`work/kit/evidence.json`), including three new spin checks that fail on v0.2.0
(contacts landing vs a lone dummy 14/14, back-steer then glide back, sweep still
in reach). Captured in-game frames show straight blade legs and hit sparks on
contacts. All 153 source tests pass. Real DSV `75bb8efc...` checkpointed; v0.2.0 ROM
retained for rollback. **Player-confirmed (2026-10-05, via v0.3.0):** spin look
and hits feel "way better".

## v0.2.0 - 2026-10-05 - "Never stand still" Red kit

Published through Play Spider-Man.cmd's stable ROM. SHA256
`935d486b93f4aadbd63cbe01c932c7c12f90dcab7c0b51fdfe5b42a002b18537`
(ARM9 `99392f5d...`). Title and Options show v0.2.0. All seven Red purchase
slots are rewritten (design: TASM_ROADMAP). Native A/B/strings/evade, Black form,
shared purchases and unowned play keep native behavior; every hook checks Red
form (actor+0x34 != 1) and the slot's existing ownership bit. Prices, ownership
bits, dependencies and saves are unchanged.

| Slot (bit, XP) | New skill | Implemented first version |
|---|---|---|
| Web Kick (13, 50) | Leapfrog | Native pull + kick connect (lower pop-up); Spidey front-flips over the target in six updates, lands 3 units past and turns back |
| Web Launch (14, 100) | Skyjack | After the Web Vault launch both fall at quarter speed; Spidey drifts to stay within reach; air finisher (action 4) within reach spikes the target to the floor |
| Mid-Air Snare (15, 150) | Spider Perch | Snare follow-ups become the stomp action while Spidey is held on the target's head; Y during the pound chains another pound; spring-off when it ends. Replaces Sling Strike (its hooks restored) |
| Spider Dance (16, 150) | Split Decision | Branch hits 1-2 turn to an enemy behind (held Left/Right wins), sweep takes the nearest; Y+back continues the branch |
| Scissor (17, 200) | Spin Cycle | Repeats run 10 more times; Left/Right steers; facing flips each loop so contacts alternate sides |
| Amazing Speed (18, 250) | Spider Reflex | R cancels Red ground/air attack states immediately; held Left/Right turns and rolls, neutral dodges; the string node survives 28 updates so Y resumes at the next hit. Native speed bonus kept |
| Ultimate Speed (19, 350) | Spider-Sense | R while an enemy within reach is in its attack state (15): Spidey appears behind it, facing it, straight into the heavy string kick (node 14). Native speed bonus kept |

New authored animations (procedural FK/IK, Catmull-Rom curves) replace the Rush
clips (Split Decision corkscrew/split kick/breakdance sweep) and add six routed
clips: Reflex flip, handstand helicopter, perch pound, Leapfrog kick-vault,
Skyjack axe kick and Spider-Sense tornado kick. Routing swaps an action's SCA only
while its skill is active; native actions keep their bindings.

Agent-tested (training room, copied save, disposable RAM; work/kit/evidence.json,
20/20 checks): every mechanic above, including damage/contact and positions; Red
bits cleared and Black-form inputs match v0.1.1 state/action/facing/position
sequences up to a uniform one-frame load phase. Spider-Sense also triggered
against live symbiote attacks in the Sewer room left of the save (story-room copy).
Menu text, purchase and boot version visually checked. All 149 source tests pass;
candidate regeneration is byte-identical. Real DSV `3f65dfac...` checkpointed and
unchanged; v0.1.1 ROM and composition retained for rollback.

Not yet player-confirmed: feel, readability, crowds/bosses, walls/ceilings,
camera, heap headroom (reserve grew 16 -> 24 KiB) and Enhanced Dodge interplay
(its native successive dodge can delay a Reflex resume). Perch requires a target
the Snare can lock; Spider-Sense reads enemy state 15 only (other attack states
unknown). No slow-motion or tingle marker yet.

## v0.1.1 - 2026-10-05 - Affordable Both Suits tools

Published through Play Spider-Man.cmd's stable ROM. SHA256
`bcc6974a08b899a2def261b550b8bf9a31b005e201c7c4e276fc46dbf3e5d842`.
Title, pause label and Options header show v0.1.1. Red prices and current combat
carry over unchanged. All seven Both Suits purchase prices are reduced:

| Shared purchase | Previous XP | v0.1.1 XP |
|---|---:|---:|
| Launching Uppercut | 50 | 25 |
| Enemy Kick-Off | 200 | 50 |
| Drill Kick | 400 | 100 |
| Jackhammer Stomp | 600 | 150 |
| Air Dodge | 200 | 50 |
| Enhanced Dodge | 800 | 200 |
| Quick Recovery | 800 | 150 |

Total 3,050 -> 725 XP (-76.2%). Existing ownership, story/traversal gates, native
shared moves, black/Core rows and save format remain intact. Native refunds use
the new prices; the publisher never changes XP or purchase flags in the real save.

Agent qualification: native menu buys each row separately, taking a disposable
5,000-XP fixture to 4,275 XP. All seven purchase bits/XP survive native save/reload.
Each native refund restores its new price; full refund returns 5,000 XP and clears
all seven bits, also verified after save/reload. Nonshared flags stay unchanged.
The same seven buys on v0.1.0 cost 3,050 XP (5,000 -> 1,950 control). Title/pause/
Options visually checked; regeneration byte-identical; all 3,736 resources verify.
Only seven shared price words in ARM9 and two versioned text resources differ
from v0.1.0. Original ROM and exact 634-byte real DSV are unchanged, with checkpoint
and old/new compositions retained. All 141 source tests pass against the published
files, including exact reconstruction of the previous numbered release.

Evidence: work/shared-economy/publication.json and full-tests.log;
build/boot-tests/Versioned-bcc6974a/{buy-all,reload-all,refund-all,reload-refunded,
boot-version,options-version}; candidate build/version-0.1.1.
Historical numbered profiles retain their own pinned prices/version metadata;
v0.1.0 still reconstructs to its exact published hash.

Current combat design lives in TASM_ROADMAP. New movements, cancels and crowd
webs remain proposals/research; this price release does not claim that overhaul
or player acceptance of earlier combat motion.

## v0.1.0 - 2026-10-05 - Versioning and affordable progression

Published through the stable launcher. Exact ROM SHA256
`e1b66ebdad90856f7af5a508bd2bcd78ade0640c6926e6668da2c6b36cee1451`.

- Boot prompt shows TASM v0.1.0. Pause-menu Options label and Options-page header
  show Options v0.1.0, with native audio/control entries intact.
- Seven Red-row XP prices change below. Ownership, requirements, levels, strings
  other than version labels, black/shared rows and native buy/refund/save routing
  remain. Existing ownership carries over; refunds use the new row prices.
- Documentation now has exactly six core roles. A layout/size test prevents new
  feature/release/session Markdown and long startup handoffs. Machine catalogs
  moved to reference/; research is consolidated in TECHNICAL.
- The ambitious TASM redesign is recorded as future work. Its new names/behaviors
  are not displayed/granted as if implemented. Current combat mechanics carry over.

| Current Red purchase | Old XP | v0.1.0 XP |
|---|---:|---:|
| Rebound | 100 | 50 |
| Web Vault | 200 | 100 |
| Sling Strike | 600 | 150 |
| Oscorp Rush | 400 | 150 |
| Scissor-Kick Special | 600 | 200 |
| Amazing Speed Boost | 800 | 250 |
| Ultimate Speed Boost | 1,000 | 350 |

Total 3,700 -> 1,250 XP (-66.2%). Existing ownership and progress are preserved.
Agent validation: title/pause/options visual captures pass; all 1,049 strings in
both locales round-trip, unedited slot bytes/prefix/tree preserved; price patch
changes only seven 32-bit words. A native Rush purchase takes 2,000 -> 1,850 XP;
its purchase bit and XP survive save/reload. Native refund takes 267 -> 417 XP and
relocks the row. Deterministic regeneration is byte-identical and all 3,736 ROM
resources verify. All 139 source tests pass against the published composition.
The player's exact 634-byte DSV and wrapper are unchanged; prior ROM and old/new
compositions are retained. Publication evidence: work/version-research/publication.json.
Player acceptance of the overall gameplay/old authored motion remains open.
Evidence: `build/version-0.1.0/`, `work/version-research/`,
`build/boot-tests/Versioned-e1b66ebd/`. Build/read-only tests never write research
save results into the player's Battery directory.

## Included legacy gameplay and visuals (before numbering)

- Movie-inspired128x128 red suit with cleaned panels/black lenses; white alternate
  appearance, clearer menus, red mission marker and bounded instruction changes.
- Free Snap Sweep replaces the red opener's resource binding while retaining its
  logical credit/follow-ups; player-confirmed. Other actor bindings remain.
- Rebound replaces Web Kick; shorter recoil plus a closer/higher enemy juggle.
  Native purchase/refund/save checks pass. Retuned feel needs player acceptance.
- Web Vault replaces Web Launch, with paid player rise alongside a successful
  enemy launch. Initial version player-confirmed; matched rise/no backward drift
  revision is agent-tested, revised feel/ceiling/boss checks remain open.
- Sling Strike replaces Mid-Air Snare: finite passing kick, clean stop/turnaround.
  Gates/native total budget/save routing agent-tested; ordinary encounters/feel open.
- Oscorp Rush replaces Spider Dance with three completely authored clips: punches,
  uppercut, knee/high kick, overhand finish. Latest revision uses larger windups,
  camera-plane extensions and brief bounded limb translations. Dedicated IDs3733..3735
  isolate choreography; native six paid contacts/clocks/HP/credit/root data stay.
- Compact continuous wounded-enemy health bars and transient composite combo
  numeral. Visible damage panels were removed per player request; actual common
  HP telemetry remains private for balance. Specialized coverage/crowding open.
- SELECT+Down restores native training-target HP without leaving Test Upgrades;
  positive/flag-clear controls preserve position, reaction, XP and combo.
- Stable launcher, byte-preserving DSV checkpoints, prior ROM/composition retention,
  guarded profiles/resource append and deterministic compact changed GMB encoding.

Rejected/reverted experiments: green-suit first proof, yellow mission marker,
dance-like Rush sway and compact/stubby boxing revision. They are evidence/history,
not current shipped claims. Threaded idle benchmarks, JIT/preload/HD previews and
Blender bridge investigations are technical research, not proven lag/HD fixes.

## Selected historical milestones

| Date / identity | Meaning and validation |
|---|---|
| 2026-10-02 / clean round trip + green proof | Exact no-op ROM; one visible texture edit cold-boots |
| 2026-10-04 / Web Vault | 81 tests and isolated checks; player later confirmed initial move |
| 2026-10-04 / feedback -> Sling -> combat flow | Higher/closer Rebound, compact bars, paid Sling, matched Vault;92 then96 tests; player refinements open |
| 2026-10-04 / original Rush + training | 102 tests/native gate/refill controls; authored-animation tooling followed |
| 2026-10-04 / 8bc72be4 | Full authored Rush, dedicated isolation and count-only control;125 tests |
| 2026-10-04 / f0382e98 | Compact refinement;125 tests; rejected by player as stubby |
| 2026-10-05 / 4d36970e | Exaggerated authored Rush;8 pose tests,3,736 verified resources; maintenance later passed131 source tests; feel still open |

Full hashes, recipes, checkpoints and replay evidence are in retained private
release/candidate folders and archived original notes. Do not invent version
numbers for these previously unnumbered builds. Ordinary/dense AI, incoming hits,
walls/ceilings, specialized enemies/bosses, interruptions and long play remain
checks for any substantial combat release.
