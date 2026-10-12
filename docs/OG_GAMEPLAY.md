# Original game behavior

USA CS5E baseline, before mod changes. Exact native records/flags/costs are in
`reference/original_gameplay.json`; engine addresses and unknown fields are in
[TECHNICAL](TECHNICAL.md). Shipped mod behavior belongs in [CHANGES](CHANGES.md).

## Controls and shared foundation

DS buttons: Y attacks, A uses suit powers, B jumps, X lifts/throws, R evades,
L switches form, D-pad moves/aims. SELECT switches minimap/objective view.
Observed local keyboard equivalents are Q/W/Space/T/E/R; mappings are player-local.
A combo “pause” means a gap between attack presses, not opening the Pause Menu.

Wall crawl/run/jump, ceiling hang, swinging and object interaction provide the
shared movement foundation. Red fights through web control, pursuit and tempo;
black emphasizes force, recall and commitment. Shared purchases supplement both.
Story acquisitions such as Reinforced Web enable heavy-object barriers; Ichor
movement and form-specific barrier interactions protect progression.

## Native suit powers

### Red foundation

| Tool | Input | Native role |
|---|---|---|
| Web Grapple | A; D-pad aim | Hold enemy or object |
| Web Pull | Away from facing direction during grapple | Pull enemy into other enemies |
| Web Zip | A + direction in air | Reach surface |

### Black foundation

| Tool | Input | Native role |
|---|---|---|
| Power Dash | A on ground | Dash contact throws enemy back |
| Hammer Spike | A in air | Drive enemy downward |
| Hammer Slam | Down + A in air | Ground impact damages surrounding enemies |

## Native purchases

Bought/refunded with XP at save points (the list shows four rows, scrolls and
wraps; A on an owned row refunds it); Test Upgrades allows practice in a bare
room (Test_Combat01) against one passive Brute dummy that never attacks, has 1
health unit and cannot die (a lethal hit leaves it at a sliver). Existing
ownership is native ability bits, also used by gameplay and saved by the game.
These are **original prices**, not the current mod prices.

### Red

| Upgrade | XP | Input / role |
|---|---:|---|
| Web Kick | 100 | Y during grapple; Pull target in and knock it back |
| Web Launch | 200 | Up during grapple; Launch held target |
| Mid-Air Snare | 600 | A in air toward an enemy; Pursue enemy and perform short combo |
| Spider Dance | 400 | Y, pause, Y, Y, Y; Early pause branch into advanced ground string |
| Scissor-Kick Special | 600 | Y, pause, Y, repeated Y; Rapid-kick extension |
| Amazing Speed Boost | 800 | Passive; Increased red attack speed |
| Ultimate Speed Boost | 1000 | Passive; Maximum advertised red attack speed |

### Black

| Upgrade | XP | Input / role |
|---|---:|---|
| Webbed Fury | 100 | A after Power Dash hit; Recall target and attack again |
| Power Launch | 200 | Up + A; Launch enemy while player remains grounded |
| Ground Rebound | 600 | Hammer Slam hit; Bounce struck enemies into air |
| Black Widowmaker | 400 | Y, Y, Y, pause, Y, Y; Late pause branch into advanced ground string |
| Poison Pummel | 600 | Y, Y, Y, pause, repeated Y; Late barrage extension |
| Super Charge | 800 | Hold Y during strikes; Charge strikes |
| Quick Charge | 1000 | Passive charge modification; Halve time to full charge |

### Both Suits

| Upgrade | XP | Input / role |
|---|---:|---|
| Launching Uppercut | 50 | Up + Y; Launch enemy |
| Enemy Kick-Off | 200 | B against mid-air enemy; Kick backward off enemy |
| Drill Kick | 400 | Y from roll; Multi-hit kick |
| Jackhammer Stomp | 600 | Down + Y in air; Four-hit stomp |
| Air Dodge | 200 | R in air; Mid-air evade |
| Enhanced Dodge | 800 | Hold R, steer Left/Right; Successive directional dodges |
| Quick Recovery | 800 | R after hit or knockdown; Prompt recovery and counterattack opportunity |

The two speed boosts play Red attack animations at 1.15 and 1.3 times normal
speed (run-time tuning values, read 2026-10-11); this covers the air string,
the back attack, the ground string and the rapid stomp.
Spider Dance is the parent of Scissor-Kick Special; Amazing Speed Boost is the
parent of Ultimate Speed Boost. An owned child prevents refunding its parent.
Other surrounding story/menu availability may add conditions. Shared Air Dodge,
recovery and traversal do not become free because a Red move launches a target.

## Combo meter, rewards and combat limits

The native meter is a combo resource, not a hit counter. Contacts earn category
credit; repetition and rising tiers reduce gains. Gauge spans0..100, with up to
five tiers. Crossing100 advances a tier and subtracts75. Grace expires into decay;
losing a tier resets gauge to75 and speeds up decay. The HUD initially appears
only at tier>0 or gauge>30, so an early credited attack can have no visible meter.

The meter improves XP rewards and damage: measured 2026-10-11 on the Red
ground string against the training dummy, each tier adds 10% (tier 5 hits for
1.5 times tier 0). Exact reward multipliers, all penalty triggers and several
target/contact categories remain unresolved. Attack
response strength, credit and actual HP loss are distinct values; only measured
HP changes establish damage. Update counts are not verified seconds.

Native action states, animation action IDs and resource IDs are separate. Enemy
resistance, collision and purchased skills determine valid routes; animation
changes alone do not prove new mechanics. Exact evasion/cancel/recovery windows,
specialized health paths, room entities/triggers and all story gates remain
research. The complete earlier gameplay/engine notes are preserved in the archive:
`ORIGINAL_GAMEPLAY.md`, `UPGRADE_ENGINE.md`, `COMBO_ENGINE.md`.

## Rooms, save points and near-death

The world is 75 rooms (Downtown, Hive, Pier, Residential, Sewer, plus test rooms)
joined by edge doors: walking into an edge loads the neighbour and places Spidey
beside its matching door, facing into the room (side doors walk him a few steps
in; overhead doors drop him). Connections keep direction: a left door leads to
the neighbour's right door, and a ceiling hatch to its floor grate. Part of the Sewer is an underground subway
station (Sewer_Map02 station and timetable, Sewer_Map03 tracks, Sewer_Map13
stairs). Each room marks itself visited on entry; certain first entries advance
the mission counter (Sewer_Map01 and Sewer_Map03 do). Some rooms run one-time
ambushes that lock their doors while enemies are alive. Hive ambushes seal the
doors with purple ichor crystals: when the wave is dead the crystals crack and
must be hit to reopen the door (running into one does nothing). Enemies spawn
around the room's spawner, not at the doors, and may stand behind a crystal.
Rooms also hold small switch puzzles. On the subway tracks (Sewer_Map03) the
rails and a boiler sitting on a floor grate are electrified: touching them
shocks and knocks Spidey back. A wall switch in the room above (Sewer_Map04,
X at the lever) cuts that power for good; then X lifts the boiler, throwing it
smashes it and unlocks the grate, and X on the grate opens it. The pit under a
grate is barely wider than Spidey: he drops in when he stands on its centre as
it opens, otherwise he stays on the rim and Down drops him in.
Liftable objects and grates show an X prompt when Spidey stands at them.
Mini-boss rooms (e.g. Downtown_Map14's rooftop arena) show a boss health bar
across the top; the boss's reward orb is a collectible that grants a story
ability. The six story abilities, one per mini-boss, gate progress: Ichor Crawl
(Sewer_Map06), Ichor Web (Downtown_Map05), Tarantula Strength
(Residential_Map08), Reinforced Web (Sewer_Map09), Bulldozer Dash (Pier_Map08:
black suit, dash with A through red ichor walls) and Sledgehammer Slam
(Downtown_Map14: black suit, Down + A in the air through red ichor floors).
Without the ability a red wall or floor cannot be broken at all.
Hive rooms are tall shafts climbed by wall crawl (run or jump into a wall,
then Up; Up also follows the ceiling) and repeated jumps (B again in the air);
B on a wall jumps off it.

The touch screen shows the current area's map: rooms appear once visited
(the current one lit), save rooms as S icons, and the mission marker "!",
with the area's name under it. A button switches between this Mini-Map page
and the Objectives page. A zoom button cycles three views: x1 the area, x2
the world (the five districts as blocks), x3 the detailed map of the current
room with its door arrows, which says "Detailed Mini-Map unavailable" until
the area's map item is owned. Rooms of the unused sixth area (the debug rooms)
get no map at all: the page stays on Objectives.

Wall crawling depends on the surface (measured in the game's own surface test
rooms, 2026-10-12): most walls and ceilings can be climbed; black ichor
surfaces only with the ichor story abilities; some surfaces can never be
climbed; some hurt on touch (one health unit and a knock-back). A jump beside
a climbable wall while holding toward it runs up it to the ceiling.

The top-screen HUD shows a spider emblem, a health bar with one segment per
health unit (red in the Red suit, purple in the Black suit) and a row of blue
pips under it. Pickup orbs for health, damage, defence and the map exist as
resources (levelled natively; not studied).

Save rooms hold a save sphere: X opens Save Options (Save, Buy Upgrades, Test
Upgrades, Continue); Save asks "Do you want to save your progress?" then shows
"Save Complete". Continue from the title resumes in the saved room.

At zero health a touch-screen minigame starts: collect health orbs and touch
poison orbs to burst them. Doing badly ("Failure! Very little health
replenished") still resumes play in the same room with a little health.
Technical formats: TECHNICAL "Native doors, spawns and game variables".
