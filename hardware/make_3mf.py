"""Emit a Bambu-loadable .3mf per hardware STL.

Adapts C:\\Users\\infin\\3dmodels\\house-finch-male\\src\\make_3mf.py (basematerials +
per-object extruder index), but these parts are single-material, so each .3mf carries one
object with one base material and one extruder assignment. Sniffs ASCII vs binary STL the
same way the repo gate scripts do (OpenSCAD default is ASCII; some here are binary with an
"OpenSCAD" 80-byte header).
"""
import struct, zipfile, os

HW  = r"C:\Users\infin\biomech-pressure-lab\hardware"
OUT = os.path.join(HW, "print")
os.makedirs(OUT, exist_ok=True)

# part.stl -> (material label, sRGB displaycolor, extruder index)
# Colours are display-only; extruder is a sensible default (user re-slots per PRINT_CARD:
# TPU parts feed the EXTERNAL spool, high-grade parts an AMS slot).
PARTS = {
 "relief_insole":        ("TPU dual (soft 85-90A + shell 95A)", "#F0B27A", 1),
 "barefoot_sole":        ("TPU soft 85A",                       "#F5CBA7", 1),
 "insole_fsr_layout":    ("TPU (6-zone FSR carrier)",           "#EDBB99", 1),
 "ankle_pod":            ("ASA",                                "#E67E22", 1),
 "ankle_pod_enclosure":  ("ASA (base+lid)",                     "#D68910", 1),
 "pressure_mat":         ("ASA / PETG-CF electrode comb",       "#CA6F1E", 1),
 "force_plate":          ("PA-CF / PETG-CF structural",         "#212F3D", 1),
 "fsr_puck":             ("PETG rigid",                         "#48C9B0", 1),
}

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MAT  = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"


def read_tris(path):
    with open(path, "rb") as f:
        data = f.read()
    looks_ascii = data[:5].lower() == b"solid"
    if looks_ascii and len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        if len(data) == 84 + n * 50:
            looks_ascii = False
    tris = []
    if looks_ascii:
        cur = []
        for line in data.decode("ascii", "replace").splitlines():
            p = line.split()
            if len(p) == 4 and p[0] == "vertex":
                cur.append((float(p[1]), float(p[2]), float(p[3])))
                if len(cur) == 3:
                    tris.append(tuple(cur)); cur = []
        return tris
    n = struct.unpack("<I", data[80:84])[0]
    for i in range(n):
        off = 84 + i * 50 + 12
        v = struct.unpack("<9f", data[off:off + 36])
        tris.append((v[0:3], v[3:6], v[6:9]))
    return tris


def dedupe(tris, tx, ty, tz):
    vm = {}; verts = []; faces = []
    for t in tris:
        idx = []
        for v in t:
            k = (round(v[0] - tx, 4), round(v[1] - ty, 4), round(v[2] - tz, 4))
            j = vm.get(k)
            if j is None:
                j = len(verts); vm[k] = j; verts.append(k)
            idx.append(j)
        if idx[0] != idx[1] and idx[1] != idx[2] and idx[0] != idx[2]:
            faces.append(idx)
    return verts, faces


def write_3mf(part, label, color, extruder):
    tris = read_tris(os.path.join(HW, part + ".stl"))
    xs = [v[0] for t in tris for v in t]; ys = [v[1] for t in tris for v in t]; zs = [v[2] for t in tris for v in t]
    tx = (min(xs) + max(xs)) / 2.0; ty = (min(ys) + max(ys)) / 2.0; tz = min(zs)  # centre XY, drop to plate
    verts, faces = dedupe(tris, tx, ty, tz)

    model = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<model unit="millimeter" xml:lang="en-US" xmlns="%s" xmlns:m="%s">' % (CORE, MAT),
             ' <metadata name="Title">%s (%s)</metadata>' % (part, label),
             ' <resources>',
             '  <basematerials id="1">',
             '   <base name="%s" displaycolor="%sFF"/>' % (label, color),
             '  </basematerials>',
             '  <object id="2" type="model" pid="1" pindex="0"><mesh><vertices>']
    model.append(''.join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % (x, y, z) for (x, y, z) in verts))
    model.append('</vertices><triangles>')
    model.append(''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % (a, b, c) for (a, b, c) in faces))
    model.append('</triangles></mesh></object>')
    model += [' </resources>', ' <build>', '  <item objectid="2"/>', ' </build>', '</model>']

    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>', '  <object id="2">',
           '    <metadata key="name" value="%s"/>' % part,
           '    <metadata key="extruder" value="%d"/>' % extruder,
           '  </object>', '</config>']

    out = os.path.join(OUT, part + ".3mf")
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', "\n".join(model))
        z.writestr('Metadata/model_settings.config', "\n".join(cfg))
    print("wrote %-24s tris=%-6d verts=%-6d size=%d" % (part + ".3mf", len(faces), len(verts), os.path.getsize(out)))


for part, (label, color, extruder) in PARTS.items():
    write_3mf(part, label, color, extruder)
print("3MF_DONE")
