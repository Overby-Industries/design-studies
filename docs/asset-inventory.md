# Asset Inventory

What design/CAD material exists, what's in this repo, and what's still
local-only and needs a decision before it moves in.

## Migrated into this repo

| Asset | Location | Notes |
|---|---|---|
| XFLR5 aerodynamics guides | [`xflr5/guides/`](../xflr5/guides/) | Four Markdown guides (body geometry, control surfaces, reading output data, testing) plus supporting SVG/PNG diagrams. |
| Project Helga XFLR5 analysis | [`xflr5/project-helga/`](../xflr5/project-helga/) | `.xfl` project file, frame-point CSV/XLSX, lifting-body renders. |
| Concept sketches | [`sketches/`](../sketches/) | Early hand-drawn aircraft design sketches. |
| Blender-to-Godot pipeline guide | [`blender/guides/`](../blender/guides/) | Asset export/import workflow, relevant to [`aevoria-simulator`](https://github.com/Overby-Industries/aevoria-simulator)'s Godot integration. |

## Not yet migrated (needs Git LFS)

These exist locally but weren't moved in during the initial scaffold,
because they're large binary files and this repo doesn't have
[Git LFS](https://git-lfs.com/) configured yet:

| Asset | Approx. size | Format |
|---|---|---|
| `project-helga/SoK-1-Proto.blend` (+ `.blend1` backup) | — | Blender |
| `project-helga/SoK-2-ProtoUAV.blend` (+ `.blend1`) | — | Blender |
| `project-helga/ssto-heavy-lift-shuttle.blend` (+ `.blend1`) | — | Blender |
| `project-helga/starlifter-2.blend` (+ `.blend1`) | — | Blender |
| `abep-mhd-core.FCStd` (+ `.FCBak`) | ~24 KB | FreeCAD -- small enough to just commit directly, actually; low priority to set up LFS just for this one |

Combined Blender asset folder is ~96 MB.

## Before migrating the Blender files

1. Set up [Git LFS](https://git-lfs.com/) in this repo:
   `git lfs install && git lfs track "*.blend"`, commit the resulting
   `.gitattributes`.
2. Decide whether to bring in the `.blend1` backup files at all -- they're
   Blender's own auto-backup of the previous save and don't need version
   control (git already versions the `.blend` file itself); recommend
   leaving these out and adding `*.blend1` to `.gitignore` instead.
3. Confirm GitHub LFS storage/bandwidth is appropriate for the account tier
   this repo lives under before pushing ~96 MB of binary history.

The FreeCAD file is small enough to just add as a normal commit whenever
someone gets to it -- no LFS needed for that one.
