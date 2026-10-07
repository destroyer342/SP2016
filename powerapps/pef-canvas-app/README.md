# PEF canvas app (Power Apps YAML)

A modern Power Apps **canvas app** that recreates the InfoPath **Project Establishment Form** ([`template.xsn`](../../template.xsn), analysed in [`docs/template-xsn.md`](../../docs/template-xsn.md)), written in Power Apps YAML (pa-yaml) using the **Parker** skill ([`skills/parker`](../../skills/parker)).

It is a **demo**:

- All data is mock data loaded in `App.OnStart`.
- The logic is Power Fx written for demonstration.
- It does not connect to SharePoint, Dataverse, Nintex or any other service.

![InfoPath Cover Page that this app recreates](../../docs/infopath%20ui.png)

---

## What is in this folder

| Path | What it is |
|---|---|
| `App.pa.yaml` | `App.OnStart`: demo data, lookup tables, the sample PEF and global variables |
| `screens/*.pa.yaml` | One file per screen (10 screens), each with root `Screens:` |
| `DESIGN.md` | Binding spec: controls, naming, tokens, layout grid, data model, canonical Power Fx snippets |
| `tools/gen_chrome.py` | Generates the shared app bar, project bar and tab bar, and checks that no screen's copy has drifted (`--check`) |
| `tools/check_app.py` | Cross-screen checks, plus Parker's `validate.py` on every screen |

---

## Screens

| # | Screen | Replaces (InfoPath) | Purpose |
|---|---|---|---|
| 1 | `scrDashboard` | Form library view | Register of PEFs: KPIs by status, search, filters, open or create a PEF |
| 2 | `scrCoverPage` | Cover Page view | Main form: identification and numbering, classification, details, people, dates and pricing, client/proposals/orders, milestones, deliverables, planned costs, service SBUs, checker, extend/close |
| 3 | `scrHoursCosts` | Hours And Costs view | Staff hours by grade and FY rates, running costs, contingency and warranty (amount or %), totals |
| 4 | `scrMotivations` | Motivations view | Motivation per revision (latest editable), project attachments |
| 5 | `scrRevisions` | Revisions view | Latest vs original, last 5 revisions, revision details |
| 6 | `scrApprovals` | Approval sections on the Cover Page | Approval route (Checker → Head → Divisional Manager → General Manager), delegates, approve/reject with comments, history |
| 7 | `scrReview` | PrintView + Start Approval gate | Validation checklist with *Go to* links, read-only summary, **Submit for approval**, Print |
| 8 | `scrClosure` | Closure view | Closure motivation, original/final/actual comparison with increases, deliverables achieved |
| 9 | `scrConfirmation` | (new) | Result of submitting, next approver, next steps |
| 10 | `scrDetailedInfo` | Detailed Information view | Troubleshooting view for administrators |

All form screens share the same chrome:

- **App bar:** brand, title, the *View as* role switcher, and the avatar.
- **Project bar:** number, title, division, status badge, revision and workflow state.
- **Tab bar:** the tabs, plus *Cancel Approval*, *Save PEF* and *Start Approval*.

---

## Importing into Power Apps Studio

Studio is the only renderer for pa-yaml. It reconciles control `@version`s when you paste.

1. Create a blank **Tablet** canvas app (1366 × 768).
2. **App → OnStart:** copy the formula from `App.pa.yaml` (everything after `OnStart: |-`, starting with `=`) into the App's `OnStart` property, then choose **Run OnStart**.
3. For each file in `screens/`, in numeric order, open it, copy its contents, then in Studio's **Tree view** right-click → **Paste** (Paste code). Each paste creates one screen with all its controls.
4. Delete the default `Screen1`, and move `scrDashboard` to the top so it is the start screen.
5. Play the app.

The input controls (`Classic/TextInput`, `Classic/DropDown`, `Classic/ComboBox`, `Classic/DatePicker`, `Classic/CheckBox`, `Classic/Radio`, `Classic/Toggle`) are **not** in Parker's proven control set. Check them on the first paste and accept Studio's version reconciliation if it prompts. See `DESIGN.md` §2.1 for why Classic inputs were chosen over Fluent (modern) controls.

---

## Demo walkthrough

1. **Dashboard:** filter by status with the KPI cards or chips, search, then **Open** `ADE-52705` (the sample, in Draft).
2. **Cover Page:**
   - Change **Revenue Stream**; the package code, project number, service profit, work package and client price follow, as in the InfoPath rules.
   - Tick **Create Project Site**: a research project now correctly gets a *ResearchProjects* site link (the InfoPath bug in [docs §16](../../docs/template-xsn.md#16-findings-bugs-risks-and-clean-up) is fixed).
3. **Hours & Costs:** add a staff line, pick a grade and FY (the rate is looked up), enter hours, and watch the totals and the Cover Page pricing recalculate.
4. **Review & Submit:** see the validation checklist. Fix any issue with **Go to**, then **Submit for approval** to land on the confirmation screen.
5. **Approvals:**
   - Switch **View as** to *Head*, add a comment and **Approve**. Then switch to *Divisional Manager* and approve.
   - Commercial projects also go to the *General Manager*. **Reject** requires a reason.
6. Once approved, tick **Extend Project** (a new revision) or **Close Project** (the Closure tab appears) as the applicant.
7. Switch **View as** to *Administrator* and use the settings icon to open **Detailed information**.

---

## Demo logic vs production

| Area | In this demo | In production |
|---|---|---|
| Data | Collections created in `App.OnStart` | SharePoint lists or Dataverse tables (the lists the InfoPath form queried: Master Contacts, Activity Rates, Project Numbers, PICs, Proposals, Orders, …) |
| Save / submit | `colPEFs` register row (`S_UPSERT`) | `Patch` to a list or table |
| Approvals | `colApprovals` state machine (`S_APPROVE` / `S_REJECT`) | Power Automate approvals (replacing the Nintex workflow) |
| Current user | *View as* switcher (`gblRole`) | `User()` and Entra ID / Office 365 Users |
| Project numbers | Next sequence from the register | A transactional counter (fixes the duplicate-number risk in docs §16) |
| Attachments | Mock file rows | Attachments control / SharePoint document library |
| Print | `Print()` on Review & Submit | Same, or a PDF from Power Automate |

When opened from the register, every PEF reuses the sample line items (staff, costs, milestones and so on), so the demo stays small. Only the header fields differ per PEF.

---

## Validation

Run these before committing any change:

```bash
python3 tools/check_app.py        # cross-screen checks + Parker validate.py on every screen
python3 tools/gen_chrome.py --check
```

Parker's validator on its own: `python3 ../../skills/parker/validate.py screens/<file>.pa.yaml`.
