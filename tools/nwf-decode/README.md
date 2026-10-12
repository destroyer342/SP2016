# nwf-decode

Turns a Nintex Workflow 2016 export (`.nwf`) into readable text. A `.nwf` file wraps the workflow definition as escaped XML, which is hard to read. This tool unwraps it and numbers every action **A001, A002, …** in export order, so the analysis, the design, the build and the tests can all refer to the same action IDs.

It is used in stages 1 and 3 of the [migration pipeline](../../docs/migration-plan.md).

## Usage

Requires Python 3.8 or later; no extra packages.

```bash
# Size and dependencies: used for the inventory and triage (stage 1)
python3 tools/nwf-decode/nwf_decode.py --summary Proposal_Approval.nwf

# Full action tree: used for the analysis (stage 3)
python3 tools/nwf-decode/nwf_decode.py Proposal_Approval.nwf > Proposal_Approval.actions.txt
```

## What the summary shows

- the list the workflow runs on, and how it starts;
- the number of actions and variables, and any disabled actions;
- a count of each action type;
- every dependency to rebuild: user-defined actions, child workflows, task forms and the lists it queries;
- every hard-coded URL;
- a suggested size (Small, Medium or Large; see [Triage and sizing](../../docs/migration-plan.md#6-triage-and-sizing)).

## What the full tree shows

For every action, in order and indented by nesting:

- its ID, type and label, and whether it is disabled;
- for conditions: the full condition, with the branches labelled. In a Nintex *Set a condition*, the **first** branch in the export runs when the condition is **false**, and the second when it is true;
- the columns it updates and the values it writes;
- query filters and the variables they fill;
- e-mail recipients, subject and body text;
- task forms and the fields they collect;
- user-defined actions and child workflows, with their inputs and outputs.

## Limits

- **User-defined actions and child workflows** are not inside the workflow export. Export them separately (*Site Settings → Manage User Defined Actions → Export*) and decode them too.
- The tool reads Nintex Workflow **2016** exports. Other Nintex versions may use a different structure.
