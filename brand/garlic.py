# $GARLIC coin image: a head of garlic, papery skin torn open, one clove replaced by a pump.fun-style pill.
# blender -b --factory-startup --python brand/garlic.py -- <out.png> [samples] [res]
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "//garlic.png"
SAMPLES = int(argv[1]) if len(argv) > 1 else 256
RES = int(argv[2]) if len(argv) > 2 else 1500
random.seed(7)

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene

N = 8                   # clove slots round the bulb (one holds the pill)
RM, H = 3.0, 5.0        # bulb radius and height
PILL_SLOT = 0           # slot index that faces the camera
FRONT = -math.pi / 2 - 0.42   # the pill's slot, left of the camera's view so its lean reads as a diagonal


def g(t):               # bulb profile: outer radius as a share of RM at height t (0 base, 1 top)
    return max(0.0, math.sin(math.pi * (0.13 + 0.87 * t))) ** 0.72


def sgnpow(x, p): return math.copysign(abs(x) ** p, x)


def clove(name, phi0, hw, scale=1.0, lift=0.0):
    bm = bmesh.new()
    NH, NR, n = 30, 28, 2.4
    rings = []
    for i in range(NH + 1):
        t = 0.985 * i / NH
        ro = RM * g(t) * scale
        ri = 0.10 * RM * (1 - t) ** 1.5
        rc, a = (ro + ri) / 2, (ro - ri) / 2
        z = H * t * (0.96 + 0.04 * scale) + lift
        ring = []
        for j in range(NR):
            th = 2 * math.pi * j / NR
            cu, sv = sgnpow(math.cos(th), 2 / n), sgnpow(math.sin(th), 2 / n)
            r = rc + a * cu
            ang = phi0 + sv * hw * (0.82 + 0.18 * (cu + 1) / 2)
            ring.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
        rings.append(ring)
    for i in range(NH):
        for j in range(NR):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % NR], rings[i + 1][(j + 1) % NR], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    tip = bm.verts.new((0.05 * math.cos(phi0), 0.05 * math.sin(phi0), H * (0.96 + 0.04 * scale) * 1.0 + lift + 0.08))
    for j in range(NR):
        bm.faces.new((rings[-1][j], rings[-1][(j + 1) % NR], tip))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    sub = ob.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 3
    return ob


def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return m, nt, bsdf


def inp(bsdf, *names):
    for nm in names:
        if nm in bsdf.inputs: return bsdf.inputs[nm]
    return None


def streaks(nt, scale=(38, 38, 2.5), detail=8):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = detail
    nz.inputs["Scale"].default_value = 1.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    return nz, tc


def bump(nt, bsdf, height, strength):
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    nt.links.new(height, b.inputs["Height"]); nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


# ---- clove flesh-and-skin material: ivory, a blush toward the base, fine vertical fibres
def clove_mat():
    m, nt, bsdf = node_mat("Clove")
    nz, tc = streaks(nt)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.50, 0.26, 0.34, 1)
    ramp.color_ramp.elements[1].position = 0.40; ramp.color_ramp.elements[1].color = (0.80, 0.70, 0.58, 1)
    e = ramp.color_ramp.elements.new(0.85); e.color = (0.86, 0.78, 0.64, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.55
    nt.links.new(ramp.outputs["Color"], mix.inputs[6]); nt.links.new(nz.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.42
    s = inp(bsdf, "Subsurface Weight", "Subsurface"); s.default_value = 0.25
    r = inp(bsdf, "Subsurface Radius"); r.default_value = (0.6, 0.45, 0.35)
    sh = inp(bsdf, "Sheen Weight", "Sheen"); sh.default_value = 0.35
    bump(nt, bsdf, nz.outputs["Fac"], 0.3)
    return m


# ---- outer papery skin: off-white, translucent, purple veins low down
def skin_mat():
    m, nt, bsdf = node_mat("Skin")
    nz, tc = streaks(nt, (90, 90, 1.2), 12)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    vein = nt.nodes.new("ShaderNodeValToRGB")
    vein.color_ramp.elements[0].position = 0.48; vein.color_ramp.elements[0].color = (0, 0, 0, 1)
    vein.color_ramp.elements[1].position = 0.62; vein.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], vein.inputs["Fac"])
    low = nt.nodes.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = 0.75; low.inputs["From Max"].default_value = 0.1
    nt.links.new(sep.outputs["Z"], low.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(vein.outputs["Color"], mul.inputs[0]); nt.links.new(low.outputs["Result"], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.84, 0.78, 0.68, 1); mix.inputs[7].default_value = (0.30, 0.12, 0.24, 1)
    nt.links.new(mul.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.62
    inp(bsdf, "Subsurface Weight", "Subsurface").default_value = 0.35
    inp(bsdf, "Sheen Weight", "Sheen").default_value = 0.6
    t = inp(bsdf, "Transmission Weight", "Transmission"); t.default_value = 0.3
    bump(nt, bsdf, nz.outputs["Fac"], 0.35)
    return m


def pill_mat(name, color, rough):
    m, nt, bsdf = node_mat(name)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    inp(bsdf, "Coat Weight", "Clearcoat").default_value = 1.0
    inp(bsdf, "Coat Roughness", "Clearcoat Roughness").default_value = 0.06
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90; nz.inputs["Detail"].default_value = 6
    bump(nt, bsdf, nz.outputs["Fac"], 0.025)
    return m


CLOVE, SKIN = clove_mat(), skin_mat()
GREEN = pill_mat("PillGreen", (0.012, 0.42, 0.075, 1), 0.2)
WHITE = pill_mat("PillWhite", (0.86, 0.87, 0.84, 1), 0.28)

# ---- cloves round the bulb, one slot left for the pill
hw = math.pi / N * 0.93
for k in range(N):
    if k == PILL_SLOT: continue
    phi = FRONT + 2 * math.pi * k / N + random.uniform(-0.05, 0.05)
    c = clove(f"Clove{k}", phi, hw, scale=random.uniform(0.95, 1.03), lift=random.uniform(-0.04, 0.06))
    c.data.materials.append(CLOVE)

# ---- the pill: a capsule standing in the front slot, leaning in like a clove
def capsule(r, L, seg=48, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings * 2, radius=r)
    for v in bm.verts:
        v.co.z += L / 2 if v.co.z > 0 else -L / 2
    me = bpy.data.meshes.new("Pill"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return me

PR, PL = 0.86, 3.0
me = capsule(PR, PL)
me.materials.append(GREEN); me.materials.append(WHITE)
for p in me.polygons: p.material_index = 0 if p.center.z > 0.0 else 1
pill = bpy.data.objects.new("Pill", me); sc.collection.objects.link(pill)
pill.modifiers.new("sub", "SUBSURF").levels = 1
bev = pill.modifiers["sub"]; bev.render_levels = 2
# seam ring between the halves
bpy.ops.mesh.primitive_torus_add(major_radius=PR * 1.0, minor_radius=0.035, major_segments=96, minor_segments=12)
seam = bpy.context.active_object; seam.name = "Seam"; seam.data.materials.append(WHITE); seam.parent = pill
phi = FRONT
base = Vector((math.cos(phi), math.sin(phi), 0))
p0 = base * (RM * 0.80) + Vector((0, 0, 1.15))       # bottom end
p1 = base * (RM * 0.30) + Vector((0, 0, H * 0.86))   # top end, leaning in
axis = (p1 - p0).normalized()
pill.location = (p0 + p1) / 2 + base * 0.15
pill.rotation_mode = "QUATERNION"; pill.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
pill.scale = (1, 1, ((p1 - p0).length) / (PL + 2 * PR) * 1.05)

# ---- outer skin: a cup round the lower bulb with a torn edge, opened wide at the front
def skin():
    bm = bmesh.new()
    NP, NT = 160, 26
    grid = []
    for i in range(NP):
        ph = 2 * math.pi * i / NP
        d = math.atan2(math.sin(ph - FRONT), math.cos(ph - FRONT))           # angle from the front
        open_ = math.exp(-(d / 0.75) ** 2)                                     # the tear at the front
        edge = 0.62 + 0.10 * math.sin(ph * 5 + 1.3) + 0.06 * math.sin(ph * 13) + random.uniform(-0.03, 0.03)
        edge = edge * (1 - 0.78 * open_) + 0.04
        col = []
        for j in range(NT + 1):
            t = edge * j / NT
            lobe = 1 + 0.045 * math.cos(N * (ph - FRONT) + math.pi)
            r = (RM * g(t) * 1.045 + 0.05) * lobe
            flare = (j / NT) ** 3 * 0.25 * (1 + open_)                          # torn edge curls outward
            col.append(bm.verts.new(((r + flare) * math.cos(ph), (r + flare) * math.sin(ph), H * t - 0.02)))
        grid.append(col)
    for i in range(NP):
        a, b = grid[i], grid[(i + 1) % NP]
        for j in range(NT):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    bot = bm.verts.new((0, 0, -0.02))
    for i in range(NP):
        bm.faces.new((grid[(i + 1) % NP][0], grid[i][0], bot))
    me = bpy.data.meshes.new("Skin"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new("Skin", me); sc.collection.objects.link(ob)
    so = ob.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.012
    ob.modifiers.new("sub", "SUBSURF").render_levels = 2
    dm = ob.modifiers.new("disp", "DISPLACE")
    tx = bpy.data.textures.new("crinkle", "CLOUDS"); tx.noise_scale = 0.9
    dm.texture = tx; dm.strength = 0.035
    ob.data.materials.append(SKIN)
    return ob

skin()

# the dry stalk the cloves wrap round
stalkmat, tnt, tbsdf = node_mat("Stalk")
snz, _ = streaks(tnt, (30, 30, 1.5), 10)
tr = tnt.nodes.new("ShaderNodeValToRGB")
tr.color_ramp.elements[0].color = (0.22, 0.16, 0.10, 1); tr.color_ramp.elements[1].color = (0.58, 0.48, 0.34, 1)
tnt.links.new(snz.outputs["Fac"], tr.inputs["Fac"]); tnt.links.new(tr.outputs["Color"], tbsdf.inputs["Base Color"])
tbsdf.inputs["Roughness"].default_value = 0.85
bump(tnt, tbsdf, snz.outputs["Fac"], 0.9)
st_disp = None
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.36, radius2=0.2, depth=1.25, location=(0.02, 0.0, H + 0.5))
st = bpy.context.active_object; st.name = "Stalk"; st.rotation_euler = (0.06, -0.08, 0); st.data.materials.append(stalkmat)
bpy.ops.object.shade_smooth()

# roots: a short dry tuft under the base
rootmat, rnt, rbsdf = node_mat("Root")
rbsdf.inputs["Base Color"].default_value = (0.42, 0.33, 0.24, 1); rbsdf.inputs["Roughness"].default_value = 0.8
for i in range(140):
    a = random.uniform(0, 2 * math.pi); rr = random.uniform(0, 0.9)
    cu = bpy.data.curves.new("root", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.007
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
    st = Vector((rr * math.cos(a), rr * math.sin(a), 0.0))
    out = Vector((math.cos(a), math.sin(a), 0))
    pts = [st, st + out * random.uniform(0.3, 0.6) + Vector((0, 0, -0.18)), st + out * random.uniform(0.7, 1.3) + Vector((random.uniform(-.3, .3), random.uniform(-.3, .3), -0.32))]
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new("Root", cu); ob.data.materials.append(rootmat); sc.collection.objects.link(ob)

# ---- set: dark slate tabletop and a sweep behind
slate, snt, sbsdf = node_mat("Slate")
nz = snt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.62
ramp = snt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.006, 0.006, 0.007, 1); ramp.color_ramp.elements[1].color = (0.022, 0.022, 0.024, 1)
snt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); snt.links.new(ramp.outputs["Color"], sbsdf.inputs["Base Color"])
rr_ = snt.nodes.new("ShaderNodeMapRange"); rr_.inputs["To Min"].default_value = 0.55; rr_.inputs["To Max"].default_value = 0.9
snt.links.new(nz.outputs["Fac"], rr_.inputs["Value"]); snt.links.new(rr_.outputs["Result"], sbsdf.inputs["Roughness"])
bump(snt, sbsdf, nz.outputs["Fac"], 0.25)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.35)); bpy.context.active_object.data.materials.append(slate)
back, bnt, bbsdf = node_mat("Back"); bbsdf.inputs["Base Color"].default_value = (0.02, 0.022, 0.024, 1); bbsdf.inputs["Roughness"].default_value = 0.9
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 22, 10), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.data.materials.append(back)

# ---- light: big soft key top left, cool fill, warm rim, a faint pump-green kicker from behind
def area(name, loc, target, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = color
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o

C = (0, 0, 2.4)
area("Key", (-9, -8, 12), C, 7, 5200, (1.0, 0.96, 0.9))
area("Fill", (10, -9, 4), C, 8, 650, (0.85, 0.9, 1.0))
area("Rim", (6, 9, 9), C, 3, 2600, (1.0, 0.93, 0.82))
kl = bpy.data.lights.new("Kick", "SPOT"); kl.energy = 2600; kl.spot_size = math.radians(22); kl.spot_blend = 0.6; kl.color = (0.4, 1.0, 0.55); kl.shadow_soft_size = 0.6
ko = bpy.data.objects.new("Kick", kl); sc.collection.objects.link(ko); ko.location = (-7, 9, 9)
ko.rotation_euler = (Vector((0, 0, 3.2)) - ko.location).to_track_quat("-Z", "Y").to_euler()
area("Glow", (0, 17, 6), (0, 22, 6), 9, 500, (0.75, 1.0, 0.82))   # pool of light on the sweep behind

w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.005, 1)

# ---- camera
cam = bpy.data.cameras.new("Cam"); cam.lens = 85; cam.dof.use_dof = True; cam.dof.aperture_fstop = 4.5
co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0.6, -21.5, 7.9)
co.rotation_euler = (Vector((0, 0, 2.55)) - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (Vector((-1.2, -2.4, 2.6)) - co.location).length

# ---- render
sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dt in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = dt; prefs.get_devices()
            if any(d.type == dt for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == dt
                sc.cycles.device = "GPU"; print("GPU", dt); break
        except TypeError: pass
except Exception as e: print("no gpu", e)
sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = False
try: sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError: pass
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
