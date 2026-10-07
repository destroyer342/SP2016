#!/usr/bin/env python3
"""Cross-screen checks for the PEF canvas app (things Parker's validate.py cannot
see because it checks one file at a time).

Usage:
    python tools/check_app.py            # all screens + App.pa.yaml
    python tools/check_app.py --quiet    # summary lines only

Checks:
  1. Every file parses; each screen file has exactly one screen under Screens.
  2. Control and screen names are unique across the whole app.
  3. Only the control types listed in DESIGN.md section 2 are used.
  4. Every property value is a formula (starts with '=').
  5. Formula sanity: balanced () [] {} and closed "strings".
  6. Every gbl*/col* name used is defined (Set / ClearCollect / Collect) somewhere.
  7. gblPEF.X, gblTotals.X, gblActuals.X, gblConfirmation.X and the fields in
     Patch(gblPEF, {...}) exist in their definitions.
  8. Control references (txtX.Text, drpX.Selected, ...) point at existing controls;
     references to a control on another screen are reported.
  9. Navigate(...) targets exist.
 10. Icon.* names are in the DESIGN.md allow-list.
 11. ThisItem.X inside a gallery matches the columns of the gallery's collection
     (when Items is a plain col*/Filter/Sort/Search over one collection).
 12. DataCard / ManualLayout container height covers children with numeric Y + Height.
 13. Parker validate.py on every screen (errors and warnings) and the chrome check.
Exit code 1 if any ERROR.
"""
import os
import re
import subprocess
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
REPO = os.path.dirname(os.path.dirname(APP))
VALIDATE = os.path.join(REPO, "skills", "parker", "validate.py")
sys.path.insert(0, HERE)
import gen_chrome  # noqa: E402

ALLOWED_CONTROLS = {
    "GroupContainer@1.5.0", "Label@2.5.1", "Classic/Button@2.2.0", "Classic/Icon@2.5.0",
    "Gallery@2.15.0", "FluidGrid@2.3.0", "DataCard@1.0.2", "Rectangle@2.3.0",
    "Classic/TextInput@2.3.2", "Classic/DropDown@2.3.1", "Classic/ComboBox@2.4.0",
    "Classic/DatePicker@2.6.0", "Classic/CheckBox@2.1.0", "Classic/Radio@2.3.0", "Classic/Toggle@2.1.0",
}
ALLOWED_ICONS = set("""Add Trash Edit Cancel Check ChevronDown ChevronUp ChevronLeft ChevronRight Reload Print Lock
Download Mail Document DocumentPDF DocumentWithContent CalendarBlank Clock People Person Home Settings Search
Hamburger Information Warning Error Post Trending DetailList Message""".split())
CONTROL_PREFIXES = ("txt", "drp", "cmb", "dte", "chk", "rad", "tgl", "gal", "lbl", "btn", "ico", "con", "rec", "fgd", "dcd")

ERRORS, WARNINGS = [], []


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def strip_strings(f):
    """Formula with string literals blanked (keeps length), plus unterminated flag."""
    out, i, n, open_ = [], 0, len(f), False
    while i < n:
        c = f[i]
        if c == '"':
            j = i + 1
            while j < n:
                if f[j] == '"':
                    if j + 1 < n and f[j + 1] == '"':
                        j += 2
                        continue
                    break
                j += 1
            if j >= n:
                open_ = True
                out.append('"' + " " * (n - i - 1))
                break
            out.append('"' + " " * (j - i - 1) + '"')
            i = j + 1
            continue
        if c == "/" and f[i:i + 2] == "//":
            j = f.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), open_


def balanced(code):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for c in code:
        if c in "([{":
            stack.append(c)
        elif c in ")]}":
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
    return not stack


def iter_controls(node, screen, parent=None, out=None):
    """Yield (name, node, screen, parent_name) for every control."""
    if out is None:
        out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, dict) and "Control" in v:
                out.append((k, v, screen, parent))
                for child in v.get("Children") or []:
                    iter_controls(child, screen, k, out)
            elif k == "Children" and isinstance(v, list):
                for child in v:
                    iter_controls(child, screen, parent, out)
    elif isinstance(node, list):
        for child in node:
            iter_controls(child, screen, parent, out)
    return out


def record_fields(text):
    """Top-level field names of the first {...} record literal in text."""
    i = text.find("{")
    if i < 0:
        return set()
    depth, j, fields, token = 0, i, set(), ""
    code, _ = strip_strings(text)
    while j < len(code):
        c = code[j]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                break
        if depth == 1:
            m = re.match(r"[{,]\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", code[j:])
            if m and c in "{,":
                fields.add(m.group(1))
        j += 1
    return fields


def main():
    quiet = "--quiet" in sys.argv
    files = [("App.pa.yaml", os.path.join(APP, "App.pa.yaml"), None)]
    for fname, screen, tag, kind in gen_chrome.SCREENS:
        files.append((fname, os.path.join(APP, "screens", fname), screen))

    docs, formulas = {}, []  # formulas: (file, control, prop, text, screen)
    for fname, path, screen in files:
        try:
            docs[fname] = load(path)
        except Exception as e:  # noqa: BLE001
            ERRORS.append(f"{fname}: cannot parse: {e}")
    app_text = (docs.get("App.pa.yaml") or {}).get("App", {}).get("Properties", {}).get("OnStart", "")
    formulas.append(("App.pa.yaml", "App", "OnStart", app_text, None))

    controls = {}  # name -> (file, screen, node)
    screens = set()
    for fname, path, screen in files[1:]:
        doc = docs.get(fname)
        if not doc:
            continue
        scr = (doc.get("Screens") or {})
        if list(scr) != [screen]:
            ERRORS.append(f"{fname}: expected exactly one screen '{screen}', found {list(scr)}")
            continue
        screens.add(screen)
        body = scr[screen] or {}
        for k, v in (body.get("Properties") or {}).items():
            formulas.append((fname, screen, k, str(v), screen))
        for name, node, s, parent in iter_controls(body, screen):
            if name in controls or name in screens:
                ERRORS.append(f"duplicate control name '{name}' ({controls.get(name, ('?',))[0]} and {fname})")
            controls[name] = (fname, s, node, parent)
            ctrl = node.get("Control")
            if ctrl not in ALLOWED_CONTROLS:
                ERRORS.append(f"{fname}: {name} uses control type '{ctrl}' not allowed by DESIGN.md")
            if not name.startswith(CONTROL_PREFIXES):
                WARNINGS.append(f"{fname}: control name '{name}' does not use a DESIGN.md prefix")
            for k, v in (node.get("Properties") or {}).items():
                sv = str(v)
                if not sv.lstrip().startswith("="):
                    ERRORS.append(f"{fname}: {name}.{k} is not a formula (missing '='): {sv[:60]!r}")
                formulas.append((fname, name, k, sv, s))

    # definitions of variables / collections
    defined = set()
    for _, _, _, text, _ in formulas:
        defined.update(re.findall(r"\bSet\(\s*(gbl\w+)", text))
        defined.update(re.findall(r"\b(?:ClearCollect|Collect)\(\s*(col\w+)", text))

    # record schemas
    def first_record_after(pattern, text):
        m = re.search(pattern, text)
        return record_fields(text[m.end():]) if m else set()

    pef_fields = first_record_after(r"Set\(gblSamplePEF,\s*", app_text)
    totals_fields = record_fields(gen_chrome.S_RECALC[gen_chrome.S_RECALC.find("{Labour"):])
    actual_fields = first_record_after(r"Set\(gblSampleActuals,\s*", app_text)
    conf_fields = first_record_after(r"Set\(gblConfirmation,\s*", app_text)
    schemas = {"gblPEF": pef_fields, "gblTotals": totals_fields, "gblActuals": actual_fields,
               "gblSampleActuals": actual_fields, "gblBlankActuals": actual_fields,
               "gblConfirmation": conf_fields, "gblSamplePEF": pef_fields, "gblNewPEF": pef_fields}

    # collection schemas from App.OnStart (first record, or [..] -> Value, or copy of another col)
    col_schema = {}
    for m in re.finditer(r"ClearCollect\(\s*(col\w+)\s*,\s*", app_text):
        name, rest = m.group(1), app_text[m.end():]
        if rest.startswith("["):
            col_schema[name] = {"Value"}
        elif rest.startswith("{"):
            col_schema[name] = record_fields(rest)
        else:
            src = re.match(r"(col\w+)", rest)
            if src:
                col_schema.setdefault(name, ("alias", src.group(1)))
    for k, v in list(col_schema.items()):
        if isinstance(v, tuple):
            col_schema[k] = col_schema.get(v[1], set()) if not isinstance(col_schema.get(v[1]), tuple) else set()

    for fname, cname, prop, text, screen in formulas:
        code, unterminated = strip_strings(text)
        where = f"{fname}: {cname}.{prop}"
        if unterminated:
            ERRORS.append(f"{where}: unterminated string literal")
        if not balanced(code):
            ERRORS.append(f"{where}: unbalanced brackets")
        for ident in set(re.findall(r"\b((?:gbl|col)[A-Z]\w*)", code)):
            if ident not in defined:
                ERRORS.append(f"{where}: '{ident}' is never defined (Set/ClearCollect/Collect)")
        for var, field in re.findall(r"\b(gbl[A-Z]\w*)\.([A-Za-z_]\w*)", code):
            if var in schemas and schemas[var] and field not in schemas[var]:
                ERRORS.append(f"{where}: {var}.{field} is not a field of {var}")
        for m in re.finditer(r"Patch\(\s*(gbl[A-Z]\w*)\s*,\s*(?=\{)", code):
            var = m.group(1)
            if schemas.get(var):
                for field in record_fields(code[m.end():]):
                    if field not in schemas[var]:
                        ERRORS.append(f"{where}: Patch({var}, ...) sets unknown field '{field}'")
        for ref, attr in re.findall(r"\b((?:" + "|".join(CONTROL_PREFIXES) + r")[A-Z]\w*)\.(\w+)", code):
            if ref not in controls:
                ERRORS.append(f"{where}: reference to unknown control '{ref}.{attr}'")
            elif screen and controls[ref][1] != screen:
                WARNINGS.append(f"{where}: references '{ref}' on another screen ({controls[ref][1]})")
        for target in re.findall(r"\bNavigate\(\s*(\w+)", code):
            if target not in screens:
                ERRORS.append(f"{where}: Navigate to unknown screen '{target}'")
        if prop == "Icon" or "Icon." in code:
            for icon in re.findall(r"\bIcon\.(\w+)", code):
                if icon not in ALLOWED_ICONS:
                    ERRORS.append(f"{where}: Icon.{icon} is not in the DESIGN.md allow-list")

    # 11. ThisItem fields vs gallery collection
    for name, (fname, screen, node, parent) in controls.items():
        if not str(node.get("Control", "")).startswith("Gallery"):
            continue
        items = str((node.get("Properties") or {}).get("Items", ""))
        code, _ = strip_strings(items)
        cols = set(re.findall(r"\b(col\w+)", code))
        if len(cols) != 1 or "Distinct(" in code or "AddColumns(" in code or "ForAll(" in code \
                or "ShowColumns(" in code or "GroupBy(" in code:
            continue
        cols_name = cols.pop()
        schema = col_schema.get(cols_name)
        if not schema:
            continue
        sub = iter_controls({name: node}, screen)
        for cname, cnode, _, _ in sub:
            for k, v in (cnode.get("Properties") or {}).items():
                vcode, _ = strip_strings(str(v))
                for field in re.findall(r"\bThisItem\.(\w+)", vcode):
                    if field not in schema:
                        ERRORS.append(f"{fname}: {cname}.{k} uses ThisItem.{field}, not a column of {cols_name} (gallery {name})")

    # 12. container/card heights
    def num(v):
        s = str(v).strip().lstrip("=").strip()
        try:
            return float(s)
        except ValueError:
            return None

    for name, (fname, screen, node, parent) in controls.items():
        ctrl = str(node.get("Control", ""))
        if not (ctrl.startswith("DataCard") or (ctrl.startswith("GroupContainer") and node.get("Variant") == "ManualLayout")):
            continue
        h = num((node.get("Properties") or {}).get("Height"))
        if h is None:
            continue
        for child in node.get("Children") or []:
            if not isinstance(child, dict):
                continue
            cname = next(iter(child))
            cp = (child[cname] or {}).get("Properties") or {}
            cy, ch = num(cp.get("Y")), num(cp.get("Height"))
            if cy is not None and ch is not None and cy + ch > h + 1:
                ERRORS.append(f"{fname}: {cname} (Y {cy:g} + Height {ch:g}) overflows {name} (Height {h:g})")

    # 13. Parker validator + chrome
    parker = {}
    for fname, path, screen in files[1:]:
        r = subprocess.run([sys.executable, "-I", VALIDATE, path], capture_output=True, text=True)
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith(("ERROR", "WARNING"))]
        parker[fname] = (r.returncode, lines, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:])
        for ln in lines:
            (ERRORS if ln.startswith("ERROR") else WARNINGS).append(f"{fname}: parker {ln}")
        if r.returncode != 0 and not lines:
            ERRORS.append(f"{fname}: parker validate.py failed: {parker[fname][2]}")
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "gen_chrome.py"), "--check"], capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith(("DRIFT", "ORDER", "MISSING")):
            ERRORS.append(f"chrome {ln}")

    n_controls = len(controls)
    print(f"Screens: {len(screens)}   Controls: {n_controls}   Formulas: {len(formulas)}")
    for fname, (rc, lines, last) in parker.items():
        print(f"  parker {fname}: {last}")
    print(f"  chrome: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()}")
    if not quiet:
        for e in ERRORS:
            print("ERROR:  ", e)
        for w in WARNINGS:
            print("WARNING:", w)
    print(f"{len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main()
