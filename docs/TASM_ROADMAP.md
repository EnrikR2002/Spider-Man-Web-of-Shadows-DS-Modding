# TASM: never stand still

Current design and player feedback, reviewed 2026-10-23 (America/Edmonton).
[TASKS](TASKS.md) owns the live build and next action; [CHANGES](CHANGES.md)
owns shipped behavior; [TECHNICAL](TECHNICAL.md) owns engine evidence and
unknowns. Build and review procedures are in [DEVELOPMENT](DEVELOPMENT.md).

## Current direction and acceptance

Keep one combined TASM1/2 Red kit: fast, acrobatic, spider-like combat against
strong and web-resistant enemies. The loop is **strike -> cancel with R ->
reposition -> resume**. Native A/B/base strings/evade, purchases, dependencies,
Both Suits traversal, story gates and earned rewards remain the foundation.
Overclock, Dragnet and Vortex are the final added Red skills. Fun and spectacle
lead. The 2026-10-22 request activates the selected 2099 Black-slot rework,
appearance first. The 2026-10-23 requests replace its combat proposal with the
film-faithful Hunter design below (revision 2: talon, web, air and boss pillars,
adding Black rows as the kit needs; not implemented). Prices, third suits and
campaign expansion remain deferred.

The current release is **v0.31.0**. Vortex is now a cocoon-only tethered
catapult/slam, the Conductor has a larger symbiote war-machine body and one boss
meter, and low-HP Vitality damage is corrected. The player's liked boss combat
programs remain. Cape-free Across the Spider-Verse 2099 and the compact Terminal
atlas remain. Native purchases, traversal and chapter progression stay intact.
Agent qualification does not establish player feel/appearance acceptance or
actual DeSmuME pacing.

| Player evidence | Decision that still matters | Later implementation / limit |
|---|---|---|
| 2026-10-23 review of Hunter revision 1: better overall, but pin/pound dominates into one trick, pins fail on bosses, no webbing, no air combos; add as many rows as a coherent kit needs, within the base game's 2D mob/boss brawler | Four pillars (talons, webs, air, boss); pinning becomes one finisher; Vulture-style Boarding for bosses; webs on X; eight new Black rows on free saved bits. | Revision 2 design only. First a Web Yank pipeline proof, then the Sky slice; no player verdict exists until a slice ships. |
| 2026-10-23: make Black play and fight as close as possible to Across the Spider-Verse's Miguel O'Hara; make it fun to play | Replace the comic-style juggle proposal with a film-faithful pursuer on the exact native A foundation. | Revision 1 (pin-centred), superseded the same day by revision 2; archived. |
| 2026-10-22: Vortex is boring; keep it conditional on regular-web/Dragnet cocoons. Boss fights well but needs larger symbiote metal war-machine anatomy, one boss bar, and a low-HP damage fix. | Rework Vortex inside its existing paid row; preserve liked boss combat; separate a shared Vitality clamp defect from boss behavior. | v0.31.0 ships the tether catapult/slam, larger articulated armor, boss-only texture and raw-damage fix; native boss timings/AI remain. Agent qualification is in TASKS; player feel/appearance acceptance remains open. |
| v0.30.2 Terminal enemies were white while the 2099 player rendered | Restore the custom enemy texture bindings in the crowded scene while retaining artwork and geometry. | v0.30.3 I4 atlas binds all three observed enemy materials. One qualified scene, not all-room or player-acceptance evidence. |
| v0.30.1 appearance liked overall; latest supplied Across the Spider-Verse image; remove the red web cape | Use the movie's navy/red mask, angular chest spider and shoulder panels; remove cape geometry rather than hiding it. | v0.30.2 implements and agent-tests this appearance. Player visual acceptance is still open. At v0.30.2, Terminal enemies remained unbound; v0.30.3 resolves the sampled crowd. |
| v0.30 appearance is a good start, but cape and forearm blades look bad; correct placement and add Spider-Verse-like muscle | Prioritize the web cape, surface-mounted blades and a stronger upper-body silhouette before combat implementation. | 0.30.1 E ships actual shared-mesh selection, a larger crimson web and balanced muscle volume; the player's new visual verdict is open. |
| Early kit play, v0.2-v0.4 | Keep responsive cancels, continuous movement and crowd play. Snap Sweep and original Web Vault are player-confirmed. | Later revisions require their own feel verdict; early praise does not approve every subsequent move. |
| v0.23 rejection, 2026-10-18 | Unconvincing hits, slow/odd animation and recognizable voices were unacceptable; room shapes were repetitive. | v0.24 repaired contact, lifecycle/audio scope and actual room envelopes. |
| v0.24 replay, 2026-10-18 | Preserve the improved environment and more distinctive enemy direction. Rigid motion, poor SFX and the slow/easy boss were rejected. | v0.25-v0.27 change motion, sound and anatomy; final enemy quality remains unconfirmed. |
| v0.25 replay, 2026-10-18 | The boss still lacked effective pressure responses; monsters seemed silent. | v0.26 adds physical responses and paired in-game audio evidence. Playback evidence does not establish sound quality. |
| v0.26 replay, 2026-10-19 | Harder/cooler mobility was welcome; blanket stagger suppression prevented combos and frustrated the player. | v0.27 restores ordinary hurt openings and limits protected commitment. |
| v0.27 replay, 2026-10-19; latest feedback | Combos are only slightly better; the boss is too easy, appears idle or misses, and the ramp is not felt. Remove two save rooms and fix the upper map order. | v0.28 addresses these requests. No v0.28 player verdict is recorded. |

Crane Row's earlier creature/presentation rejections also remain relevant.
Published fixes to rewards, voices, routes and the hoist do not establish that
its final enemies, encounter rhythm or finale are player-approved.

## Current player kit

The seven original Red slots retain ownership and native input gates. This is
the implemented kit's role map; it does not promise every interaction in an old
design draft. Unowned/native behavior and Black ownership remain protected.

| Native slot | Current move | Input / purpose |
|---|---|---|
| Web Kick | Leapfrog | Y during grapple; cross-up vault/kick. |
| Web Launch | Skyjack | Up during grapple; rise, aerial pressure and spike. |
| Mid-Air Snare | Spider Perch | Air A toward enemy; perched attacks, hop/spring exits. |
| Spider Dance | Split Decision | Y, pause, Y sequence; crowd-facing string. |
| Scissor-Kick Special | Spin Cycle | Split Decision extension/repeated Y; steerable spinning pressure. |
| Amazing Speed Boost | Spider Reflex | R during Red attacks; cancel, reposition and resume. |
| Ultimate Speed Boost | Spider-Sense | Timed R against supported threats; reversal with Reflex dependency. |

Additional shipped Red purchases are Web Rush, Ricochet, Momentum, Overclock,
Dragnet and Vortex. Both Suits Vitality I-III already exist. Preserve these rows,
their ownership and refund rules; they are not a queue for more skills or stats.
The current move/price catalog is [suit metadata](../reference/suit_roadmap.json)
and [upgrade metadata](../reference/tasm_upgrade_plan.json). Prices are retained,
with balance tuning deferred.

The v0.15.1 seven-contact Vortex was rejected as boring on2026-10-22. Its
replacement uses Down+Y with an actually webbed nearby enemy (regular A or
Dragnet), then one continuous tethered catapult and floor slam; R can cancel.
Keep the same paid Red row and the original A/B/base strings/evade. Current
candidate qualification is in TASKS; its new feel needs a player verdict.

## Recommended build order

The three Vortex/boss/health fixes requested on2026-10-22 take priority. The
2099 Hunter combat design waits for the player's go-ahead and its first-slice gates.
The chapter reviews below remain player gates when campaign iteration resumes.

The three requested follow-ups now ship in v0.29. Use its published route as
the comparison baseline; further changes need a new version.

| Delivered follow-up | Agent evidence | Remaining player question |
|---|---|---|
| Skyjack native movement | Open contacts, both walls, R exits and all 68 kit checks pass. Native/Black and unowned controls retained. | Does the corrected drift retain the desired aerial reach and responsiveness? |
| One complete Rail Skitter | Private mesh, full lifecycle motion and eight cues; all three attacks hit, native death rewards and current-owned mixed Terminal clear pass. | Does it feel fluid, distinct and satisfying at normal speed in the actual mix? |
| Ballast/Long Arm finish | Parent Freight ceiling loop reproduced; edge-clear/return works on two roofs. Red/Black wins/save/Continue and visible hoist states pass. | Are vertical pressure, warning readability, openings and the finale satisfying? |

### 1. Establish the v0.29 full-route verdict

Replay with actual purchases and ordinary native damage. Check whether the
Conductor lands fair attacks, accepts meaningful combos, counters sustained
pressure and leaves readable recovery. Compare Terminal, Floodworks, Turbine
Rise and Observatory for a felt rise in pressure, with quiet travel and safe
arrivals between fights. Check map order, the return loop, retry travel and earned
save/Continue. Assess Skitter's whole body and tell/contact/hurt/death cues at
native scale and normal speed; numerical audio playback evidence is insufficient
to decide quality. These are player verdicts, separate from lab fixtures.

Midnight has eight active rooms. Signal House/Pump Refuge remain retired; Relay
Sanctuary is the main-route save room. Keep the environment/direction the player
accepted. The final skills remain Overclock, Dragnet and Vortex.

### 2. Refine encounter decisions from the replay

The reliable counter carrier, bounded guard response, ordinary combo openings
and late-room ramp already ship. Target observed unfair overlap, idle gaps, weak
pursuit or repetitive pressure. Teach roles before combining them and retain
reachable combat landings. Prefer purposeful staging and decisions over raising
every room's HP/crowd count. Retain native boss damage/death, health meter and
saved shutdown. Keep protected commitment bounded and recovery punishable.

### 3. Review Crane's complete vertical route and payoff

Crane already has twelve rooms, two exploration loops, maps, saved power and
shortcuts, original enemies/rewards, a hoist finale and an approach checkpoint.
v0.29 corrects the reproduced Ballast overhead case and improves the hoist's
warning/guard/open/wreck presentation. Review actual traversal through the whole
route before deciding whether upper roofs need further navigation work or the
finale needs pacing changes. Two tested roofs do not prove every pursuit path.
Keep quiet checkpoints/cache, restrained harbor art, short map goals and detailed
Objectives. Moving counterweights remain scenery above fixed landings.

### 4. Extend creature presentation only after the example works

If the player accepts Skitter's normal-speed motion, silhouette and mixed audio,
apply the proven authoring approach to Warden, Eye and Conductor one at a time.
Each needs distinct patterns/voice plus complete hurt, knockdown/get-up and death.
If Skitter still fails the standard, refine it first. Pose sheets, sample counts
and clearability alone do not authorize another roster-wide pass.

## Acceptance for a future candidate

- Gameplay: native movement/collision, fair contacts, meaningful combos/R exits,
  baseline Red/Black viability and complete enemy lifecycles in mixed terrain.
- Presentation: review native-scale normal-speed footage and mixed audio before
  expanding the example. Clearability and sample counts do not decide fun.
- Persistence: preserve purchases, dependencies, rewards, story abilities and
  earned clears; test retries and fresh Continue using copied latest batteries.
- Composition: prove changed-byte scope, real-input doors for changed rooms and
  appropriate broad controls on one stable final candidate, then publish a new
  version through the guarded workflow.
- Player confirmation: record the actual verdict separately. Full-route fun,
  final creature quality and DeSmuME frame pacing remain open until observed.

## Spider-Man 2099: Black-slot rework

**Appearance (published).** v0.30.3 keeps the guarded shared-model selector and
native Red list, with Black wearing the cape-free navy/red Across the
Spider-Verse look requested on 2026-10-22 (movie reference supplied, red web cape
removed; the player liked the prior 2099 overall). Its model and native motion
are unchanged from v0.30.2. The same release compacts the shared Midnight enemy
atlas to 8 KiB I4, which binds the sampled Terminal crowd. One mixed scene is not
all-room residency, player visual acceptance or DeSmuME pacing. Details are in
`reference/spider2099_movie.json` and `reference/spider2099_enemy_texture.json`.

### Combat: the Hunter (design rev. 2, 2026-10-23)

The player's 2026-10-23 review of revision 1 found the direction better but
flawed: pinning and pounding dominated into a one-trick style, pins had no
answer against bosses, there was no webbing and no air combo, and seven rows
were an unnecessary limit. Add as many Black rows as a coherent kit needs, and
keep the movie identity inside the base game: a 2D side-view brawler against
mobs and bosses. Revision 1 and the 2026-10-22 proposal are archived as
`RETIRED_2099_DESIGNS.md`. Nothing below is implemented, agent-tested or
player-confirmed.

**Movie read.** Miguel is big, serious and relentless. He leads the Spider
Society's hunt for Miles and ends it by pinning him to a speeding train's roof.
Against the Vulture he climbs onto the villain's back, tears off a wing and
holds on as the Vulture rockets upward. His web lines are heavy and glowing
(one review calls his weapon a lariat). He is reportedly animated on ones, so
his weight comes from fluid motion, not stiffness
([film](https://en.wikipedia.org/wiki/Spider-Man:_Across_the_Spider-Verse),
[chase](https://intothespiderverse.fandom.com/wiki/Hunt_for_Miles_Morales),
[Vulture](https://intothespiderverse.fandom.com/wiki/Spider-Man:_Across_the_Spider-Verse)).

**Game read.** Mobs arrive in crowds and already support the vocabulary this
kit needs: stagger, knockdown, launch to about 25 units, air juggle, web yank
and hold, floor drag and far throw (TECHNICAL "Hit pipeline"). Bosses do not:
the Conductor turns knockdowns into standing staggers, and native mini-bosses
sit outside the kit's enemy registry. The native combo meter gives less for
repeated contacts, so a varied kit scores better than a one-trick one.

**Identity: Red never stands still; 2099 never lets go.** Red slips around a
crowd and resumes. 2099 takes a target where he wants it (into the air, into
the crowd, into the floor) and uses it against the rest. What he cannot move,
he climbs. Four pillars, each with its own verbs:

| Pillar | Verbs | Job |
|---|---|---|
| Talons | slash, hook, shred, tackle | Ground pressure that moves through and behind targets |
| Webs | yank, reel, lasso, zip | Pull light enemies in; heavy ones pull Miguel to them |
| Air | lift, rake, catch, dive | A complete launch -> air combo -> crash loop |
| Boss | board, ride, rip | The Vulture answer: climb what cannot be thrown |

**Rules.** Ground A Power Dash, air A Hammer Spike and air Down+A Hammer Slam
keep their exact native input, movement and barrier/floor story use, and never
need a target. Ordinary B, base Y strings, unowned R and shared upgrades stay
native. Purchases change enemy-contact outcomes or add follow-ups; unowned rows
behave natively and no ownership moves. R always lets go and evades. Anything
heavy (a boss or resistant enemy) pulls Miguel to it instead of moving. No
freezes, slow motion, player position writes or permanent stun.

**Webs on X.** Black has no web button: A is the dash. In Black form, X with
no native X prompt in reach becomes Miguel's web: at range a Web Yank, up close
a Collar Toss, split near the native Web Kick's 13-unit threshold. Lift, lever
and grate prompts always win. If the lab shows X cannot be shared safely, pick
a fallback input with the player before building.

**The kit: fifteen rows.** The seven native Black rows keep their bits 20..26
and native dependencies. Eight new rows use free saved bits 83..90; five free
bits (91..95) stay spare.

| Row | Move | Input | Mobs | Bosses / heavy |
|---|---|---|---|---|
| Webbed Fury | **Rundown** | A again after a dash hit, up to two links | Re-dash at the tumbling target or the next enemy ahead; the last link knocks down. | Shoulder check that stops on contact. |
| Power Launch | **Talon Lift** | Up+A; keep holding Up to rise | A rising claw launcher; holding Up carries Miguel up with the target into Sky Rake, releasing keeps him grounded. | Miguel rises to its head height instead. |
| Ground Rebound | **Freefall** | Native Down+A slam | A head-first dive; strength and radius grow with drop height up to a cap. Bounced enemies can be juggled. | Height-scaled heavy hit: the punish from above. |
| Black Widowmaker | **Talon Line** | Y,Y,Y, pause, Y,Y | Slashes that walk through the target, then a hook that flings it behind Miguel. | Two close slashes. |
| Poison Pummel | **Shredder** | Y,Y,Y, pause, repeated Y | A steerable, forward-walking flurry. The last press's direction picks the ender: Up launches, Forward blasts back, Down smashes to the floor. | Flurry, then a heavy rip. |
| Super Charge | **Talon Pounce** | Hold Y, release; Up aims high | A long talons-first leap at the enemy ahead or above: a knockdown on the ground, an air-combo starter in the air. | A strike; Up-pounce reaches its head or starts Boarding. |
| Quick Charge | **Relentless** | Passive | Halves the coil. Any 2099 ender can cancel into Pounce or Web Yank, so the hunt flows to the next target. One stored cancel. | Same. |
| New, bit 83 | **Web Yank** | X at range; Up+X yanks upward | A thick glowing line pulls the enemy into a talon strike, or up into a launch. | Zips Miguel to it (into Boarding if owned). |
| New, bit 84 | **Collar Toss** | X up close | Grab, hoist and throw along the D-pad; the thrown body knocks down whoever it hits; Down slams it to the floor. | Overhead hammer strike. |
| New, bit 85 | **Lariat** | Hold X during a Web Yank | Swing the tethered enemy around Miguel through the crowd, then fling it. A horizontal crowd sweep, unlike Red's overhead cocoon slam. | The line snaps and Miguel zips in. |
| New, bit 86 | **Sky Rake** | Air Y in Black form | The air string becomes four talon rakes and a flip kick that pops the target higher. | Air hits at head height. |
| New, bit 87 | **Reel In** | X in the air | Yank a grounded enemy up to Miguel to extend or restart the air combo. | Zips Miguel to it. |
| New, bit 88 | **Meteor Catch** | Air A on an airborne enemy | Catch it, flip and spike it into the floor; it bounces once, ready for Talon Lift or Roof Pin. Native Hammer Spike otherwise. | Native Hammer Spike. |
| New, bit 89 | **Roof Pin** | Down+Y on a downed enemy | The train-roof moment as one short finisher: pin, three tearing hits, kick away. Not a mash and not a hub. | Not available. |
| New, bit 90 | **Boarding** | Web Yank, Up-pounce or jump into a boss/big enemy while holding toward it | Cling to its back or shoulders: Y rakes, A **Wing Ripper** forces a stagger and kicks Miguel off into the air, its attacks throw him off, R leaves. | The boss tool. |

Shop chains use one-level rows: native Widowmaker -> Shredder and Super Charge
-> Relentless remain; new chains are Web Yank -> Collar Toss -> Lariat and Sky
Rake -> Reel In -> Meteor Catch; Roof Pin and Boarding stand alone, so every
pillar has a cheap entry. Prices stay deferred.

**What mob fights should look like** (purchases and nearby targets required):

- **Hunt:** Web Yank the enemy at the back -> Talon Line through it -> hook it
  behind -> Relentless pounce onto the next.
- **Sky:** Talon Lift holding Up -> Sky Rake -> Meteor Catch into the floor ->
  Talon Lift the bounce, or Reel In a fresh victim from the air.
- **Crowd:** Collar Toss into a group -> Rundown through the falling bodies ->
  wall climb -> Freefall onto the pile -> Sky Rake a bounced one.
- **Lasso:** Web Yank -> hold X for Lariat through the crowd -> fling -> Roof
  Pin whoever lands nearest.
- **Tag team:** Red cocoons a group -> L -> Collar Toss a cocoon into the rest
  (needs a cocoon-throw lab).

**Boss fights: the Vulture plan.** Bosses stagger but do not fly, fall or get
thrown, so Miguel moves instead:

1. **Close in:** Web Yank or Up-pounce zips him to the boss.
2. **Board:** cling to its back, away from its front attacks; Y rakes.
3. **Rip:** Wing Ripper's heavy tear forces a stagger and throws him clear.
4. **Punish the stagger:** Sky Rake at head height, then Freefall from above.
5. **Respect it:** its next attack throws a rider off; R or Kick-Off leaves,
   and he re-boards when it recovers. Riding ends when the boss shakes him or
   he rips, not on a timer.

No forced boss movement, permanent stun or invented armor breaks. Board, rip,
punish and get shaken off gives every boss a back-and-forth rhythm.

**Starting feel targets** (tuning starts here; the player decides): Pounce
crosses about 25 units in under half a second and never passes a wall; a Lariat
is one swing; air combos use native juggle reactions; Boarding follows the
boss by velocity, as Perch does, never by position writes.

**Presentation.** Author every clip with continuous curves at full sample
density, heavy anticipation, shoulder- or talon-led contacts and overlap; no
per-key holds. Poses: a low wide crouch, splayed talons, a stretched pounce, a
head-first dive and a clinging rider. Tint 2099's web lines red if the WebLine
colour field allows (native white is 0x7FFF). Use native impact audio; do not
rename stock attacks as new moves.

**Engineering gates before the first slice:**

1. **Space:** the 32 KiB kit stays exact for Red. 2099 needs its own guarded
   code/state block, as v0.31's autoload page did: a deliberate contract change.
2. **Shop:** move the Black list into the kit block as v0.10 moved Red's, append
   rows on bits 83..90 (events 392..399) with appended strings, and keep the
   seven native rows' bits and dependencies exact.
3. **Inputs:** prove X sharing with native prompts, held X/Y from the kit's key
   words, Down+Y on a downed enemy against native ground Down+Y, and air X.
4. **Black-only animation:** route Black-form actions to appended clips. The
   air string actions and GroundAttack15 are shared; G11/16/17 have m6.xbd users.
5. **Bodies and webs:** reuse the proven reaction kinds and the WebLine
   spawn/tie path from Vortex and Dragnet.
6. **Bosses:** Boarding needs a Perch-style velocity follow, plus a
   class-specific target adapter for native mini-bosses. Start on the Conductor.

**Build order:** one slice at a time, each with a player verdict before the next.

1. **Pipeline proof:** Web Yank alone (X input, red line, Black-only clip
   routing and the heavy-target rule).
2. **Sky slice:** Talon Lift, Sky Rake, Reel In and Meteor Catch: the first
   loop worth playing.
3. **Boss slice:** Boarding with Wing Ripper, Freefall and Talon Pounce +
   Relentless, on the Conductor.
4. **Crowd slice:** Rundown, Collar Toss, Lariat, Talon Line, Shredder and Roof
   Pin.

**Changes from revision 1:** pinning shrinks to one finisher on downed enemies
(Roof Pin), and Pounce, Freefall and Collar Toss no longer feed it. Poison
Pummel becomes Shredder. Webs, a complete air loop and a Vulture-style boss
plan arrive with eight new rows.

## Deferred work

| Idea | Current boundary |
|---|---|
| More Red skills, extra stat rows, prices/balance, save expansion | Deferred. Iterate the existing Red kit; Overclock/Dragnet/Vortex are its final added skills. The 2099 Black rows above are the only authorized shop growth and fit existing free saved bits. |
| Spider-Man 2099 combat | Hunter revision 2 above; nothing is built until the player approves its Web Yank pipeline proof. Preserve native A traversal, paid ownership and shared upgrades. |
| Third suit and other suit concepts | Deferred; TASM1/2 share one kit. No suit selector or migration is implemented by this roadmap. |
| Downtown Grid/Lost Lab, Residential Skyline Run, Hive Quarantine Heart | Deferred concepts. No new allocations are authorized by the old pitches; audit current flags/storage before any future expansion. Hive stays post-story. |
| Midnight Express, gauntlets, timed replays, collectibles/reward systems | Backlog ideas, not unfinished work required for the current chapters. |
| Moving trains, rideable loads, changing solid platforms | Need a complete native collision/ownership prototype before promising a set piece. |
| Cross-room timers/pursuit and broader music routing | Need lifecycle/channel-budget evidence. Existing timers and audible cues do not prove these larger features. |

## Historical designs

The full pre-cleanup roadmap and three planning catalogs are preserved byte for
byte in the existing verified archive, snapshot 2026-10-21. They retain detailed
early kit fantasies, rejected moves, Signal Leech/Crane construction pitches,
old allocation estimates and the seven-skill 2099 theorycraft (superseded on
2026-10-23 by the Hunter design; both retired 2099 drafts are in
`RETIRED_2099_DESIGNS.md`). They are historical
context, not a second active plan. Later implementations and player decisions
above supersede their original next/proposed wording.

```powershell
python tools/doc_archive.py list roadmap
python tools/doc_archive.py read docs/TASM_ROADMAP.md --toc
python tools/doc_archive.py read docs/TASM_ROADMAP.md --section 'Spider-Man 2099'
python tools/doc_archive.py read reference/tasm_upgrade_plan.json --lines 40
python tools/doc_archive.py read RETIRED_2099_DESIGNS.md --section 'revision 1'
```

Shipped release history stays in CHANGES; format/engine discoveries stay in
TECHNICAL. Neither belongs in a new session or release Markdown file.
