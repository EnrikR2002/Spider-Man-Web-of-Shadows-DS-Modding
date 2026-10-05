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
