# New playable suit: design and research plan

2026-10-04. **Active kit: combined TASM 1/2 identity.** The user selected a
shortlist and requested one suit at a time, beginning with the existing movie
recolor. Persisted selection:
`SUIT_ROADMAP.json`. Stage one now replaces one red-form attack; a third slot,
new combo tree, custom conditional ability and new save fields remain future work.

**Latest constraint:** the user playtested Snap Sweep and Web Vault successfully.
Snap Sweep stays the free base opener. The safe implementation path replaces
paid red-suit upgrades with native gates; the broader ten-plus-tool design and
flexible prices live in `TASM_EXPANDED_ROADMAP.md` and remain ideation until
progression support is proven. Current release status is in `TASKS.md`.

## TASM 1: quick, scrappy, evasive

**Decision: develop through the existing red form first.** This produces a playable
change while mapping action/event/hit routing. The archive currently cannot add
resource IDs. A third form also requires selector, model loading, transformation,
ability dispatch, UI and memory research. The executable retains player/state-machine
RTTI, providing concrete leads. Shared spd.xbd does not imply identical form kits:
runtime tests now prove distinct opening attacks in red and alternate forms.

Our proposed loop: **quick opener -> evade -> web reconnect -> launch -> air finish**.
These are custom ideas inspired by the movie's acrobatic fights, not powers
canonically granted by wearing its costume.

| Move / system | Proposed play | Status |
|---|---|---|
| **Snap Sweep** | Compact opening low kick, then continue the normal ground string | Implemented using an existing synchronized action triplet. Measured duration 24 versus 44 emulator frames. Native successors still execute. This is action reuse, not a new combo tree. |
| **Rebound** | Grapple -> pull into kick -> closer/higher launch | Released through the native Web Kick slot; current trajectory and feedback evidence are in `COMBAT_FEEDBACK.md`. |
| **Web Vault** | Grapple -> launch -> short player hop into the air | Released through the native Web Launch slot; the early window remains a setup for future paid pursuit/control. |
| **Slip Counter** | Well-timed dodge enables one stronger follow-up; waiting or missing consumes it | Planned first custom conditional ability. Map dodge, hit confirmation, collision and timers before patching. Tune the timing window through playtests. |
| **Momentum** | Successful counters/web follow-ups reward continued movement; getting hit or missing breaks the reward | Later transient passive; requires hit detection and suit gating. Avoid a new persistent save field. |

Proposed balance: short commitments and repositioning, modest raw damage, limited
heavy crowd clearing, no permanent invulnerability or infinite web stun. The low
kick's damage/reach/contact count have not been quantified. These balance goals
are not already implemented.

### Play the first step

Use `Play Spider-Man.cmd`, then Continue. Existing local controls are **Q = DS Y =
attack**, **R = DS L = switch form**, **E = DS R = dodge**, **Space = DS B = jump**.
In red TASM form, tap Q on the ground for the low kick; repeat Q to continue the
base string. Switch with R to compare the white form's original opener. No new
purchase is required for the opener. Existing other unlocks are retained.

The clean panels/black lenses, white alternate texture, readable instructions and
yellow mission marker are included. See `TASM1_IMPLEMENTATION.md` for exact edits,
runtime evidence and current limits.

### Current sequence

1. Completed: appearance, stable save association, pre-play/pre-release backups,
   previous-ROM rollback, input replays, read-only player telemetry.
2. Completed: one red action rebind, different pose/duration, native combo
   successors, alternate-form control and unchanged save bytes.
3. Next: hostile encounter checkpoint; map damage/contact/cancel behavior and
   implement one Web Rebound transition. Cover interruptions, misses, air/wall,
   crowds, death and room transitions before extending the kit.
4. Then: Slip Counter as one separately tested condition, followed by Momentum.
5. Independent third slot after selector/loader/ability routing is understood.

The agent handles save checks, backups, publishing and checkpoint restoration for
every release. The player's flow is open launcher, play, save in-game, close.

### Retained shortlist

Ben Reilly: impact webs/stingers/setups. Classic 2099: talons/aerial pursuit, later
glide/venom. Kaine: aggressive close combat/burst counters. Raimi: weighty punches,
strong web pulls/recovery. Classic symbiote: heavy control/charges/finishers.
TASM 2 is merged into the active combat identity; a later appearance can remain a
cosmetic variant. The expanded proposal is in `TASM_EXPANDED_ROADMAP.md`. These
backlog concepts are not parallel implementation tasks. Earlier Ben/2099 proposals
below remain useful design research.

The complete concept catalog is in `SUIT_IDEAS.json`: costumes, alternate
Spider-people, and a few deliberately labeled inspired designs. Alternate people
could initially be thematic player skins; that would not implement a full character
conversion, narrative, voice, proportions, or separate skeleton.
Every listed move is a design proposal, not a promise of engine support or a claim
that its costume canonically grants that power. Names and broad visual themes are
the starting references. Avoid tiny texture details: prioritize large panels,
readable eyes, one clear emblem, then a distinctive animation or effect.

## Two particularly promising directions

### Scarlet Spider: Ben Reilly, the web tactician

Visual: red bodysuit, blue sleeveless hoodie impression, dark chest spider, pale
lenses, wrist gear. Use the current skeleton for the first texture prototype;
a painted hoodie impression is possible, while an actual hood requires mesh work.

Marvel confirms Ben's impact webbing and sedative stingers in its
[Scarlet Spider profile](https://www.marvel.com/characters/scarlet-spider-ben-reilly).
Those suggest distinct gameplay without borrowing Kaine's identity or making
clone summoning a supposedly canonical Ben power.

Proposed combat loop: **restrain -> reposition -> launch -> web pull -> finish**.

- **Impact Web:** a concentrated shot briefly cocoons one enemy. Upgrade later to
  a small splash bind only if targeting and status mechanics support it.
- **Stinger:** a quick single-target interruption. Bosses get a short stagger at
  most; no permanent stun or unavoidable one-shot incapacitation.
- **Scarlet Rebound:** web pull -> launcher -> air kick -> rebound finisher.
  First prototype should reuse a known compatible action, without claiming that
  an animation rebind automatically adds a new input sequence or damage behavior.
- **Web Snare:** later ground trap, with a small concurrent-trap limit.
- **Resource identity:** efficient setups, limited raw damage; missed webs consume
  capacity. Immobilization builds resistance so crowds cannot be bound forever.

Potential payoff: web combat feels purposeful instead of becoming a second heavy
black suit. It is a strong first choice if the existing web/grapple machinery can
be reused. Projectile, status and suit-specific routing remain unconfirmed.

### Spider-Man 2099: the committed aerial predator

Visual: deep blue body, large red skull-like spider, angular red mask pattern.
Start without a cape. The broad color design should read well on the DS screen.

Marvel confirms Miguel's talons, venomous fangs, organic webs and airfoil glide in
its [2099 profile](https://www.marvel.com/characters/spider-man-2099-miguel-o-hara).
Our combo names and balance rules below are custom proposals.

Proposed combat loop: **close in -> rake -> launch -> pursue -> slam**.

- **Talon Rake:** short multi-hit melee string ending in a rising slash.
- **Predator Descent:** airborne attack -> descending strike -> landing finisher.
  Begin by investigating the existing launcher and dive actions, without assuming
  their named payloads already supply the desired hitboxes or suit-specific rules.
- **Venom Pin:** grab finisher gives a brief stun. Apply enemy resistance and a
  cooldown; a bite close-up/new animation is optional later art work.
- **Airfoil:** later short directional glide. Limit fuel/airtime, preserve collision,
  and test doors, ceilings and progression gates before allowing it broadly.
- **Resource identity:** consecutive successful hits charge one stronger finisher.
  Hits land hard but commit to recovery; the suit has less safe crowd control.

Potential payoff: immediately different attack cadence and a visually clear design.
Talons can initially be implied by effects and existing poses. Actual talon geometry,
gliding and a cape are later work. Time slowdown is an optional custom idea, not a
canonical costume ability or an already available engine feature.

## What the ROM actually supports so far

The clean archive exposes `spd.nsbmd`, `spd.nsbtx`, `spdB.nsbmd`, `spdB.nsbtx`,
and one player-prefixed actor definition, `spd.xbd`. There is no `spdB.xbd` in the
manifest. This does **not** prove that both forms share every move, or that the
engine supports only two possible forms. Suit selection and action routing may
live in executable code, other resources, or unknown XBD fields.

`spd.xbd` contains 311 parsed archive references; its opaque tail begins at 0x4F0.
Existing references can be replaced with existing IDs of the same type while
retaining other bytes. One synchronized red-action rebind is now runtime-tested.
Our Glob repacker
currently replaces resources and refuses adding archive IDs/names.

The manifest contains 13 numbered GroundAttack triplets: 1..6 and 11..17, not a
continuous 1..17 set. Assets named DashSlamAttack, DiveKick, RisingLauncherAttack,
GrapplePullAttack, GrapplePullAttackKick, and Transform are also directly bound.
Names are leads, not verified input mappings or semantic descriptions of payloads.
Read-only candidate metadata is recorded privately in
`build/suit-research/bindings.json`; no binary payloads are placed in this document.

| Action family | SCA binding offset / ID | GMB offset / ID | GAB offset / ID |
|---|---|---|---|
| GroundAttack1 | 0x158 / 3368 | 0x15C / 3367 | 0x160 / 3366 |
| GroundAttack2 | 0x1B8 / 3392 | 0x1BC / 3391 | 0x1C0 / 3390 |
| DashSlamAttack | 0x0A8 / 3324 | 0x0AC / 3323 | 0x0B0 / 3322 |
| DiveKick | 0x0C4 / 3331 | 0x0C8 / 3330 | 0x0CC / 3329 |
| GrapplePullAttack | 0x120 / 3354 | 0x124 / 3353 | 0x128 / 3352 |
| GrapplePullAttackKick | 0x12C / 3357 | 0x130 / 3356 | 0x134 / 3355 |
| RisingLauncherAttack | 0x3A4 / 3514 | 0x3A8 / 3513 | 0x3AC / 3512 |
| Transform | 0x40C / 3540 | 0x410 / 3539 | 0x414 / 3538 |

Offsets are bytes in clean `spd.xbd`. Tags are SCA=0, GMB=3, GAB=4. The meanings
of damage, active frames, hitboxes, state transitions, suit gates, and opaque-tail
fields remain unknown. Do not change an apparent number as if it were damage.

## Incremental implementation

1. **Choose identity and a small kit.** Pick one visual, one passive concept, one
   combo, one signature move, and one meaningful limitation. Save extra ideas for
   later. TASM 1 is selected; the active kit above supersedes the catalog-choice step.
2. **Appearance prototype.** Use an isolated existing-form replacement, clearly
   labeled as a temporary prototype. Validate texture/model round trips, retain
   all unrelated accepted mods, cold-boot, and inspect front/back/movement poses.
3. **Prove one action mapping.** Record the existing input and animation from a
   battery checkpoint. Select a compatible player action and a bounded same-type
   binding experiment. Document whether one reference or a synchronized action
   triplet must change. Boot and check timing, hit response, interruption, and
   exact edit/revert bytes. This is evidence gathering, not yet a new combo tree.
4. **Prove one gameplay field/transition.** Compare matched GAB/GMB/SCA actions and
   relevant runtime state. Change only a justified field or transition, retaining
   everything unknown. Verify an observable effect with a paired baseline. Do not
   invent damage or hitbox offsets from names or plausible-looking values.
5. **Deliver one themed combo and one signature ability.** Implement only the
   mechanisms established by the preceding experiments. Test ground/air/wall,
   interrupted moves, multiple enemies, boss resistance, and unlocked/locked cases.
6. **Add a genuinely separate selectable slot.** Investigate the form selector,
   model/texture loader, action routing, resource limits and selector UI early;
   ship the independent slot after they are understood. Retain both existing forms
   and their accepted visuals. If new archive IDs are necessary, extend the
   container and runtime consumers together with full identity/resize tests.
   This likely needs a targeted ARM9 patch; it is not enabled by adding a texture.
7. **Progression and polish.** Prefer an initially always-available third slot if
   that avoids unproven save changes. Only then investigate unlock persistence,
   purchase/menu text, tutorial prompts, and long-play stability. Preserve existing
   save fields and prove compatibility before changing any save layout.

Acceptance for the eventual full feature: all three suits selectable; different
move behavior actually observed; existing red/white visuals retained; save and
Continue work with older progress; no accidental ability requirements bypassed;
no crash on transformation, death, room transition or boss fights. Those are
future acceptance criteria, not results of this ideation pass.

## Reference scope

Broad costume inspiration is documented by
[Insomniac's suit artists](https://blog.playstation.com/2019/09/03/the-secret-history-of-marvels-spider-man-suits-as-told-by-insomniac-artists/),
[Marvel's Iron Spider history](https://www.marvel.com/amp/articles/comics/iron-spider-suit-history-explained),
[Marvel's Spider-Verse overview](https://www.marvel.com/articles/comics/weirdest-spider-heroes-variants-spider-verse-so-far-list),
and the [Identity Crisis collection](https://www.marvel.com/comics/collection/40070/spider-man_identity_crisis_trade_paperback).
Sources support names/themes; the custom mechanics in the catalog remain proposals.
