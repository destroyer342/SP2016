#!/usr/bin/env python3
"""Consolidate the per-view screen files into the 3-screen app.

Before: 10 screens (one per InfoPath view). After: 3 screens.
  01-scrDashboard.pa.yaml     register (unchanged body, navigation rewritten)
  02-scrPEF.pa.yaml           ONE form screen: shared header + tab bar; every former form
                              screen body (fgd<Tag>Body) becomes a tab container shown
                              when gblTab = "<Key>"
  03-scrConfirmation.pa.yaml  confirmation (unchanged body, navigation rewritten)

Navigation rewrite:
  inside scrPEF:          Navigate(scrHoursCosts, ...)  ->  Set(gblTab, "Hours")
  on the other screens:   Navigate(scrHoursCosts, T)    ->  Set(gblTab, "Hours"); Navigate(scrPEF, T)
  Back() on Detailed info ->  Set(gblTab, "Cover")

Usage:
    python tools/merge_screens.py --out DIR    # write the 3 files to DIR (dry run)
    python tools/merge_screens.py --apply      # write into screens/ and delete the old files
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required:  python -m pip install pyyaml")

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
SCREENS_DIR = os.path.join(APP, "screens")
sys.path.insert(0, HERE)
import gen_chrome as g  # noqa: E402  (tokens, snippets, emit helpers)

yaml.SafeLoader.add_constructor(
    "tag:yaml.org,2002:value", lambda loader, node: loader.construct_scalar(node)
)

# former screen -> (tab key, caption, tag, source file, kind)
TABS = [
    ("scrCoverPage", "Cover", "Cover Page", "Cvr", "02-scrCoverPage.pa.yaml", "form"),
    ("scrHoursCosts", "Hours", "Hours & Costs", "Hrs", "03-scrHoursCosts.pa.yaml", "form"),
    ("scrMotivations", "Motivations", "Motivations", "Mot", "04-scrMotivations.pa.yaml", "form"),
    ("scrRevisions", "Revisions", "Revisions", "Rev", "05-scrRevisions.pa.yaml", "form"),
    ("scrApprovals", "Approvals", "Approvals", "Apr", "06-scrApprovals.pa.yaml", "form"),
    ("scrReview", "Review", "Review & Submit", "Rvw", "07-scrReview.pa.yaml", "form"),
    ("scrClosure", "Closure", "Closure", "Cls", "08-scrClosure.pa.yaml", "form"),
    ("scrDetailedInfo", "Details", "Detailed info", "Dbg", "10-scrDetailedInfo.pa.yaml", "plain"),
]
SCREEN_TO_TAB = {t[0]: t[1] for t in TABS}
# tab bar geometry: (key, X, Width, Visible)
TAB_GEOMETRY = [
    ("Cover", 16, 108, None), ("Hours", 128, 116, None), ("Motivations", 248, 108, None),
    ("Revisions", 360, 96, None), ("Approvals", 460, 100, None), ("Review", 564, 128, None),
    ("Closure", 696, 88, "=gblPEF.Close"), ("Details", 788, 104, '=gblRole = "Administrator"'),
]
OTHERS = [  # (screen, tag, source file, output file)
    ("scrDashboard", "Dsh", "01-scrDashboard.pa.yaml", "01-scrDashboard.pa.yaml"),
    ("scrConfirmation", "Cnf", "09-scrConfirmation.pa.yaml", "03-scrConfirmation.pa.yaml"),
]
PEF_FILE = "02-scrPEF.pa.yaml"
PEF_TAG = "Pef"
NAV_RE = re.compile(r"Navigate\(\s*(scr[A-Za-z]+)\s*(?:,\s*(ScreenTransition\.\w+)\s*)?\)")


# ---------- generic emitter for parsed controls ----------
def emit_node(lines, indent, name, node):
    pad = " " * indent
    lines.append(f"{pad}- {name}:")
    lines.append(f"{pad}    Control: {node['Control']}")
    if node.get("Variant"):
        lines.append(f"{pad}    Variant: {node['Variant']}")
    props = node.get("Properties") or {}
    lines.append(f"{pad}    Properties:")
    for k, v in sorted(props.items()):
        head, body = g.fmt(v)
        lines.append(f"{pad}      {k}: {head}")
        for b in body or []:
            lines.append(f"{pad}        {b}")
    kids = node.get("Children")
    if kids:
        lines.append(f"{pad}    Children:")
        for child in kids:
            cname = next(iter(child))
            emit_node(lines, indent + 6, cname, child[cname])


def raw(name, node):
    return lambda lines, indent: emit_node(lines, indent, name, node)


def walk_props(node, fn):
    """Apply fn(prop_name, value) -> value to every property of node and its descendants."""
    props = node.get("Properties") or {}
    for k in list(props):
        props[k] = fn(k, str(props[k]))
    for child in node.get("Children") or []:
        cname = next(iter(child))
        walk_props(child[cname], fn)


def rewrite_nav(value, on_pef):
    def repl(m):
        target, trans = m.group(1), m.group(2)
        if target in SCREEN_TO_TAB:
            key = SCREEN_TO_TAB[target]
            if on_pef:
                return f'Set(gblTab, "{key}")'
            return f'Set(gblTab, "{key}"); Navigate(scrPEF{", " + trans if trans else ""})'
        return m.group(0)
    return NAV_RE.sub(repl, value)


# ---------- chrome for the single form screen ----------
def tab_bar_dynamic(t):
    kids = []
    captions = {key: cap for _, key, cap, _, _, _ in TABS}
    for key, x, w, visible in TAB_GEOMETRY:
        extra = {"Color": f'=If(gblTab = "{key}", RGBA(0, 94, 162, 1), RGBA(96, 94, 92, 1))',
                 "FontWeight": f'=If(gblTab = "{key}", FontWeight.Semibold, FontWeight.Normal)',
                 "Tooltip": f'="{captions[key]}"'}
        if visible:
            extra["Visible"] = visible
        kids.append(g.button(f"btn{t}Tab{key}", f'="{captions[key]}"', f"={x}", "=8", f"={w}", "=32", "tab",
                             onselect=f'=Set(gblTab, "{key}")', extra=extra))
    sx = ", ".join(f'"{k}", {x + 8}' for k, x, w, _ in TAB_GEOMETRY)
    sw = ", ".join(f'"{k}", {w - 16}' for k, x, w, _ in TAB_GEOMETRY)
    kids.append(g.ctl(f"rec{t}TabIndicator", "Rectangle@2.3.0", {
        "Fill": g.PRIMARY, "X": f"=Switch(gblTab, {sx}, 24)", "Y": "=44",
        "Width": f"=Switch(gblTab, {sw}, 92)", "Height": "=3"}))
    kids.append(g.ctl(f"rec{t}TabBarLine", "Rectangle@2.3.0", {
        "Fill": g.HAIRLINE, "X": "=0", "Y": "=47", "Width": "=Parent.Width", "Height": "=1"}))
    kids.append(g.button(f"btn{t}CancelApproval", '="Cancel Approval"', "=Parent.Width - 452", "=8", "=140", "=32",
                         "danger", onselect="=" + g.S_CANCEL_APPROVAL,
                         extra={"Visible": '=gblPEF.Status = "Pending Approval" && gblRole = "Applicant (CI)"',
                                "Tooltip": '="Withdraw the PEF from the approval workflow"'}))
    kids.append(g.button(f"btn{t}Save", '="Save PEF"', "=Parent.Width - 304", "=8", "=120", "=32",
                         "secondary", onselect="=" + g.S_SAVE,
                         extra={"Visible": '=gblRole in ["Applicant (CI)", "Administrator"]',
                                "Tooltip": '="Save the PEF without starting approval"'}))
    kids.append(g.button(f"btn{t}StartApproval", '="Start Approval"', "=Parent.Width - 176", "=8", "=160", "=32",
                         "primary", onselect='=Set(gblTab, "Review")',
                         extra={"Visible": '=gblPEF.Status in ["Draft", "Rejected"] && gblRole = "Applicant (CI)"',
                                "Tooltip": '="Review the PEF and submit it for approval"'}))
    return g.ctl(f"con{t}TabBar", "GroupContainer@1.5.0", {
        "BorderStyle": "=BorderStyle.None", "Fill": g.SURFACE,
        "X": "=0", "Y": "=112", "Width": "=Parent.Width", "Height": "=48",
    }, variant="ManualLayout", children=kids)


def app_bar_3(t, on_pef):
    """The generated App bar, with the settings icon opening the Details tab."""
    bar = yaml.safe_load(chrome_text([g.app_bar(t)]))[0]
    node = bar[f"con{t}AppBar"]
    walk_props(node, lambda k, v: (f'=Set(gblTab, "Details")' + ("" if on_pef else "; Navigate(scrPEF, ScreenTransition.Fade)"))
               if k == "OnSelect" and "scrDetailedInfo" in v else v)
    return raw(f"con{t}AppBar", node)


def chrome_text(items):
    lines = []
    for c in items:
        c(lines, 0)
    return "\n".join(lines) + "\n"


def pef_chrome():
    return [app_bar_3(PEF_TAG, True), g.project_bar(PEF_TAG), tab_bar_dynamic(PEF_TAG)]


def plain_chrome(tag):
    return [app_bar_3(tag, False)]


CHROME_NAMES = {"pef": [f"con{PEF_TAG}AppBar", f"con{PEF_TAG}ProjectBar", f"con{PEF_TAG}TabBar"]}


# ---------- load + transform ----------
def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def chrome_child_names(tag, kind):
    return set(g.chrome_names(tag, "form" if kind == "form" else "plain"))


def split_on_visible(text):
    """Strip the generated S_RECALC / S_EDITMODE prefix; return the screen-specific extras."""
    text = (text or "").strip()
    if text.startswith("="):
        text = text[1:]
    for snip in (g.S_RECALC, g.S_EDITMODE):
        text = text.replace(snip + ";", "").replace(snip, "")
    return text.strip().strip(";").strip()


def shift_y(value, dy):
    v = str(value).strip()
    body = v[1:].strip() if v.startswith("=") else v
    try:
        n = float(body)
        return "=" + (str(int(n + dy)) if (n + dy).is_integer() else str(n + dy))
    except ValueError:
        return f"=({body}) {'+' if dy >= 0 else '-'} {abs(dy)}"


def tab_body(screen, key, tag, fname, kind):
    """Return (fluidgrid_name, node, on_visible_extra) for one former screen."""
    doc = load(os.path.join(SCREENS_DIR, fname))
    body = doc["Screens"][screen]
    extra = split_on_visible((body.get("Properties") or {}).get("OnVisible", ""))
    kids = [k for k in body.get("Children") or [] if next(iter(k)) not in chrome_child_names(tag, kind)]
    fgd_name = f"fgd{tag}Body"
    if len(kids) == 1 and next(iter(kids[0])) == fgd_name:
        fgd = kids[0][fgd_name]
    else:
        # plain screen body placed at screen level from Y 48: wrap it in a FluidGrid/DataCard
        bottom = 0
        for k in kids:
            n = k[next(iter(k))]
            p = n.get("Properties") or {}
            p["Y"] = shift_y(p.get("Y", "=0"), -48)
            try:
                bottom = max(bottom, float(str(p["Y"]).lstrip("=")) + float(str(p.get("Height", "=0")).lstrip("=")))
            except ValueError:
                pass
        fgd = {"Control": "FluidGrid@2.3.0", "Properties": {}, "Children": [
            {f"dcd{tag}Body": {"Control": "DataCard@1.0.2",
                               "Properties": {"X": "=0", "Y": "=0", "Width": "=Parent.Width",
                                              "Height": f"={int(max(bottom + 24, 800))}"},
                               "Children": kids}}]}
    props = fgd.setdefault("Properties", {})
    props.update({"X": "=0", "Y": "=160", "Width": "=Parent.Width", "Height": "=Parent.Height - 160",
                  "Visible": f'=gblTab = "{key}"'})
    walk_props(fgd, lambda k, v: rewrite_nav(v, True))
    if kind == "plain":
        walk_props(fgd, lambda k, v: v.replace("Back()", 'Set(gblTab, "Cover")'))
    return fgd_name, fgd, rewrite_nav(extra, True)


def screen_text(screen, props, children, comment):
    lines = [f"# {comment}", "Screens:", f"  {screen}:", "    Properties:"]
    for k, v in sorted(props.items()):
        head, block = g.fmt(v)
        lines.append(f"      {k}: {head}")
        for b in block or []:
            lines.append(f"        {b}")
    lines.append("    Children:")
    for c in children:
        c(lines, 6)
    return "\n".join(lines) + "\n"


def build_pef():
    bodies, extras = [], []
    for screen, key, caption, tag, fname, kind in TABS:
        name, node, extra = tab_body(screen, key, tag, fname, kind)
        bodies.append(raw(name, node))
        if extra and extra not in extras:
            extras.append(extra)
    on_visible = "=" + ";\n".join([g.S_RECALC, g.S_EDITMODE] + extras)
    return screen_text("scrPEF", {"Fill": g.PAGE, "OnVisible": on_visible}, bodies + pef_chrome(),
                       "scrPEF - the PEF form: one tab container per InfoPath view (gblTab). See DESIGN.md. "
                       "Chrome (last children) is generated by tools/merge_screens.py.")


def build_other(screen, tag, fname):
    doc = load(os.path.join(SCREENS_DIR, fname))
    body = doc["Screens"][screen]
    props = dict(body.get("Properties") or {})
    for k in list(props):
        props[k] = rewrite_nav(str(props[k]), False)
    kids = [k for k in body.get("Children") or [] if next(iter(k)) not in chrome_child_names(tag, "plain")]
    out = []
    for k in kids:
        name = next(iter(k))
        walk_props(k[name], lambda p, v: rewrite_nav(v, False))
        out.append(raw(name, k[name]))
    return screen_text(screen, props, out + plain_chrome(tag),
                       f"{screen} - see DESIGN.md. Chrome (last children) is generated by tools/merge_screens.py.")


def main():
    if "--apply" in sys.argv:
        out_dir, apply = SCREENS_DIR, True
    elif "--out" in sys.argv:
        out_dir, apply = sys.argv[sys.argv.index("--out") + 1], False
    else:
        sys.exit(__doc__)
    os.makedirs(out_dir, exist_ok=True)
    files = {PEF_FILE: build_pef()}
    for screen, tag, src, dst in OTHERS:
        files[dst] = build_other(screen, tag, src)
    for name, text in files.items():
        yaml.safe_load(text)  # must parse
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"written  {os.path.join(out_dir, name)}")
    if apply:
        keep = set(files)
        for f in sorted(os.listdir(SCREENS_DIR)):
            if f.endswith(".pa.yaml") and f not in keep:
                os.remove(os.path.join(SCREENS_DIR, f))
                print(f"removed  {f}")


if __name__ == "__main__":
    main()
