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

Bought/refunded with XP at save points; Test Upgrades allows practice in a bare
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

The meter improves XP rewards. Exact reward multipliers, all penalty triggers,
damage scaling and several target/contact categories remain unresolved. Attack
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
in; overhead doors drop him). Part of the Sewer is an underground subway
station (Sewer_Map02 station and timetable, Sewer_Map03 tracks, Sewer_Map13
stairs). Each room marks itself visited on entry; certain first entries advance
the mission counter (Sewer_Map01 and Sewer_Map03 do). Some rooms run one-time
ambushes that lock their doors while enemies are alive.

Save rooms hold a save sphere: X opens Save Options (Save, Buy Upgrades, Test
Upgrades, Continue); Save asks "Do you want to save your progress?" then shows
"Save Complete". Continue from the title resumes in the saved room.

At zero health a touch-screen minigame starts: collect health orbs and touch
poison orbs to burst them. Doing badly ("Failure! Very little health
replenished") still resumes play in the same room with a little health.
Technical formats: TECHNICAL "Native doors, spawns and game variables".
