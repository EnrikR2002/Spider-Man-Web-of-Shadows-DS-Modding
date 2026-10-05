# TASM: make the fight a playground

Latest user direction: **FUN COMES FIRST.** The 26-skill catalog was rejected as
overwhelming. This replaces it. The design below is proposed; v0.1.1 remains the
published game. Implemented behavior belongs in [CHANGES](CHANGES.md).

## The pitch

**Enemies become stepping stones, bowling balls and launch points.**

Spider-Man should ricochet through a crowd: tag someone, spring over their swing,
zip to another attacker, sling a body through the group, then web the surrounding
threats and launch away. The next exciting choice should be under the same few
buttons. Short attacks and movement must join smoothly enough that the player
can improvise without remembering named moves.

Make one complete acrobatic kit feel great before deciding how to sell upgrades.
Bounce, target transfer, useful air steering and escape cancels belong together
in the prototype. They are no longer separate purchases on a 26-item checklist.

## What the player remembers

Proposed DS controls, to be tested against the native controls:

| Input | Immediate purpose | What makes it fun |
|---|---|---|
| B + direction | Jump; near an enemy, vault or spring off them | Bodies become footholds. Choose where to leave; ordinary jumping works without a target. |
| Tap A + direction | Web-zip toward the chosen enemy | Cross the fight quickly. Arrive ready to hit, bounce or change your mind, with no compulsory attack string. |
| Hold A, aim, release | Sling a webbed enemy in that direction | Bowl them into a group, pop them upward or drive them into a wall. The throw's route creates the opportunity. |
| Down + A | Burst webs around Spider-Man | An immediate, readable opening when surrounded, usable on the ground or in the air. |
| Y | Short, expressive strikes | A hit becomes a springboard into the next decision; continued presses can continue attacking. |
| R + direction | Evade and leave danger | A responsive cartwheel/flip escape, including forgiving recovery from eligible ordinary hitstun in the prototype. |

X keeps object interaction and L keeps form switching. No skill wheel, target
cycling chore or extra button for every animation. Tap/hold A must share immediate
web/target feedback; test its release timing so the tap never feels delayed.
Down+A from neutral has explicit burst priority; aiming a held tether is a
separate visible state. If that distinction proves confusing, simplify the input
before adding content. Native movement/traversal conflicts must be tested.

These are four new combat interactions to understand: **bounce, zip, sling,
burst**. Hitting and evading use familiar controls. Animations and target context
provide variety while the player's intent stays consistent.

## The interactions that should sell it

**Crowd surfing.** Zip toward a thug, hit once, then press B to spring across his
shoulders. Aim at the next enemy and tap A while airborne. You can work across
the group without touching the floor by deliberately making fresh contacts.
Air steering, input buffering and the next target's clear highlight are included.
The first prototype should be generous about finding the enemy you meant.

**Enemy bowling.** Web a front-line attacker and sling him sideways through his
friends. Immediately chase with a zip or vault over the pile-up. A wall can turn
the throw into a rebound setup. The meaningful addition is directional placement,
physical crowd reactions and immediate follow-up choices; the native game
already has a grapple/pull, so another renamed kick would fail this goal.

**The surround escape.** Burst webs as the crowd closes in, spring over the
nearest body and zip toward the exposed ranged enemy. The burst must visibly
interrupt the approach long enough to use the opening. It should work as a
standalone escape tool, without a long combo or a charged meter first.

**The trick.** Vault over a committed swing so it misses behind you, sling the
attacker back toward the group, then change targets. Pursuers should repeatedly
arrive where Spider-Man used to be. More elaborate enemy-on-enemy attack redirection
can wait; spatial movement and a convincing miss must already make this amusing.

The same basic inputs produce these routes. A new destination, wall or crowd
shape changes the outcome. We do not need separate purchases for every link.

## Feel before balance

Start the isolated prototype with the whole kit enabled, generous targeting,
strong movement, generous cancel/buffer windows and a useful web burst. Let it
be overpowered while establishing the fantasy. Do not spend this phase pricing
skills, rationing air hops, adding cooldowns, designing XP sinks or matching native
damage budgets. The user explicitly prioritizes fun over balance.

B/A/R should let the player leave ordinary attacks promptly. Ordinary hitstun
needs a deliberate rescue input rather than repeated helpless relaunches.
Keep actual grabs, cutscenes, invalid targets and room transitions as explicit
engine states; clearing hitboxes/links correctly is stability work, not balancing.

Use quick starts, stretched travel, compressed spring-offs, readable airborne
silhouettes and satisfying contact/landing feedback. A tiny hit pause can sell a
contact if it preserves control; long pauses cannot interrupt the rhythm.
No automatic cinematic should keep playing after the player chooses to leave.

## Build the smallest version that can prove the fun

1. Capture one reproducible crowd encounter on a copied battery. Use existing
   player/target traces to measure where native attacks and hitstun trap input.
   Start with the current Sling approach, native kick-off/vault, grapple/pull and
   dodge/recovery routes as research entry points, not assumed finished features.
2. Build **bounce + zip + immediate escape** as one connected prototype. First
   test: cross three attackers, change direction in flight and leave after one
   strike. Author the motion needed to make these transitions visible.
3. Add the **web burst**, then **directional enemy slinging/collisions** in that
   same room. Test both with movement immediately; avoid separate duel showcases.
4. Give the player one test build with a tiny control card and quick encounter
   restart. Judge whether they start improvising and want another run. If the
   basic loop feels awkward, revise it before progression or more mechanics.
5. Only after that, decide which few upgrades add exciting twists. No target
   skill count, no fixed purchase mapping and no need to spend every late-game XP.
   Additional shop rows/save migration are deferred until a fun mechanic needs them.

This prototype is a ROM implementation target, not an existing build or an
external toy demonstration. Native feasibility of target transfer, crowd binds,
collisions and cancels still needs proof. Use disposable saves/RAM and isolated
candidates; public progression and existing ownership require a deliberate
migration when the kit is qualified. Do not modify the real save to unlock tests.

## The playtest that decides what stays

Can the player describe the controls after one fight? Can they bounce across a
crowd, change their mind mid-approach, make space while surrounded and resume
moving after an ordinary hit? Do different target choices create visibly different
routes? Is the second attempt fun before any upgrade purchase?

Try the same tools alone and together, both facing directions, against several
attackers and near walls. Target loss, a missed input and a blocked landing must
return control cleanly. Measure stuck time, wrong targets and unwanted animation
commitment; actual HP remains useful telemetry, but damage balance is secondary.
The player saying “that was fun; let me try this other route” is the success gate.

The combined TASM identity stays first. The selected later-suit backlog remains
in reference/suit_roadmap.json. Use this document in place; do not create a new
skill catalog, experiment Markdown or progression document.
