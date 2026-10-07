#!/usr/bin/env python3
"""Validate a Power Apps canvas-app YAML (pa-yaml) screen.

Usage:
    python validate.py NEW_SCREEN.yaml [EXISTING1.yaml EXISTING2.yaml ...]

- NEW_SCREEN.yaml is the file being checked.
- The remaining (optional) files are the app's already-working screens; the
  validator treats their controls + properties as the "proven" vocabulary and
  flags anything in NEW_SCREEN.yaml that isn't proven.

Checks (see the parker skill, SKILL.md, for the why behind each):
  1. YAML parses (with a constructor for Power Apps' bare `=` value tag).
  2. Every control type / @version is proven in the existing screens.
  3. Every property name is one already used on that control type elsewhere.
  4. No Classic/* control reads Parent.TemplateWidth in X/Y/Width/Height
     (returns 0 inside a modern Gallery -> control jumps to the far left).
  5. ModernButton usage (warns: can render blank in nested auto-layouts).
  6. Horizontal auto-layout with 2+ FillPortions children (warns: distribution
     proved unreliable; prefer explicit Parent.Width * fraction).
  7. A positioning-wrapper GroupContainer carrying an opaque Fill (warns: paints
     a stray block over only its sub-column; remove the wrapper's Fill line, set
     DropShadow: =DropShadow.None, and draw backgrounds with a separate
     full-width control). Two triggers: the wrapper's only child is a Classic/*
     control, or its Width is a fraction of Parent.TemplateWidth (a gallery
     sub-column), whatever it holds. Other multi-child wrappers are not
     detected - check them by eye.
  8. GroupContainer chrome (all warnings):
     a. BorderStyle missing - the container's default is a visible border, so
        every GroupContainer sets BorderStyle: =BorderStyle.None.
     b. A GroupContainer with no solid Fill of its own (scaffolding) missing an
        explicit DropShadow, or setting it to anything other than
        =DropShadow.None (e.g. Light) - scaffolding wants
        =DropShadow.None; Light is for an elevated solid-Fill card only. Do not
        rely on DropShadow defaulting to None. A solid-Fill painted surface or
        hairline is not flagged when it omits DropShadow.
     c. A GroupContainer writing Fill: =RGBA(0,0,0,0) - omit the Fill line
        instead; the explicit transparent RGBA belongs on Classic/Button.
  9. A direct child of a ManualLayout GroupContainer whose numeric Y + Height
     exceeds the parent's numeric Height (warns: the child is clipped / renders
     detached outside the card; raise the parent Height or make it a sibling).
 10. Known-invalid Icon.* names that look plausible but do not exist in the
     Power Apps icon enum (warns: Studio shows nothing; e.g. Icon.Documents ->
     Icon.DocumentPDF). Denylist is empirical and easy to extend.
 11. A Label carrying a real OnSelect (errors: clickable text must be a
     Classic/Button - a Label gives no hover/press feedback, no focus ring and
     no keyboard reach; use Classic/Icon for icon-only tap targets).
 12. A screen whose direct children are a long flat list of loose controls
     (warns: group each region into its own named GroupContainer so it can be
     moved, hidden, restyled or duplicated as one unit).

Messages name the control instance and its type, e.g. "CellAction (GroupContainer@1.5.0)".
Exit code 0 if no ERRORS (warnings allowed), 1 otherwise; an unreadable, empty
or non-YAML file is an ERROR.
Requires: pyyaml  (pip install pyyaml)
"""
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required:  python -m pip install pyyaml")

# Plausible-looking icon names that are NOT in the Power Apps icon enum.
# Studio silently renders nothing for these. Extend as you confirm more.
INVALID_ICONS = {
    "Icon.Documents": "Icon.DocumentPDF",
}

# Controls that group other controls; everything else is a leaf for check 12.
CONTAINER_PREFIXES = ("GroupContainer", "FluidGrid", "DataCard", "Gallery", "Container")

# Check 12 heuristic: a screen with more than MAX_FLAT_CHILDREN direct children,
# more than MAX_FLAT_LEAVES of them loose controls, was never grouped.
MAX_FLAT_CHILDREN = 10
MAX_FLAT_LEAVES = 8

# Power Apps writes bare `=`-prefixed scalars; a lone `=` resolves to this tag.
yaml.SafeLoader.add_constructor(
    "tag:yaml.org,2002:value", lambda loader, node: loader.construct_scalar(node)
)

ERRORS, WARNINGS = [], []


def num(v):
    """Return the numeric value of a pa-yaml scalar like '=548', else None."""
    s = str(v).strip()
    if s.startswith("="):
        s = s[1:].strip()
    try:
        return float(s)
    except ValueError:
        return None


def is_transparent(fill):
    """True if a Fill value is fully transparent (alpha 0) or Color.Transparent."""
    s = str(fill).lower().replace(" ", "")
    if "color.transparent" in s:
        return True
    if "rgba(" in s:
        try:
            inner = s.split("rgba(", 1)[1].rsplit(")", 1)[0]
            parts = inner.split(",")
            if len(parts) >= 4:
                return float(parts[3]) == 0
        except (ValueError, IndexError):
            return False
    return False


def is_live(formula):
    """True if an OnSelect-style value actually does something."""
    s = str(formula).strip().lstrip("=").strip()
    return s not in ("", "false", "true", 'Blank()')


def children(node):
    """A control's Children list, or [] when it is missing or malformed."""
    kids = node.get("Children") if isinstance(node, dict) else None
    return kids if isinstance(kids, list) else []


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def walk(node, fn, name="?"):
    """Call fn(control_node, control_name) for every node that has a Control."""
    if isinstance(node, dict):
        if node.get("Control"):
            fn(node, name)
        for k, v in node.items():
            walk(v, fn, k)
    elif isinstance(node, list):
        for v in node:
            walk(v, fn, name)


def collect_vocab(doc, controls):
    def visit(n, _name):
        ctrl = n.get("Control")
        if ctrl:
            props = (n.get("Properties") or {}).keys()
            controls.setdefault(ctrl, set()).update(props)
    walk(doc, visit)


def audit(doc, proven):
    def visit(n, name):
        ctrl = n.get("Control")
        if not ctrl:
            return
        props = n.get("Properties") or {}
        label = f"{name} ({ctrl})"  # display only; logic below uses the raw type
        # 2. unproven control
        if proven and ctrl not in proven:
            ERRORS.append(f"{label}: unproven control type")
        # 3. unproven property names (only when we have a baseline for the control)
        if proven.get(ctrl):
            for p in props:
                if p not in proven[ctrl]:
                    WARNINGS.append(f"{label}: property '{p}' not seen on this control type in existing screens")
        # 4. classic control + TemplateWidth
        if ctrl.startswith("Classic/"):
            for k in ("X", "Y", "Width", "Height"):
                if "TemplateWidth" in str(props.get(k, "")):
                    ERRORS.append(f"{label}.{k} uses Parent.TemplateWidth - classic controls read 0; wrap in a modern GroupContainer")
        # 5. ModernButton
        if ctrl == "ModernButton@1.0.0" or ctrl.startswith("ModernButton"):
            WARNINGS.append(f"{label}: ModernButton used - can render blank in nested auto-layouts; prefer Classic/Button")
        # 6. horizontal auto-layout with multiple FillPortions children
        if ctrl.startswith("GroupContainer") and n.get("Variant") == "AutoLayout" \
                and "Horizontal" in str(props.get("LayoutDirection", "")):
            n_fill = 0
            for child in children(n):
                if not isinstance(child, dict):
                    continue
                for cv in child.values():
                    if isinstance(cv, dict):
                        fp = str((cv.get("Properties") or {}).get("FillPortions", ""))
                        # FillPortions present and not =0
                        if "FillPortions" in (cv.get("Properties") or {}) and fp.strip().lstrip("=").strip() not in ("0", ""):
                            n_fill += 1
            if n_fill > 1:
                WARNINGS.append(f"{label}: horizontal auto-layout with 2+ FillPortions children - distribution is unreliable for wide content; prefer explicit Parent.Width * fraction")
        # 7. positioning-wrapper GroupContainer with an opaque Fill. Triggers:
        #    (a) its only child is a Classic/* control, or (b) it is a gallery
        #    sub-column (Width is a fraction of Parent.TemplateWidth).
        if ctrl.startswith("GroupContainer") and "Fill" in props and not is_transparent(props["Fill"]):
            kids = [c for c in children(n) if isinstance(c, dict)]
            reason = None
            if len(kids) == 1:
                inner = next((v for v in kids[0].values() if isinstance(v, dict)), None)
                inner_ctrl = str((inner or {}).get("Control", ""))
                if inner_ctrl.startswith("Classic/"):
                    reason = f"wraps a single {inner_ctrl}"
            if reason is None and re.search(r"TemplateWidth\s*\*", str(props.get("Width", ""))):
                reason = "is a gallery sub-column (Width is a fraction of Parent.TemplateWidth)"
            if reason:
                WARNINGS.append(
                    f"{label} {reason} but has an opaque Fill ({props['Fill']}) - "
                    "a positioning-only wrapper paints a stray block over just its sub-column; "
                    "remove its Fill line (a GroupContainer is transparent without one), set "
                    "DropShadow: =DropShadow.None (it is then scaffolding), and draw any "
                    "row/card background with a separate full-width control"
                )
        # 8. GroupContainer should suppress Studio's default chrome: BOTH the
        #    border AND the shadow.
        #    8a. BorderStyle.None is not the container default.
        #    8b. DropShadow is NOT reliably None either - state it explicitly. Most
        #        containers are scaffolding (region / card / positioning wrappers)
        #        and want =DropShadow.None; only a solid-Fill elevated card takes
        #        Light. A solid-Fill painted surface may omit DropShadow.
        #    8c. Transparency is expressed by omitting Fill, not RGBA(0,0,0,0).
        if ctrl.startswith("GroupContainer"):
            if "BorderStyle" not in props:
                WARNINGS.append(f"{label} is missing BorderStyle: =BorderStyle.None - add it to suppress Studio's default container border")
            fill = props.get("Fill")
            scaffolding = fill is None or is_transparent(fill)
            if "DropShadow" not in props:
                if scaffolding:
                    WARNINGS.append(
                        f"{label} has no Fill of its own and is missing DropShadow: =DropShadow.None - "
                        "state it explicitly; an unstated shadow on a scaffolding container renders as a "
                        "grey smudge with no surface under it"
                    )
            elif scaffolding and str(props["DropShadow"]).strip().lstrip("=").strip() != "DropShadow.None":
                WARNINGS.append(
                    f"{label} has no solid Fill but sets DropShadow: {props['DropShadow']} - a positioning/region "
                    "wrapper should be =DropShadow.None; reserve Light for an elevated solid-Fill card surface"
                )
            # 8c. a container's transparency is expressed by omitting Fill, not by RGBA(0,0,0,0)
            if fill is not None and is_transparent(fill):
                WARNINGS.append(
                    f"{label} sets Fill: =RGBA(0,0,0,0) - on a GroupContainer omit the Fill line entirely; "
                    "the explicit transparent RGBA belongs on Classic/Button"
                )
        # 9. child overflows a fixed-Height ManualLayout GroupContainer
        if ctrl.startswith("GroupContainer") and n.get("Variant") == "ManualLayout":
            ph = num(props.get("Height"))
            if ph is not None:
                for child in children(n):
                    if not isinstance(child, dict):
                        continue
                    cname = next(iter(child), "?")
                    cv = child.get(cname) or {}
                    cp = (cv.get("Properties") or {}) if isinstance(cv, dict) else {}
                    cy, ch = num(cp.get("Y")), num(cp.get("Height"))
                    if cy is not None and ch is not None and cy + ch > ph + 1:
                        WARNINGS.append(
                            f"{label} (Height {ph:g}) child '{cname}' overflows: Y {cy:g} + Height {ch:g} "
                            f"= {cy + ch:g} > {ph:g} - it is clipped/detached; raise the parent Height or make it a sibling"
                        )
        # 10. known-invalid icon names (Studio renders nothing)
        for k, v in props.items():
            sval = str(v)
            for bad, good in INVALID_ICONS.items():
                if re.search(r"\b" + re.escape(bad) + r"\b", sval):
                    WARNINGS.append(f"{bad} is not a valid Power Apps icon (property {k} on {label}); use {good}")
        # 11. clickable Label - must be a button control
        if ctrl.startswith("Label") and is_live(props.get("OnSelect", "")):
            ERRORS.append(
                f"{label} has a live OnSelect - clickable text must be a Classic/Button "
                "(a Label has no hover/press feedback, focus ring or keyboard reach); "
                "use Classic/Icon for an icon-only tap target"
            )
    walk(doc, visit)


def audit_screens(doc):
    """12. Flag screens whose regions were never grouped into containers."""
    if not isinstance(doc, dict):
        return
    screens = doc.get("Screens") or {}
    if not isinstance(screens, dict):
        return
    for sname, sbody in screens.items():
        if not isinstance(sbody, dict):
            continue
        kids = children(sbody)
        leaves = 0
        for child in kids:
            if not isinstance(child, dict):
                continue
            cv = next((v for v in child.values() if isinstance(v, dict)), {})
            cctrl = str(cv.get("Control", ""))
            if not cctrl.startswith(CONTAINER_PREFIXES) and "CanvasComponent" not in cctrl:
                leaves += 1
        if len(kids) > MAX_FLAT_CHILDREN and leaves > MAX_FLAT_LEAVES:
            WARNINGS.append(
                f"screen '{sname}' has {len(kids)} direct children ({leaves} loose controls) - "
                "group each region (top bar, filter row, KPI row, card, action bar) into its own "
                "named GroupContainer so it can be moved, hidden, restyled or duplicated as one unit"
            )


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    new_file, refs = sys.argv[1], sys.argv[2:]

    # 1. parse
    try:
        doc = load(new_file)
    except yaml.YAMLError as e:
        msg = str(e)
        hint = ""
        if "mapping values are not allowed" in msg:
            hint = "  HINT: a `=` value likely contains a colon+space (e.g. =\"Status: Ready\"). Reword or split."
        sys.exit(f"ERROR: {new_file} is not valid YAML:\n{msg}\n{hint}")
    except (OSError, UnicodeDecodeError) as e:  # UnicodeDecodeError is a ValueError, not an OSError
        sys.exit(f"ERROR: cannot read {new_file}: {e}")
    if doc is None:
        sys.exit(f"ERROR: {new_file} is empty")
    if not isinstance(doc, (dict, list)):
        sys.exit(f"ERROR: {new_file} is not a screen or control list")

    proven = {}
    for r in refs:
        try:
            collect_vocab(load(r), proven)
        except Exception as e:  # noqa: BLE001 - reference file problems shouldn't crash the run
            WARNINGS.append(f"could not read reference {r}: {e}")

    audit(doc, proven)
    audit_screens(doc)

    used = {}
    collect_vocab(doc, used)
    print(f"Parse: OK")
    print(f"Controls used: {', '.join(sorted(used))}")
    if not refs:
        print("(no reference screens given — skipped proven-control/property audit)")
    print()
    for e in ERRORS:
        print(f"ERROR:   {e}")
    for w in WARNINGS:
        print(f"WARNING: {w}")
    print()
    print(f"{len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main()
