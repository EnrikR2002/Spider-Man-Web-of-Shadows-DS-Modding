# ROM-grounded improvement options

2026-10-04. Impact estimates describe player value. Effort is relative to this
project's current tooling, not a delivery promise: **S** is a bounded text/data
or asset edit; **M** needs a targeted action/engine experiment; **L** needs several
systems and extended runtime testing; **XL** needs substantial unmapped formats
or persistent state. Confidence distinguishes known editing surfaces from ideas.

## High-value small changes

| Idea | Impact | Effort | Evidence, cost or limitation |
|---|---|---|---|
| Consistent move names and input descriptions in all three menu locations | High clarity | S | English/American text codec and paid slots are mapped; retain DS glyphs and check wrapping |
| Explain prerequisites and show each skill's role in descriptions | High progression clarity | S | Native prerequisites mapped; description changes are straightforward, new menu badges are extra work |
| Tune launch/recoil/recovery per purchased move | High combat feel | S-M | GMB movement, bounded SCA keys and response words are editable; contact/credit/boss behavior needs paired checks |
| Make mission/save markers readable on dark maps | Medium-high navigation | S-M | Bounded marker palette already edited; broader palette ownership still needs testing |
| Improve objective text contrast and brevity | Medium clarity | S | Same-slot text edits are supported; background/frame changes need additional UI mapping |
| Adjust individual XP costs after measuring actual value | High progression value | S-M | Native 21-record price table is mapped; old saves, dependencies and availability still matter |
| Offer a few battle-tested difficulty presets through build recipes | Medium-high replay value | S-M | Attack response data can be bounded; global enemy/player stat scaling is not fully mapped yet |
| More expressive recovery poses and less abrupt motion | Medium visual feel | S-M | Existing dynamic SCA keys can be edited; new tracks, joints and rigs cannot yet be authored safely |

## Targeted gameplay and feedback work

| Idea | Impact | Effort | Evidence, cost or limitation |
|---|---|---|---|
| Numeric combo meter visible from the first gain | High feedback | M | Native model mapped; current HUD extension implements a composite meter value, not a hit counter |
| Actual dealt/taken HP instances and running totals | High feedback/balance | M-L | Private HP telemetry remains for balance; visible damage numbers were removed per player request. Common health bars are implemented; specialized coverage needs further checks |
| Damage/feedback display options in a proper native menu | Medium-high accessibility | M-L | UI strings are editable, but widget routing and persistent option storage remain research; avoid hijacking language/audio flags |
| Reliable paid air pursuit with a short input buffer | Very high combat feel | M-L | Vault hop/input route known; buffer, target validity, per-launch limits and ceiling collision need engine work |
| A distinct hit-count readout beside the combo resource | Medium-high feedback | M | Requires confirmed contact events; the existing gauge is not a hit count and should not be relabelled |
| Clear visual/sound cue for a counter or reconnect opportunity | High learnability | M-L | Existing action/VFX bindings can guide prototypes; new effects/audio authoring not yet supported |
| Stronger enemy wind-up poses and readable dangerous attacks | High fairness | M-L | Bounded skeletal pose edits supported; AI timing/contact windows need separate measurement |
| More useful training target: HP, meter, timing and reset | High experimentation | M-L | Native Test Upgrades room exists and isolated automation works; player-facing widgets/retry routing need mapping |
| Quick retry from training and less menu repetition | Medium QOL | M-L | Existing pause/save/testing flow can be traced; safely returning/reinitializing room state is extra work |
| Less intrusive damage reactions for small hits | Medium-high feel | M | Native reaction families exist; preserve meaningful danger and distinguish light/heavy/boss rules |
| Measured rebalance of underused native/shared skills | High variety | M-L | All 21 purchases are mapped; their full damage/credit/recovery paths need paired measurements |
| Better camera tracking during high launches | High aerial readability | L | World positions are known; camera projection, limits and interpolation remain unmapped |

## Larger projects

| Idea | Impact | Effort | Evidence, cost or limitation |
|---|---|---|---|
| Ten or more independent TASM purchases with branches | Very high variety | L-XL | More actions are plausible, but new shop rows, safe ownership storage, refunds and save migration must be proved |
| A true independent third suit with its own kit | Very high variety | L-XL | Red/alternate action routes are known; selector, persistent slot and UI are not implemented |
| Contextual wall combat and collision-safe fly-by moves | High expression | L | Root movement is editable; wall semantics and collision-safe transitions need engine/BSP research |
| Enemies that respond intelligently to repeated launch/grapple loops | High depth | L | AI/state-machine paths can be researched; changes must remain fair and preserve story encounters |
| New encounter mixes and improved enemy placement | High replay/fun | L-XL | OBJ room families inventoried, payload semantics unmapped; begin with a tiny paired room difference |
| New rooms, shortcuts or traversal challenges | Very high content | XL | BSP envelopes parsed; spatial/collision nodes and placements have no safe editor |
| New enemy/boss attacks with custom effects | High content | XL | Existing clips can be edited; full AI, hitboxes, rigs, effects and resource insertion need additional tooling |
| A clearer minimap with useful room/exit information | High navigation | L-XL | Two tiled sheets can be decoded; room graph, DAT metadata and dynamic marker routing remain partial |
| More detailed suit models and silhouette changes | High visuals | L-XL | Texture/material/UV changes work; topology, rigging and skeleton edits lack an editor |
| Better impact audio or new suit-specific sounds | Medium-high feel | L | Whole SDAT preserved; individual bank/sample/sequence editing and event ownership need research |
| User-controlled camera shake, flash and readability settings | Medium-high accessibility | L | Needs camera/effect hooks, UI routing and safe option storage; first verify what each effect actually does |

## Suggested order

Combat feedback -> Rebound/Vault/Sling connection -> readable upgrade instructions
-> training improvements -> ground/counter branches -> independent expanded
progression -> additional suits/content. Small visual/text improvements can ship
between move releases. New rooms and bosses have the greatest tooling cost and
should follow reliable combat, progression and collision editing.

The DS screen, tile/VRAM allocation, heap headroom and bounded update cost are
real constraints. Current extension reserves 16 KiB from the main heap; no
general promise of higher-resolution HUD art or an unlimited number of effects
follows from successfully adding a few numbers.

## Implemented small changes in the compact HUD / Sling release

English/American Rebound/Vault/Sling inputs and four native prerequisites are
clearer; the requested mission marker is red again; the training dummy restores
full native maximum health after defeat. Damage panels are removed in favor of
small wounded-enemy bars and a transient numeral. Prices/difficulty/objective
text were not changed without a measured need. See COMBAT_HUD.md and
TASM1_SLING_STRIKE.md. Orbit Breaker adds a late-game acrobatic area-finisher
proposal to the expanded roadmap; no new progression is granted.

## Implemented player-feedback combat-flow revision

Continuous health bars fix the native bitmap layout and per-shape canvas height.
Web Vault matches the successful common target's rise and removes incoming drift;
Sling makes a visible passing kick, stops and turns back. HUD rendering skips idle
work, checks prior owned rectangles, caches projection scale and warms the font.
Whole-core timings stayed roughly flat; do not claim a proven FPS/hitch fix.
See COMBAT_FLOW.md for measured evidence and remaining player checks.
