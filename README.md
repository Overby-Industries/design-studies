# Design Studies

**Overby Industries — diagrams, CAD, and high-level architecture visualizations.**

This repo is the shared home for cross-cutting design work that doesn't
belong to any single system repo: airframe aerodynamics analysis, CAD
source files, and architecture diagrams that get referenced from multiple
places (the org README, whitepapers, and individual system repos like
[`power-and-propulsion`](https://github.com/Overby-Industries/power-and-propulsion)).

## Repo Structure

```
design-studies/
├── xflr5/                  # Aerodynamics analysis (XFLR5) for Project Helga / Starlifter II
│   ├── guides/              # How-to guides for reading/reproducing the analysis
│   └── project-helga/       # Frame geometry, control-surface layout, analysis outputs
├── blender/
│   └── guides/               # Blender -> Godot asset pipeline guide (used by aevoria-simulator)
├── sketches/                # Early hand-drawn concept sketches
└── docs/
    └── asset-inventory.md   # What exists, where the *source* files live, and what's still local-only
```

## What's Here vs. What's Not Yet

The XFLR5 aerodynamics guides and outputs (Markdown + SVG + PNG, a few MB
total) are migrated in directly. The larger native CAD sources -- Blender
`.blend` files for Project Helga (SSTO heavy-lift shuttle, Starlifter-2,
UAV prototypes, ~96 MB) and a FreeCAD `.FCStd` file for the ABEP/MHD core
-- are **not yet migrated**, because committing tens of megabytes of binary
CAD files to a plain git repo bloats every future clone and diff. See
[`docs/asset-inventory.md`](docs/asset-inventory.md) for what exists and
the [Git LFS](https://git-lfs.com/) setup needed before those move in.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License

[Apache 2.0](LICENSE).

## Cross-repo integration

[`docs/architecture/fleet-integration.md`](docs/architecture/fleet-integration.md) describes how the system repos fit together; `integration/run_scenario.py` runs an end-to-end scenario across them and validates every packet against the OTF-1 schema.
