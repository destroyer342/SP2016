# Draws migration-architecture.svg (next to this script): today (SharePoint 2016) -> target (Microsoft 365 / Power Platform).
# Run: python3 docs/images/migration-architecture.py
# The PNG is a 2x screenshot of the SVG (any browser or converter will do).
import os
from xml.sax.saxutils import escape

W, H = 1600, 1060
FONT = "Segoe UI, Liberation Sans, Arial, sans-serif"
out = []


def text(x, y, s, size=13, weight='normal', fill='#1f2933', anchor='start', italic=False):
    style = ' font-style="italic"' if italic else ''
    out.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
               f'fill="{fill}" text-anchor="{anchor}" xml:space="preserve"{style}>{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke, rx=8, sw=1.5, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def box(x, y, w, h, title, lines, fill, stroke, title_fill=None, dash=None, tag=None):
    rect(x, y, w, h, fill, stroke, dash=dash)
    out.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{stroke}"/>')
    text(x + 18, y + 24, title, 15, 'bold', title_fill or stroke)
    if tag:
        tw = 9 + 6.6 * len(tag)
        rect(x + w - tw - 10, y + 9, tw, 20, '#ffffff', stroke, rx=10, sw=1)
        text(x + w - tw / 2 - 10, y + 23, tag, 11, 'bold', stroke, 'middle')
    for i, line in enumerate(lines):
        text(x + 18, y + 46 + i * 18, line, 13)


def bh(lines):
    return 40 + 18 * len(lines) if lines else 40


def arrow(x1, x2, y, label, color='#455a64', dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    out.append(f'<line x1="{x1}" y1="{y}" x2="{x2 - 8}" y2="{y}" stroke="{color}" stroke-width="2.2"{d} marker-end="url(#arr)"/>')
    tw = 12 + 6.9 * len(label)
    cx = (x1 + x2) / 2
    rect(cx - tw / 2, y - 12, tw, 24, '#ffffff', color, rx=12, sw=1.2)
    text(cx, y + 5, label, 12, 'bold', color, 'middle')


# ---- canvas, title
out.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
text(40, 46, 'High-level architecture: from SharePoint 2016 workflows to Power Automate', 26, 'bold', '#2c1f63')
text(40, 74, 'Left: what runs today. Right: where each part goes. Middle: what happens to it. Bottom: the pipeline that moves each workflow.', 14, 'normal', '#5f6b7a')

# ---- panels
LX, LW = 30, 520          # today panel
RX, RW = 780, 790         # target panel
PY, PH = 96, 0
PANELS_AT = len(out)
text(LX + 20, PY + 32, 'TODAY', 18, 'bold', '#7b4b3a')
text(LX + 92, PY + 32, 'SharePoint Server 2016 farm, on-premises', 15, 'bold', '#5d4037')
rect(LX + 20, PY + 44, 268, 22, '#fdecea', '#c62828', rx=11, sw=1)
text(LX + 154, PY + 59, 'Out of support since 14 July 2026', 12, 'bold', '#c62828', 'middle')
text(RX + 20, PY + 32, 'TARGET', 18, 'bold', '#0f4c81')
text(RX + 108, PY + 32, 'Microsoft 365 and Power Platform, cloud', 15, 'bold', '#0f4c81')
text(RX + 20, PY + 59, 'Same people and the same data; the logic is rebuilt and proven, then improved.', 12.5, 'normal', '#37474f', italic=True)
text((LX + LW + RX) / 2, PY + 32, 'WHAT HAPPENS', 15, 'bold', '#455a64', 'middle')

# colours
T_FILL, T_STROKE = '#f3eeeb', '#8d6e63'
PA = ('#e3f0fc', '#0f6cbd')        # Power Automate
PAPPS = ('#f3e8fb', '#7a3db8')     # Power Apps
M365 = ('#e8eafc', '#4f52b2')      # Approvals, Teams, Outlook
SPO = ('#e0f4f2', '#03787c')       # SharePoint Online
FND = ('#eef1f5', '#546e7a')       # platform foundation

BX, BW = LX + 20, LW - 40          # today boxes
TX, TW = RX + 20, 470              # target boxes
FX, FW = TX + TW + 20, RW - TW - 60  # foundation column
A1, A2 = BX + BW + 8, TX - 8       # arrow ends

rows = []
y = PY + 84
# Row: people
h = bh(['a', 'b'])
box(BX, y, BW, h, 'People and channels', ['Requesters, approvers, Admin Officers', 'Browser, InfoPath Filler 2013, e-mail'], T_FILL, T_STROKE)
box(TX, y, TW, h, 'People and channels', ['The same people', 'Browser, Microsoft Teams, Outlook, mobile'], *M365)
arrow(A1, A2, y + h / 2, 'same people, new channels')
y += h + 14
# Row: forms
box(BX, y, BW, h, 'InfoPath forms', ['Project Establishment Form (template.xsn)', 'Client-only form, 7 views, 274 rules'], T_FILL, T_STROKE)
box(TX, y, TW, h, 'Power Apps', ['Project Establishment Form as a canvas app', '(demo already in powerapps/pef-canvas-app)'], *PAPPS)
arrow(A1, A2, y + h / 2, 'rebuild as an app')
y += h + 14
# Row: workflows
wf_h = bh(['x'] * 6)
box(BX, y, BW, wf_h, 'Nintex Workflow 2016', [
    'Proposal Approval (195 actions)',
    'PEF approval workflow, Increment Project Number',
    'Child workflows: Check Signatures,',
    '   PROPOSAL CHECKER, Generate PDF',
    'User-defined actions: approval, delegate,',
    '   Admin Officer'], T_FILL, T_STROKE)
box(TX, y, TW, wf_h, 'Power Automate cloud flows', [
    'Proposal Approval main flow (same logic, step by step)',
    'Child flows: Delegate Lookup, Admin Officer Lookup,',
    '   Check Signatures, PROPOSAL CHECKER, Generate PDF',
    'PEF approval and the other rebuilt flows',
    'Approval steps as reusable scopes',
    'Every action named after its Nintex ID'], *PA, tag='solutions')
arrow(A1, A2, y + wf_h / 2, 'rebuild with parity')
y += wf_h + 14
# Row: tasks
box(BX, y, BW, h, 'Nintex task forms', ['Approval tasks and Request Data forms', 'in the Workflow Tasks list'], T_FILL, T_STROKE)
bw3 = (TW - 20) / 3
box(TX, y, bw3, h, 'Approvals', ['approve or', 'reject'], *M365)
box(TX + bw3 + 10, y, bw3, h, 'Teams cards', ['Admin Officer', 'input'], *M365)
box(TX + 2 * (bw3 + 10), y, bw3, h, 'Outlook', ['from a shared', 'mailbox'], *M365)
arrow(A1, A2, y + h / 2, 'replace')
y += h + 14
# Row: e-mail
h1 = bh(['x'])
box(BX, y, BW, h1, 'E-mail', ['Farm default sender (SMTP), Nintex message templates'], T_FILL, T_STROKE)
rect(TX, y, TW, h1, '#ffffff', '#cfd8dc', rx=8, sw=1, dash='5 4')
text(TX + 18, y + 24, 'Sent by Outlook from a shared mailbox (box above)', 13, 'normal', '#455a64')
text(TX + 18, y + 42, 'with the same recipients, subjects and texts', 13, 'normal', '#455a64')
arrow(A1, A2, y + h1 / 2, 'replace')
y += h1 + 14
# Row: data
data_h = bh(['x'] * 4)
box(BX, y, BW, data_h, 'SharePoint 2016 sites and lists', [
    '/Divisions/PDD/Projects: Draft Proposals, Project',
    '   Establishment Forms, Project Numbers, Workflow Tasks',
    '/Divisions: Master Contacts, Master Calendar,',
    '   Clients, Sites, Proposals, Orders'], T_FILL, T_STROKE)
box(TX, y, TW, data_h, 'SharePoint Online', [
    'The same sites, lists, libraries and column names',
    'Draft Proposals with content approval',
    'Master Contacts and Master Calendar for approvers',
    'and delegates'], *SPO)
arrow(A1, A2, y + 38, 'migrate the data')
arrow(A1, A2, y + data_h - 26, 'or: gateway', color='#90a4ae', dash='6 5')
y += data_h + 14
# Row: history
box(BX, y, BW, h1, 'Workflow history', ['Nintex history list on each item'], T_FILL, T_STROKE)
box(TX, y, TW, h1, 'Run history', ['Flow run history, plus an optional history list'], *PA)
arrow(A1, A2, y + h1 / 2, 'archive the old')
last_bottom = y + h1

# ---- foundation column
fy = PY + 84
fh = last_bottom - fy
box(FX, fy, FW, fh, 'Platform foundation', [], *FND)
items = [
    ('Environments', ['Development', '→ Test', '→ Production', 'with a deployment', 'pipeline']),
    ('Solutions', ['flows, settings and', 'connections packaged', 'together']),
    ('Environment variables', ['site addresses,', 'no hard-coded URLs']),
    ('Connection references', ['one service account', 'owns the connections']),
    ('Governance', ['DLP policy, run-only', 'users, monitoring']),
    ('Dataverse', ['stores approvals and', 'solution metadata']),
]
iy = fy + 42
for title, lines in items:
    h = 26 + 17 * len(lines)
    rect(FX + 12, iy, FW - 24, h, '#ffffff', '#b0bec5', rx=6, sw=1)
    text(FX + 22, iy + 19, title, 13, 'bold', '#37474f')
    for i, line in enumerate(lines):
        text(FX + 22, iy + 37 + i * 17, line, 12.5, 'normal', '#455a64')
    iy += h + 10

# gateway note
gy = last_bottom + 26
text(TX, gy, 'Gateway: only if some lists stay on SharePoint 2016 for a while (Premium licences, no Automate menu).', 12, 'normal', '#607d8b', italic=True)

# ---- panels sized to content
PH = gy + 18 - PY
out.insert(PANELS_AT, f'<rect x="{RX}" y="{PY}" width="{RW}" height="{PH}" rx="14" fill="#f6f9fd" stroke="#b8c9dc" stroke-width="1.5"/>')
out.insert(PANELS_AT, f'<rect x="{LX}" y="{PY}" width="{LW}" height="{PH}" rx="14" fill="#fbf7f5" stroke="#cdbdb6" stroke-width="1.5"/>')

# ---- pipeline band
BY = PY + PH + 22
BAND_AT = len(out)
text(50, BY + 30, 'HOW WE GET THERE', 15, 'bold', '#2c1f63')
text(230, BY + 30, 'the conversion pipeline: every workflow goes through stages 0 to 8', 13, 'normal', '#5f6b7a')
stages = [
    ('0', 'Prepare the platform', 'once'), ('1', 'Discover', 'once'), ('2', 'Triage and plan', 'once'),
    ('3', 'Export and analyse', 'each'), ('4', 'Design', 'each'), ('5', 'Build', 'each'),
    ('6', 'Prove parity', 'each'), ('7', 'Go live', 'each'), ('8', 'Operate and improve', 'after'),
]
colors = {'once': ('#e3f2fd', '#1565c0'), 'each': ('#ede7f6', '#5e35b1'), 'after': ('#e8f5e9', '#2e7d32')}
cx0, cw, gap = 50, 154, 14
cy = BY + 48
for i, (n, name, grp) in enumerate(stages):
    x = cx0 + i * (cw + gap)
    f, s = colors[grp]
    rect(x, cy, cw, 54, f, s, rx=8, sw=1.6)
    text(x + cw / 2, cy + 22, n, 14, 'bold', s, 'middle')
    text(x + cw / 2, cy + 41, name, 12.5, 'bold', '#1f2933', 'middle')
    if i < len(stages) - 1:
        out.append(f'<line x1="{x + cw + 1}" y1="{cy + 27}" x2="{x + cw + gap - 2}" y2="{cy + 27}" stroke="#78909c" stroke-width="1.8" marker-end="url(#arrs)"/>')
legend_y = cy + 80
for i, (grp, label) in enumerate([('once', 'once, for the whole estate'), ('each', 'for each workflow, wave by wave'), ('after', 'after go-live')]):
    f, s = colors[grp]
    lx = 50 + i * 260
    rect(lx, legend_y - 12, 16, 16, f, s, rx=3, sw=1.4)
    text(lx + 24, legend_y + 1, label, 12.5, 'normal', '#37474f')
text(840, legend_y + 1, 'Tools: nwf-decode (reads Nintex exports) · analysis document · rebuild guide · parity test plan', 12.5, 'normal', '#37474f')

H = legend_y + 26 + 20
out.insert(BAND_AT, f'<rect x="30" y="{BY}" width="{W - 60}" height="{legend_y + 26 - BY}" rx="14" fill="#fafafa" stroke="#cfd8dc" stroke-width="1.5"/>')
out[0] = f'<rect width="{W}" height="{H}" fill="#ffffff"/>'
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       '<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
       '<path d="M0,0 L10,5 L0,10 z" fill="#455a64"/></marker>'
       '<marker id="arrs" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
       '<path d="M0,0 L10,5 L0,10 z" fill="#78909c"/></marker></defs>' + ''.join(out) + '</svg>')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migration-architecture.svg'), 'w', encoding='utf-8').write(svg)
print('svg written', W, H, 'content bottom', y + 50, 'band top', BY)
