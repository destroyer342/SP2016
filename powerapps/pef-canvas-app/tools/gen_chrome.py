#!/usr/bin/env python3
"""Generate (or check) the shared chrome of the PEF canvas-app screens.

The app has 3 screens (DESIGN.md section 5.1):
  scrDashboard     App bar only
  scrPEF           App bar + Project bar + Tab bar; the tab bar switches gblTab, and
                   each InfoPath view is a tab container (fgd<Tag>Body, Visible when
                   gblTab = "<Key>")
  scrConfirmation  App bar only
Control names carry a tag, so they stay unique.

Usage:
    python tools/gen_chrome.py --check      # verify each screen's chrome matches (default)
    python tools/gen_chrome.py --write      # regenerate the chrome in place (after editing this file)
    python tools/gen_chrome.py --print Pef  # print one screen's chrome YAML

Requires: pyyaml
"""
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required:  python -m pip install pyyaml")

yaml.SafeLoader.add_constructor(
    "tag:yaml.org,2002:value", lambda loader, node: loader.construct_scalar(node)
)

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
SCREENS_DIR = os.path.join(APP, "screens")

# (file, screen name, tag, kind)  kind: "pef" = App bar + Project bar + Tab bar, "plain" = App bar only
SCREENS = [
    ("01-scrDashboard.pa.yaml", "scrDashboard", "Dsh", "plain"),
    ("02-scrPEF.pa.yaml", "scrPEF", "Pef", "pef"),
    ("03-scrConfirmation.pa.yaml", "scrConfirmation", "Cnf", "plain"),
]

# Tabs of scrPEF: (key, caption, X, Width, body tag, Visible formula or None).
# The body of tab <key> is the container fgd<tag>Body (Visible when gblTab = "<key>").
TABS = [
    ("Cover", "Cover Page", 16, 108, "Cvr", None),
    ("Hours", "Hours & Costs", 128, 116, "Hrs", None),
    ("Motivations", "Motivations", 248, 108, "Mot", None),
    ("Revisions", "Revisions", 360, 96, "Rev", None),
    ("Approvals", "Approvals", 460, 100, "Apr", None),
    ("Review", "Review & Submit", 564, 128, "Rvw", None),
    ("Closure", "Closure", 696, 88, "Cls", "=gblPEF.Close"),
    ("Details", "Detailed info", 788, 104, "Dbg", '=gblRole = "Administrator"'),
]

# ---- tokens (DESIGN.md section 4) ----
PAGE = "=RGBA(243, 245, 248, 1)"
SURFACE = "=RGBA(255, 255, 255, 1)"
APPBAR = "=RGBA(16, 42, 67, 1)"
PRIMARY = "=RGBA(0, 94, 162, 1)"
PRIMARY_HOVER = "=RGBA(0, 76, 132, 1)"
PRIMARY_TINT = "=RGBA(229, 241, 250, 1)"
BRAND = "=RGBA(200, 16, 46, 1)"
BRAND_HOVER = "=RGBA(168, 12, 38, 1)"
HEADING = "=RGBA(16, 42, 67, 1)"
TEXT = "=RGBA(32, 31, 30, 1)"
MUTED = "=RGBA(96, 94, 92, 1)"
ON_DARK = "=RGBA(255, 255, 255, 1)"
ON_DARK_MUTED = "=RGBA(190, 204, 219, 1)"
BORDER = "=RGBA(200, 205, 214, 1)"
HAIRLINE = "=RGBA(229, 231, 235, 1)"
ERROR = "=RGBA(196, 30, 58, 1)"
ERROR_TINT = "=RGBA(253, 231, 233, 1)"
CLEAR = "=RGBA(0, 0, 0, 0)"
FONT = "=Font.'Segoe UI'"

# ---- canonical snippets (DESIGN.md section 7) ----
S_RECALC = ('Set(gblTotals, With({lab: Sum(colStaff, Cost), opx: Sum(colRunningCosts, Amount), svc: If(gblPEF.ServiceSBURequired, Sum(colServiceSBUs, Cost), 0), com: gblPEF.RevenueStream in ["Cash", "Products and Services"]}, '
            'With({base: lab + opx + gblPEF.CarryOverLabour}, With({cont: If(gblPEF.ContingencyByPercent, base * gblPEF.ContingencyPct, gblPEF.ContingencyAmount), warr: If(gblPEF.WarrantyByPercent, base * gblPEF.WarrantyPct, gblPEF.WarrantyAmount)}, '
            'With({ctrl: base + cont + warr, svcRev: svc * (1 + gblPEF.ServiceProfit)}, With({cost: ctrl + svc}, With({price: If(com, gblPEF.ClientPriceInput, cost * 1.1)}, '
            '{Labour: lab, OPEX: opx, CarryOver: gblPEF.CarryOverLabour, PlannedCosts: base, Contingency: cont, ContingencyPctEff: If(base > 0, cont / base, 0), Warranty: warr, WarrantyPctEff: If(base > 0, warr / base, 0), ControllingCosts: ctrl, ServiceCosts: svc, ServiceRevenue: svcRev, ProjectCost: cost, ClientPrice: price, Profit: price - cost, ProfitPct: If(cost > 0, price / cost - 1, 0), ControllingRevenue: price - svcRev, ControllingProfitPct: If(ctrl > 0, (price - svcRev) / ctrl - 1, 0), ServiceProfitPct: gblPEF.ServiceProfit, IsCommercial: com})))))))')
S_EDITMODE = 'Set(gblEditMode, If(gblRole = "Applicant (CI)" && gblPEF.Status in ["Draft", "Rejected"], DisplayMode.Edit, DisplayMode.View))'
S_UPSERT = ('With({r: {ProjectNo: gblPEF.ProjectNo, ProjectTitle: gblPEF.ProjectTitle, Division: gblPEF.Division, DivisionalGroup: gblPEF.DivisionalGroup, RevenueStream: gblPEF.RevenueStream, ResponsiblePerson: gblPEF.ResponsiblePerson, ProjectCost: gblTotals.ProjectCost, ClientPrice: gblTotals.ClientPrice, Status: gblPEF.Status, WorkflowState: gblPEF.WorkflowState, StartDate: gblPEF.StartDate, EndDate: gblPEF.EndDate, RevisionNo: gblPEF.RevisionNo, Modified: Now()}}, '
            'If(IsBlank(LookUp(colPEFs, ProjectNo = gblPEF.ProjectNo)), Collect(colPEFs, r), Patch(colPEFs, LookUp(colPEFs, ProjectNo = gblPEF.ProjectNo), r)))')
S_SAVE = (S_RECALC + ";\n"
          'Set(gblPEF, Patch(gblPEF, {Modified: Now(), WorkflowState: If(gblPEF.Status = "Pending Approval", gblPEF.WorkflowState, gblPEF.Status = "Approved", "Approval Status: Pending, this motivation must be re-approved", gblPEF.Close, "Approval for a Project Closure Motivation was not Started", gblPEF.Extend, "Approval for a Project Extension Motivation was not Started", "Approval for a New Project Motivation was not Started")}));\n'
          'If(IsBlank(gblPEF.ProjectNo), Notify("Choose a Divisional Group and Revenue Stream first; the PEF is saved under its project number.", NotificationType.Warning), '
          + S_UPSERT + '; Notify("PEF " & gblPEF.ProjectNo & " saved.", NotificationType.Success))')
S_CANCEL_APPROVAL = ('UpdateIf(colApprovals, Status in ["Pending", "Waiting"], {Status: "Not started"});\n'
                     'Set(gblPEF, Patch(gblPEF, {Status: "Draft", WorkflowState: "Approval cancelled by the applicant", Modified: Now()}));\n'
                     + S_EDITMODE + ";\n" + S_UPSERT + ";\n"
                     'Notify("Approval cancelled. The PEF is back in draft.", NotificationType.Information)')


def fmt(value):
    """YAML scalar for a pa-yaml property value (block scalar when needed)."""
    v = str(value)
    if "\n" in v or ": " in v or " #" in v or v.endswith(":"):
        return "|-", v.split("\n")
    return v, None


def emit(lines, indent, name, control, props, children=None, variant=None):
    pad = " " * indent
    lines.append(f"{pad}- {name}:")
    lines.append(f"{pad}    Control: {control}")
    if variant:
        lines.append(f"{pad}    Variant: {variant}")
    lines.append(f"{pad}    Properties:")
    for k, v in sorted(props.items()):
        head, body = fmt(v)
        lines.append(f"{pad}      {k}: {head}")
        if body:
            for b in body:
                lines.append(f"{pad}        {b}")
    if children is not None:
        lines.append(f"{pad}    Children:")
        for child in children:
            child(lines, indent + 6)


def ctl(name, control, props, children=None, variant=None):
    return lambda lines, indent: emit(lines, indent, name, control, props, children, variant)


def label(name, text, x, y, w, h, size="=11", color=TEXT, weight=None, align=None, valign="=VerticalAlign.Middle", extra=None):
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "Size": size, "Color": color, "Font": FONT,
         "VerticalAlign": valign}
    if weight:
        p["FontWeight"] = weight
    if align:
        p["Align"] = align
    p.update(extra or {})
    return ctl(name, "Label@2.5.1", p)


def button(name, text, x, y, w, h, kind, onselect=None, extra=None):
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "Font": FONT, "Size": "=11",
         "FontWeight": "=FontWeight.Semibold", "RadiusTopLeft": "=4", "RadiusTopRight": "=4",
         "RadiusBottomLeft": "=4", "RadiusBottomRight": "=4"}
    if kind == "primary":
        p.update({"Fill": PRIMARY, "Color": ON_DARK, "HoverFill": PRIMARY_HOVER, "BorderThickness": "=0"})
    elif kind == "secondary":
        p.update({"Fill": SURFACE, "Color": PRIMARY, "HoverFill": PRIMARY_TINT, "BorderColor": PRIMARY, "BorderThickness": "=1"})
    elif kind == "danger":
        p.update({"Fill": SURFACE, "Color": ERROR, "HoverFill": ERROR_TINT, "BorderColor": ERROR, "BorderThickness": "=1"})
    elif kind == "tab":
        p.update({"Fill": CLEAR, "HoverFill": PRIMARY_TINT, "BorderThickness": "=0"})
    if onselect:
        p["OnSelect"] = onselect
    p.update(extra or {})
    return ctl(name, "Classic/Button@2.2.0", p)


def app_bar(t, on_pef=False):
    return ctl(f"con{t}AppBar", "GroupContainer@1.5.0", {
        "BorderStyle": "=BorderStyle.None", "Fill": APPBAR,
        "X": "=0", "Y": "=0", "Width": "=Parent.Width", "Height": "=48",
    }, variant="ManualLayout", children=[
        button(f"btn{t}Brand", '="MINTEK"', "=16", "=10", "=84", "=28", "primary",
               onselect="=Navigate(scrDashboard, ScreenTransition.Fade)",
               extra={"Fill": BRAND, "HoverFill": BRAND_HOVER, "FontWeight": "=FontWeight.Bold",
                      "Tooltip": '="Back to the PEF register"'}),
        label(f"lbl{t}AppTitle", '="Project Establishment Forms"', "=112", "=0", "=320", "=48",
              size="=13", color=ON_DARK, weight="=FontWeight.Semibold"),
        label(f"lbl{t}ViewAs", '="View as"', "=Parent.Width - 372", "=0", "=56", "=48",
              size="=10", color=ON_DARK_MUTED, align="=Align.Right"),
        ctl(f"drp{t}Role", "Classic/DropDown@2.3.1", {
            "Items": "=colRoles", "Default": "=gblRole",
            "OnChange": "=Set(gblRole, Self.Selected.Value);\n" + S_EDITMODE
                        + ';\nIf(gblTab = "Details" && gblRole <> "Administrator", Set(gblTab, "Cover"))',
            "X": "=Parent.Width - 308", "Y": "=8", "Width": "=196", "Height": "=32",
            "Fill": SURFACE, "Color": TEXT, "BorderColor": SURFACE, "Font": FONT, "Size": "=10",
            "ChevronBackground": SURFACE, "ChevronFill": PRIMARY, "HoverFill": PRIMARY_TINT,
            "Tooltip": '="Demo only: switch the simulated user to see each approver\'s view"',
        }),
        ctl(f"ico{t}Settings", "Classic/Icon@2.5.0", {
            "Icon": "=Icon.Settings", "Color": ON_DARK, "X": "=Parent.Width - 100", "Y": "=12",
            "Width": "=24", "Height": "=24", "Visible": '=gblRole = "Administrator"',
            "OnSelect": '=Set(gblTab, "Details")' + ("" if on_pef else "; Navigate(scrPEF, ScreenTransition.Fade)"),
            "Tooltip": '="Detailed information"',
        }),
        button(f"btn{t}Avatar", '=LookUp(colRolePeople, Role = gblRole, Initials)', "=Parent.Width - 56", "=8", "=32", "=32",
               "primary", extra={"DisplayMode": "=DisplayMode.View", "HoverFill": "=Self.Fill", "Size": "=10",
                                 "RadiusTopLeft": "=16", "RadiusTopRight": "=16", "RadiusBottomLeft": "=16",
                                 "RadiusBottomRight": "=16",
                                 "Tooltip": '=LookUp(colRolePeople, Role = gblRole, Person) & ", " & LookUp(colRolePeople, Role = gblRole, Position)'}),
    ])


STATUS_FILL = ('=Switch(gblPEF.Status, "Approved", RGBA(223, 246, 221, 1), "Pending Approval", RGBA(255, 244, 206, 1), '
               '"Rejected", RGBA(253, 231, 233, 1), "Closed", RGBA(229, 241, 250, 1), RGBA(237, 235, 233, 1))')
STATUS_COLOR = ('=Switch(gblPEF.Status, "Approved", RGBA(16, 124, 16, 1), "Pending Approval", RGBA(138, 90, 0, 1), '
                '"Rejected", RGBA(196, 30, 58, 1), "Closed", RGBA(0, 94, 162, 1), RGBA(96, 94, 92, 1))')


def project_bar(t):
    return ctl(f"con{t}ProjectBar", "GroupContainer@1.5.0", {
        "BorderStyle": "=BorderStyle.None", "Fill": SURFACE,
        "X": "=0", "Y": "=48", "Width": "=Parent.Width", "Height": "=64",
    }, variant="ManualLayout", children=[
        label(f"lbl{t}ProjectNo", '=If(IsBlank(gblPEF.ProjectNo), "New PEF", gblPEF.ProjectNo)', "=24", "=6", "=200", "=30",
              size="=18", color=HEADING, weight="=FontWeight.Semibold"),
        label(f"lbl{t}ProjectTitle", '=If(IsBlank(gblPEF.ProjectTitle), "Untitled project", gblPEF.ProjectTitle)',
              "=24", "=36", "=Parent.Width * 0.4", "=22", size="=11", color=MUTED),
        label(f"lbl{t}Division",
              '=If(IsBlank(gblPEF.DivisionalGroup), "Divisional group not selected", gblPEF.Division & "  ·  " & gblPEF.DivisionalGroup) & "  ·  " & If(IsBlank(gblPEF.RevenueStream), "Revenue stream not selected", gblPEF.RevenueStream)',
              "=240", "=6", "=Parent.Width - 680", "=30", size="=11", color=TEXT),
        button(f"btn{t}Status", "=gblPEF.Status", "=Parent.Width - 420", "=12", "=136", "=24", "tab",
               extra={"DisplayMode": "=DisplayMode.View", "Fill": STATUS_FILL, "Color": STATUS_COLOR,
                      "HoverFill": "=Self.Fill", "Size": "=10", "RadiusTopLeft": "=12", "RadiusTopRight": "=12",
                      "RadiusBottomLeft": "=12", "RadiusBottomRight": "=12"}),
        label(f"lbl{t}Revision", '="Revision " & gblPEF.RevisionNo', "=Parent.Width - 276", "=12", "=96", "=24",
              size="=10", color=MUTED),
        label(f"lbl{t}FormVersion", '="Form Rev_2 / 2018-04-01"', "=Parent.Width - 176", "=12", "=160", "=24",
              size="=9", color=MUTED, align="=Align.Right"),
        label(f"lbl{t}WorkflowState", "=gblPEF.WorkflowState", "=Parent.Width - 420", "=38", "=404", "=20",
              size="=9", color=MUTED, align="=Align.Right"),
        ctl(f"rec{t}ProjectBarLine", "Rectangle@2.3.0", {
            "Fill": HAIRLINE, "X": "=0", "Y": "=63", "Width": "=Parent.Width", "Height": "=1"}),
    ])


def tab_bar(t):
    kids = []
    for key, caption, x, w, _tag, visible in TABS:
        extra = {"Color": f'=If(gblTab = "{key}", RGBA(0, 94, 162, 1), RGBA(96, 94, 92, 1))',
                 "FontWeight": f'=If(gblTab = "{key}", FontWeight.Semibold, FontWeight.Normal)',
                 "Tooltip": f'="{caption}"'}
        if visible:
            extra["Visible"] = visible
        kids.append(button(f"btn{t}Tab{key}", f'="{caption}"', f"={x}", "=8", f"={w}", "=32", "tab",
                           onselect=f'=Set(gblTab, "{key}")', extra=extra))
    sx = ", ".join(f'"{k}", {x + 8}' for k, _, x, w, _, _ in TABS)
    sw = ", ".join(f'"{k}", {w - 16}' for k, _, x, w, _, _ in TABS)
    kids.append(ctl(f"rec{t}TabIndicator", "Rectangle@2.3.0", {
        "Fill": PRIMARY, "X": f"=Switch(gblTab, {sx}, 24)", "Y": "=44",
        "Width": f"=Switch(gblTab, {sw}, 92)", "Height": "=3"}))
    kids.append(ctl(f"rec{t}TabBarLine", "Rectangle@2.3.0", {
        "Fill": HAIRLINE, "X": "=0", "Y": "=47", "Width": "=Parent.Width", "Height": "=1"}))
    kids.append(button(f"btn{t}CancelApproval", '="Cancel Approval"', "=Parent.Width - 452", "=8", "=140", "=32",
                       "danger", onselect="=" + S_CANCEL_APPROVAL,
                       extra={"Visible": '=gblPEF.Status = "Pending Approval" && gblRole = "Applicant (CI)"',
                              "Tooltip": '="Withdraw the PEF from the approval workflow"'}))
    kids.append(button(f"btn{t}Save", '="Save PEF"', "=Parent.Width - 304", "=8", "=120", "=32",
                       "secondary", onselect="=" + S_SAVE,
                       extra={"Visible": '=gblRole in ["Applicant (CI)", "Administrator"]',
                              "Tooltip": '="Save the PEF without starting approval"'}))
    kids.append(button(f"btn{t}StartApproval", '="Start Approval"', "=Parent.Width - 176", "=8", "=160", "=32",
                       "primary", onselect='=Set(gblTab, "Review")',
                       extra={"Visible": '=gblPEF.Status in ["Draft", "Rejected"] && gblRole = "Applicant (CI)"',
                              "Tooltip": '="Review the PEF and submit it for approval"'}))
    return ctl(f"con{t}TabBar", "GroupContainer@1.5.0", {
        "BorderStyle": "=BorderStyle.None", "Fill": SURFACE,
        "X": "=0", "Y": "=112", "Width": "=Parent.Width", "Height": "=48",
    }, variant="ManualLayout", children=kids)


def emit_node(lines, indent, name, node):
    """Emit an already-parsed control (used by --write to keep screen bodies unchanged)."""
    pad = " " * indent
    lines.append(f"{pad}- {name}:")
    lines.append(f"{pad}    Control: {node['Control']}")
    if node.get("Variant"):
        lines.append(f"{pad}    Variant: {node['Variant']}")
    lines.append(f"{pad}    Properties:")
    for k, v in sorted((node.get("Properties") or {}).items()):
        head, body = fmt(v)
        lines.append(f"{pad}      {k}: {head}")
        for b in body or []:
            lines.append(f"{pad}        {b}")
    if node.get("Children"):
        lines.append(f"{pad}    Children:")
        for child in node["Children"]:
            cname = next(iter(child))
            emit_node(lines, indent + 6, cname, child[cname])


def write_chrome():
    """Regenerate the chrome of every screen in place; bodies are re-emitted unchanged."""
    for fname, screen, tag, kind in SCREENS:
        path = os.path.join(SCREENS_DIR, fname)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        comment = text.splitlines()[0] if text.startswith("#") else f"# {screen} - see DESIGN.md."
        body = yaml.safe_load(text)["Screens"][screen]
        names = set(chrome_names(tag, kind))
        lines = [comment, "Screens:", f"  {screen}:", "    Properties:"]
        for k, v in sorted((body.get("Properties") or {}).items()):
            head, block = fmt(v)
            lines.append(f"      {k}: {head}")
            for b in block or []:
                lines.append(f"        {b}")
        lines.append("    Children:")
        for child in body.get("Children") or []:
            cname = next(iter(child))
            if cname not in names:
                emit_node(lines, 6, cname, child[cname])
        for c in chrome(tag, kind):
            c(lines, 6)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"rewritten {fname}")


def chrome(tag, kind):
    if kind == "pef":
        return [app_bar(tag, on_pef=True), project_bar(tag), tab_bar(tag)]
    return [app_bar(tag)]


def chrome_names(tag, kind):
    return [f"con{tag}AppBar"] + ([f"con{tag}ProjectBar", f"con{tag}TabBar"] if kind == "pef" else [])


def build_screen(screen, tag, body, on_visible_extra=None, comment=None):
    """YAML for a plain screen (Dashboard, Confirmation): your body controls + the generated App bar.

    body: list of ctl()/label()/button() items placed before the App bar (body starts at Y 48).
    The PEF form screen is edited in place; its tab bodies are the fgd<Tag>Body containers.
    """
    lines = [f"# {comment or screen + ' - see DESIGN.md.'} Chrome (last children) is generated by tools/gen_chrome.py.",
             "Screens:", f"  {screen}:", "    Properties:"]
    props = {"Fill": PAGE}
    if on_visible_extra:
        props["OnVisible"] = "=" + on_visible_extra
    for k, v in sorted(props.items()):
        head, block = fmt(v)
        lines.append(f"      {k}: {head}")
        for b in block or []:
            lines.append(f"        {b}")
    lines.append("    Children:")
    for c in list(body) + chrome(tag, "plain"):
        c(lines, 6)
    return "\n".join(lines) + "\n"


def chrome_yaml(tag, kind):
    lines = []
    for c in chrome(tag, kind):
        c(lines, 0)
    return "\n".join(lines) + "\n"


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def check():
    bad = 0
    for fname, screen, tag, kind in SCREENS:
        path = os.path.join(SCREENS_DIR, fname)
        if not os.path.exists(path):
            print(f"MISSING  {fname}")
            bad += 1
            continue
        doc = load(path)
        kids = doc["Screens"][screen].get("Children") or []
        by_name = {next(iter(k)): k for k in kids if isinstance(k, dict)}
        expected = yaml.safe_load(chrome_yaml(tag, kind))
        for item in expected:
            name = next(iter(item))
            if by_name.get(name) != item:
                print(f"DRIFT    {fname}: {name} differs from the generated chrome")
                bad += 1
        if kind == "pef":
            for key, _cap, _x, _w, btag, _vis in TABS:
                fgd = by_name.get(f"fgd{btag}Body")
                if not fgd:
                    print(f"MISSING  {fname}: tab container fgd{btag}Body for tab '{key}'")
                    bad += 1
                elif str((fgd[f"fgd{btag}Body"].get("Properties") or {}).get("Visible", "")).strip() != f'=gblTab = "{key}"':
                    print(f"DRIFT    {fname}: fgd{btag}Body must have Visible: =gblTab = \"{key}\"")
                    bad += 1
        order = [next(iter(k)) for k in kids if isinstance(k, dict)]
        tail = order[-len(expected):]
        if tail != chrome_names(tag, kind):
            print(f"ORDER    {fname}: chrome must be the last children ({chrome_names(tag, kind)}), got {tail}")
            bad += 1
    print("chrome check:", "OK" if not bad else f"{bad} problem(s)")
    return bad


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if arg == "--write":
        write_chrome()
    elif arg == "--print":
        tag = sys.argv[2]
        kind = next(k for _, _, t, k in SCREENS if t == tag)
        sys.stdout.write(chrome_yaml(tag, kind))
    else:
        sys.exit(1 if check() else 0)


if __name__ == "__main__":
    main()
