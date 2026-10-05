# Project tasks and session handoff

Updated: 2026-10-04 (America/Edmonton).

## Resume here

**Current release:** combat-flow revision plus small instruction clarity pass, published with
`python tools/playtest.py build` to `build/Spider-Man-WoS-modded.nds`.
Exact tested candidate and published ROM match. Profile **tasm-combat-flow**
composes all eleven accepted overlays. See `COMBAT_FLOW.md` for current evidence;
`COMBAT_HUD.md` and `TASM1_SLING_STRIKE.md` preserve the initial release.
The current text-only addition is documented in `QOL_CLARITY.md`: sixteen shorter
shared/traversal instructions, combo-gap explanation and map/save/training tips.
Menu and training layout agent-checked; individual tutorial popups remain unvisited.

- Sling Strike keeps native aerial web targeting but now makes one visible
  passing kick, stops residual movement and turns back toward the enemy.
  600 XP / event324 / bit15 and the native 12697-Q12 total request remain.
  Both facing directions, locked case and owned ordinary aerial Y are agent-tested.
- Web Vault now copies the successfully launched common target's actual upward
  velocity and zeros its horizontal drift. Player and target rise alongside each
  other: measured height difference under0.051 units in the right-facing chain.
  Use A grapple -> Up -> A again while airborne for purchased Sling.
  200 XP / event323 / bit14 retained. Initial Vault was player-confirmed;
  this matched-height revision is agent-tested, awaiting player acceptance.
- Health bars are one continuous 24x4 strip. Fixed native column-major pixel
  order and canvas height accumulation; moving-camera cleanup visually verified.
  Positive health below resolution retains one red pixel. Tiny transient combo
  numeral, no damage numbers, native meter and red mission marker are retained.
- HUD redraws every second native HUD tick, skips idle rendering, clears only
  owned rectangles, caches projection scale and prewarms the stock font.
  Whole-core timing was roughly flat: this reduces HUD work, but does not prove
  the intermittent DeSmuME hitches are fixed. Settings were not guessed/changed.

ROM SHA256 `67472ad12cc6be60134588a992945eaba505eacc85a741f48684ce3a5f737520`.
ARM9 SHA256 `b43630d4f0bf0ea3530a6330f7c80482d6ba1f70ba194a447eb93e8a738d77ea`.
**96 tests pass; all3,733 resources verified.** Required overlay hashes are guarded
by `reference/gameplay_profile.json`. Snap, shared traversal, purchased ownership,
Rebound response and all21 native purchase records stay intact.

DeSmuME was closed throughout checkpoint/publication. Latest real save before/after:
`a22cdc22490db27af413520d4a7aa09e7decdec3ab5d41636c575bc6bd19ce46`,
634-byte DSV v0/512 payload. `before-combat-flow`, `before-clarity` and the content-addressed
before-build checkpoint retain it. Previous stable ROM
`c700f3b5bbf1d05d2c4d1b61da6256129c3a2e91648068b4f6a237aea99e09cf`
is retained in `build/releases/`. Actual latest progress copy fresh-boots to Sewer,
417 XP and bits13/14/15; idle HUD performs zero draws. Older native-menu training
batteries are isolated and were never restored over this newer player progress.
Private proof: `work/combat-flow/final-evidence.json` and
`build/boot-tests/CombatFlow-c700f3b5/`.

**Player checks pending:** revised Sling/Vault feel; ordinary/dense AI encounters,
specialized enemy/boss health paths, walls/ceilings/interruption and long play;
intermittent lag; revised Rebound pursuit. Do not describe dummy replays as ordinary
AI-contact coverage or claim guaranteed extra aerial Y hits. A direct wall-position
fixture fell outside the training floor and remains excluded. Native collision is
used, but that is not a wall-test pass. Full/dead bars expire after a bounded delay.

**Next approved development:** Oscorp Rush / Spider Dance, 400 XP. Trace purchased
and locked pause-input string, damage/credit/recovery and shared asset ownership
before changing it. Preserve Snap's borrowed GroundAttack15 assets. Further player
feedback takes priority; never run a legacy generator over the default flow recipe.

The latest player steering replaces the earlier brief Vault hop with matched rise
and no incoming target drift. Further paid pursuit/control and Air Catch's separate
purchase/bundle remain undecided. ONE combined TASM1/2 kit has thirteen paid tools
plus Snap proposed in `TASM_EXPANDED_ROADMAP.md`. Orbit Breaker remains a late-game
acrobatic area-finisher proposal with launch/reconnect setup and single-target use;
not implemented or allocated a save bit. See `IMPROVEMENT_BACKLOG.md`.

## First actions in a fresh session

1. Read AGENTS.md, this file, COMBAT_FLOW.md and QOL_CLARITY.md; initial release docs are historical.
2. Check git status/log, stable hashes, configured real battery and the current
   guarded tasm-combat-flow recipe. Never mutate progress with DeSmuME running.
3. Record new player feedback separately from agent tests. Preserve paid gates.
4. For Oscorp Rush, map the native Spider Dance owned/locked entry, contact and
   recovery, especially routes sharing Snap assets. Retain all accepted overlays.

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
- [ ] Real DeSmuME intermittent hitch/density check; whole-core benchmark gain not established.
- [ ] Oscorp Rush: replace Spider Dance, 400 XP.
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
- [ ] Optional native HUD toggle/crowding refinements remain future research.
- [ ] Broader walls/ceilings/bosses/interruption/long-play checks as the kit develops.
- [ ] Independent third suit selection; investigate without altering traversal.

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
- Current release evidence: `COMBAT_FLOW.md`; initial HUD/Sling evidence:
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
