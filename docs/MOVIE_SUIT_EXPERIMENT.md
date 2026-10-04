# First-movie-inspired suit and 128x128 texture experiment

Evidence date: 2026-10-03. User supplied gameplay screenshots confirm the previous
white suit appears white; user likes it. Preserve it unchanged. The red palette-only
pass was rejected as not matching the supplied design. No actual save was changed.

## New artwork and limits

The new procedural, model-space paint has blue upper arms/legs, narrow red torso
panel, red shoulders/mask/lower arms/boots, gold lenses, black web lines and elongated
spider legs. UVs come from the actual model, not guessed rectangular atlas regions.
This is an approximate design prototype, not a faithful painted replica. The line
pattern is visibly rough in the front preview and needs art refinement. The original
model silhouette, vertices, skeleton, normals, animations and combat remain intact.
Back emblem is currently the same long-legged motif as front; side/back seams and
animation need manual checks. No claim of added polygons or improved framerate.

Texture is genuinely 128x128 rather than 64x64: 4 times as many texels, and ordinary
I8 pixel storage rises from 4,096 to 16,384 bytes. Quantized to 256 RGB555 colors.
This increases available detail, not the game's screen resolution. Hardware memory,
crowded scenes and full-playthrough stability remain untested. 256x256 is not tested.

## Evidence and repeatability

Apicula Windows rolling release exported spd.nsbmd/spd.nsbtx to COLLADA/PNG in
ignored build/suit-model-inspect/. The downloaded archive SHA256 is
2baa745de84f299086713b3f52392d3d5d5b100279d4c0fc745e9556722c32db.
Source/provenance: scurest/apicula release continuous and scurest/nsbmd_docs.
No external library was added to the Python tooling. Export timestamps are not used
in texture generation; mesh positions/UVs are the input. Asset data remains private.

PowerShell export (requires the inspected apicula binary locally):

```powershell
& 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\work\apicula\bin\apicula.exe' convert 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\work\glob\spd.nsbmd' 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\work\glob\spd.nsbtx' -o 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\build\suit-model-inspect'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\qol_suits_menu.py'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\tools\movie_suit.py' --combined
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' build --mods 'build/movie-suit-128/combined/mods' -o 'build/movie-suit-128/combined/Spider-Man-WoS-movie-suit-qol.nds'
python 'F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding\mod.py' verify --mods 'build/movie-suit-128/combined/mods' -o 'build/movie-suit-128/combined/Spider-Man-WoS-movie-suit-qol.nds'
```

The export command refuses existing output; omit re-export if present. Generator
refuses different existing overlays. Original ROM and earlier builds untouched.
Combined build retains 35 menu changes, white suit and yellow marker (six assets).
SHA256: 13406306280aa4dd18860b198581a6e26e19dee0b238d53bc05a985ef925946c.
Open earlier QoL build to revert; do not delete other mods.

## Tests and boot evidence

42 tests pass. Texture 64x64 no-op is exact; resized texture round-trips and retains
palette/dictionary/unknown bytes except documented sizes/offsets/dimension bits.
Model 1x no-op is exact; doubled UVs can be divided back to reproduce original bytes;
only UV command parameters and material width/height change. All 3,733 resources
verified in the combined ROM; only the listed six differ.

Separate original-art 128x128 control and painted 128x128 builds generated complete
1,800-frame capture sets and boot.json, showing opening Residential gameplay.
PowerShell stderr pipeline reported exit 1 despite completed capture runs; this is
recorded rather than presented as a clean process exit. Control retains coherent
original-art mapping; painted capture shows the new red/blue layout. These are
limited runtime checks, not texture-budget or full animation certification.
The final combined ROM also generated its complete 1,800-frame capture set;
frame 1799 was inspected and shows coherent painted-suit opening gameplay.

Manual acceptance: cold boot, inspect standing/running/jumping/wall poses and both
suits, verify front/back seams and readable eyes/emblems. Check menu glyphs, save
and Continue; never use an old emulator state. Different ROM filenames may require
separate battery saves. Follow TESTING_WORKFLOW.md if transferring progress.