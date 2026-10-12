#!/usr/bin/env python3
"""Decode a Nintex Workflow 2016 export (.nwf) into readable text.

A .nwf file wraps the workflow definition as escaped XML. This script unwraps it and prints:

  --summary  counts and dependencies, used to size and triage a workflow
  (default)  the full action tree: every action numbered A001, A002, ... in export order,
             with its conditions, column updates, queries, e-mails, tasks and sub-workflow calls

Usage:
  python3 nwf_decode.py Proposal_Approval.nwf            > Proposal_Approval.actions.txt
  python3 nwf_decode.py --summary Proposal_Approval.nwf
"""
import argparse
import collections
import html
import re
import sys
import xml.etree.ElementTree as ET

# Parameters that only hold designer or scheduling noise
SKIP_PARAMS = {
    'ExpandCollapsed', 'Schedule', 'AvoidBatch', 'UseSchedule', 'IsSetToBuilderMode', 'StoreRawValue',
    'ItemLimitLookup', 'MinutesReminder', 'HoursReminder', 'DaysReminder', 'HoursEscalation', 'DaysEscalation',
    'MinutesEscalation', 'ReminderWaitMode', 'EscalationWaitMode', 'EscalationComments', 'DelegateTo',
    'DelegateToPrincipalType', 'CurrentlyEditingCT', 'HumanWorkflowID', 'TaskID', 'StoreAttachmentsIn',
    'DisplayAttachments', 'AddWorkflowItemLink', 'AddItemProperties', 'ContentTypeName',
}
CONTAINERS = {'WFSequence', 'WFIfElseBranch'}


def load(path):
    """Return (outer root, inner workflow root)."""
    outer = ET.parse(path).getroot()
    inner_text = outer.findtext('ExportedWorkflowSeralized')
    if inner_text is None:
        sys.exit(f'{path}: no ExportedWorkflowSeralized element; is this a Nintex 2016 export?')
    return outer, ET.fromstring(inner_text.encode('utf-8'))


def clean(fragment):
    """Make a parameter's XML readable: values in quotes, variables as $name."""
    s = html.unescape(fragment)
    s = re.sub(r' (Required|StartupOptionsConfigured|ControlType|Initiate|Description|Direction|RowIndex|DefaultValue)="[^"]*"', '', s)
    s = re.sub(r'<RunNowOptions[^>]*/>', '', s)
    s = re.sub(r'<PrimitiveValue Value="([^"]*)" ValueType="([^"]*)" />', r'"\1"(\2)', s)
    s = re.sub(r'<Variable Name="([^"]*)"(?: Type="([^"]*)")? />',
               lambda m: '$' + m.group(1) + (f':{m.group(2)}' if m.group(2) else ''), s)
    s = re.sub(r'<Coercion>([^<]*)</Coercion>', r' [coerce \1]', s)
    s = re.sub(r'</?Params>|</Param>', '', s)
    s = re.sub(r'<Param Name="(\w+)">', r' \1=', s)
    s = re.sub(r'xmlns:xsi="[^"]*" ', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def inner_xml(element):
    return ''.join(ET.tostring(child, encoding='unicode') for child in element)


def plain(param):
    """The raw value of a parameter that holds a single PrimitiveValue, else its readable form."""
    pv = param.find('PrimitiveValue') if param is not None else None
    return pv.get('Value') if pv is not None else (clean(inner_xml(param)) if param is not None else '')


def action_type(action):
    return action.findtext('Type').split('.')[-1].replace('Adapter', '')


def walk_actions(root):
    """Yield (id, depth, branch label, action) for every action in export order."""
    counter = [0]

    def walk(action, depth, branch):
        counter[0] += 1
        yield f'A{counter[0]:03d}', depth, branch, action
        children = action.findall('ChildActivities/NWActionConfig')
        if action_type(action) == 'WFIfElse':
            # The first child is the left branch (LLabel, default "No": condition FALSE),
            # the second is the right branch (RLabel, default "Yes": condition TRUE).
            left = (action.findtext('LLabel') or 'No').upper()
            right = (action.findtext('RLabel') or 'Yes').upper()
            labels = [f'<<{left} branch: condition FALSE>> ', f'<<{right} branch: condition TRUE>> ']
            for i, child in enumerate(children):
                yield from walk(child, depth + 1, labels[i] if i < 2 else '')
        else:
            for child in children:
                yield from walk(child, depth + 1, '')

    for top in root.findall('Configurations/ActionConfigs/NWActionConfig'):
        yield from walk(top, 0, '')


def print_tree(outer, root):
    title = root.findtext('Title')
    print(f'=== WORKFLOW "{title}" (export version {outer.findtext("Version")}, '
          f'type {outer.findtext("WorkflowType")}, id {outer.findtext("WorkflowId")})')
    for lr in outer.iter('ListReference'):
        if lr.findtext('IsSourceList') == 'true':
            print(f'=== Runs on list "{lr.findtext("ListName")}" {{{lr.findtext("ListId")}}}')
    print('=== "Set a condition": the FIRST child branch runs when the condition is FALSE, the SECOND when it is TRUE.')
    print('=== "Run if": its children run only when the condition is TRUE.')
    print()
    print('=== VARIABLES')
    for variables in root.iter('WorkflowVariables'):
        for v in variables:
            extra = '  [start form]' if v.get('StartupOptionsConfigured') == 'true' else ''
            print(f'  ${v.get("Name")} : {v.get("Type")}{extra}')
    print()
    print('=== ACTIONS')
    for aid, depth, branch, a in walk_actions(root):
        t = action_type(a)
        indent = '  ' * depth
        line = f'{indent}[{aid}] {branch}{t} "{a.findtext("TLabel") or ""}"'
        if a.findtext('Enabled') != 'true':
            line += ' **DISABLED**'
        if a.findtext('IsValid') != 'true':
            line += ' **INVALID**'
        if a.findtext('BLabel'):
            line += f'  (label: "{a.findtext("BLabel")}")'
        print(line)
        p = indent + '    | '
        cond = a.find('Condition')
        if cond is not None:
            print(p + 'CONDITION: ' + clean(ET.tostring(cond, encoding='unicode')))
        if t != 'NWWorkflowVariables':
            for prm in a.findall('Parameters/Parameter'):
                if prm.get('Name') not in SKIP_PARAMS:
                    print(p + f'{prm.get("Name")} = ' + clean(inner_xml(prm))[:4000])
        for fr in a.findall('FieldReferences/FieldReference'):
            print(p + f'FIELD "{fr.get("Name")}" [{fr.get("Value")}:{fr.get("Type")}] = ' + clean(inner_xml(fr))[:1500])
        for vs in a.findall('ValueStorages/ValueStorageItems/ValueStorage'):
            print(p + f'OUTPUT {vs.get("ValueIdentifier")} -> ${vs.get("VariableName")}:{vs.get("VariableType")}')
        approvers = a.find('Approvers')
        if approvers is not None and len(approvers):
            print(p + 'TO: ' + ', '.join(x.get('User') or clean(ET.tostring(x, encoding='unicode')) for x in approvers))
        msg = a.find('Message')
        if msg is not None:
            print(p + 'FROM: ' + str(msg.findtext('From/UserID')))
            print(p + 'CC: ' + ', '.join(u.findtext('UserID') or '' for u in msg.findall('CcList/User')))
            print(p + 'SUBJECT: ' + str(msg.findtext('Subject')))
            body = re.sub(r'<[^>]+>', ' ', html.unescape(msg.findtext('Body') or ''))
            print(p + 'BODY (text): ' + re.sub(r'\s+', ' ', body).strip()[:3000])
        if t == 'NWWorkflowVariables':
            for prm in a.findall('Parameters/Parameter'):
                print(p + f'{prm.get("Name")} = ' + clean(inner_xml(prm))[:300])


def print_summary(outer, root):
    actions = list(walk_actions(root))
    types = collections.Counter(action_type(a) for _, _, _, a in actions)
    real = sum(n for t, n in types.items() if t not in CONTAINERS)
    print(f'Workflow:        {root.findtext("Title")}')
    for lr in outer.iter('ListReference'):
        if lr.findtext('IsSourceList') == 'true':
            print(f'Runs on list:    {lr.findtext("ListName")}')
    start = {p.get('Name'): plain(p) for p in actions[0][3].findall('Parameters/Parameter')}
    print(f'Starts:          manual={start.get("StartManually")} on create={start.get("StartOnCreate")} '
          f'on change={start.get("StartOnChange")}')
    print(f'Actions:         {len(actions)} in the export, {real} excluding containers')
    print(f'Variables:       {sum(len(v) for v in root.iter("WorkflowVariables"))}')
    disabled = [aid for aid, _, _, a in actions if a.findtext('Enabled') != 'true']
    print(f'Disabled:        {", ".join(disabled) or "none"}')
    print()
    print('Action types:')
    for t, n in types.most_common():
        print(f'  {n:4d}  {t}')
    print()
    print('Dependencies (each must be rebuilt or replaced):')
    for aid, _, _, a in actions:
        t = action_type(a)
        params = {p.get('Name'): plain(p) for p in a.findall('Parameters/Parameter')}
        if t == 'UserDefinedActionWrapper':
            print(f'  {aid}  user-defined action {params.get("Id")} "{a.findtext("TLabel")}"')
        elif t == 'NWStartWorkflow2':
            print(f'  {aid}  starts workflow {params.get("AssociationId")}')
        elif t == 'NWCollectData':
            print(f'  {aid}  task form "{a.findtext("TLabel")}" ({params.get("TaskName")})')
        elif t == 'NWQueryList':
            lists = re.findall(r'List Title="([^"]+)"', html.unescape(params.get('Query', '')))
            print(f'  {aid}  queries list {", ".join(lists)} at {params.get("BaseUrl")}')
    urls = sorted(set(u for u in re.findall(r'https?://[^\s"<>&]+', html.unescape(ET.tostring(root, encoding='unicode')))
                      if 'w3.org' not in u))
    print()
    print('Hard-coded URLs:')
    for u in urls:
        print(f'  {u}')
    size = 'Large' if real > 120 or types['UserDefinedActionWrapper'] or types['NWStartWorkflow2'] > 1 else \
           'Medium' if real > 40 or types['NWCollectData'] or types['NWStartWorkflow2'] else 'Small'
    print()
    print(f'Suggested size:  {size} (see docs/migration-plan.md, "Sizing")')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nwf', help='path to the .nwf export')
    ap.add_argument('--summary', action='store_true', help='print counts and dependencies only')
    args = ap.parse_args()
    outer, root = load(args.nwf)
    (print_summary if args.summary else print_tree)(outer, root)


if __name__ == '__main__':
    main()
