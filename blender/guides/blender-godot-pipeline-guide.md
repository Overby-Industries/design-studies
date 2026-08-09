# Blender → Godot Asset Pipeline Reference

A working reference for two asset pipelines feeding **Godot 4.6.3**:

- **Project 1 — Asteroid Miner**: hard-surface hulls, pre-rendered to a single transparent PNG per object, used as flat `Sprite2D` art.
- **Project 2 — Project Helga**: the SSTO-44 Starlifter II, a real-time flight-sim aircraft exported as glTF (`.glb`) and rendered live in Godot.

These two pipelines are **not variations on the same workflow** — they solve opposite problems (a static image vs. a live mesh) and most of the advice in one section is actively wrong if applied to the other project. Every section below is labeled for which project it applies to, and Section 5 is a side-by-side cheat sheet if you ever mix them up mid-task.

Written assuming a current Blender release (4.2 or later, including 4.5 LTS), where the real-time engine is called **Eevee Next**. Menu paths below are for that generation of Blender; if your installed version differs meaningfully, the panel names below are the ones to search for.

---

## Table of Contents

0. [How This Doc Is Organized](#0-how-this-doc-is-organized)
1. [Shared Blender Basics](#1-shared-blender-basics)
2. **Project 1 — Asteroid Miner (pre-rendered sprites)**
   - [2.1 Pipeline Overview](#21-pipeline-overview)
   - [2.2 Modeling the Hull](#22-modeling-the-hull)
   - [2.3 The Camera Angle Rule, Explained](#23-the-camera-angle-rule-explained)
   - [2.4 Setting Up & Locking the Orthographic Camera](#24-setting-up--locking-the-orthographic-camera)
   - [2.5 Lighting a Flat Game Sprite](#25-lighting-a-flat-game-sprite)
   - [2.6 Render Settings for Transparent PNG](#26-render-settings-for-transparent-png)
   - [2.7 Framing & Resolution](#27-framing--resolution)
   - [2.8 Sanity-Check Before Committing](#28-sanity-check-before-committing)
   - [2.9 Project 1 Quick Checklist](#29-project-1-quick-checklist)
3. **Project 2 — Project Helga (real-time flight sim)**
   - [3.1 Pipeline Overview](#31-pipeline-overview)
   - [3.2 The XFLR5 → Blender Handoff](#32-the-xflr5--blender-handoff)
   - [3.3 Modeling Everything XFLR5 Doesn't Cover](#33-modeling-everything-xflr5-doesnt-cover)
   - [3.4 Clean Quad Topology for Close-Up Scrutiny](#34-clean-quad-topology-for-close-up-scrutiny)
   - [3.5 UV Unwrapping a Large Aircraft](#35-uv-unwrapping-a-large-aircraft)
   - [3.6 Material / PBR Texture Setup](#36-material--pbr-texture-setup)
   - [3.7 glTF Export Settings for Godot 4](#37-gltf-export-settings-for-godot-4)
   - [3.8 Sanity-Check Before Committing](#38-sanity-check-before-committing)
   - [3.9 Secondary Note: XFLR5 Data → Flight Model Tuning](#39-secondary-note-xflr5-data--flight-model-tuning)
   - [3.10 Project 2 Quick Checklist](#310-project-2-quick-checklist)
4. **Custom Liveries (Both Projects)**
   - [4.1 Tool Boundaries at a Glance](#41-tool-boundaries-at-a-glance)
   - [4.2 What Must Happen in Blender](#42-what-must-happen-in-blender)
   - [4.3 What Happens Outside Blender](#43-what-happens-outside-blender)
   - [4.4 Runtime Swap — Helga (Live 3D)](#44-runtime-swap--helga-live-3d)
   - [4.5 Runtime Swap — Asteroid Miner (Pre-Rendered)](#45-runtime-swap--asteroid-miner-pre-rendered)
   - [4.6 Minimal First Livery Pass for Helga](#46-minimal-first-livery-pass-for-helga)
5. [Divergence Cheat Sheet](#5-divergence-cheat-sheet)
6. [Appendix: Menu Path & Shortcut Index](#6-appendix-menu-path--shortcut-index)

---

## 0. How This Doc Is Organized

Each major section is self-contained and skimmable — headers to scan, numbered steps to follow, exact menu paths in `code font`. You shouldn't need to read this front-to-back; jump to the section for the project and task you're working on.

Callout boxes like this mark places where the two projects genuinely diverge:

> **DIVERGES:** A note like this means "don't carry this rule into the other project."

---

## 1. Shared Blender Basics

Skip this if you're already oriented in the Blender UI. Quick reference for the vocabulary used throughout this doc:

- **Object Mode vs. Edit Mode**: `Tab` toggles between them. Object Mode moves/rotates whole objects; Edit Mode edits vertices/edges/faces inside one object.
- **Viewport navigation**: middle-mouse-drag orbits, scroll wheel zooms, `Numpad 1/3/7` snap to Front/Right/Top orthographic views (`Ctrl+Numpad 1/3/7` for the opposite side), `Numpad 0` looks through the active camera.
- **The Properties editor** (right-hand column of tabs): the icons that matter most here are the orange square (**Object Properties**), the green camera or lightbulb (**Object Data Properties** — changes based on what's selected), the camera-back icon (**Render Properties**), the printer icon (**Output Properties**), and the checkered sphere (**Material Properties**).
- **The N-panel**: press `N` in the 3D viewport to open/close the sidebar showing Location/Rotation/Scale for the selected object.
- **Scene units**: Blender's default unit is meters. This matters enormously for Helga (a real 1:1-scale aircraft) and essentially not at all for Asteroid Miner (the render is scaled arbitrarily by pixel dimensions, not by Blender's unit system) — see the divergence note in 2.2.

---

# PROJECT 1 — ASTEROID MINER (Pre-Rendered Sprites)

## 2.1 Pipeline Overview

**Model in Blender → render one still frame → transparent PNG → `Sprite2D` texture in Godot, scaled by code.** That's the entire pipeline. Nothing about the art changes at runtime except the position and rotation of that one flat image — there is no live 3D happening in the shipped game for these objects.

That single fact drives every recommendation in this section: since Godot will only ever rotate and scale a flat picture, your job in Blender is to produce **one correct picture**, not a model that looks good "from any angle" the way a real-time asset would. A 3D detail that's invisible from the locked camera angle is wasted effort here — this is the opposite priority order from Project 2 (see [3.4](#34-clean-quad-topology-for-close-up-scrutiny)).

Scope reminder: model **only the static hull/body**. Thruster flame, the glowing drill tip, lit windows — anything that changes per-frame based on game state — stay as procedural overlays drawn in code on top of this PNG. Don't spend modeling time on them.

---

## 2.2 Modeling the Hull

A small mining ship and a larger mothership are both simple hard-surface jobs. Recommended workflow:

1. **Block out with primitives.** `Shift+A` → `Mesh` → `Cube` (or `Cylinder` for a rounder hull) as your starting volume. Push/pull/scale it toward the ship's rough proportions before adding any detail.
2. **Work in Top Orthographic view** (`Numpad 7`) for most of the modeling, since that's the exact silhouette the camera will eventually capture. A shape that reads fine in a 3/4 view can look wrong or lopsided from directly above — check often from this angle rather than only at the end.
3. **Optional reference image**: `Add` → `Image` → `Reference` to drop a top-down concept sketch into the viewport and trace over it.
4. **Symmetric hulls — use the Mirror Modifier**: `Modifier Properties` (wrench icon) → `Add Modifier` → `Generate` → `Mirror`. Since the nose points **+X** and a typical ship is symmetric left-to-right, mirror across the **Y** axis (the Mirror modifier's "X/Y/Z" toggles mirror *across* that coordinate — for a ship whose long axis is X and whose left/right symmetry plane is the XZ plane, that means enabling **Y**, not X). Model only one half.
5. **Hard-surface detail**: `Ctrl+B` for interactive bevels on edges you want to catch light and read clearly at small size (or a non-destructive **Bevel modifier** for the same effect); `Ctrl+R` for loop cuts to lay in panel-line edge flow; the **Knife tool** (`K`) or a shallow **Boolean modifier** for cutouts/canopy shapes.
6. **Shading**: `Object` menu → `Shade Auto Smooth` to remove faceting on curved sections (in Blender 4.1+ this adds a **Smooth by Angle** modifier under the hood — same menu entry either way). Use `Edge` → `Mark Sharp` on hard corners you want to stay crisp rather than smoothed.
7. **Center the model on the world origin** (0,0,0) — use `Shift+C` to reset the 3D cursor to the origin before you start blocking out, and `Object` → `Set Origin` → `Origin to Geometry` if the pivot drifts. Godot's sprite convention assumes centered art.
8. **Nose points +X.** Build to this convention from the start so the camera setup in 2.4 doesn't need extra compensating rotation.

> **DIVERGES:** Topology cleanliness matters far less here than in Project 2. This is a one-off still image, not a deforming or close-up real-time asset — n-gons and slightly messy geometry are forgivable as long as the silhouette and shading read correctly from the locked camera angle. Don't over-invest in "proper" topology at the expense of just getting the shape right; save that discipline for Helga (3.4).

> **DIVERGES:** Blender's real-world unit scale is cosmetic here. Only the final render's **pixel aspect ratio** matters (see 2.7) — the game scales the PNG to whatever target size it wants. Model at whatever scale feels comfortable to work with (e.g., treating 1 Blender unit ≈ 1 meter so the ship "feels" human-vehicle-sized is a fine mental crutch), then let the camera's orthographic scale (2.4) and render resolution (2.7) do the real framing work. This is the opposite of Helga, where scale is physically load-bearing.

Do not model thruster flame, drill glow, or window lighting — see 2.1.

---

## 2.3 The Camera Angle Rule, Explained

This is the part worth understanding properly, not just following blindly, because it's easy to get subtly wrong.

**The mental model:** Godot rotating a `Sprite2D` at runtime is exactly like spinning a printed photograph between your fingers. It cannot reveal any face of the ship that wasn't visible in the original render, and it cannot re-angle the "camera" — it only rotates the flat image *in its own plane*.

An **orthographic, dead-on top-down** camera is the one viewing angle where that trick stays correct: looking straight down the object's vertical axis produces a view that is rotationally symmetric about that same axis. Spinning the resulting flat image is therefore geometrically identical to actually orbiting an orthographic top-down camera around the ship and re-rendering it at every heading — the math happens to work out.

Any other angle breaks this the moment the ship turns more than a few degrees:

- **A 3/4 angle** bakes in one specific set of visible faces (you can see the top *and* one side). Rotate that image 90° in Godot and you're now looking at what should be a totally different set of visible faces — the picture doesn't update to show them, so the illusion collapses. Past roughly 90° of rotation this becomes obviously wrong.
- **Perspective** (as opposed to orthographic) distorts based on camera distance and field of view — parallel edges converge, nearer parts look bigger. None of that is consistent with a flat sprite meant to represent the same rigid object at arbitrary rotations; orthographic removes the distortion so the flat image "means the same thing" no matter how it's spun.

**Player ship (rotates freely at runtime) → must use straight-on orthographic top-down.** No exceptions, no "slightly angled for style" — a slight tilt is exactly what breaks past ~90°.

**Mothership / static hazards / props (never rotate — only moved or scaled) → free to use whatever angle looks best,** typically a nicer fixed 3/4 view, because that render is always shown at the one orientation it was captured at. There's no rotation to expose the trick.

> **DIVERGES:** In Project 2, camera angle in Blender is irrelevant to the final product — Godot's free-flying camera generates its own view of the live mesh at runtime. The entire concept of "the camera angle is baked into the art" doesn't apply there.

---

## 2.4 Setting Up & Locking the Orthographic Camera

Applies to the **player ship** (and anything else that rotates at runtime). For the mothership/static props, skip the "must be exactly top-down" steps and just frame a pleasing 3/4 shot.

1. **Add or select a camera.** `Shift+A` → `Camera` if you don't have one.
2. **Get an exact top-down angle without guessing numbers:**
   - Press `Numpad 7` to snap the viewport itself to Top Orthographic.
   - Select the camera.
   - `View` menu → `Align View` → `Align Active Camera to View` (shortcut `Ctrl+Alt+Numpad 0`). This snaps the camera's position and rotation to exactly match the current viewport — guaranteed dead-on top-down, no manual rotation math.
3. **Switch the camera to Orthographic**: select the camera → **Object Data Properties** tab (the green camera icon) → `Lens` panel → `Type` → `Orthographic`.
4. **Set the Orthographic Scale** in the same panel — this controls zoom/framing (larger number = more zoomed out). Fine-tune it once resolution is set in 2.7.
5. **Verify no rotation drift**: `N` panel → `Item` tab, check the camera's Rotation values are clean, round numbers (confirms the Align-to-View snap actually landed on-axis rather than picking up viewport orbit drift from before you pressed `Numpad 7`).
6. **Lock the camera down** so nothing can nudge it later:
   - **Object Properties** tab (orange square icon) → `Transform` panel → click the small padlock icons next to Location X/Y/Z and Rotation X/Y/Z. Locked axes silently ignore any attempt to move or rotate the object in the viewport.
   - In the viewport's `N` panel → `View` tab, confirm **"Lock Camera to View" is UNCHECKED**. (This is the opposite of what you want — if checked, simply orbiting the viewport while looking through the camera drags the real camera along with your navigation and silently ruins the locked angle.) Leaving it unchecked lets you freely preview through the camera (`Numpad 0`) without touching its transform.
   - Optional extra safety: in the **Outliner**, click the small cursor/arrow icon next to the camera's row to toggle off "Selectable" — now it can't even be accidentally clicked and dragged while you work on other objects.
7. **Confirm Depth of Field is off**: Object Data Properties → `Depth of Field` panel, checkbox unchecked (default). A soft-focus blur has no meaning on an orthographic render and would look wrong on a flat sprite regardless.

---

## 2.5 Lighting a Flat Game Sprite

**Why this needs special handling:** any strong directional shadow you bake into the render is baked *relative to the ship's own geometry*, not to world space. When Godot rotates the sprite in gameplay, that shadow rotates right along with it — visually, this reads as the light source itself swinging around the ship as it turns, which looks obviously wrong to a viewer even if they can't articulate why. Ambient occlusion (crevices darkening because they're crevices) is safe, because it's a property of the geometry itself, not a world-space light direction — it stays correct under rotation.

Practical steps:

1. **Avoid a single strong key light from a steep angle** (a lone angled Sun lamp is the classic mistake here).
2. **Light flat and even instead.** Options, roughly in order of simplicity:
   - **World lighting**: `World Properties` tab (globe icon) → set a flat `Color`/`Strength`, or use an HDRI `Environment Texture` for soft light from every direction at once.
   - **Balanced multi-light**: two or three Area/Sun lights placed symmetrically around the ship so no single direction dominates.
   - **Light coincident with the camera axis**: a soft light pointed straight down the same axis the camera looks down. Because it shares the camera's axis, it's rotationally symmetric along with the object-camera system — any shading it produces stays consistent no matter how the flat image is later spun.
3. **Use Ambient Occlusion for depth cues, not directional shadow.** In current Blender (4.2+), Eevee Next folded the old standalone "Ambient Occlusion" panel into ray tracing — enable it via **Render Properties → `Raytracing`** (check the box to enable, then the AO-related falloff options live in that same panel). Cycles computes equivalent occlusion as part of its normal light transport with no separate toggle needed.
4. **A solid default recipe**: low-to-medium World strength for flat fill + one soft light along the camera axis + Raytracing/AO enabled. Dimensional enough to read as a 3D object, flat enough to survive rotation.

> **DIVERGES — mothership & static props**: none of this restriction applies. Since it's only ever shown at one fixed orientation, use normal 3-point lighting (key + fill + rim) for a more dramatic, dimensional look. A strong angled key light is *encouraged* here, not banned.

> **DIVERGES — Project 2**: Helga's lighting is not baked at all — it's real Godot lights (sun, etc.) hitting a real PBR material in real time, changing constantly as the aircraft flies. The entire "will this shadow look wrong when rotated" problem is specific to the pre-rendered pipeline and doesn't exist for Helga.

---

## 2.6 Render Settings for Transparent PNG

1. **Choose an engine — Render Properties tab (camera-back icon) → `Render Engine` dropdown:**
   - **Eevee Next**: near-instant feedback, great for iterating on framing/lighting live.
   - **Cycles**: more physically-grounded, more forgiving of an imperfect light setup, generally the highest achievable quality for soft AO and reflections.
   - **Recommendation**: since this pipeline only needs a handful of one-off stills (not hundreds of animation frames), render time is a non-issue — use Eevee Next while you're actively moving the camera/lights around for speed, then do your final "keeper" render in Cycles for the extra quality margin. Either engine is genuinely fine if you don't want to switch.
2. **Enable transparency**: same panel → `Film` section → check **`Transparent`**. This checkbox exists identically in Eevee, Cycles, and Workbench.
3. **Output format — Output Properties tab (printer icon) → `Output` panel:**
   - `File Format` → **PNG**
   - `Color` → **RGBA** (not RGB — this is what actually carries the transparency; skipping this silently gives you a solid-colored background instead)
   - `Color Depth` → 8-bit is fine for game sprites.
4. **Color Management** (same Render Properties tab, `Color Management` panel near the bottom): Blender 4.x defaults `View Transform` to **AgX**, which noticeably shifts contrast/saturation away from the raw color values you picked. For a flat game sprite where predictable, "what I picked is what I get" colors usually matter more than filmic richness, consider switching to **Standard**. Either is fine — just stay consistent across every ship you render so they match each other.
5. **Sampling** (`Sampling` panel): push sample counts up for a clean, noise-free still since render time doesn't matter at this volume — e.g. Cycles `Render Samples` around 256–512 with the denoiser (OpenImageDenoise) on; Eevee Next similarly if you've enabled Raytracing for AO.
6. **Render**: `Render` menu → `Render Image` (`F12`), then in the Image Editor that opens, `Image` → `Save As`, double-checking PNG + RGBA are still set on the save dialog itself.
7. **Watch for alpha edge fringing.** A thin dark or light halo around the silhouette once composited into Godot usually means a straight-vs-premultiplied alpha mismatch. If you see it: double-check you haven't added compositor nodes that touch alpha, and check the fringing-fix option on the texture's Import settings on the Godot side.

---

## 2.7 Framing & Resolution

Canvas **aspect ratio** is the only thing that has to be exact — Godot scales the whole image down to fit the target box, so raw pixel counts don't matter as long as you're rendering comfortably larger than the target for quality headroom.

- **Player ship** — target box 26×20 → ratio simplifies to **13:10**. Example resolution: `1300 × 1000`.
- **Mothership** — target box 100×58 → ratio simplifies to **50:29**. Example resolution: `1500 × 870`.

Steps:

1. **Output Properties → `Format` panel → Resolution X/Y** — set to your chosen numbers preserving the exact ratio above. Blender does not auto-lock aspect ratio to anything, so compute these by hand each time.
2. **Frame the shot**: `Numpad 0` to look through the camera, adjust `Orthographic Scale` (Object Data Properties, 2.4) until the hull fills the frame with a small safety margin — avoid cropping geometry, but don't waste resolution on excess empty padding either.
3. Re-confirm the camera is still locked (2.4) after any framing adjustments — if you had to nudge orthographic scale, that's a Data Properties value, not a transform, so the earlier transform locks are unaffected. Good.

---

## 2.8 Sanity-Check Before Committing

Don't consider a render final until you've actually watched it rotate. Two ways to check, fastest first:

1. **Test it in Godot directly (recommended — this is literally the runtime behavior).** Drop the PNG into a scratch scene as a `Sprite2D`, select it, and either drag the rotate gizmo or punch a few values into `Rotation Degrees` in the Inspector (try 0°, 45°, 90°, 180°, 270°). If it looks right here, it is right — there's no more faithful test than the real thing.
2. **Or preview inside Blender before ever opening Godot**: apply the rendered PNG to a plane using an **Emission** shader (not Principled BSDF — you don't want the preview itself to be relit) so it displays exactly as an unlit 2D engine would. Parent the plane to an Empty and manually spin the Empty's Z rotation through a few test values in the viewport.
3. **What you're checking for**: the silhouette still reads as ship-like at every test angle (no weird foreshortening baked in), no shadow or highlight appears to swing around unnaturally as it spins, the nose direction matches what Godot's movement code will compute as "forward," no stray fringing/background color at the edges.

### Final checklist before calling a render done

- [ ] Camera `Type` = Orthographic, not Perspective
- [ ] Camera is exactly top-down (used Align Camera to View; rotation values are clean)
- [ ] `Film → Transparent` enabled
- [ ] Output `Color` = RGBA
- [ ] Render resolution exactly matches the target box's aspect ratio
- [ ] Only static hull geometry is visible — no thruster flame / glow / lit windows baked in
- [ ] Lighting has no single strong directional shadow (rotation-tested per above)
- [ ] Rotation sanity check done in Godot (or the Blender Empty-spin preview) before treating the render as final

---

## 2.9 Project 1 Quick Checklist

- Model hull only, centered on origin, nose at **+X**, mirrored on **Y** if symmetric.
- Player ship / anything that rotates at runtime → locked, dead-on **orthographic top-down** camera. Static props → free 3/4 angle.
- Flat/even lighting + AO for anything that rotates; normal 3-point lighting is fine for anything that doesn't.
- `Film → Transparent` on, PNG output, `Color` = RGBA.
- Resolution ratio matches the target box ratio exactly (13:10 ship, 50:29 mothership).
- Rotate-test the actual PNG (in Godot or a Blender Empty) before calling it final.

---

# PROJECT 2 — PROJECT HELGA (Real-Time Flight Sim)

## 3.1 Pipeline Overview

**XFLR5 validates the flying surfaces first → Blender builds the full detailed visual model second → glTF export → live mesh rendered in real time by Godot.** This is the opposite kind of asset from Project 1 in almost every respect:

| | Asteroid Miner | Project Helga |
|---|---|---|
| Final output | One flat PNG | A live mesh with materials |
| Viewed from | One fixed, locked angle | Any angle, any distance, in real time |
| Lighting | Baked once, must survive rotation | Real Godot lights, changes every frame |
| Blender scale | Arbitrary | Real 1:1 meters |
| Modeling bar | Silhouette from one angle | Full scrutiny from every angle |

Nothing here can be "faked" the way a pre-rendered sprite can — there's no single locked camera angle to hide behind, and the lighting is out of your hands at modeling time (Godot's sun/lights do that live). The model, materials, and topology all have to be genuinely correct, because the camera is free and the light is real.

> **DIVERGES:** If you find yourself thinking about camera angles, baked shadows, or transparent PNG settings while working on Helga, stop — those are Project 1 concepts and don't apply here at all.

---

## 3.2 The XFLR5 → Blender Handoff

**This is the crux of the whole Helga pipeline** — the point of doing aero analysis first is worthless if the Blender geometry doesn't actually match what XFLR5 validated. Here's how to make that true.

### 3.2.1 What XFLR5 actually gives you

XFLR5 is an analysis tool built around 2D airfoil sections stacked into a 3D planform — that structure is exactly what makes the handoff possible:

- **Per-station airfoil coordinates.** Every wing/tail station in XFLR5's `Wing and Plane Design` module references a 2D airfoil (stock, from the UIUC database, or hand-drawn in XFLR5's airfoil direct-design tool) — an ordered list of (x, y) points around the section outline, normalized to unit chord. These export per-airfoil as **`.dat` files in Selig format** (coordinates start at the trailing edge, trace over the top surface to the leading edge, then back along the bottom surface to the trailing edge).
- **Planform placement data**: chord length, sweep, dihedral, and twist (incidence) at every defined station, plus the span position of each. XFLR5 can export this as a **`.csv`** describing each station's chord and leading-/trailing-edge XYZ points, and/or as a plain-text wing geometry file (**`.xwimp`**, importable back into XFLR5 itself for re-editing).
- **A basic fuselage/body tool** exists in XFLR5 (revolution- or frame-based), but it exists purely so the panel-method solver can account for fuselage interference in the *aerodynamic* analysis — it is not meant to produce finished visual geometry. Treat anything XFLR5 draws for the fuselage as disposable aero reference, never as a mesh to import as-is.
- **STL export** (added in XFLR5 v6.13) can dump the analyzed wing/body as a literal triangulated mesh. This is useful as a dimensional ghost reference to snap against in Blender, but it is a triangle soup with no usable quad topology or UVs — never treat it as final geometry.

### 3.2.2 Getting the airfoil sections into Blender

Two realistic paths. Both start from the same XFLR5 exports (`.dat` per airfoil + the planform table); they differ in how you place and loft them in Blender.

**Path A — Addon-assisted (fastest way to a first result):**

1. In XFLR5, for every station you need (root, any kink points where sweep/airfoil changes, tip — enough to capture the double-delta's planform breaks), export that airfoil to a `.dat` file from the airfoil view: `File` → `Export` → save as `.dat` (Selig format).
2. Record the exact per-station numbers from XFLR5's wing definition (or the exported `.csv`): span position, chord length, sweep offset, dihedral, twist.
3. In Blender, install the **"Add Airfoil"** extension (by Nerk, on the official Blender Extensions platform, supports Blender 4.2 LTS and newer): `Edit` → `Preferences` → `Get Extensions` tab → search "Add Airfoil" → install (or drag-and-drop the downloaded `.zip` straight into the Blender window).
4. For each station: `File` → `Import` → `Add Airfoil` (or `Shift+A` → `Mesh` → `Add Airfoil` in the 3D viewport) and select the matching `.dat` file. This drops in a correctly-shaped 2D cross-section at unit chord.
5. Position each cross-section using the XFLR5 numbers **exactly**, entered numerically into the `N`-panel's Location/Rotation/Scale fields rather than eyeballed: scale to the station's chord length, offset along span, sweep, and dihedral, rotate for twist/incidence. This step is what keeps the Blender geometry faithful to the analyzed wing — you're transcribing XFLR5's own numbers, not approximating them.
6. With every station's cross-section correctly placed, loft a surface through them: enter Edit Mode, select matching edge loops on adjacent stations in span order, and use `Edge` → `Bridge Edge Loops` to skin a clean quad surface between each pair. Repeat station-to-station along the span. This produces genuine quad topology, unlike the STL export.
7. Mirror to get the other half: **Mirror Modifier**, **X** axis — if you build to the export-time convention in 3.7 (nose along Blender's -Y, up along +Z), the left/right centerline is the X axis, same logic as the ship in 2.2 just with a different "forward" axis. Verify visually regardless; get it wrong and you'll mirror the aircraft front-to-back instead of side-to-side.

**Path B — Scripted (worth it if the planform will get revised, or has many stations):**

1. Same inputs: per-station `.dat` files plus the planform table.
2. In Blender's **Scripting workspace**, write a short Python script that reads each `.dat` file's coordinates, builds a curve or mesh cross-section from them, positions/scales/rotates it per the planform table programmatically, then bridges/lofts a surface through the ordered set of cross-sections (via `bmesh` operations, or by driving `bpy.ops.mesh.bridge_edge_loops` across the generated sections).
3. This is a well-established pattern in the RC/model-aircraft community for exactly this XFLR5-to-Blender handoff — the open-source `wingLib.py`-based scripts in the `blenderCadCamTools` project (part of the `foss-toolchain-mpcnc` documentation site) are a working example of the shape of this approach (import `.dat` → place sections → bridge surface) worth looking at even if you end up writing your own from scratch.
4. Payoff: if you re-run an XFLR5 analysis pass and the planform changes even slightly, you regenerate the Blender base mesh in seconds by re-running the script instead of redoing manual placement.

**Recommendation**: given a blended-wing-body double-delta is exactly the kind of planform you'll likely want to re-tune a few times in XFLR5, Path B pays for itself quickly if you're comfortable spending an afternoon on the script — and you already write GDScript/C++, so this will likely feel more natural than manual placement anyway. Path A is completely fine if you just want a correct one-off result today without the scripting overhead.

### 3.2.3 What's authoritative from XFLR5 vs. what you model freely

Keep this boundary explicit as you work:

**From XFLR5 (geometrically authoritative — build to match exactly):** wing and tail/canard planform (span, chord, sweep, taper), airfoil sections (camber, thickness distribution) at every defined station, twist/washout, dihedral.

**Not from XFLR5 — yours to model freely in Blender, using the validated wing/tail as a fixed spatial reference:** fuselage shape and cross-sections, cockpit and canopy, panel lines and access-panel seams, landing gear (struts, wheels, bay doors), control-surface hinge lines and gaps (elevons, rudder — XFLR5 knows these exist as deflection surfaces for the *aerodynamic* analysis, but has zero opinion on how the physical hinge line, gap, or fairing actually looks), antennas, lights, intakes, exhaust nozzles, and all other greeble.

**Practical sequencing tip**: block out the fuselage using the now-precisely-placed wing root as your anchor point — build the fuselage to meet the wing where the wing root already is, rather than building the fuselage first and eyeballing the wing to fit it. Doing it the other way around defeats the entire point of validating the aero geometry first.

### 3.2.4 A note specific to the blended-wing-body / double-delta shape

XFLR5's wing definition works in discrete stations with straight-line interpolation between them. For a true blended-wing-body — where the "wing" continuously merges into the fuselage rather than meeting it at a distinct root — you'll typically represent this on the XFLR5 side using thick, flat, fuselage-like airfoils for the inboard station(s), rather than expecting XFLR5 to model an actual wing/fuselage blend. That's an XFLR5-side modeling choice, not a Blender question — but it does mean the visual blending surface between "clearly wing" and "clearly body" in Blender is entirely your own hard-surface work. Treat the inboard XFLR5 station as a rough cross-sectional cue for that blend, not a literal contour to trace.

---

## 3.3 Modeling Everything XFLR5 Doesn't Cover

1. **Protect the validated geometry.** Once the wing/tail from 3.2 is finalized, put it in its own Collection and consider renaming it clearly (e.g. `WING_REFERENCE_XFLR5`) or toggling off its selectability in the Outliner (same cursor-arrow icon technique as 2.4) so unrelated fuselage work can't accidentally reshape an aerodynamically-validated surface.
2. **Block out the fuselage from cross-sections.** For a blended-wing-body, place a series of curves or edge loops at fuselage stations along the length (nose to tail) sized to your real dimensions (120 ft / ~36.6 m), then loft between them with `Bridge Edge Loops` the same way you did the wing, blending the outermost stations into the wing root cross-section from 3.2.
3. **Use real reference images.** Since you have actual dimensioned sketches from your own aircraft-design tool, bring them in as background reference: `Add` → `Image` → `Reference`, one per relevant orthographic view (`Numpad 1` front, `Numpad 3` side, `Numpad 7` top), and keep proportions honest against the real 100 ft span / 120 ft length.
4. **Panel lines and greeble**: shallow `Boolean` difference, or `Inset Faces` (`I`) followed by a small push/pull, read well under close-up scrutiny and changing light — this level of surface detail matters far more here than in Project 1, where it would be invisible at sprite scale.
5. **Cockpit**: model the interior only to the extent it will actually be visible through the canopy at gameplay camera distances; greybox first, add detail as needed. Canopy gets its own glass material (3.6).
6. **Landing gear**: keep as separate objects/sub-hierarchy from the fixed hull, since gear typically animates (retract/extend) — this keeps a future Godot-side animation or separate glTF node targeting the gear clean and unambiguous.
7. **Control-surface hinge lines**: model the actual hinge gap as real geometry (a thin beveled seam) positioned at the same span/chordwise boundary XFLR5's aero model treats as the elevon/rudder edge — pull those boundary positions directly from your XFLR5 control-surface definitions so the visual hinge line lands exactly where the aerodynamic model assumes the surface breaks. Keeps the visual and analyzed aircraft consistent even down to this detail.

---

## 3.4 Clean Quad Topology for Close-Up Scrutiny

**Why this matters here and didn't in Project 1**: a free-flying, close-range, real-time camera means every curved surface has to hold up under moving light from any angle. N-gons and stray triangles on curved geometry cause visible shading pinches and artifacts that a distant, fixed-angle sprite render would never expose.

- Prefer quads everywhere achievable. Reserve triangles for unavoidable poles (nose tip, wingtip cap) and keep them off highly visible curved panels.
- Use **Loop Cuts** (`Ctrl+R`) to add edge flow that follows the surface's natural curvature (fuselage stations, wing chordlines) — don't add detail that breaks the quad flow just to add detail.
- Use the **Bevel tool** (`Ctrl+B`, 2–3 segments) on hard edges like panel breaks and leading edges so they catch specular highlights correctly instead of looking razor-thin or aliased.
- Check for n-gons and non-manifold geometry before export: in Edit Mode, `Select` → `All by Trait` → `Non-Manifold` (catches holes and internal faces); `Select` → `All by Trait` → `Faces by Sides`, set to "Greater Than" 4, to catch n-gons for cleanup.
- Use `Shade Auto Smooth` / the **Smooth by Angle** modifier (same as 2.2) rather than uniformly flat or smooth shading, so curved panels shade smoothly while intentional hard edges stay crisp.
- Build at **literal real-world scale**: keep Blender's scene unit at meters (the default) and model the actual dimensions — 100 ft wingspan ≈ **30.5 m**, 120 ft fuselage length ≈ **36.6 m**. This isn't optional the way it was for Project 1 — Helga's export must land in Godot as true 1:1 meters (3.7), and topology/texel-density decisions (3.5) both assume you're working at real scale as you go, not scaling up at the end.
- Apply modifiers that add real geometry (Mirror, Bevel, Subdivision) before final export prep, or make sure "Apply Modifiers" is checked in the glTF exporter (3.7).

> **DIVERGES:** This is the mirror image of the 2.2 divergence note — here, topology rigor is non-negotiable; in Project 1 it was explicitly the thing you were allowed to skimp on.

---

## 3.5 UV Unwrapping a Large Aircraft

1. **Seam placement**: put seams along natural panel breaks and low-visibility lines (trailing edges, the underside centerline, gear bay edges) so any stretching or resolution discontinuity hides as an intentional panel line rather than a visible paint break. This matters doubly once liveries are involved (Section 4) — a seam through the middle of a paint scheme will visibly misalign between UV islands.
   - Mark seams: in Edit Mode, select edges, `Edge` → `Mark Seam` (or `Ctrl+E` → `Mark Seam`).
2. **Unwrap method**: for large, close-to-developable surfaces like wing skins, a plain `Unwrap` (`U` → `Unwrap`, Angle Based or Conformal method) along your marked seams is clean, since wings are close to single-curvature. For the fuselage and any wing-body blend area, seam placement matters more than the algorithm — mark seams generously around compound-curvature regions (nose, blend zone) and unwrap those as their own islands.
3. **Avoid `Smart UV Project` as your primary method** for the aircraft's hero surfaces — it's fast but produces many small, inconsistent islands that hurt texel-density consistency and complicate livery painting later. It's fine for quick greybox/utility parts (small hardware, gear struts) where seam artistry doesn't matter.
4. **Keep texel density consistent** across the whole aircraft, so resolution doesn't visibly jump between, say, the fuselage and a wingtip. The free **Texel Density Checker** addon (by mrven, available on GitHub and Blender Market/Superhive) measures and rescales UV islands against a target density — pick a texture resolution relative to real-world size and match every island to it.
5. **Check for stretching**: apply a checker-pattern image in the UV Editor / Material Preview shading and look for squares that stay roughly even and square across curved surfaces; visible stretching means the seam layout needs adjusting in that area.
6. **Plan texture sets around the aircraft's size**: at ~30–37 m, you'll likely want either one large texture set (4K or 8K) or a few logical UV tiles/materials (fuselage, wings, tail, gear) to keep texel density reasonable without one enormous texture. Godot handles multiple materials on one mesh without issue — this is a judgment call based on target texture budget, not a hard rule.
7. **Leave UV island padding**: `UV` → `Pack Islands` has a `Margin` setting — enough gap between islands prevents mip-mapping bleed across island borders when the aircraft is viewed from a distance in the flight sim.

---

## 3.6 Material / PBR Texture Setup

1. **Use the Principled BSDF** for everything — it maps directly and predictably onto glTF's metallic-roughness PBR model on export, which is exactly what Godot 4's glTF importer expects on the other end.
2. **Base Color**: an Image Texture node's color output → Principled BSDF `Base Color` input. Becomes glTF's `baseColorTexture` / Godot's albedo.
3. **Roughness/Metallic — pack as an ORM texture.** glTF's convention packs **Occlusion → R, Roughness → G, Metallic → B** of a single image for efficiency. Build your texture that way, bring it in as an Image Texture node set to **Non-Color** data, run it through a **Separate Color (RGB)** node, and wire G → `Roughness`, B → `Metallic` on the Principled BSDF.
4. **Occlusion specifically**: the Principled BSDF has no direct AO input, so to get baked occlusion into the export correctly, add a **glTF Material Output** node (`Shader Editor` → `Add` → `Output` → `glTF Material Output` — built into Blender's glTF I/O addon, enabled by default) and plug the ORM texture's R channel into its `Occlusion` input. The glTF exporter specifically looks for this node to complete the ORM packing on export.
5. **Normal map**: an Image Texture (Color Space set to **Non-Color**) → **Normal Map** node → Principled BSDF `Normal` input. This is where panel lines, rivets, and fine greeble that aren't worth modeling as real geometry belong, given real-time performance budgets.
6. **Canopy/glass**: its own material — Principled BSDF with `Transmission` raised and `Roughness` near zero for a clear canopy, so it exports as a proper glTF transmissive material. Double-check how this actually reads once imported into Godot, since real-time transmission handling can differ from Blender's viewport preview — you may need to adjust the material on the Godot side after import.
7. **Keep material-slot count reasonable** — a handful of slots (hull, canopy, gear/metal, maybe emissive strobes), not one per tiny part. This keeps livery texture-swapping simple later (Section 4).
8. **Preview in Eevee Next's Material Preview / Rendered shading**, not Cycles, while working — it's the closer real-time approximation of how Godot will actually render the material. This is the one place Project 2's engine-choice logic is the *opposite* of Project 1's: here you're matching a real-time renderer, not chasing the single best-looking still.

---

## 3.7 glTF Export Settings for Godot 4

1. **Apply all transforms first**: `Object` → `Apply` → `All Transforms` (or `Ctrl+A` → `All Transforms`) on every object, including empties/parents. Leftover unapplied rotation or non-uniform scale is the single most common cause of broken normals, tangent-space lighting bugs, and — worst of all — misaligned physics/collision after import.
2. **Finalize modifiers** you want baked into the mesh (Mirror, Bevel, Subdivision, Boolean) — either apply them directly (Modifier Properties → dropdown → `Apply`) or make sure `Apply Modifiers` is checked in the exporter (step 7 below).
3. **Set the origin to Helga's actual reference point** before export: place the 3D Cursor exactly at the coordinate your flight-computer code already expects (`Shift+Right-click` to place by hand, or `Shift+S` → `Cursor to World Origin` then offset numerically to the exact point), then `Object` → `Set Origin` → `Origin to 3D Cursor`. Pull this coordinate from your existing flight-model code rather than guessing — it has to match exactly.
4. **Orientation before export**: build the aircraft nose-first along Blender's own **-Y** axis (Blender's "forward," matching the Front orthographic view, `Numpad 1`), with "up" along Blender's **+Z**. Blender's glTF exporter performs the Z-up-to-Y-up axis conversion for you when `+Y Up` is enabled (see below) — it converts Blender's -Y-forward/+Z-up convention into glTF/Godot's **-Z-forward/+Y-up** convention automatically. You don't need to manually rotate the aircraft to "pre-compensate" for this; building it the normal Blender way and letting the exporter's axis conversion do its job is correct.
5. **Open the exporter**: `File` → `Export` → `glTF 2.0 (.glb/.gltf)`.
6. **Format**: `glTF Binary (.glb)` — a single self-contained file, matching the project's existing convention of dropping a `.glb` straight into `godot/models/`.
7. **Key settings in the export side panel:**
   - `Include` → limit to what you actually need (e.g. `Selected Objects` if Helga isn't the only thing in the file).
   - `Transform` → **`+Y Up`**: checked (default) — this is the axis conversion from step 4; leave it on for Godot.
   - `Geometry` → **`Apply Modifiers`**: checked, so your modifier stack bakes into the exported mesh.
   - `Geometry` → keep **UVs**, **Normals**, and **Tangents** enabled — tangents specifically matter for correct normal-map lighting once it's in Godot.
   - `Geometry` → **`Export Materials`** set to `Export` (not `Placeholder`/`None`).
   - Material export picks up the ORM/Occlusion setup automatically once the glTF Material Output node from 3.6 is wired in.
8. **Scale**: leave the exporter's `Scale` at `1.0`. Since you've already built at real 1:1 meters and applied transforms, no export-time scale factor should be necessary — introducing one here is a common way non-uniform/baked scale sneaks back in right at the last step.
9. **Pitfalls to check for before you export, not after:**
   - **N-gons**: Blender triangulates these automatically on export, but not necessarily the way you'd choose on a highly visible curved panel. Resolve them yourself first (`Face` → `Triangulate Faces`, or better, avoid creating them per 3.4) so you control the result.
   - **Non-manifold geometry**: can cause broken normals or lighting artifacts, and if this mesh is ever used to generate physics/collision shapes, non-manifold geometry can break collision generation outright. Clean it up per the 3.4 checklist.
   - **Baked-in non-uniform scale**: the single most common cause of "the imported model looks subtly wrong" or "collision doesn't line up." Always apply all transforms (step 1) immediately before export.
   - **Mismatched sub-object origins**: if the aircraft is built from several objects (fuselage, gear, canopy) with inconsistent individual origins, they can import as separate Godot nodes with confusing pivots. Either join what should be visually rigid into one mesh (`Ctrl+J`), or make sure each sub-object's origin is intentionally where you want its Godot-side node pivot to be (e.g., a gear strut pivoting at its hinge, for future retraction animation).
10. **After export**: drop the `.glb` into `godot/models/` and assign it to the `imported_model` export variable on the `HelgaAirframeVisual` node's Inspector in Godot. Per your existing scaffolding, that's the whole hookup — no further code changes needed.

---

## 3.8 Sanity-Check Before Committing

1. **Import standalone first.** Drop the `.glb` into `godot/models/`, let Godot auto-import it, and open it in a scratch scene (or just double-click to inspect) before wiring it to `HelgaAirframeVisual` — check the Output panel for import warnings before anything else.
2. **Scale check**: against a known reference (Godot's default grid, or a temporary 1-meter-cube placeholder), confirm the aircraft reads as roughly **30.5 m wingspan / 36.6 m length**. If it's off by a large, suspiciously round factor (100x, 0.01x), that's almost always a units mismatch between Blender's scene unit and the export scale.
3. **Orientation check**: in a scene, confirm the nose points along **-Z** and "up" is **+Y** once it's actually sitting in Godot's 3D view, matching your flight code's forward/up expectations — before assigning it to the real `HelgaAirframeVisual` node.
4. **Assign and verify origin alignment**: set it as `imported_model` on `HelgaAirframeVisual`, confirm it replaces the procedural placeholder correctly at runtime, and check that the mesh's origin lines up with where the physics/flight-computer code expects the vehicle's reference point — a temporary debug gizmo at the physics origin is a good way to check this visually if there's any doubt.
5. **Checklist:**
   - [ ] No import errors/warnings in Godot's Output panel
   - [ ] Real-world scale confirmed correct (~30.5 m span / ~36.6 m length)
   - [ ] Forward/up orientation confirmed correct (-Z forward, +Y up)
   - [ ] Origin matches the flight-computer's reference point
   - [ ] Materials appear textured correctly (not pink/missing-texture)
   - [ ] No obviously inverted/broken normals (dark flickering faces)

---

## 3.9 Secondary Note: XFLR5 Data → Flight Model Tuning

Once the final validated wing/tail geometry is locked (and matches what actually got built in Blender), XFLR5's own analysis — Type 1/2/4 analyses over your intended flight envelope of angle-of-attack, sideslip, and speed, via the lifting-line, VLM, or 3D panel method — produces real **Cl, Cd, Cm curves** (lift, drag, and pitching-moment coefficients) and **stability derivatives** (the standard longitudinal and lateral-directional derivatives, e.g. pitch stability, yaw/roll coupling). These describe how the *actual analyzed shape* behaves, and could eventually replace hand-estimated constants in the flight model (lift-curve slope, induced drag factor, pitch stability coefficient, etc.) with numbers grounded in the real modeled geometry rather than guesses.

Export path: from XFLR5's Polar view, right-click a polar → export (or `View` → `Polars` → export) to get the analysis results as text/CSV.

This is a genuine "nice to have later," not something this guide needs to solve now — noted so it's on your radar once the flight model needs real tuning data instead of estimates.

---

## 3.10 Project 2 Quick Checklist

- Validate wing/tail planform and airfoils in XFLR5 **before** modeling final geometry in Blender.
- Import per-station `.dat` airfoil files via the **Add Airfoil** extension (or a script), place stations using XFLR5's exact numbers, loft with `Bridge Edge Loops`.
- Fuselage, cockpit, gear, hinge lines: modeled freely in Blender, anchored to the validated wing root — XFLR5 has no opinion on these.
- Real 1:1 meter scale throughout (100 ft ≈ 30.5 m span, 120 ft ≈ 36.6 m length).
- Clean quad topology, no stray n-gons/non-manifold geometry — this model gets seen up close from every angle.
- Sensible UV seams + consistent texel density, especially since liveries will paint across this UV set later.
- Principled BSDF materials, ORM-packed roughness/metal/occlusion via the glTF Material Output node, tangent-space normal maps.
- Export as `.glb`, `+Y Up` checked, modifiers applied, transforms applied, scale left at 1.0, origin set to the flight-computer's reference point.
- Verify scale/orientation/origin in Godot itself before treating the export as final.

---

# CUSTOM LIVERIES (Both Projects)

Livery support touches three different tools, and it's worth being explicit about which one owns which part of the job before diving in.

## 4.1 Tool Boundaries at a Glance

| Job | Where it happens |
|---|---|
| UV unwrap in a livery-friendly way (seams, texel density, texture-slot setup) | **Blender**, once, structurally |
| Actually painting a livery's colors/markings | **Blender Texture Paint**, or an **external 2D tool** (Krita/GIMP/Substance Painter) |
| Swapping which livery is active at runtime | **Godot** — and the mechanism is completely different per project (4.4 vs. 4.5) |

Blender's job is entirely one-time and structural: make the mesh capable of accepting any number of future liveries without being touched again. Painting and runtime-swapping both happen downstream of that setup.

## 4.2 What Must Happen in Blender

1. **Livery-friendly UV unwrap** (Helga: builds on 3.5; Asteroid Miner: only relevant if you go the re-render-per-livery or hand-painted route rather than a flat-shaded hull — see 4.5):
   - Consistent **texel density** across all panels, so a livery doesn't read blurrier on some parts of the aircraft than others.
   - Seams placed so continuous paint elements (fuselage stripes, roundels, nose art) don't cross a seam and visibly misalign between UV islands — plan seams around where real liveries already tend to break (panel lines, wing roots) rather than through the middle of a design element.
   - **Don't overlap mirrored UVs** if asymmetric livery details are even remotely plausible later (unique nose art on one side only, non-mirrored squadron markings) — mirroring UVs forces both sides to always show identical paint. This is cheap to avoid now (just don't overlap the UV islands for the two mirrored mesh halves, even though the mesh itself can still use a Mirror modifier) and expensive to fix retroactively.
2. **Material/texture-slot setup that supports swapping without touching the mesh**: keep the livery-relevant Base Color texture on its own Image Texture node, separate from AO/roughness/metallic/normal maps — those represent physical surface properties that typically stay identical across liveries, not paint, so a livery swap should only ever need to touch the one Base Color image.

## 4.3 What Happens Outside Blender

Two realistic ways to actually paint a livery, for a solo dev:

1. **Blender's own Texture Paint mode** (`Texture Paint` workspace tab): paint directly on the model with the UV unwrap already applied, no separate application needed. Export the result via the Image Editor's `Image` → `Save As`. The zero-extra-software option.
2. **External 2D tools** (Krita, GIMP, Substance Painter): export a UV layout template first — `UV Editing` workspace → `UV` menu → `Export UV Layout` (saves a PNG/SVG of the UV wireframe) — as a guide layer, paint the livery there with a fuller 2D toolset (better brushes, layers, symmetry tools than Blender's paint mode in most cases), then bring the finished texture back in as the material's Base Color image.

**Recommendation for a solo dev without a dedicated texture-painting tool already installed**: **Krita** (free, open-source) is the practical sweet spot for hand-painted livery work — good layers/masking, much better suited to flat vector-ish paint schemes than Blender's paint mode, without Substance Painter's cost and smart-material setup overhead (which is really built for a different kind of PBR-heavy workflow than "paint a livery"). Blender's Texture Paint is completely fine as a zero-install starting point, especially for the first pass in 4.6.

## 4.4 Runtime Swap — Helga (Live 3D)

Straightforward, as expected for a live-rendered mesh: swap the material's texture at runtime.

1. Each livery is one Base Color image, matching the UV layout from 4.2, shipped as e.g. `res://liveries/<name>_albedo.png`.
2. At runtime, get a **material override** on the aircraft's `MeshInstance3D` (`set_surface_override_material`) rather than editing the imported resource's material directly — this way, re-exporting/re-importing the `.glb` from Blender later doesn't wipe out your runtime livery logic.
3. Set that override material's `albedo_texture` (if it's a `StandardMaterial3D`) or the equivalent shader uniform (if it's a custom `ShaderMaterial`) to the chosen livery's image.
4. Since AO/roughness/metallic/normal stay constant across liveries (per 4.2), only the one texture reference needs to change per swap — cheap, simple, and scales to as many liveries as you want with zero re-export from Blender.

## 4.5 Runtime Swap — Asteroid Miner (Pre-Rendered)

This is the part that genuinely isn't straightforward, because the "art" is a single flattened PNG with lighting already baked in — there's no live material to swap a texture on. Two real options:

**Option A — Re-render a separate PNG per livery in Blender.**
Duplicate the material/color setup per livery, re-run the full pipeline from Section 2 once per livery scheme, end up with N separate PNGs (`ship_default.png`, `ship_red.png`, `ship_blue.png`...).
- **Pro**: zero added runtime complexity — Godot just picks which texture file to load into the `Sprite2D`, identical to how the pipeline already works today.
- **Con**: doesn't scale — every new livery is a full manual Blender re-render, *plus* re-running the rotation sanity check from 2.8. Fine for a handful of liveries, painful for many.

**Option B — Runtime recolor/tint in Godot (shader-based).**
Skip re-rendering: render the hull once in a way that supports recoloring, then remap colors at runtime via a shader on the `Sprite2D`.
- **Hue-shift shader**: a fragment shader that rotates the hue of the sprite (or of pixels in a target hue range). Simple, but only really works if the base render's colors are saturated/distinctive to begin with, and struggles with liveries that need genuinely different patterns (stripes, logos), not just a different base hue.
- **Color-mask channel approach**: render (or paint) an auxiliary mask image alongside the main PNG, where channels or grayscale bands mark which pixels belong to "paintable region 1," "region 2," etc. A shader samples the mask and recolors each region independently from per-livery color parameters passed in as shader uniforms. This can reproduce genuine multi-color schemes (hull + stripe + trim) without re-rendering, but requires building that mask (hand-painted, or rendered as a separate flat-color "ID pass" in Blender) and writing/maintaining the shader.

**Recommendation**: given the project's own scope — "a small 2D game with a handful of ships," not a large livery catalog — **Option A (re-render per livery) is the practical choice**. It's simpler to build, has zero shader-maintenance burden, and Option A's "doesn't scale" downside only actually bites at a scale (many ships × many liveries) this project isn't targeting. Reach for Option B only if livery count or variety grows enough that re-rendering becomes a genuine bottleneck (procedurally-generated faction colors, dozens of skins) — which is also the point where the shader investment starts paying for itself.

## 4.6 Minimal First Livery Pass for Helga

A concrete, ordered starting point, since this is the nearer-term need:

1. Finish the base UV unwrap per 3.5/4.2 — seams placed sensibly, texel density consistent, left/right kept unmirrored in UV space if any asymmetric marking is even remotely likely later. Cheap now, expensive to redo after a livery is already painted.
2. Export a UV layout template (`UV Editing` workspace → `UV` menu → `Export UV Layout`) at a resolution matching your intended texture size (e.g. 4096×4096).
3. Paint one base/default livery first, and keep it simple — it only needs to prove the pipeline works: base hull color, one or two accent colors, a basic panel-line pass. Use Blender's Texture Paint for the fastest route to something in-engine, or Krita if you'd rather test the external-tool workflow you'll use for future liveries anyway.
4. Bring the painted texture back in as the material's Base Color image and re-export the `.glb` — UVs and mesh are unchanged, so this is just a re-export, not a re-model.
5. Wire it up in Godot per 4.4 (material override on the `MeshInstance3D`, swap `albedo_texture`) and check it in a real flight-sim scene under moving light, at close range. This is the actual test of whether the UV/texel-density work in step 1 was good enough — if you spot stretching or seam mismatches now, fix the UVs before painting a second livery, not after.
6. Only once that first livery round-trips cleanly, start additional liveries — each one from here on is just "new painted texture, same UVs/mesh," which is the entire point of doing the Blender-side setup carefully once, up front.

---

## 5. Divergence Cheat Sheet

If you're ever unsure which project's rules apply, check here first.

| Aspect | Asteroid Miner | Project Helga |
|---|---|---|
| Final output | Single transparent PNG | Live glTF (`.glb`) mesh |
| Viewed how | One fixed, locked camera angle, forever | Free camera, any angle/distance, real time |
| Camera in Blender | Locked orthographic top-down (rotating objects) or free 3/4 (static objects) | Irrelevant — Godot's camera generates the view |
| Blender scale | Arbitrary/cosmetic — only render aspect ratio matters | Real 1:1 meters, physically load-bearing |
| Topology standard | Loose — silhouette from one angle is all that matters | Strict clean quads — full scrutiny from every angle |
| Lighting | Baked once; must be flat/rotation-safe for spinning objects, free for static ones | Real Godot lights, changes every frame — nothing baked |
| Dynamic FX (thrusters, glow, lit windows) | Excluded from the model — drawn procedurally in code, on top | N/A — Helga has no equivalent pre-render step |
| Materials | Simple flat-shaded hard-surface hull | Full PBR (Principled BSDF, ORM packing, normal maps) |
| Render engine choice | Eevee Next (iterate) → Cycles (final still), either is fine | Eevee Next Material Preview (matches Godot's real-time look) |
| Export | Render → PNG (`F12` + Save As) | `File → Export → glTF 2.0 (.glb)` |
| Livery swap at runtime | Re-render a PNG per livery (small livery counts), or a runtime tint/mask shader (many liveries) | Swap the Base Color texture on a material override |

---

## 6. Appendix: Menu Path & Shortcut Index

Grouped for fast lookup. All paths assume Blender 4.2+.

**Viewport & navigation**
- `Tab` — toggle Object Mode / Edit Mode
- `N` — toggle the sidebar (Item/View/etc. tabs)
- `Numpad 1 / 3 / 7` — Front / Right / Top orthographic view (`Ctrl+` for the opposite side)
- `Numpad 0` — look through the active camera
- `Shift+A` — Add menu (mesh, camera, image reference, etc.)
- `Shift+C` — reset 3D cursor to world origin and frame all
- `Shift+Right-click` — place the 3D cursor precisely

**Modeling**
- `Ctrl+B` — interactive Bevel
- `Ctrl+R` — Loop Cut
- `K` — Knife tool
- `I` — Inset Faces
- `Ctrl+J` — Join selected objects into one
- `Edge` menu → `Bridge Edge Loops` — loft a surface between two edge loops
- `Edge` menu → `Mark Sharp` / `Mark Seam`
- `Object` menu → `Shade Auto Smooth` (adds a **Smooth by Angle** modifier in 4.1+)
- `Object` menu → `Set Origin` → `Origin to Geometry` / `Origin to 3D Cursor`
- `Select` → `All by Trait` → `Non-Manifold` / `Faces by Sides` — cleanup checks before export
- `Face` → `Triangulate Faces`
- Modifier Properties (wrench icon) → `Add Modifier` → `Generate` → `Mirror` / `Bevel` / `Boolean`

**Camera**
- `View` → `Align View` → `Align Active Camera to View` (`Ctrl+Alt+Numpad 0`)
- Object Data Properties (green camera icon) → `Lens` → `Type` → `Orthographic`, and `Orthographic Scale`
- Object Properties (orange square icon) → `Transform` panel → padlock icons to lock Location/Rotation
- `N` panel → `View` tab → **"Lock Camera to View"** (keep this unchecked)
- Outliner → cursor/arrow icon per object → toggle "Selectable"
- Object Data Properties → `Depth of Field` panel

**Render & output (Project 1)**
- Render Properties (camera-back icon) → `Render Engine` dropdown (Eevee Next / Cycles)
- Render Properties → `Film` panel → `Transparent` checkbox
- Render Properties → `Raytracing` (Eevee Next's home for AO, replacing the old standalone AO panel)
- Render Properties → `Color Management` panel → `View Transform` (Standard vs. AgX)
- Render Properties → `Sampling` panel
- Output Properties (printer icon) → `Format` panel → Resolution X/Y
- Output Properties → `Output` panel → `File Format` (PNG) / `Color` (RGBA) / `Color Depth`
- `Render` menu → `Render Image` (`F12`); Image Editor → `Image` → `Save As`

**UV (Project 2 / liveries)**
- `Ctrl+E` → `Mark Seam`
- `U` → `Unwrap` (Angle Based / Conformal)
- `U` → `Smart UV Project` (utility parts only — avoid on hero surfaces)
- `UV` menu → `Pack Islands` (`Margin` setting)
- `UV` menu → `Export UV Layout`
- Texel Density Checker addon (mrven) — measure/match UV island density

**Shading & materials (Project 2)**
- Shader Editor → Principled BSDF (Base Color, Roughness, Metallic, Normal, Transmission inputs)
- Shader Editor → `Add` → `Output` → `glTF Material Output` (Occlusion input)
- `Separate Color (RGB)` node — for unpacking an ORM texture
- `Normal Map` node — for tangent-space normal maps
- `Texture Paint` workspace tab

**Export (Project 2)**
- `Object` → `Apply` → `All Transforms` (`Ctrl+A`)
- `File` → `Export` → `glTF 2.0 (.glb/.gltf)`
- Exporter panel: `Transform → +Y Up`, `Geometry → Apply Modifiers`, `Geometry → Export Materials`

**XFLR5 handoff (Project 2)**
- XFLR5: `File` → `Export` (airfoil `.dat`, Selig format)
- XFLR5: `Wing and Plane Design` module — planform/station table, `.csv` / `.xwimp` export
- Blender: `Edit` → `Preferences` → `Get Extensions` → "Add Airfoil"
- Blender: `File` → `Import` → `Add Airfoil` (or `Shift+A` → `Mesh` → `Add Airfoil`)
- Blender: Scripting workspace, for the scripted lofting path
