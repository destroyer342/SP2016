# PEF Canvas App: design spec

This is the single source of truth for building and maintaining the Power Apps canvas app that recreates the InfoPath **Project Establishment Form** (`template.xsn`, analysed in [`docs/template-xsn.md`](../../docs/template-xsn.md)). Every screen file must follow it. The authoring rules come from the **Parker** skill ([`skills/parker/SKILL.md`](../../skills/parker/SKILL.md)).

---

## 1. Files

| File | Contents |
|---|---|
| `App.pa.yaml` | `App.OnStart`: all demo data, lookup tables and global variables |
| `screens/01-scrDashboard.pa.yaml` | PEF register (landing) |
| `screens/02-scrCoverPage.pa.yaml` | Cover Page (main form) |
| `screens/03-scrHoursCosts.pa.yaml` | Hours & Costs |
| `screens/04-scrMotivations.pa.yaml` | Motivations & attachments |
| `screens/05-scrRevisions.pa.yaml` | Revision history |
| `screens/06-scrApprovals.pa.yaml` | Approval chain and actions |
| `screens/07-scrReview.pa.yaml` | Review & Submit (validation + summary, replaces PrintView) |
| `screens/08-scrClosure.pa.yaml` | Project closure |
| `screens/09-scrConfirmation.pa.yaml` | Confirmation after submit |
| `screens/10-scrDetailedInfo.pa.yaml` | Detailed Information (diagnostics) |
| `tools/check_app.py` | Cross-screen checks (unique names, known variables/fields, bracket balance) + runs Parker's `validate.py` |

Each screen file has the root `Screens:` with exactly one screen, the same shape as Parker's worked example.

---

## 2. Control vocabulary

Use **only** these control types and versions.

| Purpose | Control | Notes |
|---|---|---|
| Region / card / wrapper | `GroupContainer@1.5.0` (`Variant: ManualLayout`) | Proven (Parker) |
| Text | `Label@2.5.1` | Proven |
| Text button, badge, chip, tab, link, avatar | `Classic/Button@2.2.0` | Proven |
| Icon button / glyph | `Classic/Icon@2.5.0` | Proven |
| Repeating rows | `Gallery@2.15.0` (`Variant: Vertical`) | Proven |
| Scroll viewport + tall card | `FluidGrid@2.3.0` → `DataCard@1.0.2` | Proven (Parker scroll idiom) |
| Hairline / divider / stripe | `Rectangle@2.3.0` | Proven |
| Single-line / multi-line text input | `Classic/TextInput@2.3.2` | Input control, not in Parker's proven list (see §2.1) |
| Single choice from a list | `Classic/DropDown@2.3.1` | Input control (see §2.1) |
| Multi-select / searchable people & items | `Classic/ComboBox@2.4.0` | Input control (see §2.1) |
| Date | `Classic/DatePicker@2.6.0` | Input control (see §2.1) |
| Yes/no flag | `Classic/CheckBox@2.1.0` | Input control (see §2.1) |
| Mutually exclusive options | `Classic/Radio@2.3.0` | Input control (see §2.1) |
| On/off switch | `Classic/Toggle@2.1.0` | Input control (see §2.1) |

### 2.1 Why Classic inputs

Parker's proven set has no input controls, and it warns that modern (Fluent) controls such as `ModernButton` can render blank and that their `@version`s are not portable. The app is a working demo that needs real data entry, so it uses the **Classic** input family, which uses the same property model as the proven `Classic/Button`. The modern look comes from styling (flat fills, 4 px radius, Segoe UI, Fluent-like palette) instead of from Fluent controls. Studio reconciles `@version`s on import. Verify these input controls on the first paste.

### 2.2 Allowed `Icon.*` names

`Add`, `Trash`, `Edit`, `Cancel`, `Check`, `ChevronDown`, `ChevronUp`, `ChevronLeft`, `ChevronRight`, `Reload`, `Print`, `Lock`, `Download`, `Mail`, `Document`, `DocumentPDF`, `DocumentWithContent`, `CalendarBlank`, `Clock`, `People`, `Person`, `Home`, `Settings`, `Search`, `Hamburger`, `Information`, `Warning`, `Error`, `Post`, `Trending`, `DetailList`, `Message`.

Never use `Icon.Documents`; it does not exist.

---

## 3. Naming

- Screens: `scr<Name>`.
- Controls: `<prefix><Tag><Name>`, where `<Tag>` is the screen tag. Control names are app-wide and must be **unique across all screens**.

| Screen | Tag |
|---|---|
| `scrDashboard` | `Dsh` |
| `scrCoverPage` | `Cvr` |
| `scrHoursCosts` | `Hrs` |
| `scrMotivations` | `Mot` |
| `scrRevisions` | `Rev` |
| `scrApprovals` | `Apr` |
| `scrReview` | `Rvw` |
| `scrClosure` | `Cls` |
| `scrConfirmation` | `Cnf` |
| `scrDetailedInfo` | `Dbg` |

| Prefix | Control |
|---|---|
| `con` | GroupContainer |
| `lbl` | Label |
| `btn` | Classic/Button |
| `ico` | Classic/Icon |
| `gal` | Gallery |
| `rec` | Rectangle |
| `fgd` | FluidGrid |
| `dcd` | DataCard |
| `txt` | Classic/TextInput |
| `drp` | Classic/DropDown |
| `cmb` | Classic/ComboBox |
| `dte` | Classic/DatePicker |
| `chk` | Classic/CheckBox |
| `rad` | Classic/Radio |
| `tgl` | Classic/Toggle |

Examples: `conCvrSecIdentity` (section card), `conCvrFldProjectTitle` (field wrapper), `lblCvrProjectTitle`, `txtCvrProjectTitle`, `galHrsStaff`, `btnRvwSubmit`.

Global variables use `gbl…`; collections use `col…`. Only use the names defined in §6.

---

## 4. Design tokens

Write colours as literal `RGBA(...)` values exactly as listed (Parker: reuse tokens exactly).

| Token | Value | Use |
|---|---|---|
| Page | `RGBA(243, 245, 248, 1)` | Screen `Fill` |
| Surface | `RGBA(255, 255, 255, 1)` | Cards, bars |
| AppBar | `RGBA(16, 42, 67, 1)` | Top app bar |
| Primary | `RGBA(0, 94, 162, 1)` | Primary buttons, active tab, links, section titles accent |
| PrimaryHover | `RGBA(0, 76, 132, 1)` | Primary button hover |
| PrimaryTint | `RGBA(229, 241, 250, 1)` | Hover on secondary buttons, info backgrounds, table header |
| Brand red | `RGBA(200, 16, 46, 1)` | Brand mark, required-field asterisk, danger |
| BrandRedHover | `RGBA(168, 12, 38, 1)` | Brand hover |
| Heading text | `RGBA(16, 42, 67, 1)` | Section titles, page titles |
| Text | `RGBA(32, 31, 30, 1)` | Body, inputs |
| Muted text | `RGBA(96, 94, 92, 1)` | Field labels, hints, captions |
| On-dark text | `RGBA(255, 255, 255, 1)` | Text on AppBar / primary |
| On-dark muted | `RGBA(190, 204, 219, 1)` | Secondary text on AppBar |
| Border | `RGBA(200, 205, 214, 1)` | Input borders |
| Hairline | `RGBA(229, 231, 235, 1)` | Dividers, table row lines |
| Stripe | `RGBA(249, 250, 251, 1)` | Zebra rows, read-only value boxes |
| Error | `RGBA(196, 30, 58, 1)` | Validation borders and messages |
| ErrorTint | `RGBA(253, 231, 233, 1)` | Error banner background |
| Success | `RGBA(16, 124, 16, 1)` | Success text |
| SuccessTint | `RGBA(223, 246, 221, 1)` | Success background |
| Warning | `RGBA(138, 90, 0, 1)` | Warning text |
| WarningTint | `RGBA(255, 244, 206, 1)` | Warning background |
| Neutral | `RGBA(96, 94, 92, 1)` | Neutral badge text |
| NeutralTint | `RGBA(237, 235, 233, 1)` | Neutral badge background |

**Typography:** `Font: =Font.'Segoe UI'` on every Label, input and button.

| Element | Size and weight |
|---|---|
| Page title | `Size: =18`, `FontWeight.Semibold` |
| Section title | `Size: =13`, `FontWeight.Semibold`, heading colour |
| Field label | `Size: =10`, `FontWeight.Semibold`, muted colour |
| Body text and inputs | `Size: =11` |
| Captions and hints | `Size: =9` |
| Table header | `Size: =10`, `FontWeight.Semibold` |

**Shape:** cards radius 8, inputs and buttons radius 4, pills and badges radius 12.

### 4.1 Status badges

A `Classic/Button` with `DisplayMode: =DisplayMode.View` and `HoverFill: =Self.Fill`, radius 12, `Size: =10`, `FontWeight.Semibold`.

PEF status (`Draft`, `Pending Approval`, `Approved`, `Rejected`, `Closed`):

```
Fill: =Switch(<status>, "Approved", RGBA(223, 246, 221, 1), "Pending Approval", RGBA(255, 244, 206, 1), "Rejected", RGBA(253, 231, 233, 1), "Closed", RGBA(229, 241, 250, 1), RGBA(237, 235, 233, 1))
Color: =Switch(<status>, "Approved", RGBA(16, 124, 16, 1), "Pending Approval", RGBA(138, 90, 0, 1), "Rejected", RGBA(196, 30, 58, 1), "Closed", RGBA(0, 94, 162, 1), RGBA(96, 94, 92, 1))
```

Approval-step status (`Not started`, `Waiting`, `Pending`, `Approved`, `Rejected`, `Not required`) uses the same pattern: Approved is green, Pending is amber, Rejected is red, Waiting is blue (PrimaryTint / Primary), and Not started / Not required are neutral.

### 4.2 Buttons

All buttons are `Classic/Button`, `Height: =32`, radius 4, `Size: =11`, `FontWeight.Semibold`.

| Kind | Fill | Color | HoverFill | Border |
|---|---|---|---|---|
| Primary | Primary | On-dark | PrimaryHover | `BorderThickness: =0` |
| Secondary | Surface | Primary | PrimaryTint | `BorderColor: =RGBA(0, 94, 162, 1)`, `BorderThickness: =1` |
| Danger | Surface | Error | ErrorTint | `BorderColor: =RGBA(196, 30, 58, 1)`, `BorderThickness: =1` |
| Link | `RGBA(0, 0, 0, 0)` | Primary | PrimaryTint | `BorderThickness: =0`, `Align: =Align.Left` |

---

## 5. Layout

- Design size 1366 × 768 (tablet landscape). Everything is responsive through `Parent.Width` / `Parent.Height`.
- **No horizontal `FillPortions`.** Columns are `Parent.Width * fraction` or `(Parent.Width - gaps) / n` with explicit `X`.

### 5.1 Form-screen chrome (generated, do not edit by hand)

Every form screen (`Cvr`, `Hrs`, `Mot`, `Rev`, `Apr`, `Rvw`, `Cls`) gets the same three bars from `tools/gen_chrome.py`. They are emitted **after** the scrolling body so that they render on top.

| Bar | Y | Height | Contents |
|---|---|---|---|
| `con<Tag>AppBar` | 0 | 48 | Brand button (→ Dashboard), app title, "View as" role switcher, diagnostics icon (Administrator only), avatar |
| `con<Tag>ProjectBar` | 48 | 64 | Project number, title, division · group · revenue stream, status badge, revision, workflow state |
| `con<Tag>TabBar` | 112 | 48 | Tabs (Cover Page, Hours & Costs, Motivations, Revisions, Approvals, Review & Submit, Closure*) and commands (Cancel Approval*, Save PEF, Start Approval*) |

`*` = conditional. Body: `fgd<Tag>Body` (FluidGrid) at `Y: =160`, `Height: =Parent.Height - 160`, holding `dcd<Tag>Body` (DataCard). The DataCard's fixed `Height` must be ≥ the bottom of its lowest child + 24.

Tabs are live tap targets (Parker): every tab, including the active one, keeps `DisplayMode` Edit and its `Navigate` `OnSelect`. The active tab is marked by Primary text and a 3 px underline (`rec<Tag>TabIndicator`). **Start Approval** in the tab bar opens `scrReview`, which is the validation gate. **Save PEF** runs `S_SAVE`, and **Cancel Approval** runs `S_CANCEL_APPROVAL`.

`scrDashboard`, `scrConfirmation` and `scrDetailedInfo` get the App bar only (`con<Tag>AppBar`, Y 0 to 48). Their body starts at `Y: =48`. They may use their own `FluidGrid` → `DataCard` if the body is taller than the screen.

Regenerate or verify the chrome with `python tools/gen_chrome.py --check`. Never hand-edit the chrome; change `gen_chrome.py` and regenerate instead.

### 5.2 Body grid (inside `dcd<Tag>Body`)

- **Content column:** `X: =24`, `Width: =Parent.Width - 48`. Stack cards vertically with a 16 px gap and fixed `Y` values.
- **Section card:** `GroupContainer` ManualLayout, `Fill: =RGBA(255, 255, 255, 1)`, radius 8, `BorderStyle: =BorderStyle.None`, `DropShadow: =DropShadow.Light` (a real elevated surface).
  - Title label at `X: =16`, `Y: =12`, `Height: =24`.
  - Optional hint at `Y: =36`, `Height: =18`.
  - Hairline `Rectangle` at `Y: =48`, `Height: =1`, `X: =16`, `Width: =Parent.Width - 32`.
  - First field row at `Y: =60`.
- **Field wrapper:** `con<Tag>Fld<Name>`, ManualLayout, no `Fill`, `BorderStyle: =BorderStyle.None`, `DropShadow: =DropShadow.None`, `Height: =64`.
  - Label at `X: =0`, `Y: =0`, `Width: =Parent.Width`, `Height: =20`.
  - Input at `X: =0`, `Y: =24`, `Width: =Parent.Width`, `Height: =36`.
  - Add 20 px (`Height: =84`) when the field shows an inline error label at `Y: =62`, `Height: =18`.
- **Columns inside a card (16 px padding, 16 px gutter):**

| Columns | Width | X of column `i` (0-based) |
|---|---|---|
| 2 | `(Parent.Width - 48) / 2` | `16 + i * ((Parent.Width - 48) / 2 + 16)` |
| 3 | `(Parent.Width - 64) / 3` | `16 + i * ((Parent.Width - 64) / 3 + 16)` |
| 4 | `(Parent.Width - 80) / 4` | `16 + i * ((Parent.Width - 80) / 4 + 16)` |

- **Row pitch:** 72 px (64 field + 8 gap), so rows are at `Y` = 60, 132, 204, …
- **Required fields:** label text ends with `" *"`.
- **Inline validation:** when `gblShowErrors` is true and the value is missing, the input's `BorderColor` turns Error and an error label appears.
- **Read-only values** (calculated): a `Label` with `Fill` Stripe, `PaddingLeft: =8`, radius not available, height 36, `Align.Right` for money.

### 5.3 Tables and repeating rows (Parker responsive-table pattern)

- The header row is a `GroupContainer` with `Fill` PrimaryTint, `Height: =36`, and header labels placed by `Parent.Width * fraction`.
- The `Gallery` rows use **the same fractions** of `Parent.TemplateWidth`.
- Any `Classic/*` control inside a gallery (inputs, buttons, icons, badges) sits in a transparent wrapper `GroupContainer` positioned by `Parent.TemplateWidth * fraction`. The control itself uses a fixed `X` (for example 4) and `Width: =Parent.Width - 8`.
- Row separator: `Rectangle` `Height: =1`, `Y: =Parent.TemplateHeight - 1`, `Width: =Parent.TemplateWidth`, `Fill` Hairline.
- **Add row:** a secondary `Classic/Button` with "+ Add …" below the gallery, using `Collect(col…, {ID: Coalesce(Max(col…, ID), 0) + 1, …})`.
- **Delete row:** `Classic/Icon` `Icon.Trash` in the last column with `Remove(col…, ThisItem)`.
- **Edit a cell:** `OnChange` → `Patch(col…, ThisItem, {Field: …})`, then the recalculation snippet `S_RECALC` if the field affects costs.
- **Empty state:** a centered muted Label when `CountRows(...) = 0`.
- Size the gallery to show all rows, with no inner scroll: `Height: =Max(1, CountRows(<items>)) * TemplateSize`. Inside a card, the card grows with it: card `Height` = fixed part + gallery height. When the content height is dynamic, give the DataCard `Height` enough headroom for the sample data plus about 6 extra rows.

### 5.4 YAML rules (Parker)

- Any formula containing `: ` (colon + space, for example a record `{A: 1}`), ` #` or a line break **must** be a block scalar:

  ```yaml
  OnSelect: |-
    =Set(gblPEF, Patch(gblPEF, {Extend: true}))
  ```

- 2-space indentation. A list item `- name:` sits at its parent key's indent + 2, and the item's keys at the item's indent + 4 (copy the skeleton's indentation exactly).
- Every `GroupContainer` has `BorderStyle: =BorderStyle.None`.
  - A wrapper with no `Fill` also has `DropShadow: =DropShadow.None`.
  - Cards with a solid `Fill` have `DropShadow: =DropShadow.Light` (elevated) or `=DropShadow.None` (bars).
  - Never write `Fill: =RGBA(0,0,0,0)` on a `GroupContainer`.
- Never put an `OnSelect` on a `Label`. Clickable text is a `Classic/Button`; icon-only actions use `Classic/Icon`.
- No `Classic/*` control may reference `Parent.TemplateWidth` in `X`, `Y`, `Width` or `Height`.
- A child of a ManualLayout container must fit: `Y + Height ≤` the parent's `Height`.

---

## 6. Data model (defined in `App.OnStart`)

### 6.1 Session and state variables

| Variable | Type | Meaning |
|---|---|---|
| `gblDemoLoaded` | Boolean | OnStart has run |
| `gblRole` | Text | Simulated user role (one of `colRoles`) |
| `gblEditMode` | DisplayMode | `Edit` for the applicant on a Draft/Rejected PEF, otherwise `View` (see `S_EDITMODE`) |
| `gblShowErrors` | Boolean | Show inline validation (set after a failed submit) |
| `gblPEF` | Record | The PEF being edited (fields in §6.2) |
| `gblSamplePEF` | Record | Fully populated sample (ADE-52705) |
| `gblNewPEF` | Record | Blank template for **New PEF** |
| `gblTotals` | Record | Calculated totals (see `S_RECALC`): `Labour`, `OPEX`, `CarryOver`, `PlannedCosts`, `Contingency`, `ContingencyPctEff`, `Warranty`, `WarrantyPctEff`, `ControllingCosts`, `ServiceCosts`, `ServiceRevenue`, `ProjectCost`, `ClientPrice`, `Profit`, `ProfitPct`, `ControllingRevenue`, `ControllingProfitPct`, `ServiceProfitPct`, `IsCommercial` |
| `gblActuals` | Record | Closure actuals: `ClientPrice`, `ProjectCost`, `Labour`, `OPEX`, `Contingency`, `Warranty`, `ServiceSBUs`, `ExchangeRate`, `StartDate`, `EndDate` |
| `gblSampleActuals`, `gblBlankActuals` | Record | Same shape as `gblActuals` |
| `gblConfirmation` | Record | `{Title, Message, Kind}` for `scrConfirmation`, where `Kind` is `"Success"`, `"Warning"` or `"Info"` |
| `gblSelectedSBU` | Number | `ID` of the service SBU selected on the Cover Page |

### 6.2 `gblPEF` fields

| Field | Type | InfoPath source |
|---|---|---|
| `ProjectNo` | Text | `Required_Fields/Project_No.` |
| `SequenceNo` | Text | `Sequencel_No.` |
| `AutoProjectNo` | Boolean | `Div_Short_Code` ("Automated Project No.") |
| `PackageCode` | Text | `Cover_Page/Package_Code` |
| `Division`, `DivisionCode`, `DivisionalGroup` | Text | Division header, `Division_Code`, `Required_Fields/Divisions` |
| `RevenueStream` | Text | `Revenue_Stream` |
| `PIC` | Text | `PIC_Number` |
| `SalesGroup` | Text | `Cover_Page/Sales_Group` |
| `CostCentre`, `WorkCentre` | Text | `Cost_Centre`, `Work_Centre` |
| `WorkPackage`, `Equipment` | Text | `Cover_Page/Work_Package`, `Equipment` |
| `CreateProjectSite` | Boolean | `Project_Size` = Large |
| `ProjectSiteUrl` | Text | `Project_Site_Link` |
| `ProjectTitle` | Text | Max 40 characters (SAP limit) |
| `Description` | Text | `Project_Description` |
| `Extend`, `Close`, `CheckerRequired` | Boolean | Flags |
| `Checker`, `CheckerPosition`, `CheckerMintekNo` | Text | `group41` |
| `AdminOfficer`, `ResponsiblePerson`, `CIMintekNo`, `Head`, `HeadMintekNo`, `DivisionalManager`, `GeneralManager` | Text | People |
| `StartDate`, `EndDate` | Date | |
| `ClientPriceInput` | Number | Client price typed in (commercial streams only) |
| `ServiceSBURequired` | Boolean | `Cover_Page/ServiceSBU` |
| `ServiceProfit` | Number | 0.1 for research streams, 0.2 for commercial |
| `CarryOverLabour` | Number | |
| `ContingencyByPercent`, `WarrantyByPercent` | Boolean | Option "Use percentage" |
| `ContingencyPct`, `ContingencyAmount`, `WarrantyPct`, `WarrantyAmount` | Number | Percentages are fractions (0.05 = 5 %) |
| `ClientName`, `SiteName`, `Currency` | Text | |
| `OrderValue`, `ExchangeRate` | Number | |
| `ProjectType`, `Location`, `Risks` | Text | |
| `Status` | Text | `Draft`, `Pending Approval`, `Approved`, `Rejected`, `Closed` |
| `WorkflowState` | Text | Free text, mirrors InfoPath `Workflow_State` |
| `Submitted` | Boolean | |
| `RevisionNo` | Number | |
| `Created` | Date | |
| `Modified` | DateTime | |
| `ClosureDescription` | Text | |

### 6.3 Lookup collections (read-only)

| Collection | Columns |
|---|---|
| `colRoles` | `Value` (role name) |
| `colRolePeople` | `Role`, `Person`, `Initials`, `Position` |
| `colDivisionInfo` | `DivisionalGroup`, `Division`, `DivisionCode`, `Prefix`, `CostCentre`, `WorkCentre`, `Head`, `HeadMintekNo`, `Manager`, `GeneralManager`, `AdminOfficer` |
| `colRevenueStreams` | `Title`, `Letter`, `ServiceProfit`, `IsCommercial` |
| `colSalesGroups` | `Value` (Z01 … Z15, exact InfoPath list) |
| `colWorkPackages` | `Value` |
| `colPICs` | `Title`, `Url` |
| `colPeople` | `Name`, `MintekNo`, `Position`, `DivisionalGroup` |
| `colGradeRates` | `Grade`, `ActivityType`, `FinancialYear`, `Rate` |
| `colFinancialYears` | `Value` |
| `colCostElements` | `Title`, `CostElement` |
| `colProducts` | `Value` |
| `colCurrencies` | `Value` |
| `colProposals` | `ProposalNo`, `Title`, `Client`, `Site`, `Value`, `Division` |
| `colOrders` | `OrderNo`, `Title`, `Client`, `ProposalNo`, `Value`, `Currency`, `ExchangeRate` |
| `colDelegations` | `Role`, `Delegate`, `FromDate`, `ToDate` (Master Calendar) |
| `colServiceDivisions` | `Division`, `Head`, `CI` (service SBUs that can be added on the Cover Page) |

For dropdowns over a column, use `Items: =Distinct(<collection>, <Column>)` and read `Self.Selected.Value`. For `Value` collections, use `Items: =<collection>`.

### 6.4 Working collections (editable line items)

| Collection | Columns |
|---|---|
| `colPEFs` | `ProjectNo`, `ProjectTitle`, `Division`, `DivisionalGroup`, `RevenueStream`, `ResponsiblePerson`, `ProjectCost`, `ClientPrice`, `Status`, `WorkflowState`, `StartDate`, `EndDate`, `RevisionNo`, `Modified` (the register) |
| `colStaff` | `ID`, `Grade`, `StaffInvolved`, `Comments`, `FinancialYear`, `CostCentre`, `ActivityType`, `Rate`, `Hours`, `Cost` |
| `colRunningCosts` | `ID`, `Description`, `CostElementTitle`, `CostElement`, `Amount` |
| `colMilestones` | `ID`, `Milestone`, `BillPct` (fraction), `TargetDate` |
| `colServiceSBUs` | `ID`, `Division`, `SBUHead`, `SBUCI`, `Cost`, `DeliveryDate`, `Description`, `Approval`, `ApprovedBy`, `ApprovalDate` |
| `colSBUServices` | `ID`, `SBUID`, `Description`, `Amount` (service lines per SBU) |
| `colDeliverables` | `No`, `Original`, `Final`, `Achieved`, `Comment` |
| `colMotivations` | `RevNo`, `RevDate`, `Motivation` |
| `colAttachments` | `FileNo`, `FileName`, `FileSize`, `UploadedBy`, `Uploaded` |
| `colRevisions` | `Rev` (0 = Original), `RevDate`, `ClientPrice`, `ProjectCost`, `Labour`, `OPEX`, `Contingency`, `Warranty`, `ServiceSBUs`, `Profit`, `ProfitPct`, `ExchangeRate`, `StartDate`, `EndDate`, `ProjectType`, `Location`, `Risks`, `Deliverables` |
| `colApprovals` | `Step`, `Role`, `Approver`, `Required`, `Status`, `ActionDate`, `ActedBy`, `Comments` |
| `colNotifiers` | `Value` (selected names) |
| `colSelectedProducts`, `colSelectedProposals`, `colSelectedOrders` | `Value` |

Each working collection has a sample copy named `colSample<Name>` (for example `colSampleStaff`) that is used to reload demo data.

---

## 7. Canonical Power Fx snippets

Paste these **verbatim** wherever the spec calls for them. They are referenced as `S_…`. When you combine snippets, separate them with `;`.

### S_RECALC

Recalculate the totals. Run it in every form screen's `OnVisible` and after any change that affects costs: staff lines, running costs, carry-over, contingency and warranty, revenue stream, client price, service SBUs and Service SBU Required.

```
Set(gblTotals, With({lab: Sum(colStaff, Cost), opx: Sum(colRunningCosts, Amount), svc: If(gblPEF.ServiceSBURequired, Sum(colServiceSBUs, Cost), 0), com: gblPEF.RevenueStream in ["Cash", "Products and Services"]}, With({base: lab + opx + gblPEF.CarryOverLabour}, With({cont: If(gblPEF.ContingencyByPercent, base * gblPEF.ContingencyPct, gblPEF.ContingencyAmount), warr: If(gblPEF.WarrantyByPercent, base * gblPEF.WarrantyPct, gblPEF.WarrantyAmount)}, With({ctrl: base + cont + warr, svcRev: svc * (1 + gblPEF.ServiceProfit)}, With({cost: ctrl + svc}, With({price: If(com, gblPEF.ClientPriceInput, cost * 1.1)}, {Labour: lab, OPEX: opx, CarryOver: gblPEF.CarryOverLabour, PlannedCosts: base, Contingency: cont, ContingencyPctEff: If(base > 0, cont / base, 0), Warranty: warr, WarrantyPctEff: If(base > 0, warr / base, 0), ControllingCosts: ctrl, ServiceCosts: svc, ServiceRevenue: svcRev, ProjectCost: cost, ClientPrice: price, Profit: price - cost, ProfitPct: If(cost > 0, price / cost - 1, 0), ControllingRevenue: price - svcRev, ControllingProfitPct: If(ctrl > 0, (price - svcRev) / ctrl - 1, 0), ServiceProfitPct: gblPEF.ServiceProfit, IsCommercial: com})))))))
```

### S_EDITMODE

```
Set(gblEditMode, If(gblRole = "Applicant (CI)" && gblPEF.Status in ["Draft", "Rejected"], DisplayMode.Edit, DisplayMode.View))
```

### S_UPSERT

Write the register row for the current PEF.

```
With({r: {ProjectNo: gblPEF.ProjectNo, ProjectTitle: gblPEF.ProjectTitle, Division: gblPEF.Division, DivisionalGroup: gblPEF.DivisionalGroup, RevenueStream: gblPEF.RevenueStream, ResponsiblePerson: gblPEF.ResponsiblePerson, ProjectCost: gblTotals.ProjectCost, ClientPrice: gblTotals.ClientPrice, Status: gblPEF.Status, WorkflowState: gblPEF.WorkflowState, StartDate: gblPEF.StartDate, EndDate: gblPEF.EndDate, RevisionNo: gblPEF.RevisionNo, Modified: Now()}}, If(IsBlank(LookUp(colPEFs, ProjectNo = gblPEF.ProjectNo)), Collect(colPEFs, r), Patch(colPEFs, LookUp(colPEFs, ProjectNo = gblPEF.ProjectNo), r)))
```

### S_SAVE

The **Save PEF** button.

```
<S_RECALC>;
Set(gblPEF, Patch(gblPEF, {Modified: Now(), WorkflowState: If(gblPEF.Status = "Pending Approval", gblPEF.WorkflowState, gblPEF.Status = "Approved", "Approval Status: Pending, this motivation must be re-approved", gblPEF.Close, "Approval for a Project Closure Motivation was not Started", gblPEF.Extend, "Approval for a Project Extension Motivation was not Started", "Approval for a New Project Motivation was not Started")}));
If(IsBlank(gblPEF.ProjectNo), Notify("Choose a Divisional Group and Revenue Stream first; the PEF is saved under its project number.", NotificationType.Warning), <S_UPSERT>; Notify("PEF " & gblPEF.ProjectNo & " saved.", NotificationType.Success))
```

### S_BUILD_APPROVALS

Rebuild the approval chain from the current status.

```
ClearCollect(colApprovals, {Step: 1, Role: "Checker", Approver: gblPEF.Checker, Required: gblPEF.CheckerRequired, Status: "Not started", ActionDate: If(false, Now()), ActedBy: "", Comments: ""}, {Step: 2, Role: "Head", Approver: gblPEF.Head, Required: true, Status: "Not started", ActionDate: If(false, Now()), ActedBy: "", Comments: ""}, {Step: 3, Role: "Divisional Manager", Approver: gblPEF.DivisionalManager, Required: true, Status: "Not started", ActionDate: If(false, Now()), ActedBy: "", Comments: ""}, {Step: 4, Role: "General Manager", Approver: gblPEF.GeneralManager, Required: gblPEF.RevenueStream in ["Cash", "Products and Services"], Status: "Not started", ActionDate: If(false, Now()), ActedBy: "", Comments: ""});
UpdateIf(colApprovals, true, {Status: If(!Required, "Not required", gblPEF.Status in ["Approved", "Closed"], "Approved", gblPEF.Status = "Pending Approval", "Waiting", "Not started"), ActionDate: If(Required && gblPEF.Status in ["Approved", "Closed"], gblPEF.Modified, If(false, Now())), ActedBy: If(Required && gblPEF.Status in ["Approved", "Closed"], Approver, "")});
If(gblPEF.Status = "Pending Approval", Patch(colApprovals, First(Filter(colApprovals, Required)), {Status: "Pending"}))
```

### S_APPLY_DIVISION

Run after the Divisional Group changes.

```
With({d: LookUp(colDivisionInfo, DivisionalGroup = gblPEF.DivisionalGroup)}, Set(gblPEF, Patch(gblPEF, {Division: d.Division, DivisionCode: d.DivisionCode, CostCentre: d.CostCentre, WorkCentre: d.WorkCentre, Head: d.Head, HeadMintekNo: d.HeadMintekNo, DivisionalManager: d.Manager, GeneralManager: d.GeneralManager, AdminOfficer: d.AdminOfficer})))
```

### S_APPLY_NUMBERING

Run after the Divisional Group, Revenue Stream, Sequence No., Automated Project No. or Create Project Site changes. It fixes the InfoPath bug where research projects got a *CommercialProjects* link.

```
With({rs: LookUp(colRevenueStreams, Title = gblPEF.RevenueStream), d: LookUp(colDivisionInfo, DivisionalGroup = gblPEF.DivisionalGroup)}, Set(gblPEF, Patch(gblPEF, {PackageCode: If(IsBlank(rs) || IsBlank(d), "", d.Prefix & rs.Letter)})));
Set(gblPEF, Patch(gblPEF, {ProjectNo: If(!gblPEF.AutoProjectNo, gblPEF.SequenceNo, IsBlank(gblPEF.PackageCode) || IsBlank(gblPEF.SequenceNo), "", gblPEF.PackageCode & "-" & gblPEF.SequenceNo)}));
Set(gblPEF, Patch(gblPEF, {ProjectSiteUrl: If(gblPEF.CreateProjectSite && !IsBlank(gblPEF.ProjectNo), "http://portal/Divisions/" & gblPEF.DivisionCode & "/Projects/" & If(gblPEF.RevenueStream in ["Cash", "Products and Services"], "CommercialProjects", "ResearchProjects") & "/FY" & Text(If(Month(gblPEF.Created) <= 3, Year(gblPEF.Created), Year(gblPEF.Created) + 1)) & "Projects/" & gblPEF.ProjectNo, "")}))
```

### S_APPLY_STREAM

The Revenue Stream dropdown's `OnChange` (`Self.Selected.Value`).

```
Set(gblPEF, Patch(gblPEF, {RevenueStream: Self.Selected.Value}));
With({rs: LookUp(colRevenueStreams, Title = gblPEF.RevenueStream)}, Set(gblPEF, Patch(gblPEF, {ServiceProfit: rs.ServiceProfit, WorkPackage: If(rs.IsCommercial, "Commercial", gblPEF.WorkPackage = "Commercial", "", gblPEF.WorkPackage), ClientName: If(rs.IsCommercial, If(gblPEF.ClientName = "Mintek", "", gblPEF.ClientName), "Mintek"), ProjectType: gblPEF.RevenueStream, Location: If(rs.IsCommercial, gblPEF.Location, "RSA"), Risks: If(rs.IsCommercial, gblPEF.Risks, "None")})));
<S_APPLY_NUMBERING>;
<S_RECALC>
```

### S_LOAD_SAMPLE_LINES

Reload all working collections from their samples.

```
ClearCollect(colStaff, colSampleStaff); ClearCollect(colRunningCosts, colSampleRunningCosts); ClearCollect(colMilestones, colSampleMilestones); ClearCollect(colServiceSBUs, colSampleServiceSBUs); ClearCollect(colSBUServices, colSampleSBUServices); ClearCollect(colDeliverables, colSampleDeliverables); ClearCollect(colMotivations, colSampleMotivations); ClearCollect(colAttachments, colSampleAttachments); ClearCollect(colRevisions, colSampleRevisions); ClearCollect(colNotifiers, colSampleNotifiers); ClearCollect(colSelectedProducts, colSampleSelectedProducts); ClearCollect(colSelectedProposals, colSampleSelectedProposals); ClearCollect(colSelectedOrders, colSampleSelectedOrders)
```

### S_START_APPROVAL

The Review screen's **Submit for approval**, used only when there are no validation issues.

```
<S_RECALC>;
Set(gblPEF, Patch(gblPEF, {Status: "Pending Approval", Submitted: true, Modified: Now(), WorkflowState: If(gblPEF.Close, "Approval for a Project Closure Motivation has Started", gblPEF.Extend, "Approval for a Project Extension Motivation has Started", "Approval for a New Project Motivation has Started")}));
<S_BUILD_APPROVALS>;
<S_EDITMODE>;
<S_UPSERT>;
Set(gblConfirmation, {Title: "Submitted for approval", Message: "PEF " & gblPEF.ProjectNo & " was submitted. " & LookUp(colApprovals, Status = "Pending").Approver & " (" & LookUp(colApprovals, Status = "Pending").Role & ") has been asked to approve it.", Kind: "Success"});
Navigate(scrConfirmation, ScreenTransition.Fade)
```

### S_APPROVE

Approve the pending step (`txtAprComments` is the comments box on `scrApprovals`).

```
With({s: LookUp(colApprovals, Status = "Pending")}, Patch(colApprovals, s, {Status: "Approved", ActionDate: Now(), ActedBy: LookUp(colRolePeople, Role = gblRole, Person), Comments: txtAprComments.Text}); With({nxt: First(Sort(Filter(colApprovals, Required && Status = "Waiting"), Step))}, If(IsBlank(nxt), If(gblPEF.Extend, Collect(colRevisions, {Rev: gblPEF.RevisionNo, RevDate: Today(), ClientPrice: gblTotals.ClientPrice, ProjectCost: gblTotals.ProjectCost, Labour: gblTotals.Labour, OPEX: gblTotals.OPEX, Contingency: gblTotals.Contingency, Warranty: gblTotals.Warranty, ServiceSBUs: gblTotals.ServiceCosts, Profit: gblTotals.Profit, ProfitPct: gblTotals.ProfitPct, ExchangeRate: gblPEF.ExchangeRate, StartDate: gblPEF.StartDate, EndDate: gblPEF.EndDate, ProjectType: gblPEF.ProjectType, Location: gblPEF.Location, Risks: gblPEF.Risks, Deliverables: Concat(colDeliverables, Final, "; ")})); Set(gblPEF, Patch(gblPEF, {Status: If(gblPEF.Close, "Closed", "Approved"), Extend: false, WorkflowState: If(gblPEF.Close, "Closure approved: project closed", "Approved: all approvals complete"), Modified: Now()})), Patch(colApprovals, nxt, {Status: "Pending"}); Set(gblPEF, Patch(gblPEF, {WorkflowState: "Waiting for " & nxt.Role & " approval", Modified: Now()})))));
Reset(txtAprComments);
<S_EDITMODE>;
<S_UPSERT>;
Notify("Approved.", NotificationType.Success)
```

### S_REJECT

Reject the pending step. Comments are mandatory, so disable the button when `IsBlank(txtAprComments.Text)`.

```
With({s: LookUp(colApprovals, Status = "Pending")}, Patch(colApprovals, s, {Status: "Rejected", ActionDate: Now(), ActedBy: LookUp(colRolePeople, Role = gblRole, Person), Comments: txtAprComments.Text}); UpdateIf(colApprovals, Status = "Waiting", {Status: "Not started"}); Set(gblPEF, Patch(gblPEF, {Status: "Rejected", WorkflowState: "Rejected by " & s.Role & ". Reason given: " & txtAprComments.Text, Modified: Now()})));
Reset(txtAprComments);
<S_EDITMODE>;
<S_UPSERT>;
Notify("Rejected. The applicant can now revise and resubmit.", NotificationType.Warning)
```

### S_CANCEL_APPROVAL

```
UpdateIf(colApprovals, Status in ["Pending", "Waiting"], {Status: "Not started"});
Set(gblPEF, Patch(gblPEF, {Status: "Draft", WorkflowState: "Approval cancelled by the applicant", Modified: Now()}));
<S_EDITMODE>;
<S_UPSERT>;
Notify("Approval cancelled. The PEF is back in draft.", NotificationType.Information)
```

### S_OPEN_PEF

Open a register row (`ThisItem` from `colPEFs`).

```
Set(gblPEF, Patch(gblSamplePEF, {ProjectNo: ThisItem.ProjectNo, ProjectTitle: ThisItem.ProjectTitle, DivisionalGroup: ThisItem.DivisionalGroup, RevenueStream: ThisItem.RevenueStream, ResponsiblePerson: ThisItem.ResponsiblePerson, Status: ThisItem.Status, WorkflowState: ThisItem.WorkflowState, StartDate: ThisItem.StartDate, EndDate: ThisItem.EndDate, RevisionNo: ThisItem.RevisionNo, Modified: ThisItem.Modified, SequenceNo: Last(Split(ThisItem.ProjectNo, "-")).Value, Close: ThisItem.Status = "Closed", Submitted: ThisItem.Status <> "Draft"}));
<S_APPLY_DIVISION>;
With({rs: LookUp(colRevenueStreams, Title = gblPEF.RevenueStream)}, Set(gblPEF, Patch(gblPEF, {ServiceProfit: rs.ServiceProfit, WorkPackage: If(rs.IsCommercial, "Commercial", gblPEF.WorkPackage), ClientName: If(rs.IsCommercial, "Kalahari Aero Components", "Mintek"), ClientPriceInput: If(rs.IsCommercial, ThisItem.ClientPrice, 0), PackageCode: Left(ThisItem.ProjectNo, 3)})));
<S_LOAD_SAMPLE_LINES>;
Set(gblActuals, If(gblPEF.Status = "Closed", gblSampleActuals, gblBlankActuals));
<S_BUILD_APPROVALS>;
<S_RECALC>;
<S_EDITMODE>;
Set(gblShowErrors, false);
Navigate(scrCoverPage, ScreenTransition.Fade)
```

### S_NEW_PEF

```
Set(gblPEF, Patch(gblNewPEF, {SequenceNo: Text(Max(colPEFs, Value(Last(Split(ProjectNo, "-")).Value)) + 1), Created: Today(), Modified: Now()}));
Clear(colStaff); Clear(colRunningCosts); Clear(colMilestones); Clear(colServiceSBUs); Clear(colSBUServices); Clear(colMotivations); Clear(colAttachments); Clear(colRevisions); Clear(colNotifiers); Clear(colSelectedProducts); Clear(colSelectedProposals); Clear(colSelectedOrders);
ClearCollect(colDeliverables, {No: 1, Original: "", Final: "", Achieved: false, Comment: ""});
Set(gblActuals, gblBlankActuals);
<S_BUILD_APPROVALS>;
<S_RECALC>;
<S_EDITMODE>;
Set(gblShowErrors, false);
Navigate(scrCoverPage, ScreenTransition.Fade)
```

### S_ISSUES

The validation table, a **Value** formula (not behaviour). Use it as the `Items` of the Review screen's issue gallery and in `CountRows(...)` checks.

```
Filter(Table({Area: "Cover Page", Field: "Divisional Group", Message: "Select the divisional group.", Missing: IsBlank(gblPEF.DivisionalGroup)}, {Area: "Cover Page", Field: "Revenue Stream", Message: "Select the revenue stream.", Missing: IsBlank(gblPEF.RevenueStream)}, {Area: "Cover Page", Field: "Project Title", Message: "Enter the project title (max 40 characters).", Missing: IsBlank(gblPEF.ProjectTitle)}, {Area: "Cover Page", Field: "PIC", Message: "Select the Project Information Chart (PIC).", Missing: IsBlank(gblPEF.PIC)}, {Area: "Cover Page", Field: "Sales Group", Message: "Sales Group is required.", Missing: IsBlank(gblPEF.SalesGroup)}, {Area: "Cover Page", Field: "Work Package", Message: "Work Package Code is required for State Grant projects.", Missing: gblPEF.RevenueStream = "State Grant" && IsBlank(gblPEF.WorkPackage)}, {Area: "Cover Page", Field: "Start Date", Message: "Start Date is required.", Missing: IsBlank(gblPEF.StartDate)}, {Area: "Cover Page", Field: "End Date", Message: "End Date is required and must be after the Start Date.", Missing: IsBlank(gblPEF.EndDate) || gblPEF.EndDate < gblPEF.StartDate}, {Area: "Cover Page", Field: "Checker", Message: "Select a checker or untick Checker Approval.", Missing: gblPEF.CheckerRequired && IsBlank(gblPEF.Checker)}, {Area: "Cover Page", Field: "Client Price", Message: "Client Price is required.", Missing: gblTotals.ClientPrice <= 0}, {Area: "Cover Page", Field: "Service SBUs", Message: "Every service SBU needs a division, head and cost.", Missing: gblPEF.ServiceSBURequired && (CountRows(colServiceSBUs) = 0 || CountRows(Filter(colServiceSBUs, IsBlank(Division) || IsBlank(SBUHead) || Cost <= 0)) > 0)}, {Area: "Hours & Costs", Field: "Project Cost", Message: "Project costs are required.", Missing: gblTotals.ProjectCost <= 0}, {Area: "Hours & Costs", Field: "Staff", Message: "Select at least 1 grade who will be involved in the project.", Missing: CountRows(colStaff) = 0}, {Area: "Hours & Costs", Field: "Staff lines", Message: "Every staff line needs a grade, financial year, hours and comments.", Missing: CountRows(Filter(colStaff, IsBlank(Grade) || IsBlank(FinancialYear) || Hours <= 0 || IsBlank(Comments))) > 0}, {Area: "Hours & Costs", Field: "Running costs", Message: "Every running cost needs a cost element, amount and description.", Missing: CountRows(Filter(colRunningCosts, IsBlank(CostElementTitle) || Amount <= 0 || IsBlank(Description))) > 0}, {Area: "Motivations", Field: "Motivation", Message: "Motivation is required.", Missing: IsBlank(Last(colMotivations).Motivation)}, {Area: "Closure", Field: "Closure description", Message: "Explain time and cost overruns and deliverables not achieved.", Missing: gblPEF.Close && IsBlank(gblPEF.ClosureDescription)}, {Area: "Closure", Field: "Actuals", Message: "Enter the actual client price, project costs, labour, exchange rate and dates.", Missing: gblPEF.Close && (gblActuals.ClientPrice <= 0 || gblActuals.ProjectCost <= 0 || gblActuals.Labour <= 0 || gblActuals.ExchangeRate <= 0 || IsBlank(gblActuals.StartDate) || IsBlank(gblActuals.EndDate))}), Missing)
```

Map `Area` to a screen when navigating to it: `Switch(ThisItem.Area, "Cover Page", Navigate(scrCoverPage), "Hours & Costs", Navigate(scrHoursCosts), "Motivations", Navigate(scrMotivations), "Closure", Navigate(scrClosure))`.

### Formatting

| Value | Formula |
|---|---|
| Money | `"R " & Text(<n>, "#,##0.00")` |
| Percentage | `Text(<fraction>, "0.00%")` |
| Date | `Text(<d>, "dd mmm yyyy")` |
| Date and time | `Text(<dt>, "dd mmm yyyy hh:mm")` |
| Hours | `Text(<n>, "#,##0")` |

---

## 8. Screen catalogue (InfoPath → Power Apps)

| Screen | InfoPath source | Contents |
|---|---|---|
| `scrDashboard` | Form library view (new) | KPI cards by status, search and status filter chips, register table (`colPEFs`), **New PEF**, open row |
| `scrCoverPage` | Cover Page view | Sections: Project identification · Classification & PIC · Project details · People · Dates & pricing summary · Client, proposals & orders (commercial) · Milestones & billing plan · Deliverables · Controlling SBU planned costs · Service SBUs (when required) · Checker (when required) · Project flags (Extend / Close) |
| `scrHoursCosts` | Hours And Costs view | Hourly planning table, carry-over labour, running costs table, contingency and warranty (amount or %), totals |
| `scrMotivations` | Motivations view | Motivation history (latest editable), project attachments (mock upload) |
| `scrRevisions` | Revisions view | Latest vs Original vs revisions table; last 5 shown; empty state |
| `scrApprovals` | Approval sections of the Cover Page | Approval chain stepper, delegates, comments, Approve / Reject for the simulated role |
| `scrReview` | PrintView + Start Approval gate | Validation checklist with **Go to** links; read-only summary; Submit for approval; Print |
| `scrClosure` | Closure view | Closure motivation; Original / Final / Actual comparison with increases; deliverables achieved |
| `scrConfirmation` | After submit (new) | Result card, next steps, buttons |
| `scrDetailedInfo` | Detailed Information view | Workflow state, simulated user, approvers, delegates, flags, package code, totals |
