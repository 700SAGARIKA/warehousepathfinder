"""
Warehouse Path Finder
=====================

Upload an SVG floor plan -> let the app propose waypoints and rack faces -> refine
them on a snapping grid -> route between any two bins.

BIN NAMING
----------
Every shelf level gets a canonical name from a prefix + zero-padded counter:
bin0001, bin0002, ... bin9999 (prefix, pad width and start number are all
adjustable; the counter simply grows past the pad width rather than wrapping).
A rack ID typed in the picker is kept alongside as a separate `rack` / `alias`
column, so you get uniform machine-friendly IDs without losing your own
labelling.

MULTI-SHELF BINS
----------------
One click marks a rack *face* — a floor footprint holding 1..N shelf levels.
It expands into that many bin nodes sharing the same (x, y) with distinct
names, joined by zero-cost edges since moving between levels at one face
costs no floor travel.

GRID + SNAPPING
---------------
Snapping priority is guides > alignment > grid, per axis independently:
  * guides    — the plan's own detected rack/aisle lines
  * alignment — reuse an existing point's x or y, so a row stays a row
  * grid      — fixed pitch, adjustable spacing and origin
Hold SHIFT to place a point exactly at the cursor. Press R to array the delta
between the last two points N more times.

THEME
-----
The deep blue-black styling is injected as CSS so this stays a single file.
For a cleaner result (widget internals, menus, scrollbars) also create
`.streamlit/config.toml` next to this script:

    [theme]
    base = "dark"
    primaryColor = "#38bdf8"
    backgroundColor = "#070b18"
    secondaryBackgroundColor = "#0e1630"
    textColor = "#e6ecff"

Run with:
    streamlit run streamlit_app.py
"""

import io
import csv
import json
import math
import heapq
import re
import base64
from collections import defaultdict

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw
from scipy import ndimage
import cairosvg

MAX_SHELVES = 8

# deep blue-black palette, shared by the page, the picker and the overlays
THEME = {
    "BG":       "#070b18",
    "BG2":      "#0a1024",
    "PANEL":    "#0e1630",
    "PANEL2":   "#131c3d",
    "BORDER":   "#1c2a4d",
    "TEXT":     "#e6ecff",
    "MUTED":    "#8798c4",
    "ACCENT":   "#38bdf8",   # cyan — waypoints, focus
    "ACCENT2":  "#f472b6",   # pink — bins
    "OK":       "#10b981",
    "WARN":     "#f59e0b",
    "DANGER":   "#f43f5e",
}

WP_RGB = (56, 189, 248)
BIN_RGB = (244, 114, 182)
EDGE_RGB = (16, 185, 129)
PATH_RGB = (245, 158, 11)
GUIDE_RGB = (120, 150, 210)

st.set_page_config(page_title="Warehouse Path Finder", page_icon="📦",
                   layout="wide")


# ----------------------------------------------------------------------
# 0. THEME + HEADER
# ----------------------------------------------------------------------

PAGE_CSS = """
<style>
  :root{
    color-scheme: dark;
    --wpf-bg:{{BG}}; --wpf-bg2:{{BG2}}; --wpf-panel:{{PANEL}};
    --wpf-panel2:{{PANEL2}}; --wpf-border:{{BORDER}}; --wpf-text:{{TEXT}};
    --wpf-muted:{{MUTED}}; --wpf-accent:{{ACCENT}}; --wpf-accent2:{{ACCENT2}};
  }
  .stApp, [data-testid="stAppViewContainer"]{
    background:
      radial-gradient(1100px 520px at 12% -8%, #12224d 0%, transparent 62%),
      radial-gradient(900px 460px at 88% 4%, #0d2b46 0%, transparent 58%),
      {{BG}};
    color:{{TEXT}};
  }
  [data-testid="stHeader"]{background:transparent;}
  [data-testid="stSidebar"]{background:{{BG2}}; border-right:1px solid {{BORDER}};}
  .block-container{padding-top:1.4rem; max-width:1500px;}

  h1,h2,h3,h4,h5,h6,p,span,label,li,div[data-testid="stMarkdownContainer"]{color:{{TEXT}};}
  [data-testid="stCaptionContainer"], .stCaption, small{color:{{MUTED}} !important;}

  /* header banner */
  .wpf-head{
    border:1px solid {{BORDER}};
    background:
      linear-gradient(135deg, rgba(56,189,248,.10) 0%, rgba(244,114,182,.07) 55%, transparent 100%),
      {{PANEL}};
    border-radius:16px; padding:18px 22px; margin:0 0 18px;
    display:flex; align-items:center; gap:18px; flex-wrap:wrap;
    box-shadow:0 12px 34px rgba(0,0,0,.42);
  }
  .wpf-mark{
    width:46px; height:46px; border-radius:13px; flex:none;
    display:flex; align-items:center; justify-content:center; font-size:23px;
    background:linear-gradient(140deg,{{ACCENT}},{{ACCENT2}});
    box-shadow:0 0 24px rgba(56,189,248,.35);
  }
  .wpf-title{font-size:23px; font-weight:700; letter-spacing:-.015em; line-height:1.2;}
  .wpf-title span{
    background:linear-gradient(92deg,{{ACCENT}},{{ACCENT2}});
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  }
  .wpf-sub{color:{{MUTED}}; font-size:12.5px; margin-top:3px;}
  .wpf-chips{margin-left:auto; display:flex; gap:8px; flex-wrap:wrap;}
  .wpf-chip{
    border:1px solid {{BORDER}}; background:{{BG2}}; border-radius:999px;
    padding:5px 12px; font-size:11.5px; color:{{MUTED}}; white-space:nowrap;
  }
  .wpf-chip b{color:{{TEXT}}; font-variant-numeric:tabular-nums;}
  .wpf-dot{display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:6px;}

  /* widgets */
  [data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stTabs"] [role="tabpanel"]{
    background:{{PANEL}}; border:1px solid {{BORDER}}; border-radius:12px;
  }
  [data-testid="stMetric"]{padding:12px 14px;}
  [data-testid="stMetricValue"]{color:{{ACCENT}};}
  [data-testid="stExpander"] summary{color:{{TEXT}};}
  .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"]>div{
    background:{{BG2}} !important; color:{{TEXT}} !important; border-color:{{BORDER}} !important;
  }
  .stButton>button, .stDownloadButton>button{
    background:{{PANEL2}}; color:{{TEXT}}; border:1px solid {{BORDER}};
    border-radius:9px; font-weight:600;
  }
  .stButton>button:hover, .stDownloadButton>button:hover{
    border-color:{{ACCENT}}; color:{{ACCENT}};
  }
  .stButton>button[kind="primary"]{
    background:linear-gradient(135deg,{{ACCENT}},#2563eb); color:#04121f; border:0;
  }
  [data-testid="stFileUploaderDropzone"]{
    background:{{PANEL}}; border:1px dashed {{BORDER}}; border-radius:12px;
  }
  [data-testid="stFileUploaderDropzone"] button{
    background:linear-gradient(135deg,{{ACCENT}},#2563eb) !important;
    color:#04121f !important; border:0 !important; border-radius:9px;
    font-weight:700; opacity:1 !important;
  }
  [data-testid="stFileUploaderDropzone"] button:hover{
    filter:brightness(1.08);
  }
  [data-testid="stFileUploaderDropzone"] button span,
  [data-testid="stFileUploaderDropzone"] button p{
    color:#04121f !important;
  }
  [data-testid="stDataFrame"]{border:1px solid {{BORDER}}; border-radius:10px;}
  hr, [data-testid="stDivider"]{border-color:{{BORDER}};}
  [data-testid="stImage"] img{border-radius:12px; border:1px solid {{BORDER}};}
  ::-webkit-scrollbar{width:11px; height:11px;}
  ::-webkit-scrollbar-track{background:{{BG}};}
  ::-webkit-scrollbar-thumb{background:{{BORDER}}; border-radius:8px;}
  ::-webkit-scrollbar-thumb:hover{background:{{ACCENT}};}
</style>
"""


def themed(text):
    for k, v in THEME.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def page_header(chips=()):
    chip_html = "".join(
        f'<div class="wpf-chip"><span class="wpf-dot" style="background:{c}"></span>'
        f'{label} <b>{value}</b></div>'
        for label, value, c in chips)
    st.markdown(themed(f"""
      <div class="wpf-head">
        <div class="wpf-mark">📦</div>
        <div>
          <div class="wpf-title">Warehouse <span>Path Finder</span></div>
          <div class="wpf-sub">Floor-plan digitiser · rack-face picker ·
            shelf-level bin graph · shortest-path routing</div>
        </div>
        <div class="wpf-chips">{chip_html}</div>
      </div>"""), unsafe_allow_html=True)


st.markdown(themed(PAGE_CSS), unsafe_allow_html=True)


# ----------------------------------------------------------------------
# 1. DETECTION: coloured dots
# ----------------------------------------------------------------------

def detect_blobs(arr, kind):
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    if kind == "red":
        mask = (r > 150) & (g < 90) & (b < 90)
    else:  # yellow
        mask = (r > 180) & (g > 140) & (b < 120)
    lbl, n = ndimage.label(mask)
    centers = ndimage.center_of_mass(mask, lbl, range(1, n + 1))
    sizes = ndimage.sum(mask, lbl, range(1, n + 1))
    return [(c[1], c[0]) for c, s in zip(centers, sizes) if s >= 3]


def cluster_1d(vals, tol=8):
    vals = sorted(vals)
    groups, cur = [], [vals[0]]
    for v in vals[1:]:
        if v - cur[-1] <= tol:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    return groups


# ----------------------------------------------------------------------
# 2. STRUCTURE: the long straight lines the plan is drawn with
# ----------------------------------------------------------------------

def ink_mask(arr, thresh=230):
    return arr.mean(axis=2) < thresh


def _longest_runs(mask, bridge=6):
    """Longest horizontal ink run per row, after bridging small dashes."""
    if bridge > 1:
        mask = ndimage.binary_closing(mask, structure=np.ones((1, bridge)))
    out = np.zeros(mask.shape[0])
    for i, row in enumerate(mask):
        if not row.any():
            continue
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        if starts.size:
            out[i] = (ends - starts).max()
    return out


def detect_lines(mask, axis, min_frac=0.18, merge_tol=3, bridge=6):
    """axis='h' -> y of horizontal lines; 'v' -> x of vertical lines."""
    m = mask if axis == "h" else mask.T
    runs = _longest_runs(m, bridge=bridge)
    idx = np.flatnonzero(runs >= min_frac * m.shape[1])
    if idx.size == 0:
        return []
    groups, cur = [], [idx[0]]
    for v in idx[1:]:
        if v - cur[-1] <= merge_tol:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    out = []
    for g in groups:
        w = runs[g]
        out.append(float(np.average(g, weights=w) if w.sum() else np.mean(g)))
    return out


def classify_bands(lines, min_aisle, min_rack=3):
    racks, aisles = [], []
    for a, b in zip(lines, lines[1:]):
        gap = b - a
        if gap >= min_aisle:
            aisles.append({"lo": a, "hi": b, "center": (a + b) / 2, "width": gap})
        elif gap >= min_rack:
            racks.append({"lo": a, "hi": b, "center": (a + b) / 2, "depth": gap})
    return racks, aisles


def _band_extent(mask, band, axis, min_frac=0.05):
    lo, hi = int(round(band["lo"])), int(round(band["hi"]))
    sub = mask[lo:hi + 1, :] if axis == "h" else mask[:, lo:hi + 1].T
    if sub.size == 0:
        return None
    prof = sub.sum(axis=0)
    hits = np.flatnonzero(prof >= max(1, min_frac * sub.shape[0]))
    return (float(hits[0]), float(hits[-1])) if hits.size else None


def suggest_layout(arr, min_aisle=28, pitch=45, min_frac=0.18, access=45,
                   ink_thresh=230, max_points=1200):
    """Propose waypoints on aisle centrelines and bin faces on rack faces."""
    mask = ink_mask(arr, ink_thresh)
    h_lines = detect_lines(mask, "h", min_frac=min_frac)
    v_lines = detect_lines(mask, "v", min_frac=min_frac)
    h_racks, h_aisles = classify_bands(h_lines, min_aisle)
    v_racks, v_aisles = classify_bands(v_lines, min_aisle)

    waypoints, faces = [], []

    def add_faces(band, axis):
        ext = _band_extent(mask, band, axis)
        if not ext:
            return
        lo, hi = ext
        if hi - lo < pitch * 0.5:
            return
        centers = [a["center"] for a in (h_aisles if axis == "h" else v_aisles)]
        if not centers:
            return
        near = min(centers, key=lambda c: abs(c - band["center"]))
        if abs(near - band["center"]) > access:
            return  # this face fronts no aisle, so it isn't reachable
        n = max(1, int(round((hi - lo) / pitch)))
        step = (hi - lo) / n
        for i in range(n + 1):
            t = lo + i * step
            faces.append((t, band["center"]) if axis == "h" else (band["center"], t))
            waypoints.append((t, near) if axis == "h" else (near, t))

    for band in h_racks:
        add_faces(band, "h")
    for band in v_racks:
        add_faces(band, "v")

    for ha in h_aisles:                      # aisle intersections keep zones joined
        for va in v_aisles:
            waypoints.append((va["center"], ha["center"]))

    def dedupe(pts, tol=6):
        kept = []
        for p in pts:
            if all(abs(p[0] - q[0]) > tol or abs(p[1] - q[1]) > tol for q in kept):
                kept.append(p)
        return kept

    guides = {"x": [round(v, 1) for v in v_lines],
              "y": [round(v, 1) for v in h_lines]}
    stats = {"h_lines": len(h_lines), "v_lines": len(v_lines),
             "h_racks": len(h_racks), "v_racks": len(v_racks),
             "h_aisles": len(h_aisles), "v_aisles": len(v_aisles)}
    return dedupe(waypoints)[:max_points], dedupe(faces)[:max_points], guides, stats


def draw_suggestions(image, waypoints, faces, guides):
    im = image.copy().convert("RGB")
    d = ImageDraw.Draw(im)
    w, h = im.size
    for x in guides.get("x", []):
        d.line([(x, 0), (x, h)], fill=GUIDE_RGB, width=1)
    for y in guides.get("y", []):
        d.line([(0, y), (w, y)], fill=GUIDE_RGB, width=1)
    for x, y in faces:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=BIN_RGB, width=2)
    for x, y in waypoints:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=WP_RGB, width=2)
    return im


# ----------------------------------------------------------------------
# 3. CORRIDOR GRAPH
# ----------------------------------------------------------------------

def build_corridor_edges(red):
    xs = sorted(set(round(p[0]) for p in red))
    x_centers = [sum(g) / len(g) for g in cluster_1d(xs, tol=6)]
    ys = sorted(set(round(p[1]) for p in red))
    y_centers = [sum(g) / len(g) for g in cluster_1d(ys, tol=6)]

    def nearest(v, centers, tol=8):
        best = min(centers, key=lambda c: abs(c - v))
        return best if abs(best - v) <= tol else None

    col_of = {p: nearest(p[0], x_centers) for p in red}
    row_of = {p: nearest(p[1], y_centers) for p in red}
    cols, rows = defaultdict(list), defaultdict(list)
    for p in red:
        cols[col_of[p]].append(p)
        rows[row_of[p]].append(p)

    def row_span(pts):
        xs_ = [p[0] for p in pts]
        return max(xs_) - min(xs_) if xs_ else 0

    # the main corridor is the row spanning the widest x-range: it threads
    # through every zone plus the staging lane, unlike shelf rows which span
    # only one zone each.
    main_row = max(y_centers, key=lambda yc: row_span(rows[yc]))
    main_row_cols = {col_of[p] for p in rows[main_row]}

    edges = set()
    main_band = sorted(rows[main_row], key=lambda p: p[0])
    for a, b in zip(main_band, main_band[1:]):
        edges.add((a, b))
    for c in main_row_cols:
        pts_sorted = sorted(cols[c], key=lambda p: p[1])
        for a, b in zip(pts_sorted, pts_sorted[1:]):
            edges.add((a, b))

    # shelf rungs: a rack-face waypoint links sideways into the nearest
    # aisle-spine dot in its own zone, never vertically through the shelf.
    # Lone bridge dots are excluded from the spine so rungs don't snap to them.
    spine_cols = {c for c in main_row_cols if len(cols[c]) > 1}
    for p in red:
        if col_of[p] in main_row_cols or not spine_cols:
            continue
        spine_col = min(spine_cols, key=lambda sc: abs(sc - p[0]))
        edges.add((p, min(cols[spine_col], key=lambda s: abs(s[1] - p[1]))))
    return list(edges)


# ----------------------------------------------------------------------
# 4. BIN STACKS + NAMING
# ----------------------------------------------------------------------

def order_bin_points(bin_points):
    """Stable pick order: left-to-right by x-column, then top-to-bottom.
    This is the order the bin0001, bin0002 … counter follows."""
    if not bin_points:
        return []
    xs = sorted(set(p["x"] for p in bin_points))
    centers = sorted(sum(g) / len(g) for g in cluster_1d(xs, tol=10))

    def col_id(x):
        return min(range(len(centers)), key=lambda i: abs(centers[i] - x))

    cols = defaultdict(list)
    for i, p in enumerate(bin_points):
        cols[col_id(p["x"])].append(i)
    order = []
    for c in sorted(cols):
        order.extend(sorted(cols[c], key=lambda i: bin_points[i]["y"]))
    return order


def make_bin_name(scheme, counter, prefix, pad, stack_idx, level):
    """bin0001-style names by default. The counter keeps counting past the pad
    width (bin9999 -> bin10000) rather than wrapping or truncating."""
    if scheme == "padded":
        return f"{prefix}{counter:0{pad}d}"
    if scheme == "face-level":
        return f"{prefix}{stack_idx:0{pad}d}-{level}"
    return counter  # plain integer


def parse_start_token(s):
    """Split a typed starting name like 'bin0001' or 'A00' into
    (prefix, start_number, pad_width) — the trailing digit run sets both the
    start number and its own width; any leading text becomes the prefix."""
    m = re.match(r'^(\D*)(\d+)$', (s or "").strip())
    if not m:
        return (s or "").strip(), 1, 4
    prefix, digits = m.group(1), m.group(2)
    return prefix, int(digits), len(digits)


def expand_bin_stacks(bin_points, scheme="padded", start=1, default_count=1,
                      prefix="bin", pad=4, level_from_bottom=True,
                      label_as_name=False):
    """One picked rack face -> one bin record per shelf level, all sharing the
    face's (x, y) since the stack is vertical and adds no footprint.

    `label` (the rack ID typed in the picker) is preserved as `rack`/`alias`
    rather than replacing the canonical name, unless label_as_name is set.
    """
    order = order_bin_points(bin_points)
    counter, out = int(start), []
    for stack_idx, i in enumerate(order, start=1):
        p = bin_points[i]
        count = max(1, min(MAX_SHELVES, int(p.get("count") or default_count or 1)))
        rack = str(p.get("label", "") or "").strip()
        for lvl in range(1, count + 1):
            level = lvl if level_from_bottom else (count - lvl + 1)
            name = make_bin_name(scheme, counter, prefix, pad, stack_idx, level)
            alias = (f"{rack}-{level}" if rack and count > 1 else rack) or ""
            if label_as_name and alias:
                name = alias
            out.append({"x": float(p["x"]), "y": float(p["y"]),
                        "bin_number": name, "alias": alias, "rack": rack,
                        "stack": stack_idx, "level": level, "stack_size": count})
            counter += 1
    return out


def dedupe_bin_ids(bins):
    seen, dupes = {}, 0
    for b in bins:
        bid = b["bin_number"]
        if bid in seen:
            dupes += 1
            seen[bid] += 1
            b["bin_number"] = f"{bid}#{seen[bid]}"
        else:
            seen[bid] = 1
    return dupes


# ----------------------------------------------------------------------
# 5. NODES + EDGES
# ----------------------------------------------------------------------

def build_nodes_edges(red, bins, stack_cost=0.0, wp_prefix="W", wp_start=0, wp_pad=1):
    red = list(dict.fromkeys((round(x, 4), round(y, 4)) for x, y in red))
    corridor = build_corridor_edges(red)

    nodes, wp_id, nid = [], {}, 0
    for wp_idx, (x, y) in enumerate(red):
        wp_id[(x, y)] = nid
        wp_name = f"{wp_prefix}{wp_start + wp_idx:0{wp_pad}d}"
        nodes.append({"id": nid, "x": round(x, 1), "y": round(y, 1),
                      "type": "waypoint", "name": wp_name, "bin_number": "",
                      "alias": "", "rack": "", "stack": "", "level": ""})
        nid += 1

    bin_ids = []
    for b in bins:
        bin_ids.append(nid)
        nodes.append({"id": nid, "x": round(b["x"], 1), "y": round(b["y"], 1),
                      "type": "bin", "name": b["bin_number"],
                      "bin_number": b["bin_number"],
                      "alias": b["alias"], "rack": b["rack"],
                      "stack": b["stack"], "level": b["level"]})
        nid += 1

    edges = []
    for a, b in corridor:
        edges.append({"node_a": wp_id[a], "node_b": wp_id[b],
                      "distance": round(math.hypot(a[0] - b[0], a[1] - b[1]), 2),
                      "kind": "corridor"})
    for node_i, b in zip(bin_ids, bins):
        w = min(red, key=lambda r: math.hypot(r[0] - b["x"], r[1] - b["y"]))
        edges.append({"node_a": wp_id[w], "node_b": node_i,
                      "distance": round(math.hypot(w[0] - b["x"], w[1] - b["y"]), 2),
                      "kind": "access"})

    # levels of one face: no floor travel between them. Without these edges a
    # level-1 -> level-3 hop would detour out to the aisle and back.
    by_stack = defaultdict(list)
    for node_i, b in zip(bin_ids, bins):
        by_stack[b["stack"]].append((b["level"], node_i))
    for stack in by_stack.values():
        stack.sort()
        for (_, a), (_, b) in zip(stack, stack[1:]):
            edges.append({"node_a": a, "node_b": b,
                          "distance": round(float(stack_cost), 2), "kind": "stack"})
    return nodes, edges


def waypoint_bin_map(nodes, edges):
    byid = {n["id"]: n for n in nodes}
    served = defaultdict(list)
    for e in edges:
        if e.get("kind") != "access":
            continue
        a, b = e["node_a"], e["node_b"]
        wp, bn = (a, b) if byid[a]["type"] == "waypoint" else (b, a)
        served[wp].append((byid[bn], e["distance"]))

    rows = []
    for n in nodes:
        if n["type"] != "waypoint":
            continue
        items = served.get(n["id"], [])
        rows.append({
            "waypoint_id": n["id"], "name": n.get("name", ""),
            "x": n["x"], "y": n["y"],
            "rack_faces": len({b["stack"] for b, _ in items}),
            "bins": len(items),
            "access_distance": round(min((d for _, d in items), default=0.0), 2),
            "bin_ids": ", ".join(str(b["bin_number"]) for b, _ in items),
        })
    return rows


def to_csv_bytes(rows, fieldnames):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


# ----------------------------------------------------------------------
# 6. PATHFINDING
# ----------------------------------------------------------------------

class WarehouseTree:
    def __init__(self, nodes, edges, speed=1.0):
        self.speed = speed
        self.nodes = {n["id"]: dict(n, neighbors=[]) for n in nodes}
        self.bin_to_node = {n["bin_number"]: n["id"]
                            for n in nodes if n["type"] == "bin"}
        for e in edges:
            a, b, d = e["node_a"], e["node_b"], e["distance"]
            self.nodes[a]["neighbors"].append((b, d))
            self.nodes[b]["neighbors"].append((a, d))

    def shortest_path(self, start_id, end_id):
        if start_id == end_id:
            return [start_id], 0.0
        dist, prev, visited = {start_id: 0.0}, {}, set()
        pq = [(0.0, start_id)]
        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            if u == end_id:
                break
            for v, w in self.nodes[u]["neighbors"]:
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if end_id not in dist:
            return None, math.inf
        path = [end_id]
        while path[-1] != start_id:
            path.append(prev[path[-1]])
        path.reverse()
        return path, dist[end_id]

    def path_between_bins(self, bin_a, bin_b):
        a_id, b_id = self.bin_to_node[bin_a], self.bin_to_node[bin_b]
        path_ids, total = self.shortest_path(a_id, b_id)
        if path_ids is None:
            return None
        steps = [{"x": self.nodes[i]["x"], "y": self.nodes[i]["y"],
                  "type": self.nodes[i]["type"],
                  "bin_number": self.nodes[i]["bin_number"],
                  "level": self.nodes[i]["level"]} for i in path_ids]
        return {"distance": round(total, 2),
                "time_sec": round(total / self.speed, 2), "steps": steps}


# ----------------------------------------------------------------------
# 7. DRAWING
# ----------------------------------------------------------------------

def _dedupe_consecutive(pts):
    out = []
    for p in pts:
        if not out or p != out[-1]:
            out.append(p)
    return out


def _fan_offset(level, stack_size, r=5.0):
    if not stack_size or stack_size <= 1:
        return 0.0, 0.0
    ang = -math.pi / 2 + (level - 1) * (2 * math.pi / stack_size)
    return r * math.cos(ang), r * math.sin(ang)


def _stack_sizes(nodes):
    ss = {}
    for n in nodes:
        if n["type"] == "bin":
            ss[n["stack"]] = max(ss.get(n["stack"], 0), n["level"])
    return ss


def draw_path_on_image(image, steps):
    im = image.copy().convert("RGB")
    d = ImageDraw.Draw(im)
    pts = _dedupe_consecutive([(s["x"], s["y"]) for s in steps])
    if len(pts) > 1:
        d.line(pts, fill=(15, 23, 42), width=7, joint="curve")   # dark casing
        d.line(pts, fill=PATH_RGB, width=4, joint="curve")
    for x, y in pts:
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=PATH_RGB)
    sx, sy = pts[0]
    ex, ey = pts[-1]
    d.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], outline=WP_RGB, width=3)
    d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], outline=BIN_RGB, width=3)
    return im


def draw_skeleton_on_image(image, nodes, edges, fan=True):
    im = image.copy().convert("RGB")
    d = ImageDraw.Draw(im)
    pos = {n["id"]: (n["x"], n["y"]) for n in nodes}
    ss = _stack_sizes(nodes)
    for e in edges:
        if e.get("kind") == "stack":
            continue  # zero-length on the plan
        d.line([pos[e["node_a"]], pos[e["node_b"]]], fill=EDGE_RGB, width=2)
    for n in nodes:
        x, y = n["x"], n["y"]
        if n["type"] == "bin":
            if fan:
                dx, dy = _fan_offset(n["level"], ss.get(n["stack"], 1))
                x, y = x + dx, y + dy
            color = BIN_RGB
        else:
            color = WP_RGB
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=color)
    return im


def skeleton_to_svg(image, nodes, edges, fan=True):
    w, h = image.size
    img_b64 = png_b64(image)
    pos = {n["id"]: (n["x"], n["y"]) for n in nodes}
    ss = _stack_sizes(nodes)
    lines = "".join(
        f'<line x1="{pos[e["node_a"]][0]}" y1="{pos[e["node_a"]][1]}" '
        f'x2="{pos[e["node_b"]][0]}" y2="{pos[e["node_b"]][1]}" '
        f'stroke="{THEME["OK"]}" stroke-width="2" />'
        for e in edges if e.get("kind") != "stack")

    circles = []
    for n in nodes:
        x, y = n["x"], n["y"]
        if n["type"] == "bin":
            if fan:
                dx, dy = _fan_offset(n["level"], ss.get(n["stack"], 1))
                x, y = x + dx, y + dy
            fill = THEME["ACCENT2"]
            title = (f'{n["bin_number"]} — face {n["stack"]}, level {n["level"]}'
                     + (f' ({n["alias"]})' if n.get("alias") else ''))
        else:
            fill, title = THEME["ACCENT"], n.get("name") or f'Waypoint {n["id"]}'
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{fill}">'
                       f'<title>{title}</title></circle>')

    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">\n'
            f'  <image href="data:image/png;base64,{img_b64}" width="{w}" height="{h}" />\n'
            f'  <g>{lines}</g>\n  <g>{"".join(circles)}</g>\n</svg>\n')


# ----------------------------------------------------------------------
# 8. IMAGE LOADING
# ----------------------------------------------------------------------

def _resolve_css_vars(svg_text):
    # cairosvg has no CSS var() support; inline the fallback so it isn't parsed
    # as a literal colour (draw.io emits var(--ge-adaptive-bg, #ffffff)).
    return re.sub(r"var\(\s*--[\w-]+\s*,\s*([^)]+)\)", r"\1", svg_text)


def _viewbox_size(svg_text):
    m = re.search(r'viewBox\s*=\s*["\']\s*([-\d.eE]+)[,\s]+([-\d.eE]+)[,\s]+'
                  r'([-\d.eE]+)[,\s]+([-\d.eE]+)', svg_text)
    if m:
        return float(m.group(3)), float(m.group(4))
    w = re.search(r'\bwidth\s*=\s*["\']([\d.]+)', svg_text)
    h = re.search(r'\bheight\s*=\s*["\']([\d.]+)', svg_text)
    return (float(w.group(1)), float(h.group(1))) if w and h else None


MIN_PLAN_DIM = 200   # upscale tiny viewBoxes so the picker has enough pixels to click on
MAX_PLAN_DIM = 4000  # display/detection raster cap — kept small for speed and low memory use.
                     # This no longer trades off precision: exported coordinates are scaled
                     # back to the SVG's native viewBox size regardless of this cap (see
                     # native_size below), so oversized plans stay fast to work with on-screen
                     # while nodes.csv / waypoint_bins.csv still report exact original-file pixels.


def _decode_svg(raw_bytes):
    """Best-effort text decode: honour a BOM or an XML-declared encoding
    before falling back to utf-8, then latin-1 (which never raises)."""
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return raw_bytes.decode("utf-8-sig")
    if raw_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw_bytes.decode("utf-16")
    m = re.match(rb'<\?xml[^>]*encoding=["\']([\w-]+)["\']', raw_bytes)
    if m:
        try:
            return raw_bytes.decode(m.group(1).decode("ascii"))
        except (LookupError, UnicodeDecodeError):
            pass
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return raw_bytes.decode("latin-1")


def load_plan_image(uploaded):
    """Returns (image, native_size). `image` is a display/detection raster capped at
    MAX_PLAN_DIM for speed. `native_size` is the SVG's own viewBox/width-height in its
    original units — callers use it to scale picked coordinates back to the exact pixel
    space of the uploaded file, independent of how small the working raster is."""
    svg_text = _resolve_css_vars(_decode_svg(uploaded.getvalue()))
    size = _viewbox_size(svg_text)
    kwargs = {}
    native_size = None
    if size and math.isfinite(size[0]) and math.isfinite(size[1]) and size[0] > 0 and size[1] > 0:
        w, h = size
        native_size = (w, h)
        longest = max(w, h)
        if longest > MAX_PLAN_DIM:
            scale = MAX_PLAN_DIM / longest
        elif longest < MIN_PLAN_DIM:
            scale = MIN_PLAN_DIM / longest
        else:
            scale = 1.0
        kwargs = {"output_width": max(1, int(round(w * scale))),
                  "output_height": max(1, int(round(h * scale)))}
    png = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), **kwargs)
    image = Image.open(io.BytesIO(png)).convert("RGB")
    return image, native_size


def png_b64(image):
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ----------------------------------------------------------------------
# 9. EMBEDDED PICKER
# ----------------------------------------------------------------------

PICKER_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  :root{
    --bg:{{BG}}; --bg2:{{BG2}}; --panel:{{PANEL}}; --panel2:{{PANEL2}};
    --border:{{BORDER}}; --text:{{TEXT}}; --muted:{{MUTED}};
    --accent:{{ACCENT}}; --accent2:{{ACCENT2}}; --danger:{{DANGER}};
  }
  *{box-sizing:border-box;}
  body{margin:0; font-family:-apple-system,Segoe UI,Arial,sans-serif;
       background:
         radial-gradient(700px 320px at 10% -10%, #12224d 0%, transparent 60%),
         var(--bg);
       color:var(--text); display:flex; height:__HEIGHT__px;}
  #sidebar{width:348px; min-width:348px; border-right:1px solid var(--border);
           padding:13px; display:flex; flex-direction:column; gap:10px;
           overflow-y:auto; background:rgba(10,16,36,.72);}
  h1{font-size:15px; margin:0 0 4px;}
  h1 span{background:linear-gradient(92deg,var(--accent),var(--accent2));
          -webkit-background-clip:text; background-clip:text;
          -webkit-text-fill-color:transparent;}
  p.hint{color:var(--muted); font-size:11px; margin:0; line-height:1.5;}
  .row{display:flex; gap:6px;}
  label.f{color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.03em;}
  .chk{display:flex; align-items:center; gap:6px; font-size:11px;}
  button{background:var(--panel2); border:1px solid var(--border); color:var(--text);
         padding:7px 9px; border-radius:7px; cursor:pointer; font-size:12px; flex:1;}
  button:hover{border-color:var(--accent); color:var(--accent);}
  button.primary{background:linear-gradient(135deg,var(--accent),#2563eb);
                 color:#04121f; border:0; font-weight:700;}
  button.danger:hover{border-color:var(--danger); color:var(--danger);}
  button:disabled{opacity:.4; cursor:not-allowed;}
  .mode button.on{outline:2px solid var(--accent); color:var(--accent);}
  .shelf button{padding:6px 0; font-variant-numeric:tabular-nums;}
  .shelf button.on{background:linear-gradient(135deg,var(--accent),#2563eb);
                   color:#04121f; font-weight:700; border:0;}
  input[type=text], input[type=number]{
    width:100%; background:var(--bg2); color:var(--text); border:1px solid var(--border);
    border-radius:6px; padding:5px 7px; font-size:12px;}
  fieldset{border:1px solid var(--border); border-radius:9px; padding:9px; margin:0;
           display:flex; flex-direction:column; gap:7px; background:rgba(14,22,48,.6);}
  legend{color:var(--muted); font-size:10px; text-transform:uppercase;
         letter-spacing:.04em; padding:0 4px;}
  #readout{background:var(--panel); border:1px solid var(--border);
           border-radius:9px; padding:7px 10px;}
  #readout .val{font-size:17px; color:var(--accent); font-weight:600;
                font-variant-numeric:tabular-nums;}
  #snapNote{font-size:10px; color:var(--accent); min-height:12px;}
  table{width:100%; border-collapse:collapse; font-size:11px;}
  th, td{padding:4px 5px; text-align:left; border-bottom:1px solid var(--border);}
  th{color:var(--muted); font-weight:600; position:sticky; top:0; background:var(--panel);}
  td.num{font-variant-numeric:tabular-nums;}
  .tag{padding:1px 5px; border-radius:4px; font-size:10px; font-weight:700;}
  .tag.wp{background:rgba(56,189,248,.18); color:var(--accent);}
  .tag.bin{background:rgba(244,114,182,.18); color:var(--accent2);}
  select.cnt{background:var(--bg2); color:var(--text); border:1px solid var(--border);
             border-radius:4px; font-size:10px;}
  #pointsWrap{flex:1; min-height:110px; overflow-y:auto; border:1px solid var(--border);
              border-radius:9px; background:rgba(7,11,24,.55);}
  .del{color:var(--danger); cursor:pointer; font-weight:700;}
  textarea{width:100%; height:52px; background:var(--bg2); color:var(--muted);
           border:1px solid var(--border); border-radius:6px; font-size:10px;
           font-family:ui-monospace,Menlo,monospace; padding:6px; resize:vertical;}
  #stage{flex:1; overflow:auto; padding:16px; display:flex; align-items:flex-start;
         justify-content:center;}
  #svgHost{background:#fff; box-shadow:0 10px 40px rgba(0,0,0,.6);
           border:1px solid var(--border); border-radius:6px; overflow:hidden;
           cursor:crosshair; line-height:0;}
  #svgHost svg{display:block;}
  #empty{color:var(--muted); font-size:11px; padding:8px;}
  #zoomLbl{color:var(--muted); font-size:11px; align-self:center; min-width:42px; text-align:center;}
  #tally{color:var(--muted); font-size:11px;} #tally b{color:var(--text);}
  .ghost{cursor:pointer;}
  ::-webkit-scrollbar{width:9px; height:9px;}
  ::-webkit-scrollbar-track{background:var(--bg);}
  ::-webkit-scrollbar-thumb{background:var(--border); border-radius:8px;}
  ::-webkit-scrollbar-thumb:hover{background:var(--accent);}
</style>
</head>
<body>

<div id="sidebar">
  <div>
    <h1>Coordinate <span>Picker</span></h1>
    <p class="hint">One click = one rack face. Snapping keeps rows straight —
      hold <b>Shift</b> to place exactly at the cursor.
      Keys: <b>W</b>/<b>B</b> mode, <b>G</b> grid, <b>R</b> repeat,
      <b>Z</b> undo. Hold <b>Ctrl</b>/<b>Cmd</b> + scroll to zoom on the
      cursor, like draw.io.</p>
  </div>

  <div class="row mode">
    <button id="modeWp" class="on">Waypoint (W)</button>
    <button id="modeBin">Bin (B)</button>
  </div>

  <fieldset>
    <legend>Grid &amp; snapping</legend>
    <label class="chk"><input type="checkbox" id="gridOn" checked> Show grid (G)</label>
    <div class="row">
      <div style="flex:1"><label class="f">Spacing</label>
        <input type="number" id="gridStep" value="__GRIDSTEP__" min="2" step="1"></div>
      <div style="flex:1"><label class="f">Origin x</label>
        <input type="number" id="gridOx" value="0" step="1"></div>
      <div style="flex:1"><label class="f">Origin y</label>
        <input type="number" id="gridOy" value="0" step="1"></div>
    </div>
    <label class="chk"><input type="checkbox" id="snapGuides" checked>
      Snap to plan lines (<span id="guideCount">0</span> found)</label>
    <label class="chk"><input type="checkbox" id="snapAlign" checked>
      Snap to align with existing points</label>
    <label class="chk"><input type="checkbox" id="snapGrid"> Snap to grid</label>
    <div><label class="f">Snap tolerance (px)</label>
      <input type="number" id="snapTol" value="10" min="1" step="1"></div>
    <div id="snapNote"></div>
  </fieldset>

  <fieldset>
    <legend>Repeat / array</legend>
    <p class="hint">Place two points, set a count, then Repeat: the delta
      between the last two is stamped that many more times.</p>
    <div class="row">
      <input type="number" id="repN" value="5" min="1" max="200" style="flex:1">
      <button id="repBtn">Repeat (R)</button>
    </div>
  </fieldset>

  <fieldset id="ghostBox" style="display:none">
    <legend>Suggestions</legend>
    <p class="hint"><b id="ghostN">0</b> proposed points. Click a hollow marker
      to accept it, or take them wholesale and prune.</p>
    <div class="row">
      <button id="ghostWp">Accept waypoints</button>
      <button id="ghostBin">Accept bins</button>
    </div>
    <div class="row">
      <button id="ghostAll">Accept all</button>
      <button id="ghostClear" class="danger">Hide</button>
    </div>
  </fieldset>

  <div id="readout">
    <div class="f">Cursor position (original file px)</div>
    <div class="val" id="coordVal">x: —, y: —</div>
  </div>

  <div id="tally">Faces: <b id="tFaces">0</b> · waypoints: <b id="tWp">0</b>
    · stacks: <b id="tStacks">0</b> · bins: <b id="tBins">0</b></div>

  <div class="row">
    <button id="zoomOut">−</button><div id="zoomLbl">100%</div><button id="zoomIn">+</button>
  </div>
  <div class="row">
    <button id="zoomFit">Fit screen</button><button id="zoom100">100%</button>
  </div>
  <div class="row">
    <button id="undoBtn" disabled>Undo</button>
    <button id="clearBtn" class="danger" disabled>Clear all</button>
  </div>
  <div class="row">
    <button id="copyBtn" class="primary" disabled>Copy points</button>
    <button id="jsonBtn" disabled>Download JSON</button>
  </div>
  <p class="hint" id="copyMsg">Copy, then paste into the “Points JSON” box below.</p>
  <textarea id="jsonOut" readonly></textarea>

  <div id="pointsWrap">
    <table>
      <thead><tr><th>#</th><th>type</th>
        <th title="pixel coordinate in your original SVG file">x</th>
        <th title="pixel coordinate in your original SVG file">y</th>
        <th>lvl</th><th>rack</th><th></th></tr></thead>
      <tbody id="pointsBody"></tbody>
    </table>
    <div id="empty">No points yet — click on the plan.</div>
  </div>
</div>

<div id="stage">
  <div id="svgHost">
    <svg id="plan" xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 __W__ __H__" width="__W__" height="__H__">
      <defs>
        <pattern id="gridPat" width="__GRIDSTEP__" height="__GRIDSTEP__" patternUnits="userSpaceOnUse">
          <path d="M __GRIDSTEP__ 0 L 0 0 0 __GRIDSTEP__" fill="none"
                stroke="{{ACCENT}}" stroke-width="0.5" stroke-opacity="0.4"/>
        </pattern>
      </defs>
      <image href="data:image/png;base64,__IMG__" x="0" y="0" width="__W__" height="__H__" />
      <rect id="gridRect" x="0" y="0" width="__W__" height="__H__" fill="url(#gridPat)" pointer-events="none"/>
      <g id="guides" pointer-events="none"></g>
      <g id="ghosts"></g>
      <g id="crosshair" pointer-events="none"></g>
      <g id="markers" pointer-events="none"></g>
    </svg>
  </div>
</div>

<script>
(function(){
  const $ = id => document.getElementById(id);
  const svgEl=$('plan'), markerLay=$('markers'), ghostLay=$('ghosts'),
        guideLay=$('guides'), crossLay=$('crosshair'), gridRect=$('gridRect'),
        gridPat=$('gridPat');
  const NS='http://www.w3.org/2000/svg';
  const W=__W__, H=__H__, MAXS=__MAXS__;
  const C_WP='{{ACCENT}}', C_BIN='{{ACCENT2}}', C_SNAP='{{WARN}}';

  let points = __SEED__;
  let ghosts = __GHOSTS__;
  const guides = __GUIDES__;
  const NSX=__NSX__, NSY=__NSY__;   // raster px -> original-file px, for display only
  let mode='waypoint', shelves=__DEFCOUNT__, zoom=__ZOOM__, shiftHeld=false;

  $('guideCount').textContent = (guides.x||[]).length + (guides.y||[]).length;

  function drawGuides(){
    guideLay.innerHTML='';
    if (!$('snapGuides').checked) return;
    const mk=(x1,y1,x2,y2)=>{
      const l=document.createElementNS(NS,'line');
      l.setAttribute('x1',x1); l.setAttribute('y1',y1);
      l.setAttribute('x2',x2); l.setAttribute('y2',y2);
      l.setAttribute('stroke',C_WP); l.setAttribute('stroke-width',0.6);
      l.setAttribute('stroke-opacity',0.45); guideLay.appendChild(l);
    };
    (guides.x||[]).forEach(x=>mk(x,0,x,H));
    (guides.y||[]).forEach(y=>mk(0,y,W,y));
  }

  function applyGrid(){
    const s=Math.max(2,+$('gridStep').value||40);
    gridPat.setAttribute('width',s); gridPat.setAttribute('height',s);
    gridPat.setAttribute('x',(+$('gridOx').value||0)%s);
    gridPat.setAttribute('y',(+$('gridOy').value||0)%s);
    gridPat.firstElementChild.setAttribute('d',`M ${s} 0 L 0 0 0 ${s}`);
    gridRect.style.display=$('gridOn').checked?'':'none';
  }
  ['gridStep','gridOx','gridOy'].forEach(id=>$(id).addEventListener('input',applyGrid));
  $('gridOn').addEventListener('change',applyGrid);
  $('snapGuides').addEventListener('change',drawGuides);

  function nearestIn(list,v,tol){
    let best=null,bd=tol;
    (list||[]).forEach(c=>{const d=Math.abs(c-v); if(d<=bd){bd=d;best=c;}});
    return best;
  }
  function snap(p){
    if (shiftHeld) return {x:p.x,y:p.y,note:'free (shift)'};
    const tol=Math.max(1,+$('snapTol').value||10);
    let x=p.x,y=p.y,hitX=null,hitY=null;
    if ($('snapGuides').checked){
      const gx=nearestIn(guides.x,x,tol); if(gx!==null){x=gx;hitX='line';}
      const gy=nearestIn(guides.y,y,tol); if(gy!==null){y=gy;hitY='line';}
    }
    if ($('snapAlign').checked){
      if(hitX===null){const ax=nearestIn(points.map(q=>q.x),x,tol); if(ax!==null){x=ax;hitX='align';}}
      if(hitY===null){const ay=nearestIn(points.map(q=>q.y),y,tol); if(ay!==null){y=ay;hitY='align';}}
    }
    if ($('snapGrid').checked){
      const s=Math.max(2,+$('gridStep').value||40);
      const ox=+$('gridOx').value||0, oy=+$('gridOy').value||0;
      if(hitX===null){x=Math.round((x-ox)/s)*s+ox; hitX='grid';}
      if(hitY===null){y=Math.round((y-oy)/s)*s+oy; hitY='grid';}
    }
    return {x,y,note:(hitX||hitY)?`snapped x:${hitX||'—'} y:${hitY||'—'}`:''};
  }

  function drawCross(x,y,snapped){
    crossLay.innerHTML='';
    const mk=(x1,y1,x2,y2)=>{
      const l=document.createElementNS(NS,'line');
      l.setAttribute('x1',x1); l.setAttribute('y1',y1);
      l.setAttribute('x2',x2); l.setAttribute('y2',y2);
      l.setAttribute('stroke',snapped?C_SNAP:'#94a3b8');
      l.setAttribute('stroke-width',snapped?1:0.5);
      l.setAttribute('stroke-dasharray','4 3'); crossLay.appendChild(l);
    };
    mk(x,0,x,H); mk(0,y,W,y);
  }

  function setMode(m){
    mode=m;
    $('modeWp').classList.toggle('on',m==='waypoint');
    $('modeBin').classList.toggle('on',m==='bin');
  }
  $('modeWp').addEventListener('click',()=>setMode('waypoint'));
  $('modeBin').addEventListener('click',()=>setMode('bin'));

  document.addEventListener('keydown',(e)=>{
    if(e.key==='Shift') shiftHeld=true;
    const t=e.target.tagName;
    if(t==='TEXTAREA'||t==='INPUT') return;
    const k=e.key.toLowerCase();
    if(k==='w') setMode('waypoint');
    if(k==='b') setMode('bin');
    if(k==='z'){points.pop(); render();}
    if(k==='g'){$('gridOn').checked=!$('gridOn').checked; applyGrid();}
    if(k==='r') repeatLast();
  });
  document.addEventListener('keyup',(e)=>{ if(e.key==='Shift') shiftHeld=false; });

  function applyZoom(){
    svgEl.setAttribute('width',W*zoom); svgEl.setAttribute('height',H*zoom);
    $('zoomLbl').textContent=Math.round(zoom*100)+'%';
  }
  function fitZoom(){
    const stage=$('stage');
    const availW=stage.clientWidth-32, availH=stage.clientHeight-32;   // minus stage padding
    return Math.max(0.1,Math.min(6,Math.min(availW/W,availH/H)));
  }
  $('zoomIn').addEventListener('click',()=>{zoom=Math.min(6,zoom*1.25);applyZoom();});
  $('zoomOut').addEventListener('click',()=>{zoom=Math.max(0.1,zoom/1.25);applyZoom();});
  $('zoom100').addEventListener('click',()=>{zoom=1.0;applyZoom();});
  $('zoomFit').addEventListener('click',()=>{
    zoom=fitZoom();
    applyZoom();
  });

  // Ctrl/Cmd + scroll to zoom, anchored on the cursor — same gesture as draw.io.
  $('stage').addEventListener('wheel',(e)=>{
    if(!(e.ctrlKey||e.metaKey)) return;
    e.preventDefault();
    const stage=$('stage');
    const rect=stage.getBoundingClientRect();
    const cx=e.clientX-rect.left, cy=e.clientY-rect.top;
    const before=zoom;
    zoom=Math.max(0.1,Math.min(6,zoom*(e.deltaY<0?1.1:1/1.1)));
    applyZoom();
    const ratio=zoom/before;
    stage.scrollLeft=(stage.scrollLeft+cx)*ratio-cx;
    stage.scrollTop=(stage.scrollTop+cy)*ratio-cy;
  },{passive:false});

  function toSvgCoords(evt){
    const pt=svgEl.createSVGPoint(); pt.x=evt.clientX; pt.y=evt.clientY;
    const ctm=svgEl.getScreenCTM();
    return ctm?pt.matrixTransform(ctm.inverse()):null;
  }
  const round2=v=>Math.round(v*100)/100;

  svgEl.addEventListener('mousemove',(evt)=>{
    const raw=toSvgCoords(evt); if(!raw) return;
    const s=snap(raw);
    $('coordVal').textContent=`x: ${(s.x*NSX).toFixed(2)}, y: ${(s.y*NSY).toFixed(2)}`;
    $('snapNote').textContent=s.note;
    drawCross(s.x,s.y,!!s.note&&!shiftHeld);
  });
  svgEl.addEventListener('mouseleave',()=>{
    $('coordVal').textContent='x: —, y: —';
    $('snapNote').textContent=''; crossLay.innerHTML='';
  });

  function addPoint(x,y,type,count){
    const rec={x:round2(x),y:round2(y),type:type};
    if(type==='bin') rec.count=count||shelves;
    points.push(rec);
  }
  svgEl.addEventListener('click',(evt)=>{
    const raw=toSvgCoords(evt); if(!raw) return;
    const s=snap(raw); addPoint(s.x,s.y,mode); render();
  });

  function repeatLast(){
    if(points.length<2){$('copyMsg').textContent='Repeat needs two points first.'; return;}
    const n=Math.max(1,Math.min(200,+$('repN').value||1));
    const b=points[points.length-1], a=points[points.length-2];
    const dx=b.x-a.x, dy=b.y-a.y;
    if(!dx&&!dy){$('copyMsg').textContent='Those two points are identical.'; return;}
    for(let i=1;i<=n;i++){
      const rec={x:round2(b.x+dx*i),y:round2(b.y+dy*i),type:b.type};
      if(b.type==='bin') rec.count=b.count||shelves;
      points.push(rec);
    }
    render();
  }
  $('repBtn').addEventListener('click',repeatLast);

  function drawGhosts(){
    ghostLay.innerHTML='';
    $('ghostBox').style.display=ghosts.length?'':'none';
    $('ghostN').textContent=ghosts.length;
    const r=Math.max(3,W*0.005);
    ghosts.forEach((g,i)=>{
      const c=document.createElementNS(NS,'circle');
      c.setAttribute('cx',g.x); c.setAttribute('cy',g.y); c.setAttribute('r',r);
      c.setAttribute('fill','transparent');
      c.setAttribute('stroke',g.type==='bin'?C_BIN:C_WP);
      c.setAttribute('stroke-width',Math.max(0.8,r*0.3));
      c.setAttribute('stroke-dasharray',`${r*0.7} ${r*0.5}`);
      c.setAttribute('class','ghost');
      c.addEventListener('click',(ev)=>{
        ev.stopPropagation();               // don't also drop a point at the cursor
        addPoint(g.x,g.y,g.type,g.count); ghosts.splice(i,1); render();
      });
      ghostLay.appendChild(c);
    });
  }
  function acceptGhosts(f){
    ghosts.filter(f).forEach(g=>addPoint(g.x,g.y,g.type,g.count));
    ghosts=ghosts.filter(g=>!f(g)); render();
  }
  $('ghostWp').addEventListener('click',()=>acceptGhosts(g=>g.type!=='bin'));
  $('ghostBin').addEventListener('click',()=>acceptGhosts(g=>g.type==='bin'));
  $('ghostAll').addEventListener('click',()=>acceptGhosts(()=>true));
  $('ghostClear').addEventListener('click',()=>{ghosts=[]; render();});

  function addMarker(p,idx){
    const r=Math.max(2.5,W*0.005);
    const g=document.createElementNS(NS,'g');
    const isBin=p.type==='bin';
    const n=isBin?Math.max(1,p.count||1):1;
    if(isBin&&n>1){
      const ring=document.createElementNS(NS,'circle');
      ring.setAttribute('cx',p.x); ring.setAttribute('cy',p.y);
      ring.setAttribute('r',r*2.1); ring.setAttribute('fill','none');
      ring.setAttribute('stroke',C_BIN);
      ring.setAttribute('stroke-width',Math.max(0.8,r*0.35));
      ring.setAttribute('stroke-dasharray',`${r*0.9} ${r*0.55}`);
      g.appendChild(ring);
    }
    const c=document.createElementNS(NS,'circle');
    c.setAttribute('cx',p.x); c.setAttribute('cy',p.y); c.setAttribute('r',r);
    c.setAttribute('fill',isBin?C_BIN:C_WP);
    c.setAttribute('stroke','#04081a'); c.setAttribute('stroke-width',1);
    g.appendChild(c);
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',p.x+r*2.4); t.setAttribute('y',p.y-r*0.8);
    t.setAttribute('font-size',r*2); t.setAttribute('font-weight','700');
    t.setAttribute('fill','#111');
    t.textContent=(idx+1)+(isBin&&n>1?' ×'+n:'');
    g.appendChild(t); markerLay.appendChild(g);
  }

  function render(){
    markerLay.innerHTML=''; points.forEach(addMarker); drawGhosts();
    const body=$('pointsBody'); body.innerHTML='';
    points.forEach((p,i)=>{
      const isBin=p.type==='bin';
      const n=isBin?Math.max(1,p.count||1):1;
      let cnt='—';
      if(isBin){
        let opts='';
        for(let k=1;k<=MAXS;k++) opts+=`<option value="${k}"${k===n?' selected':''}>${k}</option>`;
        cnt=`<select class="cnt" data-i="${i}">${opts}</select>`;
      }
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${i+1}</td>`+
        `<td><span class="tag ${isBin?'bin':'wp'}">${isBin?'BIN':'WP'}</span></td>`+
        `<td class="num">${(p.x*NSX).toFixed(2)}</td><td class="num">${(p.y*NSY).toFixed(2)}</td>`+
        `<td>${cnt}</td><td>${p.label||''}</td>`+
        `<td class="del" data-i="${i}">&#10005;</td>`;
      body.appendChild(tr);
    });
    $('empty').style.display=points.length?'none':'block';

    const stacks=points.filter(p=>p.type==='bin');
    $('tFaces').textContent=points.length;
    $('tWp').textContent=points.length-stacks.length;
    $('tStacks').textContent=stacks.length;
    $('tBins').textContent=stacks.reduce((s,p)=>s+Math.max(1,p.count||1),0);

    $('jsonOut').value=JSON.stringify(points);
    const has=points.length>0;
    $('undoBtn').disabled=$('clearBtn').disabled=
      $('copyBtn').disabled=$('jsonBtn').disabled=!has;
  }

  $('pointsBody').addEventListener('click',(e)=>{
    if(e.target.classList.contains('del')){
      points.splice(parseInt(e.target.dataset.i,10),1); render();
    }
  });
  $('pointsBody').addEventListener('change',(e)=>{
    if(e.target.classList.contains('cnt')){
      points[parseInt(e.target.dataset.i,10)].count=parseInt(e.target.value,10); render();
    }
  });
  $('undoBtn').addEventListener('click',()=>{points.pop(); render();});
  $('clearBtn').addEventListener('click',()=>{points=[]; render();});

  $('copyBtn').addEventListener('click',async()=>{
    const txt=JSON.stringify(points);
    try{
      await navigator.clipboard.writeText(txt);
      $('copyMsg').textContent='Copied '+points.length+' faces — paste below.';
    }catch(err){
      $('jsonOut').select(); document.execCommand('copy');
      $('copyMsg').textContent='Copied via fallback — paste below.';
    }
  });
  $('jsonBtn').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify(points,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url; a.download='picked_points.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  zoom = fitZoom() * zoom;   // land fitted to the stage, like draw.io on open; __ZOOM__ acts as a multiplier on that
  applyZoom(); applyGrid(); drawGuides(); render();
})();
</script>
</body>
</html>
"""


def render_picker(image, seed_points, ghosts=None, guides=None, height=700,
                  zoom=1.0, default_count=4, grid_step=40,
                  native_scale=(1.0, 1.0)):
    w, h = image.size
    html = themed(PICKER_TEMPLATE)
    for token, value in [("__IMG__", png_b64(image)), ("__W__", str(w)),
                         ("__H__", str(h)), ("__HEIGHT__", str(height - 20)),
                         ("__ZOOM__", str(zoom)), ("__MAXS__", str(MAX_SHELVES)),
                         ("__DEFCOUNT__", str(default_count)),
                         ("__GRIDSTEP__", str(int(grid_step))),
                         ("__NSX__", str(native_scale[0])),
                         ("__NSY__", str(native_scale[1])),
                         ("__GHOSTS__", json.dumps(ghosts or [])),
                         ("__GUIDES__", json.dumps(guides or {"x": [], "y": []})),
                         ("__SEED__", json.dumps(seed_points))]:
        html = html.replace(token, value)
    components.html(html, height=height, scrolling=False)


def parse_points(text):
    """Picker JSON, or CSV with x,y[,type][,count][,label]."""
    text = (text or "").strip()
    if not text:
        return []

    def norm(x, y, typ, count, label):
        is_bin = str(typ or "waypoint").strip().lower().startswith("bin")
        try:
            c = int(float(count)) if str(count).strip() not in ("", "None") else 1
        except (TypeError, ValueError):
            c = 1
        return {"x": float(x), "y": float(y),
                "type": "bin" if is_bin else "waypoint",
                "count": max(1, min(MAX_SHELVES, c)) if is_bin else 1,
                "label": str(label or "").strip()}

    if text[0] in "[{":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("points", [])
        return [norm(d["x"], d["y"], d.get("type"), d.get("count", 1),
                     d.get("label", "")) for d in data]

    rows = [r for r in csv.reader(io.StringIO(text)) if r and any(c.strip() for c in r)]
    if not rows:
        return []
    header = [c.strip().lower() for c in rows[0]]
    if "x" in header and "y" in header:
        idx = {k: (header.index(k) if k in header else None)
               for k in ("x", "y", "type", "count", "label")}
        rows = rows[1:]
    else:
        idx = {"x": 0, "y": 1, "type": 2, "count": 3, "label": 4}

    out = []
    for r in rows:
        def cell(key, default=""):
            i = idx.get(key)
            return r[i] if i is not None and len(r) > i else default
        try:
            out.append(norm(r[idx["x"]], r[idx["y"]], cell("type", "waypoint"),
                            cell("count", 1), cell("label")))
        except (ValueError, IndexError, TypeError):
            continue
    return out


def split_points(pts):
    red = [(p["x"], p["y"]) for p in pts if p["type"] != "bin"]
    return red, [p for p in pts if p["type"] == "bin"]


# ----------------------------------------------------------------------
# 10. STREAMLIT UI
# ----------------------------------------------------------------------

page_header()

uploaded = st.file_uploader("Upload warehouse floor plan", type=["svg"])
if uploaded is None:
    st.info("Upload the warehouse floor plan (SVG) to get started.")
    st.stop()

try:
    image, native_size = load_plan_image(uploaded)
except Exception as e:
    st.error(f"Couldn't read that SVG: {e}")
    st.stop()
arr = np.array(image)
native_scale = ((native_size[0] / image.size[0], native_size[1] / image.size[1])
                if native_size else (1.0, 1.0))
caption = f"Plan loaded at {image.size[0]} × {image.size[1]} px — picker and graph " \
          "coordinates share this grid."
if native_size and (round(native_scale[0], 4), round(native_scale[1], 4)) != (1.0, 1.0):
    caption += (f" Original file is {native_size[0]:.0f} × {native_size[1]:.0f} px; "
                "exported CSVs include native_x/native_y scaled back to that size.")
st.caption(caption)

mode = st.radio("Where do the graph nodes come from?",
                ["Manual pick (coordinate picker)",
                 "Auto-detect coloured dots",
                 "Auto-detect, then edit in the picker"])

auto_red, auto_yellow = [], []
if mode != "Manual pick (coordinate picker)":
    with st.spinner("Detecting coloured dots..."):
        auto_red = detect_blobs(arr, "red")
        auto_yellow = detect_blobs(arr, "yellow")
    st.write(f"Auto-detected **{len(auto_red)}** red waypoints and "
             f"**{len(auto_yellow)}** yellow rack faces.")

st.subheader("Bin naming & stacking")
n1, n1b = st.columns(2)
with n1:
    start_token = st.text_input("Bin start at", value="A00",
                                help="Type the exact first bin name, e.g. A00 or "
                                     "bin0001. The trailing digits auto-increment "
                                     "(their width sets the zero-padding); any "
                                     "leading text becomes the prefix.")
    prefix, start_num, pad = parse_start_token(start_token)
with n1b:
    wp_start_token = st.text_input("Waypoint start at", value="W0",
                                   help="Same idea as bin start, but for waypoints "
                                        "— e.g. W0 gives W0, W1, W2 …")
    wp_prefix, wp_start, wp_pad = parse_start_token(wp_start_token)

scheme, default_count, label_as_name, stack_cost = "padded", 1, False, 0.0

st.caption(f"Detected prefix '{prefix}', {pad}-digit counter starting at {start_num}. "
           f"Preview: {make_bin_name(scheme, start_num, prefix, pad, 1, 1)} · "
           f"{make_bin_name(scheme, start_num + 1, prefix, pad, 1, 2)} · "
           f"{make_bin_name(scheme, start_num + 2, prefix, pad, 1, 3)} …")

points, ghosts, guides = [], [], {"x": [], "y": []}

if mode == "Auto-detect coloured dots":
    if not auto_red:
        st.error("No red corridor-waypoint dots detected. Switch to manual picking.")
        st.stop()
    points = ([{"x": x, "y": y, "type": "waypoint", "count": 1, "label": ""}
               for x, y in auto_red] +
              [{"x": x, "y": y, "type": "bin", "count": int(default_count), "label": ""}
               for x, y in auto_yellow])
else:
    st.subheader("① Suggested layout (optional)")
    st.caption("The plan is scanned for long straight lines. Lines close "
               "together form a rack band; wide gaps between them are aisles. "
               "Waypoints go on aisle centrelines, bin faces on the rack faces "
               "that front them.")
    if st.checkbox("Analyse the plan and propose points", value=False):
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            min_aisle = st.number_input("Min aisle width (px)", 5, 500, 28, 1)
        with q2:
            pitch = st.number_input("Rack-face pitch (px)", 5, 500, 45, 1)
        with q3:
            line_frac = st.slider("Line length threshold", 0.02, 0.9, 0.18, 0.01,
                                  help="A row counts as a line when its longest "
                                       "unbroken ink run covers this fraction of "
                                       "the plan width. Lower it if racks are "
                                       "drawn as short segments.")
        with q4:
            access = st.number_input("Max face→aisle distance (px)", 5, 500, 45, 1)

        with st.spinner("Analysing plan structure..."):
            sw, sf, guides, stats = suggest_layout(
                arr, min_aisle=min_aisle, pitch=pitch, min_frac=line_frac,
                access=access)

        st.write(f"Lines found: **{stats['h_lines']}** horizontal, "
                 f"**{stats['v_lines']}** vertical → "
                 f"**{stats['h_aisles'] + stats['v_aisles']}** aisles, "
                 f"**{stats['h_racks'] + stats['v_racks']}** rack bands → "
                 f"**{len(sw)}** waypoints and **{len(sf)}** faces proposed "
                 f"(≈ {len(sf) * int(default_count)} bins).")
        if not sw and not sf:
            st.warning("Nothing proposed. Lower the line-length threshold or the "
                       "min aisle width — this plan's racks may be drawn as short "
                       "or dashed segments.")
        st.image(draw_suggestions(image, sw, sf, guides),
                 caption="Cyan rings = proposed waypoints, pink rings = proposed "
                         "rack faces, pale lines = detected geometry.",
                 use_container_width=True)

        if st.checkbox("Load these into the picker as ghosts", value=True):
            ghosts = ([{"x": round(x, 2), "y": round(y, 2), "type": "waypoint"}
                       for x, y in sw] +
                      [{"x": round(x, 2), "y": round(y, 2), "type": "bin",
                        "count": int(default_count)} for x, y in sf])

    seed = []
    if mode == "Auto-detect, then edit in the picker":
        seed = ([{"x": round(x, 2), "y": round(y, 2), "type": "waypoint"}
                 for x, y in auto_red] +
                [{"x": round(x, 2), "y": round(y, 2), "type": "bin",
                  "count": int(default_count)} for x, y in auto_yellow])

    st.subheader("② Pick the rack faces")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        pheight = st.slider("Picker height (px)", 400, 1200, 720, 20)
    with pc2:
        pzoom = st.slider("Initial zoom (× fit-to-screen)", 0.2, 3.0, 1.0, 0.1)
    with pc3:
        grid_step = st.number_input("Grid spacing (px)", 2, 500, 40, 1)

    render_picker(image, seed, ghosts=ghosts, guides=guides, height=pheight,
                  zoom=pzoom, default_count=int(default_count),
                  grid_step=int(grid_step), native_scale=native_scale)

    st.subheader("③ Hand the points back to Python")
    hc1, hc2 = st.columns([2, 1])
    with hc1:
        pasted = st.text_area(
            "Points JSON (paste from the picker's “Copy points” button)",
            height=110,
            placeholder='[{"x":420,"y":260,"type":"bin","count":4,"label":"R1-A"}, ...]',
            key="pasted_points")
    with hc2:
        pfile = st.file_uploader("…or upload picked_points.json / .csv",
                                 type=["json", "csv"], key="pts_file")

    raw = pfile.getvalue().decode("utf-8") if pfile is not None else (pasted or "")
    if not raw.strip():
        st.info("Pick your faces above, press **Copy points**, then paste them here.")
        st.stop()
    try:
        points = parse_points(raw)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Couldn't parse those points: {exc}")
        st.stop()

# --- build the graph ---------------------------------------------------
red, bin_faces = split_points(points)
if not red:
    st.error("No waypoint points supplied — the graph needs at least one "
             "corridor waypoint to route through.")
    st.stop()

bins = expand_bin_stacks(bin_faces, scheme=scheme, start=start_num,
                         default_count=int(default_count), prefix=prefix,
                         pad=pad, label_as_name=label_as_name)
dupes = dedupe_bin_ids(bins)
if dupes:
    st.warning(f"{dupes} duplicate bin name(s) — suffixed with #2, #3 … to keep "
               "every bin addressable.")

sig = json.dumps([sorted(red), bins, stack_cost, uploaded.name,
                  wp_prefix, wp_start, wp_pad], sort_keys=True, default=str)
if st.session_state.get("_sig") != sig:
    with st.spinner("Building graph..."):
        nodes, edges = build_nodes_edges(red, bins, stack_cost=stack_cost,
                                         wp_prefix=wp_prefix, wp_start=wp_start,
                                         wp_pad=wp_pad)
    st.session_state.update({"nodes": nodes, "edges": edges, "_sig": sig})

nodes, edges = st.session_state["nodes"], st.session_state["edges"]
n_bins = sum(1 for n in nodes if n["type"] == "bin")
n_wp = sum(1 for n in nodes if n["type"] == "waypoint")

st.subheader("④ Graph")
first, last = (bins[0]["bin_number"], bins[-1]["bin_number"]) if bins else ("—", "—")
st.markdown(themed(f"""
  <div class="wpf-chips" style="margin:0 0 10px;">
    <div class="wpf-chip"><span class="wpf-dot" style="background:{THEME['ACCENT']}"></span>
      Waypoints <b>{n_wp}</b></div>
    <div class="wpf-chip"><span class="wpf-dot" style="background:{THEME['ACCENT2']}"></span>
      Rack faces <b>{len(bin_faces)}</b></div>
    <div class="wpf-chip"><span class="wpf-dot" style="background:{THEME['ACCENT2']}"></span>
      Bins <b>{n_bins}</b> · {first} → {last}</div>
    <div class="wpf-chip"><span class="wpf-dot" style="background:{THEME['OK']}"></span>
      Edges <b>{len(edges)}</b></div>
  </div>"""), unsafe_allow_html=True)

wp_map = waypoint_bin_map(nodes, edges)
orphans = [r for r in wp_map if r["bins"] == 0]

nodes_native = [dict(n, native_x=round(n["x"] * native_scale[0], 2),
                     native_y=round(n["y"] * native_scale[1], 2)) for n in nodes]
wp_map_native = [dict(r, native_x=round(r["x"] * native_scale[0], 2),
                      native_y=round(r["y"] * native_scale[1], 2)) for r in wp_map]

g1, g2, g3, g4 = st.columns(4)
with g1:
    st.download_button("⬇ nodes.csv",
                       to_csv_bytes(nodes_native, ["id", "name", "x", "y", "native_x",
                                            "native_y", "type", "bin_number",
                                            "alias", "rack", "stack", "level"]),
                       "warehouse_nodes.csv", "text/csv")
with g2:
    st.download_button("⬇ edges.csv",
                       to_csv_bytes(edges, ["node_a", "node_b", "distance", "kind"]),
                       "warehouse_edges.csv", "text/csv")
with g3:
    st.download_button("⬇ waypoint_bins.csv",
                       to_csv_bytes(wp_map_native, ["waypoint_id", "name", "x", "y",
                                             "native_x", "native_y", "rack_faces",
                                             "bins", "access_distance", "bin_ids"]),
                       "waypoint_bin_map.csv", "text/csv")
with g4:
    st.download_button("⬇ skeleton.svg",
                       skeleton_to_svg(image, nodes, edges).encode("utf-8"),
                       "warehouse_skeleton.svg", "image/svg+xml")

t1, t2 = st.tabs([f"Bins ({n_bins})", f"Waypoint → bins ({n_wp})"])
with t1:
    st.dataframe([{"bin_node": b["bin_number"], "x": b["x"], "y": b["y"]}
                  for b in bins],
                 use_container_width=True, hide_index=True)
with t2:
    if orphans:
        st.caption(f"{len(orphans)} waypoint(s) serve no bins — pure corridor "
                   "nodes, or faces you haven't placed yet.")
    st.dataframe([{"waypoint_name": r["name"], "x": r["x"], "y": r["y"]}
                  for r in wp_map],
                 use_container_width=True, hide_index=True)

st.image(draw_skeleton_on_image(image, nodes, edges),
         caption="Graph skeleton — cyan = waypoints, pink = bins. Stacked bins "
                 "are fanned a few pixels apart for visibility only; their real "
                 "coordinates are identical.",
         use_container_width=True)

st.divider()

if n_bins == 0:
    st.info("No bins yet — add bin faces in the picker (press B) or download "
            "nodes.csv/edges.csv above.")
    st.stop()

st.subheader("⑤ Route between two bins")
bin_nodes = [n for n in nodes if n["type"] == "bin"]
bin_numbers = [n["bin_number"] for n in bin_nodes]
alias_of = {n["bin_number"]: n["alias"] for n in bin_nodes}


def bin_label(b):
    return f"{b} · {alias_of[b]}" if alias_of.get(b) else str(b)


c1, c2, c3 = st.columns(3)
with c1:
    bin_a = st.selectbox("From bin", bin_numbers, index=0, format_func=bin_label)
with c2:
    bin_b = st.selectbox("To bin", bin_numbers, index=min(1, len(bin_numbers) - 1),
                         format_func=bin_label)
with c3:
    speed = st.number_input("Speed (units/sec)", min_value=0.01, value=1.0, step=0.1)

if st.button("Find shortest path", type="primary"):
    tree = WarehouseTree(nodes, edges, speed=speed)
    result = tree.path_between_bins(bin_a, bin_b)
    if result is None:
        st.error("No path found between those bins.")
    else:
        annotated = draw_path_on_image(image, result["steps"])
        st.image(annotated, caption=f"{bin_a} → {bin_b}", use_container_width=True)
        floor_hops = len(_dedupe_consecutive(
            [(s["x"], s["y"]) for s in result["steps"]]))
        m1, m2, m3 = st.columns(3)
        m1.metric("Distance", f"{result['distance']} units")
        m2.metric("Est. time", f"{result['time_sec']} sec")
        m3.metric("Floor stops", floor_hops)
        if floor_hops == 1:
            st.info("Same rack face — no floor travel, just a different shelf level.")
        buf = io.BytesIO()
        annotated.save(buf, format="PNG")
        st.download_button("⬇ Download annotated image", buf.getvalue(),
                           f"path_{bin_a}_to_{bin_b}.png", "image/png")
