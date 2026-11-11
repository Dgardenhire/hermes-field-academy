"""Foundations mission 9: Stop a mistake before it happens, or undo it.

Learner text comes from .planning/field-academy-v3/missions/09-safety.v2.md, learner sections only. Check 4 (the grid)
is read by Field Academy against the profile's settings, cell by cell, from the six choices the learner makes, with
their "how you know" lines kept as written. Check 2 needs the app's own snapshot list (rollback.list, read by the page
through host.requestProfile) beside the checkpoint store's branch for the practice folder, which Field Academy reads by
name; without the app's list it says how to look by hand.
"""

_GRID = [{'value': 'asks', 'label': 'Something asks first'},
         {'value': 'some_slip', 'label': 'It asks, but a saved "always" lets some through'},
         {'value': 'nothing', 'label': 'Nothing asks'}]
_UNDO = [{'value': 'undo', 'label': 'A snapshot can undo it'}, {'value': 'nothing', 'label': 'Nothing undoes it'}]
_DOOR = [{'value': 'no_connector', 'label': 'No connector in this profile'}, {'value': 'asks', 'label': 'It asks first (untrusted)'},
         {'value': 'nothing', 'label': 'Nothing asks (full trust)'}]


def _cell(cid, label, choices, phase='first'):
    return {'id': cid, 'label': label, 'kind': 'choice', 'choices': choices, 'required': True, 'for': phase}


def _why(cid, label, phase='first'):
    return {'id': cid + '_why', 'label': label, 'kind': 'text', 'max': 300, 'for': phase}


MISSION = {'id': 'f.safety',
 'title': 'Stop a mistake before it happens, or undo it',
 'order': 9,
 'idea_refs': [],
 'domain': 'D8',
 'level': 'beginner',
 'minutes': {'read': 25, 'do': 35},
 'cost': {'chats': 4,
          'words': 'small change on most providers',
          'line': 'Expected cost: three or four short chats in the practice profile. Type `/usage` at the end of each '
                  'one to see what it cost on your provider.'},
 'as_of': [{'fact': 'Checkpoints are off by default and keep 20 snapshots per folder',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"checkpoints": \\{\\s*"enabled": False,(?:\\s*#[^\\n]*)*\\s*"max_snapshots": 20',
            'since': '0.22'},
           {'fact': 'Files over 10 MB are left out of snapshots',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"max_file_size_mb": 10',
            'since': '0.22.4'},
           {'fact': 'Approvals default to smart, with a 300-second wait',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"mode": "smart",\\s*"timeout": 300',
            'since': '0.22'},
           {'fact': 'Saved "always" answers live in command_allowlist, empty by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"command_allowlist": \\[\\]',
            'since': '0.22'},
           {'fact': 'rm -r matches the rule called recursive delete',
            'file': 'tools/approval_detection.py',
            'pattern': '"recursive delete"\\)',
            'since': '0.22.4'},
           {'fact': 'Every /rollback first takes a pre-rollback snapshot',
            'file': 'tools/checkpoint_manager.py',
            'pattern': 'pre-rollback snapshot \\(restoring to',
            'since': '0.22.4'},
           {'fact': 'A removed always-allow entry stops counting at the next check, without a restart',
            'file': 'tools/approval.py',
            'pattern': 'must stop being honoured now',
            'since': '0.22.4'},
           {'fact': 'A connector with no trust setting runs at full trust',
            'file': 'tools/mcp_tool_registration.py',
            'pattern': "None -> ``full`` \\(compat default\\)",
            'since': '0.22.4'}],
 'recall': {'lead': 'Last mission you set up a job that runs with nobody watching. From memory, write two things:',
            'prompts': ['what a scheduled job does when it reaches a risky command',
                        "one thing your job's request had to say because the job couldn't ask you"],
            'seconds': 180,
            'from': 'f.schedules'},
 'claim': {'text': 'For anything Hermes does in a profile, I can say whether a mistake would be caught before it '
                   'happens or undone after, and I can set the profile up so every gap that can be closed is closed.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 # Shown on the Practice and Your turn steps, before the first chat (0.9 persona test).
 'practice_note': "Field Academy never changes this profile's approvals, and nothing in this mission asks you to turn them off. It added one connector, left at Hermes's default trust, so nothing asks before that connector acts. Until you fix it, it can write inside the practice folder without asking. Keep practice chats away from files you care about.",
 'fresh_text': 'This mission builds a new `academy-practice` when you set up practice.',
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "It replaces the one from an earlier mission, along with any job left in it. Field Academy saves its evidence first and asks you before it removes anything.",
 'standard': [{'id': 's1', 'text': 'Checkpoints are on in the practice profile.', 'proves_by': 'live:checkpoints_on'},
              {'id': 's2', 'text': 'You undid a file change with `/rollback`, and opening the file shows it.',
               'proves_by': 'live:rolled_back'},
              {'id': 's3',
               'text': "You read the practice profile's approval settings, and nothing there lets a risky terminal "
                       'command run unchecked.',
               'proves_by': 'live:approvals_safe'},
              {'id': 's4',
               'text': 'You filled in the grid below for the practice profile as you left it, and every cell matches '
                       'what Hermes really does there.',
               'proves_by': 'live:grid_matches'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.safety.try.md',
 'idea': 'md/f.safety.idea.md',
 'expert': 'md/f.safety.expert.md',
 'expert_lead': 'Loretta Abernathy keeps the books for a church and two small nonprofits on the shared computer in '
                'the church office. She wanted Hermes to tidy the monthly donation spreadsheets without putting '
                'anything else on that machine at risk.',
 'expert_note': 'Loretta is made up for this lesson. The settings and commands she uses are real.',
 'expert_slots': ['Which cell of the grid do you see people leave empty most often, and what did it cost them?',
                  'Do you ever use YOLO? When, and with what in place?',
                  "What's the one thing you'd never let Hermes do without asking, on a client's machine?",
                  'Have you ever needed /rollback for real? What happened?',
                  "When would you tell a client to run Hermes in a container, and when is that overkill?"],
 'record_example': 'md/f.safety.record-example.md',
 'lab': {'body': "The practice folder has a few files to work with. Before you arrived, Field Academy added one "
                 "connector to the practice profile and left it at Hermes's default trust. Finding it is part of the "
                 'job. Field Academy never changes your approval settings, and it never runs a command for you. The '
                 "approval card in this mission is Hermes's own, and you answer it.\n"
                 '\n'
                 '1. Set up the practice profile so a mistake can be caught before it happens and undone after. Use '
                 '**Settings → Safety**, with **Applies to** set to `academy-practice`. Open **Approvals**, read the '
                 'mode and the **Command Allowlist** box, and leave the mode on Smart or choose Manual. Leave the '
                 "allowlist empty. Then open the practice profile's connectors.\n"
                 '2. Check the **Working folder** line on the mission page says pass. Then press **Open practice '
                 'chat** and give Hermes a real tidying job in the practice folder, such as merging the two donation '
                 "files and deleting the `old-tests` folder. Paste the folder's location from the mission page into "
                 'your request. When the approval card for the delete appears, read it, deny it once, ask again, and '
                 'choose **Allow this session**. Never **Always allow**. Then prove each of the four checks in your '
                 'standard.\n'
                 '3. Fill in the six cells of the grid for the practice profile as you left it. One line per cell: '
                 "what's there, and how you know. For the connector row, say what the connector there does "
                 'once you have left it.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's settings and checkpoint list itself, in the "
                        'background.\n'
                        '\n'
                        '- Settings: are checkpoints on, are approvals on with nothing risky always allowed, and is the connector '
                        "no longer acting without asking? *Field Academy reads these. It changes none of them.*\n"
                        '- Checkpoint list: a snapshot for the practice folder, and the safety snapshot Hermes takes '
                        'whenever you roll back. *Field Academy reads this.*\n'
                        '- The restored file: does it match the snapshot you rolled back to? *Open it yourself: Field '
                        "Academy doesn't compare its contents.*\n"
                        "- Your grid: does each cell match the profile's settings and what you did? *Field Academy "
                        'reads the settings and checks each cell.*\n'
                        '\n'
                        'Your prediction sits beside each result.',
         'profile': {'soul': ''},
         'setup': 'safety',
         'folder': True,
         'panels': ['folder', 'working_folder', 'rollback_sample'],
         'try_fields': [{'id': 'guess_asks', 'label': 'Your guess: will Hermes ask you before it changes the file?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'guess_undo', 'label': 'Your guess: if you don\'t like the result, can you undo it?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'asked', 'label': 'What happened: did Hermes ask first?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                        {'id': 'undone', 'label': 'What happened: did /rollback give the file back?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]}],
         'note_fields': [_cell('tb', 'Terminal commands, before', _GRID), _why('tb', 'How you know'),
                         _cell('ta', 'Terminal commands, after', _UNDO), _why('ta', 'How you know'),
                         _cell('fb', 'File edits, before', _GRID), _why('fb', 'How you know'),
                         _cell('fa', 'File edits, after', _UNDO), _why('fa', 'How you know'),
                         _cell('cb', 'Connected tools, before', _DOOR), _why('cb', 'How you know, and what a new connector would bring'),
                         _cell('ca', 'Connected tools, after', _UNDO), _why('ca', 'How you know'),
                         _cell('tb', 'Terminal commands, before', _GRID, 'transfer'),
                         _cell('ta', 'Terminal commands, after', _UNDO, 'transfer'),
                         _cell('fb', 'File edits, before', _GRID, 'transfer'),
                         _cell('fa', 'File edits, after', _UNDO, 'transfer'),
                         _cell('cb', 'Connected tools, before (the email connector)', _DOOR, 'transfer'),
                         _cell('ca', 'Connected tools, after', _UNDO, 'transfer'),
                         {'id': 'worry', 'label': "The cell you'd worry about most, and the one setting that shrinks that "
                                                  'worry', 'kind': 'long', 'for': 'transfer', 'required': True, 'min': 15,
                          'max': 600}],
         'plants': ['open_connector'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1}},
 'live_checks': [{'id': 'checkpoints_on', 'reader': 'safety.checkpoints_on', 'visible': True},
                 {'id': 'rolled_back', 'reader': 'safety.rolled_back', 'visible': True},
                 {'id': 'approvals_safe', 'reader': 'safety.approvals_safe', 'visible': True},
                 {'id': 'grid_matches', 'reader': 'safety.grid_matches', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 'shared_grid', 'reader': 'safety.shared_grid', 'visible': True}],
 'explain': {'lead': 'Use your own run to answer:',
             'question': "Hermes sent an email you didn't mean to send. Which of your settings would have stopped it, "
                         "which wouldn't, and why?",
             'rubric': {1: 'Says checkpoints or `/rollback` would undo it',
                        2: "Knows nothing undoes it, but can't name a setting that would have stopped it",
                        3: 'Names what would have stopped it beforehand (an untrusted connector), and explains why '
                           "approvals don't see it: they watch terminal commands",
                        4: 'Adds a point from your own run: the cell your try landed in, a cell you found empty when '
                           'you opened the profile, or what an always-allow entry would do in a scheduled job'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Fill in the grid for a client's shared work computer, where three people use one Hermes profile "
                      'and one of them sends invoices through a connected email tool.\n'
                      '\n'
                      "- For each cell, write what you'd put there, or why it stays empty.\n"
                      "- Name the cell you'd worry about most, and the one setting that shrinks that worry.\n"
                      '\n'
                      "You don't apply these anywhere. Field Academy checks each cell against this mission's grid, set "
                      'up the way it teaches.',
              'live_checks': ['shared_grid']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/09-safety.v2.md (Hermes v0.22.4); the grid is read '
                                               'by Field Academy cell by cell.'}]}
