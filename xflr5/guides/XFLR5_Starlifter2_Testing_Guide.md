# Testing the Starlifter 2 Assembly in XFLR5

What to run, in what order, and how to keep it from silently failing. Companion to the body and control-surface guides.

---

## 0. Before you test anything: look at it from all four views

Your renders show the assembly coming together, and one thing is worth a second look before you invest time in analysis: in the front view, the Body reads as a tall, narrow, pointed shape rising well above the wing — closer to a mast standing on the wing than a fuselage lying along it. If that's intentional (a dorsal spine/canopy that genuinely stands proud of the wing), fine. If the Body's 120 ft *length* axis ended up pointed vertically instead of running nose-to-tail with the wing's chord, every test in this guide will run "successfully" and produce numbers that mean nothing, because the panel method will happily compute lift and drag on whatever geometry it's given. Cheap check: flip through the front/top/side preset views (not just the iso view) and confirm the Body's long axis reads as horizontal in the top and side views specifically. Since you've got the geometry side handled, treat this as a one-line reminder rather than a diagnosis.

With that caveat out of the way — here's the order things actually need to happen in.

---

## 1. The dependency chain

XFLR5's analyses build on each other. Skipping a step is the single most common cause of "why won't this converge":

1. **Foil polars (XFoil Direct Analysis, Type 1)** — every foil used anywhere in the plane (Main Wing sections, Elevator, any Fin) needs Type 1 polars covering the full Re and α range it will actually see. The 3D wing/plane solvers don't re-run XFoil live — they interpolate from this pre-generated mesh.
2. **Wing-alone analysis** — Main Wing by itself, sanity-checked before it's buried inside the full plane.
3. **Plane analysis** — Body + Main Wing + Elevator (+ Fin) together.
4. **Stability analysis (Type 7)** — needs 1–3 already working, plus inertia properties defined and correct.

Skip straight to step 4 and you'll get cryptic non-convergence — the log will often trace back to a gap in step 1's polar mesh.

---

## 2. Choosing an analysis method

| Method | Good for | Watch out for |
|---|---|---|
| **LLT** (Lifting Line) | Quick spanwise loading, stall estimates | Explicitly **not recommended** for wings with low aspect ratio, high sweep, or high dihedral — your Main Wing (AR 4.17, sweep 35.75°) trips two of those three. Use it only for rough checks. |
| **VLM** (Vortex Lattice) | Lift-curve slope, Cl0, general polars — the recommended default for your planform | Wing-only; doesn't see the Body's own panels |
| **3D Panel** | Includes the Body's own surface in the solve, pressure distributions | Slower; wing and elevator wakes must not sit in the same horizontal plane (see error table) |

Given your Main Wing's geometry, **VLM or 3D Panel** are the right defaults — not LLT, despite LLT being the "quick" option. Use 3D Panel specifically whenever you want the Body's lifting-body shape actually contributing to the numbers, since VLM only sees the wing.

---

## 3. The core test matrix

| Test | Polar type | What it tells you | Notes for this design |
|---|---|---|---|
| Basic sweep | Type 1 (fixed speed/Re) | Baseline Cl, Cd, Cm vs α | Run this first on Main Wing alone, then on the full Plane |
| Re sensitivity | Type 4 (fixed α, variable Re) | Where results get unreliable at low Re | Your wing tapers to a 4 ft tip chord — check this specifically near the tip |
| **Glide polar** | Type 2 (fixed weight, constant lift) | Speed, sink rate, and glide angle at each α — this is literally the unpowered-landing test | γ = arctan(Cd/Cl), V = √(2mg/ρSCl) — directly answers "how does Starlifter 2 fly with the engines off," the same regime the Shuttle Orbiter and the lifting-body program actually validated by gliding |
| Neutral point hunt | Type 1, repeated with XCmRef moved | Where the true Neutral Point sits (see the data-reading guide) | Do this before trusting any Tail Volume or stability number — directly relevant given the -0.017 flag from the body guide |
| Control derivatives | Type 7, one control group active at a time | Aileron/elevon, elevator, rudder derivatives | Covered in the control-surfaces guide — same prerequisites apply here |

For the glide polar specifically: unless your wing needs LLT excluded per Section 2, the documented default LLT settings are Relax Factor = 20 and 20 stations along the span — but given the sweep/AR flags above, run this as VLM instead and skip straight to that.

---

## 4. Non-convergence: causes and fixes

This table is the single most useful thing in the official documentation for actually finishing a test session instead of staring at a red error:

| Scope | Cause | Fix |
|---|---|---|
| All methods | Foil Type 1 polar mesh doesn't cover the flight envelope (**by far the most common failure**) | Extend the foils' Type 1 polar meshes over a wider Re/α range |
| Type 2 (glide) | Lift comes out negative | Only calculate for higher angles of attack |
| Type 2 (glide) | Speed pushed outside the polar mesh (speed → ∞ at low α, → 0 at high α) | Extend the Type 1 polar mesh |
| Any wing/plane analysis | Tip chord too small → Reynolds number too low to have polar data | Either check "Store OpPoints outside the Polar mesh," or omit the very tip from the planform definition |
| LLT | Relaxation factor too small | Increase it in LLT Settings |
| LLT | Too many stations across the span | Decrease the station count |
| VLM | Singular matrix from conflicting panel layout | Regenerate the mesh manually rather than relying on auto-mesh |
| 3D Panel | Wing and Elevator wakes sit in the same horizontal (Z) plane | Offset one of them slightly in Z so the wakes don't overlap |

The tip-chord row is worth flagging directly: your Main Wing's 4 ft tip chord (from a 60 ft root, taper 0.067) is exactly the shape that triggers the low-Re polar gap. Expect to hit this, and know the fix before you do.

The log file (Operating Point → View Log File) names the specific points of the flight envelope that failed — check it before changing settings blind.

---

## 5. What this can validate for an SSTO, restated for testing specifically

Every test above runs on subsonic, incompressible potential-flow math. The **glide polar (Type 2) and stability analysis (Type 7) are legitimately meaningful** for Starlifter 2's unpowered approach and landing — the same flight regime the X-24/HL-10 lifting bodies and the Shuttle Orbiter actually flight-tested. Nothing in this test matrix says anything about the scramjet ascent or the reentry environment; don't let a clean convergence on those two tests read as more validation than it is.

---

## Files in this package

- `XFLR5_Starlifter2_Testing_Guide.md` — this guide
- Diagrams for reading the results are in the companion data-interpretation guide

## Quick checklist

- [ ] Confirm the Body's 120 ft axis reads as horizontal in top/side preset views, not vertical
- [ ] Type 1 foil polars generated for every foil, covering the full Re/α range you'll fly
- [ ] Wing-alone analysis run and sane before moving to the full Plane
- [ ] VLM or 3D Panel selected instead of LLT (AR/sweep rule out LLT here)
- [ ] Type 2 glide polar run — this is your unpowered-landing characterization
- [ ] Neutral point located by moving XCmRef and re-running Type 1, before trusting Tail Volume alone
- [ ] Type 4 Re-sensitivity checked near the 4 ft tip chord
- [ ] "Store OpPoints outside the Polar mesh" checked, or the very tip trimmed, if convergence fails near the tip
- [ ] Wing/Elevator Z-offset confirmed non-coplanar before running 3D Panel
- [ ] Stability analysis (Type 7) run last, one control group at a time, per the control-surfaces guide
