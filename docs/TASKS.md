# Project tasks and session handoff

Updated: 2026-10-04 (America/Edmonton).

## Resume here

**Current release: compact boxing refinement of authored Oscorp Rush**,
published through `python tools/playtest.py build` to
`build/Spider-Man-WoS-modded.nds`. Profile **tasm-oscorp-rush-authored** composes
seventeen guarded overlays. Published ROM, qualified candidate and a fresh
regeneration from the published composition are byte-identical. Current evidence:
`OSCORP_RUSH_ANIMATION.md`; initial motion release: `TASM1_OSCORP_RUSH.md`.
Feature source, tools and evidence notes are committed and pushed to GitHub
`main` as `572bfc9` (Author isolated Oscorp Rush with compact fighting choreography).

- Rush400 XP/event325/bit16: Y, let Snap finish, Y,Y,Y enters jab-cross-hook,
  a knee/kick and overhand cross. All three paid clips are authored
  across their full39/12/20 samples using FK/IK and quaternion controls. Native
  six-contact HP/credit, sample clocks, commitment and prior root advance remain.
  Close guard, restrained hip motion and correctly oriented shoulder twist
  replace the dance-like sway rejected by the player. Novelty was confirmed;
  this refined animation's quality/feel still awaits player acceptance.
- Dedicated SCA IDs3733..3735 isolate the player choreography. All original3733
  IDs, original animation payloads, Snap and other actor bindings stay exact
  against the parent. m6 also uses G11/16/17: none is a globally unused spare.
  Only three player SCA bindings and the Glob count literal change for routing.
- Prior native purchase/refund/save/reload and locked checks remain recorded;
  gates, bindings and ARM9 are exact against that release. The latest revision
  matches contact frames, HP/credit and final position in both facing directions.
  Scissor remains the600-XP/bit17 repeat extension, not the proposed Barrage.
  A rapid-input fixture repeats action60 four times for eight contacts; this
  is not a universal cap. Final and old builds have matching native HP/credit.
- All contacts including unchanged Snap shift two emulator frames earlier. A
  count-only control with old player bindings/text has the same final contact
  frames. Relative timing, native clocks and final position stay exact; this
  does not establish an FPS or speed change.
- Accepted suit, Rebound, matched-rise Vault, passing/turning Sling, compact
  feedback, red marker, instruction clarity and SELECT+Down training refill
  are retained. Original Vault is player-confirmed. Refined Rush and the later
  move/feedback revisions are agent-tested, awaiting player acceptance.

ROM SHA256 `f0382e984ae3bd6038e0bb87a14effa4d844fd390456ab1f36eb67159d386d4b`.
ARM9 SHA256 `72ab438e0998ec2b021bd79a4f36adf5e88a456ccbe51afff100c81461390b12`.
**125 revision-source tests pass; all3,736 resources verified during build.** ARM9 differs
from the accepted Rush parent only at source0x77F8: Glob count3733 ->3736.
The ordinary overlay workflow still rejects manual GlobFiles/arbitrary additions;
only this authored profile permits its three fixed hash-pinned SCA filenames.

DeSmuME was closed during checkpoint/publication. Latest real save before/after:
`84ede9fb98686a88a789775d4ceba67abc38dc1859926d327f21651381f59414`,
634-byte DSVv0/512 payload. Content-addressed `before-rush-refine` and
`before-build` checkpoints preserve it. Prior8bc72be4 ROM remains in
`build/releases/<old-sha>/`; its active recipe and overlays are preserved under
`visual-refinement-parent/`. Earlier releases/checkpoints remain. No research
purchase, HP, Scissor fixture or older save was restored to the real battery.
Current assertions: `work/animation-research/visual-refinement-evidence.json`;
current replays: `build/boot-tests/OscorpAuthored-f0382e98/`;
initial qualification: `work/animation-research/dedicated-evidence.json` and
`build/boot-tests/OscorpAuthored-8bc72be4/`;
count-only: `build/boot-tests/CountControl-409c6d41/count-only-owned/`.

**Performance/visual deep dive:** `PERFORMANCE_VISUALS.md`. Added deterministic
compact0x60 GMB encoding (all769 native decoded round trips), benchmark tooling
and a read-only272-archive/1654-texture census. Only two changed Rush wrappers use
compact encoding; their combined892 bytes avoid15092 literal bytes, without an
FPS claim. Threaded software rendering reduced average pinned-core host cost
~15.9% over two alternating idle Sewer rounds; tails/idle poses vary, exact PNG
parity is not established. This is not a measured DeSmuME hitch/dense-AI fix.
Actual INI plus release source suggest software/interpreter/disk streaming/1x.
Optional JIT12/preload and AUTOGL/2x presets are prepared, not activated. The
launcher doesn't edit INI, but DeSmuME itself persists renderer selection.

**Player checks pending:** full Rush strike readability/feet/transition/feel;
revised Sling/Vault/Rebound feel; ordinary/dense AI, specialized enemies/bosses,
walls/ceilings/interruption and long play. Training floor replays are not those
encounter checks. Real DeSmuME hitch and optional2x visual acceptance remain open.
Health-bar specialized coverage and crowding remain open. A prior wall fixture
fell outside the floor and remains excluded.

**Next approved move:** Rebound Barrage / Scissor-Kick Special600 XP/event326/bit17,
retaining Rush dependency. First measure native action60 repeat entry/cap/control,
then isolate a distinct authored Barrage sequence/mechanic. Rush's new bridge SCA
is dedicated to its paid route; preserve its current budget and the other actor's
native clips. Useful gate0x020B5444, table0x0211BB70;
`work/animation-research/scissor-input.json`, `dedicated-evidence.json`,
`work/rush/research.py`, `tables.txt`, `probe.py`; native inputs under
`reference/combat-inputs/oscorp-*.json`.

Latest design remains ONE combined TASM1/2 kit with13 proposed paid tools plus
Snap. Paid pursuit/control extensions, Air Catch purchase/bundle, independent
shop rows/save migration and third suit remain research. Orbit Breaker remains
a late-game area-finisher proposal, not implemented or allocated a save bit.
Preserve `TASM_EXPANDED_ROADMAP.md`, `IMPROVEMENT_BACKLOG.md` and selected suit backlog.

## First actions in a fresh session

The player confirmed Rush's full choreography was new but rejected its dance-like
sway. A compact jab-cross-hook, knee/kick and overhand refinement is now published.
Record feedback on the close guard, strike readability and transition before
marking this revision player-confirmed.
`sca_author.py` retains all869 exact sample-document and126 player independent
bake tests. `animation_rig.py` maps canonical37 names/parents. Procedural FK/IK
enables original choreography now; a Blender bridge remains separate work.

Immediate next action: ordinary encounter/player checks of planted feet, strike
readability, start/end transitions, facing, walls and interruptions. Refine the
control curves if feedback warrants. For the next paid move, trace/measure the
Scissor repeat path and author an independently routed Barrage. Do not reuse
original G11 as spare storage: m6 still binds it. All original player animations
are referenced by actor XBDs. Existing IDs must stay stable.

Tools: `oscorp_animation.py`, `oscorp_resources.py`, `rush_choreography.py`;
candidate `build/oscorp-visual-refinement/`, regeneration
`build/oscorp-refinement-regenerated/`, count-only `build/oscorp-count-control/`;
private `work/animation-research/{visual-refinement-evidence.json,
check-visual-refinement.py,promote-visual-refinement.py}`. Initial compiler/recovery proof remains in
ANIMATION_AUTHORING.md. Blender bind/axis round trip, scale edits, retiming,
unused-track compaction and measured heap headroom remain open.

Controlled research uses copied `before-oscorp-rush` bytes; earlier Continue
qualification used a read-only copy of the then-current real battery. Live save
advanced independently to84ede9fb
and is preserved by this release. Never restore older a22cdc or0d063aa6 progress
over it. Re-read the actual latest battery while closed before any next release.

1. Read AGENTS.md, this file, OSCORP_RUSH_ANIMATION.md, COMBAT_FLOW.md and PERFORMANCE_VISUALS.md.
2. Check git status, stable hashes, actual configured battery and guarded authored
   recipe. Keep DeSmuME closed before save mutations/publication.
3. Record player feedback separately from agent checks. Preserve accepted overlays,
   native paid gates/shared traversal and the stable launcher/save flow.
4. For Barrage, isolate native bit17 extension on the current paid parent; for
   lag, isolate JIT/preload/renderer before changing more game code.
5. Retain original choreography as the priority for future move replacements;
   a stock clip with a new name is insufficient visual differentiation.

## Active incremental TASM task list

- [x] Clean movie suit panels and black lenses; preserve accepted cosmetics/QoL.
- [x] Stable ROM/launcher, battery backups and named checkpoints.
- [x] Snap Sweep base opener; player confirmed working.
- [x] Map original gameplay, all 21 purchases, native combo meter and animation formats.
- [x] Rebound: purchase/refund, save carryover, facing and native credit checked.
- [x] Web Vault: implemented, agent-tested and player-confirmed.
- [x] Sling Strike: purchased Mid-Air Snare replacement, 600 XP; agent-tested.
- [x] Feedback revision: continuous bars, matched Vault rise and bounded passing/turning Sling; agent-tested.
- [ ] Player check for revised Sling/Vault feel and unusual encounters.
- [ ] Real DeSmuME intermittent hitch/density check; idle threaded-core mean gain~15.9% is not a DeSmuME hitch fix.
- [ ] Isolated JIT/preload/renderer trials, then2x visual acceptance; optional presets prepared but inactive.
- [x] Oscorp Rush: replaces Spider Dance,400 XP; native buy/refund/save/reload, both facing and locked cases agent-tested.
- [ ] Player check of Oscorp Rush feel, spacing and unusual encounters.
- [ ] Rebound Barrage: replace Scissor-Kick Special, 600 XP; retain dependency.
- [ ] Slip Counter: replace Amazing Speed Boost, 800 XP; engine research required.
- [ ] Momentum: replace Ultimate Speed Boost, 1,000 XP; retain dependency.
- [x] Player check for Web Vault in normal DeSmuME play; worked well.
- [x] Revised Rebound juggle response implemented; both facing directions/locked case agent-tested.
- [ ] Player check of revised Rebound juggle response.
- [x] Private common enemy/player HP telemetry retained for balance; numeric panels removed per user.
- [ ] Compact health bars in ordinary AI encounters, specialized health paths and density player checks.
- [x] Compact transient numeral only after positive enemy loss; Snap12 visible without label or meter overlap.
- [x] Combined TASM 1/2 expanded kit and impact/effort improvement list drafted for discussion.
- [ ] Agree on Air Catch as a separate purchase versus a Sling Strike extension.
- [ ] Independent additional shop rows/ownership/save migration research before expanding purchases.
- [x] Remove damage numbers; wounded common enemies use small actor-anchored health bars.
- [x] Restore red mission marker, clearer upgrade inputs/prerequisites and full dummy refill.
- [x] Small shared/traversal, combo-gap and map/save/training instruction clarity pass; menu layout agent-tested.
- [x] SELECT+Down native training HP refill; positive/flag-clear controls and help text agent-tested.
- [ ] Optional native HUD toggle/crowding refinements remain future research.
- [ ] Broader walls/ceilings/bosses/interruption/long-play checks as the kit develops.
- [ ] Independent third suit selection; investigate without altering traversal.
- [x] Sampled SCA compiler, canonical rig map and independent-track game proof; research only.
- [ ] Blender bind/axes calibration and exact native clip export/import.
- [x] Complete original three-clip paid Rush choreography, dedicated resource isolation and controlled qualification; player acceptance pending.
- [ ] Broad gameplay/transition checks for the authored Rush sequence; refine from player feedback.

## Selected suit backlog

Finish the combined TASM kit first. Then retain Scarlet Spider (Ben Reilly),
classic Spider-Man 2099, Scarlet Spider (Kaine), Raimi Spider-Man and classic
symbiote. TASM 2 identity is merged into the active kit; a cosmetic variant can
be discussed later. Exact selection is in `SUIT_ROADMAP.json`.

## Working rules and evidence

- Player flow: `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
  Agent handles releases and checkpoints. Keep the everyday ROM filename stable.
- Free Snap Sweep is accepted. Use native paid slots/costs/gates for the already
  approved incremental path. The latest user direction permits an expanded kit
  and different future prices; those remain design work until implemented safely.
  Existing ownership carries over. Preserve shared traversal/upgrades.
- Preserve the original ROM. Test isolated candidates with battery copies before
  promotion; never use a stale emulator state over changed assets.
- Approved scope/order: `TASM1_UPGRADE_PLAN.md` / `.json`.
- Original behavior: `ORIGINAL_GAMEPLAY.md`, `UPGRADE_ENGINE.md`, `COMBO_ENGINE.md`.
- Animation data: `ANIMATION_RESEARCH.md`, `FORMAT_NOTES.md`, `MODDABILITY_MATRIX.md`.
- Current release evidence: `TASM1_OSCORP_RUSH.md`, `PERFORMANCE_VISUALS.md` and `COMBAT_FLOW.md`; initial HUD/Sling evidence:
  `COMBAT_HUD.md`, `TASM1_SLING_STRIKE.md`; historical move evidence:
  `TASM1_WEB_VAULT.md` and `TASM1_REBOUND.md`;
  save workflow: `TESTING_WORKFLOW.md`.

## Session log

- 2026-10-04: recovered prior session and confirmed Web Vault is next. Added this
  tracker and an AGENTS.md read/update rule so future sessions have a durable handoff.
- 2026-10-04: released Web Vault. Preserved real battery bytes and previous ROM;
  81 tests plus isolated runtime checks pass. Next approved move: Sling Strike.
- 2026-10-04: player confirmed Web Vault. Released higher/closer Rebound plus
  actual HP recent-hit/SUM and numeric combo HUD. 86 tests pass; both facing and
  refund control, Vault regression, low-meter Snap, native controlled player
  health, menus/return cleanup and 10,000-frame resume pass. Preserved latest real
  save, checkpoint and previous ROM. Combined TASM roadmap and impact/effort
  backlog drafted. Next move stays Sling Strike; feedback player checks pending.

- 2026-10-04: user requested compact combat feedback, health bars, red marker and
  next paid move. Released gated Sling Strike with the native total request budget,
  both facing/locked/free-Y checks, native refund/save/reload and short passing
  recovery. Damage panels removed; small recent-damage numeral and wounded bars
  reuse stock assets. Clearer prerequisites/input text and full dummy refill ship.
  92 tests/3,733 resources verified; latest closed real save checkpointed/preserved,
  prior ROM retained. Orbit Breaker area-finisher recorded as a proposal. Player
  acceptance and unusual-encounter/wall checks remain open. Next: Oscorp Rush.

- 2026-10-04: player reported Sling overlap with native Mid-Air Snare, split bars,
  mismatched Vault rise/backward target drift and lag. Released tasm-combat-flow:
  visible passing/turning kick, matched successful launch and continuous bars.
  Fixed column-major pixels and per-shape canvas height; reduced HUD render work,
  but overall core benchmark stayed flat. Both facing/gate/owned-Y controls pass;
  96 tests and3,733 resources verified. Latest a22cdc real DSV preserved exactly,
  checkpoint and prior92f4 ROM retained. Player acceptance/actual lag checks open;
  next paid move remains Oscorp Rush400.

- 2026-10-04: user authorized GitHub commit/push and further small proposed QoL.
  Committed combat-flow/HUD/Sling source as d6725dc. Added sixteen bounded text
  improvements with menu/training captures, full slot round-trip/byte confinement
  and unchanged ARM9. Published clarity67472ad1 through the stable playtest build;
  latest a22cdc save preserved, before-clarity checkpoint and c700f3b5 prior ROM
  retained. Oscorp Rush and larger menu/camera/settings work stay queued.

- 2026-10-04: continued after usage interruption and released Oscorp Rush400,
  bounded purchased advance/recovery and SELECT+Down training HP refill.102 tests
  and3,733 resources pass; native buy/refund/save/reload, owned/locked/mirrored
  contact/credit and positive/negative refill controls pass. Latest a22cdc DSV
  preserved exactly, before-oscorp-rush checkpoint and prior67472ad1 ROM retained.
  Added compact GMB encoding, texture census and performance/visual report.
  Threaded idle core mean improves~15.9%; DeSmuME hitch and HD acceptance remain
  open. Next move Rebound Barrage600; earlier player checks stay queued.

- 2026-10-04: player asked for original attack choreography. Added sampled SCA
  export/import with independent rotation/translation tracks and canonical37-bone
  ancestry; all869 exact sample round trips and126 player independent bakes pass.
  Isolated unchanged rebake and six-bone recovery play in-game; training contacts,
  actual HP/credit, ownership and final position match. This is an authoring proof,
  not a complete new attack or tested Blender bridge. All115 tests and3,733
  resource verification pass. Historical combat-flow generation now refuses a
  Rush parent. Stable ecb07b9a remains unchanged; real save advanced independently
  to observed0d063aa6 and was never mutated by research. Next concrete action:
  calibrate DCC bind/axes, prove a native-clip round trip, then author a whole paid
  GroundAttack17 finisher. See ANIMATION_AUTHORING.md and the private candidate/
  evidence paths in First actions. Rebound Barrage and prior player checks remain
  queued; no animation prototype was published.

- 2026-10-04: player reported Rush looked like Scissor and authorized full
  choreography. Published grounded alternating palms, knee/kick and turning
  backfist across39/12/20 samples using FK/IK. m6 references rejected the spare-G11
  trial; appended three dedicated SCAs instead, preserving every original ID,
  animation payload and other actor binding. Patched only the confirmed Glob
  count literal beyond the accepted engine. Both facing, locked/refund/native
  save/reload/latest Continue and count-only control pass;125 tests and3,736
  resources verified. Stable8bc72be4 matches candidate/fresh regeneration. Latest
  b58ed2ac battery preserved exactly; before-oscorp-animation checkpoint and prior
  ecb07b9a ROM/recipe/overlays retained. Scissor's native repeat relation is now
  measured; Barrage and prior player/ordinary encounter checks remain queued.
  Next action: player transition/readability/encounter feedback, then isolated
  native repeat measurement and distinct Barrage authoring. Blender remains open.

- 2026-10-04: player confirmed a distinct animation but rejected the broad sway
  as dance-like. Published compact jab-cross-hook, guarded knee/kick and overhand
  cross with quiet hips, loaded shoulder and corrected local-X vertical torso
  twist. Only three dedicated SCAs and localized input text change against8bc72be4;
  all gameplay code/bindings/events remain exact. Both facing floor replays match
  HP/credit/contact frames/final position;125 source tests pass and all3736
  resources are verified. Stablef0382e98 matches the candidate and a fresh
  generation from the published profile. Latest84ede9fb DSV preserved exactly;
  before-rush-refine/before-build checkpoints and old ROM/active composition
  retained. Feature source committed and pushed to GitHub main as572bfc9. Player acceptance of this
  revision remains open; next gameplay work remains authored Rebound Barrage.
