# Current work and handoff

Updated2026-10-21 (America/Edmonton). Read AGENTS first. Workflow: DEVELOPMENT;
engine contracts: TECHNICAL; shipped behavior: CHANGES; design: TASM_ROADMAP.

## Current player direction

0.27 is only slightly better for combos; the boss is too easy/appears idle or
misses, and the ramp is not felt. Remove Signal House77/Pump Refuge82 and their
incoming doors. Correct the upper map order to match play. Reliability and fun
are the priority. This supersedes0.27's optimistic agent balance claims.

Preserve native abilities/purchases/ownership/rewards and32KiB player kit.
Overclock, Dragnet and Vortex remain the final added skills. Prices, third suit,
shop/save expansion and other branches stay deferred.

## Published identity and current candidate

Stable build/Spider-Man-WoS-modded.nds is0.28.0; canonical, active recipe,
release_info and history match. Guarded publication completed. Prior identity:
reference/midnight_finale.json; preflight/backups:
work/midnight-reliability/publication-preflight.json.
Accepted final K: build/version-0.28.0-final/Versioned.nds. Its exact hash,
changes, retained controls and qualification: reference/midnight_reliability.json.
Stable, canonical, candidate and release metadata identify
6819cb91e824961552b86690c3fdd112930bbd1cbb70d5c3c76978b5ce932a20. The previous
0.27 ROM/metadata/recipe are retained. The latest actual634-byte DSV still matches
the publication checkpoint. Published bytes are immutable.

## Findings and implementation

A live0.27 probe confirms native type8 uses Terminal8/3 and Observatory12/4:
the budget change was real, but insufficient. Counter74 plays with active
GMB/GAB yet produces no native boss-to-player contacts in grounded B pressure.
C's verified136 route produces actual result4/HP loss. Normal136 and counter136
are distinguished by owned descriptor pointer. State-only poise also left
incoming native impulses active; the new guarded adapter skips only that
impulse block, preserving native damage/death and normal hurt outside commitment.

Native block states26/27 dominate much of F's Red fight. I queues a counter after
12 guard updates, retaining its cooldown, and resets private owners/slots during
the native arena RUN=0 lifecycle to avoid stale retry data. Both decision passes
share short normal impact commitment and full counter commitment. Native movement
brakes in reach/faces during gaps; no player placement or slow time.

77/82 are absent from the active graph/map and their main-room trigger/events/
portal geometry are removed. Orphan IDs retain safe one-way recovery for old
checkpoints. Eight rooms are unfolded in actual left-to-right travel order,
including87 ->89 ->88 and an explicit return loop. Main doors keep their IDs.
Late rooms now have stronger mixed groups, staged native constructor HP, a
four-actor cap, faster Skitter pursuit and committed Warden windups. Player
abilities/kit, enemy meshes/animations/textures/audio and Crane are preserved.

190 broad checks and45 focused/publication checks pass with explicit byte-scope.
I current-owned Red wins/saves; J Black does likewise. All18 directed doors pass
on final K. All four ramp rooms clear without agent refills using the measured
current purchases/XP/initial HP. K reduces Terminal live cost4->3 and stages
Turbine's late wave on a continuous upper landing; both are requalified. Boss
phase reaches all four programs. No-R attack pressure dies from native damage;
R/B reactive controls win. Both earned saves pass fresh Continue/cleared-boss
return on K. Removed-entry and legacy recovery checks pass; the first legacy
script hit the save prompt and is retained as a driver failure. Native map view
is reviewed; only one save-room icon remains. Native guide strings no longer
send players to the removed saves.17 resources change;15 binary resources
round-trip. Enemy resources/audio and32KiB kit are exact to0.27.

## Safety and next exact action

The latest actual634-byte DSV was freshly read and copied into
work/midnight-reliability; no research data was written to it. Original ROM is
unchanged. Source/documentation and permitted authored references are being
prepared for GitHub; ROMs, batteries, extracted game art/audio and binary texture
conversions remain private.

Next: commit and push the completed source/docs change set to the existing GitHub
remote, excluding ROMs, extracted copyrighted assets and local build/playtest data.
Fun/full-route balance and actual DeSmuME pacing remain player gates; Crane
overhang limitation is unchanged.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
