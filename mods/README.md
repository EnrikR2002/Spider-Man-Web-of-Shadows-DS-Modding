# Personal overlays

Put only changed Glob assets here, using exact names from `python mod.py list`.
Example: `mods/spd.nsbtx`. Unchanged resources come directly from the clean ROM.
Do not copy `GlobFiles.txt`. Ordinary additions/renames are rejected. The current
player recipe permits three fixed Rush SCA additions plus twelve fixed kit SCAs,
all hash-pinned. Chapter/creature post-passes generate their additional resources
through guarded builders; they are not arbitrary overlay additions.
Build with `python mod.py build`; verify with `python mod.py verify`. Both default
to `build/candidate/Spider-Man-WoS-modded.nds`. Qualify that candidate, then install
the stable player ROM through `python tools/playtest.py build` with DeSmuME closed.
This README is the sole non-asset ignored by the overlay loader.
Extracted resources and overlays are private copyrighted material: do not publish.
