---
name: parker
description: Use when creating or editing Power Apps canvas-app screens in the YAML source format (pa-yaml / *.fx.yaml) that get pasted or imported into Power Apps Studio — building screens, galleries / data tables, responsive columns, status cards, or debugging controls that overflow, clip, render empty, or land in the wrong column.
---

# Parker (Power Apps Canvas YAML)

## Overview

Power Apps canvas screens can be authored as YAML "source format" (pa-yaml) and pasted/imported into Studio. **Studio is the only renderer** — you cannot preview from the CLI, and it reconciles control `@version`s on import. The only local check is YAML well-formedness plus a control/property audit.

**Core principle: only use control types, versions, and property names already proven in the target app's existing screens.** Studio silently mis-renders or drops unknown controls/properties — there is no error you'll see locally.

## First step: inventory the target app (never hardcode)

This skill is project-agnostic. Before authoring, derive the vocabulary from the app's *existing* screens — don't copy values from another app:

- **Controls + versions**: `grep -h "Control:" *.yaml | sort -u` → the only safe set (e.g. `GroupContainer@1.5.0`, `Label@2.5.1`, `Classic/Button@2.2.0`, `Classic/Icon@2.5.0`, `Gallery@2.15.0`, `FluidGrid@2.3.0`, `DataCard@1.0.2`, `Rectangle@2.3.0`, `CanvasComponent`).
- **Style tokens**: grep the recurring `RGBA(...)`, `Font.'...'`, `Size`, radius values. Reuse them exactly.
- **Layout idioms**: skim one existing screen for how cards/rows/scroll are built.

Shared chrome (headers, nav, menus) is usually external `CanvasComponent`s placed by `ComponentName` — reference them, don't rebuild.

## YAML gotchas (these silently break the paste)

- **Colon-space.** Values are unquoted plain scalars starting with `=`. A value containing `: ` (colon+space), e.g. `Text: ="Status: Ready"`, breaks plain-scalar parsing (`mapping values are not allowed here`). Three escapes: (1) reword; (2) split into two labels; or (3) **concatenate so no `: ` appears in the scalar** — `Text: ="Status:" & " Ready"` still renders `Status: Ready`, because the colon is now followed by a quote, not a space. The concat trick keeps the exact display text in one control (handy for filter chips like `="FICA:" & " All"`). Times like `16:00` (colon, no space) are fine. **Formulas with record literals** (`ClearCollect(c, {Field: value})`) contain colon-spaces — put them in a block scalar: `OnVisible: |-` then `=…` on the next line(s).
- **Bare `=`.** A lone `=` resolves to a YAML value tag — any validator must register a constructor for `tag:yaml.org,2002:value` (the bundled `validate.py` does this).
- **Indentation.** 2-space, deeply nested. A list item (`- Name:`) sits at parent-key indent + 2; that item's keys at item indent + 4. Match the surrounding file exactly.

## Control gotchas (each one cost a broken render — verified)

- **`FillPortions` does NOT reliably constrain horizontal columns.** Multiple `FillPortions` children in a horizontal auto-layout overflowed off-screen instead of shrinking. For table columns / multi-column rows use **explicit `Parent.Width * <fraction>`** with absolute `X`, fractions summing to 1.0. The header row and the gallery rows must use the **same fractions** so columns align. Vertical stacking with FillPortions is fine.
- **Classic controls can't read `Parent.TemplateWidth`.** Inside a modern `Gallery@2.x`, `Classic/*` controls (`Classic/Button`, `Classic/Icon`) read `Parent.Width` but get **0** from `Parent.TemplateWidth` — so `X: =Parent.TemplateWidth*0.5 + 8` collapses to `8` and the control jumps to the far left. Fix: wrap the classic control in a modern `GroupContainer` positioned by `Parent.TemplateWidth`, and give the classic control a **fixed** `X` offset inside. Modern controls (`Label`, `Rectangle`, `GroupContainer`) read `Parent.TemplateWidth` fine.
- **A positioning-wrapper `GroupContainer` must be transparent — and shadow-free.** When a `GroupContainer` exists only to *place* a child — the `Parent.TemplateWidth` wrap above, or any sub-column container — **omit its `Fill` line entirely** (don't write `Fill: =RGBA(0,0,0,0)` on a container) and give it `DropShadow: =DropShadow.None`. A non-transparent `Fill` paints an opaque block over **only that sub-column's width**; inside a gallery row it renders as a stray rectangle behind just the icon/badge (not the whole row). For an actual row/card background use a **separate full-width** control (e.g. a `GroupContainer` at `Width: =Parent.TemplateWidth`) placed **first** in the children so it sits behind the content. (A wide card that intentionally has a `Fill` and holds real content — e.g. a KPI card — is fine; the trap is a *narrow wrapper whose only job is positioning*.)
- **`ModernButton` can render blank** in nested auto-layouts. For an icon+text button, use a `GroupContainer` holding a `Classic/Icon` + a `Classic/Button` (transparent `Fill: =RGBA(0,0,0,0)`), or a `Classic/Button` alone.
- **`Image` has no portable `@version`.** Studio prompts to reconcile it on import; expect that one prompt. Use a placeholder like `Image: =SampleImage`.
- **`Icon.*` names must be real enum members — Studio renders nothing for unknown ones.** There is no local error; the slot just goes blank. Plausible-but-wrong names are the trap: **`Icon.Documents` does not exist — use `Icon.DocumentPDF`**; prefer confirmed names (`Icon.Document`, `Icon.DocumentPDF`, `Icon.DocumentWithContent`, `Icon.CalendarBlank`, `Icon.Clock`, `Icon.People`, `Icon.Person`, `Icon.Home`, `Icon.Settings`, `Icon.Search`, `Icon.Hamburger`, `Icon.Information`, `Icon.Warning`, `Icon.Error`, `Icon.Check`, `Icon.Post`, `Icon.Trending`, `Icon.DetailList`, `Icon.Message`). When in doubt, verify the name renders in Studio. `validate.py` denylists known-bad names (extend `INVALID_ICONS`).
- **A child must fit inside a ManualLayout parent — overflow is clipped/detached, not scrolled.** If a child's `Y + Height` exceeds the parent `GroupContainer`'s `Height`, Studio paints it *outside* the parent's bounds (it does not grow the card). This bites when you nest a second card inside the first instead of as a sibling. Fix: make the lower card a **sibling** at screen/body coordinates, or raise the parent `Height` to cover `Y + Height` of every child. `validate.py` flags this numerically.

## Authoring rules (decide these before you pick a control)

- **Anything clickable is a button control — never a `Label` with an `OnSelect`.** A `Label` *will* fire `OnSelect`, but it renders as flat static text: no hover or press feedback, no focus ring, no keyboard reach, no disabled state — nothing tells the user it is a tap target. Use a **`Classic/Button`** for every text tap target: CTA, filter chip, tab, pagination, row action, "See all", card footer link, segmented-toggle segment. Recipe: `Text`, `OnSelect`, `Fill`, `Color`, `HoverFill` (a shade off `Fill`), and the four `Radius*` corners. For a text-link look, keep `Fill: =RGBA(0,0,0,0)` with the link `Color` and a faint `HoverFill`. **Icon-only** affordances stay a `Classic/Icon` with `OnSelect` — it is a real interactive control; pair it with a transparent `Classic/Button` when the icon needs a label beside it. The inverse still holds: a **non-interactive** pill/badge is a `Classic/Button` with `DisplayMode: =DisplayMode.View` + `HoverFill: =Self.Fill`, and pure display text stays a `Label`. `validate.py` errors on a `Label` carrying a real `OnSelect`.
- **Group related controls into a `GroupContainer` — one per region.** Every logical region (top bar, filter row, KPI row, each card, a form section, a footer action bar) gets its own **named** `GroupContainer` (`BorderStyle: =BorderStyle.None`), positioned once; its children then use `Parent.Width` / `Parent.Height` and small local offsets instead of screen-absolute math. You move, hide (`Visible`), restyle or duplicate the whole region by editing one control, and the Studio tree stays readable. Reach for a container when: a screen has more than ~8-10 direct children; you are repeating the same `X` base offset across several controls; several controls share one `Visible` / `DisplayMode` condition; or the group repeats (build it once, copy it). Don't over-nest: a wrapper holding a single control that adds no positioning is noise, and a positioning-only wrapper must stay transparent (see above).

## Layout idioms (reliable)

- **Scrolling a too-tall body**: canvas screens and auto-layout containers do NOT scroll. Wrap the body in a `FluidGrid` (the scroll viewport, `Height: =Parent.Height`) holding **one** `DataCard` with a **large fixed `Height`** (≥ the tallest child's `Y + Height`) that contains all the content. Keep fixed chrome (sidebar, top bar) as **screen-level siblings emitted *after* the `FluidGrid`** so they render on top and don't scroll. If the `DataCard` spans the full width from `X: =0, Y: =0`, body controls keep their original screen `X/Y` (their `Parent.Width` still equals the screen width). Auto-layout containers also **clip** the last child when `Height` < sum(children) + `LayoutGap`s — size them generously. **For a single long list/table screen you don't need the FluidGrid** — a `Gallery` scrolls its own rows natively; keep search/filters/the column-header row fixed above it and give the `Gallery` `Height: =Parent.Height - <top>` (or `=Parent.Height - <headerH>` inside a card) so it fills the rest and scrolls.
- **Vertical stacks**: `GroupContainer` AutoLayout (`LayoutDirection.Vertical`, `LayoutAlignItems.Stretch`, `LayoutGap`). Works well.
- **Columns / pixel-precise / right-anchor**: `GroupContainer` ManualLayout + `Parent.Width` formulas (right-anchor with `X: =Parent.Width - <w>`).
- **Status pills / badges**: `Classic/Button` with `DisplayMode: =DisplayMode.View` and `HoverFill: =Self.Fill` (non-interactive look).
- **Fake a select / dropdown** (when no native `ComboBox`/`DropDown` is in the proven set): a `GroupContainer` (white `Fill`) holding a left-aligned `Label` for the value and a right-anchored chevron `Classic/Icon` (e.g. `Icon.ChevronDown`) at `X: =Parent.Width - 28`. Reads as a dropdown in a mockup; swap for a real picker when wiring data.
- **Avatar + name in a table column**: the avatar is a round `Classic/Button` (high `Radius`, `DisplayMode.View`, initials as `Text`) — a `Classic/*`, so wrap the whole cell in a `GroupContainer` positioned by `Parent.TemplateWidth` and give the avatar a **fixed** inner `X`; the name `Label` sits at a fixed `X` beside it.
- **Segmented toggle** (Day/Week/Month, List/Board/Calendar): a `GroupContainer` with a light `Fill` (the track) holding N `Classic/Button`s — the **active** one gets a solid `Fill` + `Radius`, the rest `Fill: =RGBA(0,0,0,0)` (transparent) with grey text. Each segment is a live tap target, so use the tap-target recipe from *Authoring rules*: `OnSelect` sets the selected value (e.g. `=Set(varView, "Week")`), and `Fill`/`Color` are driven by that value so the active segment gets the solid fill, with a faint `HoverFill` rather than `=Self.Fill`. Do not put `DisplayMode.View` on segments: that is the non-interactive badge recipe.
- **Kanban / board columns**: a `BoardRow` `GroupContainer` holding N column `GroupContainer`s placed by `Parent.Width * fraction` (4 cols ≈ 0.235 wide at X 0 / 0.255 / 0.510 / 0.765). Each column = a header `Label` + its **own** vertical `Gallery` that scrolls independently (`Height: =Parent.Height - <headerH>`). A card is a white `GroupContainer` as the row's first child — this is one of the few places `DropShadow: =DropShadow.Light` is right, because it has a solid `Fill` and is meant to lift; the column and row wrappers around it still take `=DropShadow.None`. Its priority badge (`Classic/Button`) uses a **fixed** `X`, and the avatar (`Classic/Button`) is wrapped by `Parent.TemplateWidth` at the card's right.
- **Empty state**: one `Label` sized to fill the card (`Width: =Parent.Width`, `Height: =Parent.Height`, `Align.Center` + `VerticalAlign.Middle`) — centers the message both ways.
- **Dense text in narrow columns** (e.g. a left nav steals ~40px): drop body `Size` to 9 and give long-value rows extra height / 2 lines so they don't wrap-overlap the next row.
- **Suppress container chrome — set `BorderStyle` on every `GroupContainer`, and `DropShadow` on every scaffolding one (no solid `Fill` of its own).** Every `GroupContainer` gets `BorderStyle: =BorderStyle.None` (the container default is a **visible border**). **Do not assume `DropShadow` defaults to `None` and leave it off a scaffolding container** — write it out (a solid-`Fill` painted surface or hairline may omit it, see below), and for the large majority of containers the correct value is **`DropShadow: =DropShadow.None`**, not `Light`. Most `GroupContainer`s on a screen are invisible scaffolding — region containers, card/panel wrappers, `Parent.TemplateWidth` positioning wraps, nav-row wrappers — and a shadow on one of those paints a grey smudge with no surface under it. Reserve **`DropShadow: =DropShadow.Light` for a genuinely elevated card surface only**: a container with a real solid `Fill` that is meant to lift off the page. A whole dense screen can legitimately contain **zero** `DropShadow.Light` (verified: a 27-container SAP catalog home screen used `None` on all 17 wrappers and `Light` on none).
- **A transparent container omits `Fill` entirely — don't write `Fill: =RGBA(0,0,0,0)` on a `GroupContainer`.** Leaving the property off is the house style and reads cleaner in the Studio tree; the explicit transparent RGBA belongs on `Classic/Button` (link/nav buttons), not on containers. So a scaffolding container is exactly two chrome lines plus geometry:

  ```yaml
  - SomeWrapper:
      Control: GroupContainer@1.5.0
      Variant: ManualLayout
      Properties:
        BorderStyle: =BorderStyle.None
        DropShadow: =DropShadow.None
        Height: =…
        Width: =…
  ```

  A container that is a **real painted surface** (sidebar, top bar) or a **1px hairline** (divider, edge, rule) keeps its solid `Fill` and needs no `DropShadow` line at all — it has no wrapper ambiguity to resolve.

## Worked example

[example-responsive-table.yaml](example-responsive-table.yaml) is a minimal, validated screen showing the two patterns that are easiest to get wrong: responsive columns via `Parent.Width * fraction` (header + gallery rows sharing the same fractions) and a `Classic/*` control wrapped in a modern `GroupContainer` inside a `Gallery`. Copy it and adapt the columns.

## Studio round-trip (expected — not a bug)

Importing pa-yaml into Studio and re-exporting **normalizes** it. Verified on a real round-trip:

- **Some default-valued properties are stripped.** A few `Size`/`Height`/`VerticalAlign` values that matched defaults were dropped on re-export. `BorderStyle: =BorderStyle.None` was **kept**. **`DropShadow: =DropShadow.None` is NOT reliably a no-op — write it anyway.** An earlier version of this skill claimed `None` was the default and told you to skip it; that guidance was wrong and got corrected from a real screen where wrapper containers rendered with unwanted shadows until `None` was set explicitly. If a round-trip does strip it, re-adding costs nothing; omitting it can cost you a visible shadow. Treat `DropShadow` as a property you always state on a scaffolding `GroupContainer` (one with no solid `Fill` of its own); only a painted surface or hairline with a solid `Fill` may omit it, as described above.
- **Colliding control names get a `_2`/`_3` suffix.** A second screen reusing the same control names (e.g. another `SearchBox`, `LogoIcon`, `NavIcon`) comes back as `SearchBox_2`, `LogoIcon_2`, … This is the signal to **factor shared chrome (sidebar, top bar, nav) into one `CanvasComponent`** referenced by every screen instead of copying it per screen.
- Formulas survive intact — the colon-space concat (`="FICA:" & " All"`), `Switch` badge colors, and `Parent.TemplateWidth` wraps all came back unchanged.

## Validate every file before handing off

`validate.py` parses the file (with the `=` constructor) and audits it against the app's existing screens. It flags unproven controls/properties, `Classic/*` controls reading `Parent.TemplateWidth`, `ModernButton`, horizontal `FillPortions`, an opaque `Fill` on a positioning wrapper (when its only child is a `Classic/*` control or it is a gallery sub-column sized by `Parent.TemplateWidth`), `GroupContainer` `BorderStyle` / `DropShadow` / transparent-`Fill` chrome, numeric child overflow, denylisted `Icon.*` names, clickable `Label`s and flat screens (the full list is in its docstring). It cannot tell every positioning wrapper from a painted card, and it only knows the `Icon.*` names in its denylist, so other multi-child wrappers with a `Fill` and unlisted icon names still need your eye. Each message names the control instance, e.g. `CellAction (GroupContainer@1.5.0)`. Run it after authoring and after each edit:

```bash
python validate.py NEW_SCREEN.yaml EXISTING1.yaml EXISTING2.yaml ...
```

See [validate.py](validate.py).

## Common mistakes

| Symptom in Studio | Cause | Fix |
|---|---|---|
| Paste fails / "mapping values not allowed" | colon-space in a `=` value | reword or split label |
| Right columns + buttons run off-screen | `FillPortions` horizontal distribution | explicit `Parent.Width * fraction`, sum to 1.0 |
| Badge/icons jammed at far left of a gallery row | `Classic/*` reading `Parent.TemplateWidth` (=0) | wrap in modern `GroupContainer`, fixed inner `X` |
| Stray opaque block behind only one column of a gallery row | a positioning-wrapper `GroupContainer` has a `Fill` | remove the wrapper's `Fill` line (a container is transparent without one) and set `DropShadow: =DropShadow.None`; draw row backgrounds with a separate full-width control placed first |
| Faint border outline around containers, cards or wrappers | `GroupContainer` default `BorderStyle` is a visible border | set `BorderStyle: =BorderStyle.None` |
| Grey smudge / halo around a wrapper that has no visible surface | `DropShadow` left unstated on a scaffolding `GroupContainer`, or set to `Light` by habit | set `DropShadow: =DropShadow.None`; keep `Light` for elevated card surfaces only |
| Button shows as an empty box | `ModernButton` in nested layout | `Classic/Button` (+ `Classic/Icon`) |
| A tap target gives no hover/press feedback, can't be tabbed to | clickable text built as a `Label` with `OnSelect` | `Classic/Button` for text, `Classic/Icon` for icon-only |
| Moving or hiding a section means editing 15 controls; flat unreadable tree | region not wrapped in a container | one named `GroupContainer` per region; children position off `Parent.*` |
| An icon slot renders blank | `Icon.*` name not in the enum (e.g. `Icon.Documents`) | use a real name (`Icon.DocumentPDF`); verify in Studio |
| A nested card renders outside/below its parent card | child `Y + Height` exceeds the ManualLayout parent `Height` | make it a sibling, or raise the parent `Height` |
| Body too tall, lower content unreachable (no scroll) | screen/auto-layout don't scroll | wrap body in `FluidGrid` → tall `DataCard`; keep chrome as siblings on top |
| Last row/section of a container is cut off | container `Height` < children + gaps | increase container `Height` |
| Only some columns visible, header misaligned | header & rows use different widths | identical fraction set for both |

## Red flags — stop and reconsider

- Using a control/`@version`/property not found in the target app's existing screens.
- `FillPortions` on 3+ children of a *horizontal* container that holds wide content.
- `Parent.TemplateWidth` referenced by any `Classic/*` control.
- `ModernButton` for anything that must reliably show text/icon.
- A `Label` with an `OnSelect` - any clickable text that isn't a `Classic/Button`.
- A screen that is a long flat list of direct children instead of one `GroupContainer` per region.
- A `GroupContainer` whose only job is wrapping/positioning a single child but that carries a non-transparent `Fill` (paints a stray block over its sub-column).
- A `GroupContainer` missing `BorderStyle: =BorderStyle.None` (its default border leaks through) **or, when it has no solid `Fill` of its own, missing an explicit `DropShadow`** — state it, and default to `=DropShadow.None`.
- Any `DropShadow` other than `=DropShadow.None` (most often `Light` by habit) on a container that is scaffolding rather than an elevated surface (region wrapper, positioning wrap, transparent card/panel wrapper). If it has no solid `Fill` of its own, it wants `None`.
- `Fill: =RGBA(0,0,0,0)` written on a `GroupContainer` — omit the `Fill` line instead; the explicit transparent RGBA is for `Classic/Button`.
- An `Icon.*` name you haven't confirmed exists (unknown names render blank — `Icon.Documents` is the classic trap; use `Icon.DocumentPDF`).
- A card/section nested inside another card whose `Y + Height` exceeds the parent `Height` (it renders detached; make it a sibling).
- A body taller than the screen without a `FluidGrid` → `DataCard` scroll wrapper.
- A `Text: =` value containing `: ` (colon-space).
