"""Foundations mission 1: Check whether Hermes really did what it says.

Learner text comes from .planning/field-academy-v3/missions/01-loop.v2.md, learner sections only (everything from "## Build
notes" down stays in the planning file). Converted unchanged except where the format needs it: the expert run's steps
carry Did, Saw, Noticed and Ruled out lines. Plants live in plants_a.py, checks in foundations_checks_a.py, and every
as_of pattern is checked against the Hermes source by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.loop',
 'title': 'Check whether Hermes really did what it says',
 'order': 1,
 'idea_refs': [1],
 'domain': 'D1',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 3,
          'words': 'usually a few cents',
          'line': 'Expected cost: three short chats in the practice profile. The record shows what Hermes logged for '
                  'them.'},
 'as_of': [{'fact': 'There is no limit on the number of trips by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"max_turns":\\s*None',
            'since': '0.22'},
           {'fact': 'Reads and searches in one trip can run together',
            'file': 'agent/tool_dispatch_helpers.py',
            'pattern': '_PARALLEL_SAFE_TOOLS = frozenset',
            'since': '0.22.4'},
           {'fact': 'A file save is titled Edited file whether or not it worked',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "write_file: \\{ done: 'Edited file'",
            'since': '0.22.4'}],
 'recall': {'lead': 'This is your first mission, so reach back further. Think of the last time someone told you a '
                    "job was finished and it wasn't. A contractor, a coworker, an app. Write two things:",
            'prompts': ["how you found out it wasn't done", "what you'd check first if it happened again"],
            'seconds': 180,
            'from': ''},
 'claim': {'text': 'I can tell, from what Hermes actually did, whether its "done" is true.', 'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': 'When you press **Start**, Field Academy builds a new practice profile called `academy-practice`, '
               'with its own practice folder, just for this mission. If one is left from an earlier mission, it '
               "saves that one's evidence to your record first, asks you to confirm, and then replaces it. Your own "
               "profile isn't touched.",
 'standard': [{'id': 's1',
               'text': 'You can say what Hermes did, step by step, in order.',
               'proves_by': 'live:steps_match'},
              {'id': 's2', 'text': 'You name every claim in its final answer.', 'proves_by': 'live:claims_listed'},
              {'id': 's3', 'text': 'You check each claim against the real result.', 'proves_by': 'rubric:explain'},
              {'id': 's4',
               'text': "You find what's wrong with the real result, whether or not Hermes admitted it, and get the "
                       'output right.',
               'proves_by': 'live:plant_fixed'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. Nobody grades "
                     "the guess. When you finish, you'll see it beside your result, so you learn how well you judge "
                     'your own work.'},
 'try': 'md/f.loop.try.md',
 'try_prompt': '',
 'idea': 'md/f.loop.idea.md',
 'expert': 'md/f.loop.expert.md',
 'expert_lead': 'Bev Kowalski manages the office for a plumbing company with six vans. Every Friday she combines the '
                "week's job sheets into one summary for the owner. She's trying Hermes on it.",
 'expert_note': 'Bev and her numbers are made up for illustration.',
 'expert_slots': ['When Hermes hands you a summary, which claim do you check first, and why that one?',
                  'Has a Hermes "done" ever cost you something? What was the tell you missed?',
                  'When do you steer, and when do you stop the turn and start over?'],
 'record_example': 'md/f.loop.record-example.md',
 'lab': {'body': 'The practice folder has three small files. This page shows a request card for them, with the '
                 "folder's full location already filled in. Something about those files will make the real result "
                 'come out wrong. Hermes may tell you, or it may not.\n'
                 '\n'
                 '1. Press **Open practice chat** and paste the request from the card.\n'
                 '2. Watch the rows as it runs. Steer it if it wanders.\n'
                 '3. Before you read the answer closely, write down what Hermes did, step by step.\n'
                 '4. Read the answer and write every claim it makes, one per line.\n'
                 "5. Check each claim against the real files. The box below shows how to see a file's date and how "
                 'to unlock a file.\n'
                 "6. Write down what's wrong with the real result. Look for an output that didn't change, an input "
                 "that's empty, and rows that are missing or made up.\n"
                 '7. Fix the cause and get the output right. If an input is empty or short, the right output says so '
                 "plainly: which file, and what's missing. Don't let Hermes fill the gap with guesses.\n"
                 '\n'
                 '**If Hermes told the truth.** Sometimes the answer admits the problem: "I couldn\'t save the '
                 'file," or "one file was empty." Then no claim is false. Show the evidence for each claim anyway, '
                 'the row and the real file behind it, and still fix the cause.\n'
                 '\n'
                 "> **Seeing a file's date, and unlocking a file.**\n"
                 '>\n'
                 '> - **Windows.** Open the folder in File Explorer (paste the location into the address bar). '
                 'Choose **View → Details**; the **Date modified** column shows when each file last changed. To '
                 'unlock a file, right-click it, choose **Properties**, clear the **Read-only** box, and press '
                 '**OK**.\n'
                 '>\n'
                 '> - **Mac.** Open the folder in Finder (**Go → Go to Folder**, paste the location). Press `Cmd+2` '
                 'for the list view, which shows **Date Modified**. To unlock a file, select it, press `Cmd+I`, and '
                 'clear the **Locked** box.\n'
                 '>\n'
                 "> - **Linux.** `ls -l` in the folder shows each file's date. `chmod u+w` and the file name makes "
                 'it writable.\n'
                 '>\n'
                 "> A file whose date is older than the moment you sent the request wasn't written by this job, "
                 'whatever the answer says.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice folder and Hermes's own chat record itself. You don't need "
                        'to copy anything out of Hermes.\n'
                        '\n'
                        "- Your step list beside the steps in Hermes's record, in order. Steps Hermes ran together "
                        'in one trip can be listed in any order.\n'
                        '- Your claim list beside the answer. Did you catch every claim?\n'
                        "- Your list of what's wrong with the real result. Does it name the problem in the files? If "
                        'the answer hid it, is that claim marked false? If the answer admitted it, does each claim '
                        'have its evidence?\n'
                        '- For each claim you checked, did you name something real you looked at?\n'
                        '- The output file after your fix. Is it there, written after the job started, with the '
                        'right content?\n'
                        '- The real number of trips the model made, shown beside your estimate from the Practice step.',
         'profile': {'soul': ''},
         'plants': ['output_locked', 'input_empty', 'rows_short'],
         'plants_at': {'beginner': 1, 'intermediate': 2, 'advanced': 2},
         'note_fields_a': {'first': [{'id': 'steps',
                                      'label': 'What Hermes did, step by step, one per line',
                                      'kind': 'lines',
                                      'min_lines': 2,
                                      'max': 3000},
                                     {'id': 'claims',
                                      'label': 'Every claim in its final answer, one per line',
                                      'kind': 'lines',
                                      'min_lines': 1,
                                      'max': 3000},
                                     {'id': 'checked',
                                      'label': 'For each claim, what real thing you looked at',
                                      'kind': 'textarea',
                                      'min': 20,
                                      'max': 3000},
                                     {'id': 'wrong',
                                      'label': "What's wrong with the real result",
                                      'kind': 'textarea',
                                      'min': 10,
                                      'max': 2000},
                                     {'id': 'false_claims',
                                      'label': 'Claims you marked false, if the answer hid the problem',
                                      'kind': 'textarea',
                                      'required': False,
                                      'max': 2000}],
                           'transfer': [{'id': 'plan',
                                         'label': "Before you read the answer: the claims you'll check, and how, one "
                                                  'per line',
                                         'kind': 'lines',
                                         'min_lines': 2,
                                         'max': 2000},
                                        {'id': 'steer_after',
                                         'label': 'Which step your /steer note arrived after',
                                         'kind': 'text',
                                         'min': 3,
                                         'max': 300}],
                           'try': [{'id': 'guess',
                                    'label': 'Your guess: how many steps?',
                                    'kind': 'int',
                                    'min': 0,
                                    'max': 500},
                                   {'id': 'rows', 'label': 'Rows you counted', 'kind': 'int', 'min': 0, 'max': 500},
                                   {'id': 'sentence',
                                    'label': 'One sentence from the answer that says Hermes did something',
                                    'kind': 'text',
                                    'min': 5,
                                    'max': 400}]}},
 'live_checks': [{'id': 'steps_match', 'reader': 'loop.steps_match', 'visible': True},
                 {'id': 'claims_listed', 'reader': 'loop.claims_listed', 'visible': True},
                 {'id': 'trips', 'reader': 'loop.trips', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'loop.result_right', 'visible': False},
                 {'id': 'second_job', 'reader': 'loop.second_job', 'visible': True}],
 'explain': {'lead': 'Use what you saw in your run to answer this:',
             'question': 'Your colleague says Hermes "did the whole report." What three things do you check before '
                         'you believe it?',
             'rubric': {1: 'Says to "check it," with no specific check',
                        2: "Names checks, but only against Hermes's words or its rows",
                        3: 'Names three checks, at least one against the real output, with what each would catch',
                        4: 'Adds a reason from your own run and a sensible order: the claims a mistake would hide in '
                           'come first'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'A second job, with different files, is waiting in the practice folder. Its request card is on '
                      'this page. Press **Open practice chat** for a fresh chat and paste it.\n'
                      '\n'
                      "- This time, before you read the answer, write which claims you'll check and how you'll check "
                      'each one.\n'
                      '- Use `/steer` once on purpose, even if Hermes is on track. Note which step your note arrived '
                      'after.\n'
                      '\n'
                      'Then compare: did the plan you wrote before reading catch anything your first run missed?',
              'live_checks': ['second_job']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/01-loop.v2.md (Hermes v0.22.4).'}]}
