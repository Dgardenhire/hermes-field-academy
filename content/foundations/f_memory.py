"""Foundations mission 3: Save a fact to memory and check it stuck.

Learner text comes from .planning/field-academy-v3/missions/03-memory.v2.md, unchanged except where the format needs
it (the expert run's steps carry Did, Saw, Noticed and Ruled out lines). The build notes became the seed notes, the
plants, the live checks and the "as of Hermes" facts below. Every as_of pattern is checked against the Hermes source
by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.memory',
 'title': 'Save a fact to memory and check it stuck',
 'order': 3,
 'idea_refs': [4, 5, 11],
 'domain': 'D3',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 4,
          'words': 'usually a few cents',
          'line': 'Expected cost: about four short chats, mostly one-line questions.'},
 'as_of': [{'fact': 'MEMORY.md holds 2,200 characters by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"memory_char_limit":\\s*2200',
            'since': '0.22'},
           {'fact': 'USER.md holds 1,375 characters by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"user_char_limit":\\s*1375',
            'since': '0.22'},
           {'fact': 'Hermes estimates about 2.75 characters per token',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '2\\.75 chars/token',
            'since': '0.22'},
           {'fact': 'Memory approvals are off by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"write_approval":\\s*False,\\s*\\n\\s*"memory_char_limit"',
            'since': '0.22'},
           {'fact': 'Old chats are kept until you choose to clear them',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"auto_prune":\\s*False,(?:\\s*#[^\\n]*)*\\s*"retention_days":\\s*90',
            'since': '0.22.4'},
           {'fact': 'A save waiting for approval is reported as success, staged',
            'file': 'tools/memory_tool.py',
            'pattern': '"success":\\s*True,\\s*"staged":\\s*True',
            'since': '0.22.4'},
           {'fact': "A staged save says it isn't saved yet",
            'file': 'tools/write_approval.py',
            'pattern': 'Staged for approval \\(.*\\n.*Not yet saved',
            'since': '0.22.4'},
           {'fact': "Staged saves wait in the profile's pending folder",
            'file': 'tools/write_approval.py',
            'pattern': '"pending" / subsystem',
            'since': '0.22.4'},
           {'fact': 'The app titles a successful memory row Saved to memory',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "memory: \\{ done: 'Saved to memory'",
            'since': '0.22.4'},
           {'fact': 'Only a refused memory save gets the amber title',
            'file': 'apps/desktop/src/components/assistant-ui/tool/fallback-model/index.ts',
            'pattern': "memoryMissed = part\\.toolName === 'memory'",
            'since': '0.22.4'},
           {'fact': 'A real save reports how full memory is, like 29% — 640/2,200 chars',
            'file': 'tools/memory_tool_store.py',
            'pattern': '% — \\{current:,\\}/\\{limit:,\\} chars',
            'since': '0.22'},
           {'fact': 'A full memory makes Hermes remove or shorten other notes in one batch',
            'file': 'tools/memory_tool_store.py',
            'pattern': 'removes or shortens \\(patch\\) stale entries',
            'since': '0.22.4'}],
 'recall': {'lead': 'From the last two missions, write two things:',
            'prompts': ['the three layers of evidence for a claim, weakest to strongest',
                        'the parts of the package Hermes sends on every trip, and which one was biggest in your '
                        'setup'],
            'seconds': 180,
            'from': ['f.loop', 'f.cost']},
 'claim': {'text': "I can get one fact into Hermes's memory and prove, from the memory file and a brand-new chat, "
                   'that it stuck, without relying on what Hermes tells me.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': "This mission starts from a new `academy-practice`, set up with a few weeks' worth of notes already saved.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "A practice profile from an earlier mission is still here. When you set up practice, Field Academy saves its evidence to your record, asks you to confirm, and replaces it with this one.",
 'standard': [{'id': 's1',
               'text': 'The fact is in the memory file of the profile you used, as one short line.',
               'proves_by': 'live:memory_line'},
              {'id': 's2',
               'text': 'A brand-new chat uses the fact without you mentioning it.',
               'proves_by': 'live:fresh_use'},
              {'id': 's3',
               'text': 'You can say which kind of memory holds it, and why that kind.',
               'proves_by': 'rubric:explain'},
              {'id': 's4',
               'text': 'If something in your setup stops the fact from being saved, or costs you another note, you '
                       'find it and say how.',
               'proves_by': 'live:plant_fixed'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside your result at the end.'},
 'try': 'md/f.memory.try.md',
 'try_prompt': 'What do you know about how things are set up here, and what do you know about me?',
 'idea': 'md/f.memory.idea.md',
 'expert': 'md/f.memory.expert.md',
 'expert_lead': 'Ines Carvalho runs bookkeeping for six small clients. She wants Hermes to stop asking which client '
                'uses which accounting software.',
 'expert_note': 'Ines is made up; the clients and numbers are illustrative.',
 'expert_slots': ['What makes you distrust a "Saved"? What do you check first?',
                  'What do you check first when Hermes "forgot"?',
                  'Have you hit a full memory? How did you notice, and what did it cut?'],
 'record_example': 'md/f.memory.record-example.md',
 'lab': {'memory_view': True,  # the page offers Show memory file on this mission (0.9 persona test)
         'body': "The box above lists two notes already in this profile's memory that its owner can't lose. Whatever "
                 'happens to the other notes, those two stay.\n'
                 '\n'
                 '1. Pick one real fact Hermes should know about how you work: a deadline, a preference, a tool you '
                 'use. Keep it to one line.\n'
                 '2. Press **Open practice chat** and ask Hermes to save it to memory.\n'
                 '3. Prove each of the four checks above. How you prove them is up to you. For a new chat, press '
                 '**Open practice chat** again. For the file, press **Show memory file**; it shows both `MEMORY.md` '
                 'and `USER.md`.\n'
                 '\n'
                 'The practice setup has one snag waiting that can block your save or cost you a note. If the file '
                 "and the new chat don't agree with what Hermes told you, find the reason before you press Check.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's memory files, its settings and its chat records "
                        "itself. You don't need to copy anything out of Hermes.\n"
                        '\n'
                        "- Is your fact's line in `MEMORY.md` or `USER.md` for `academy-practice`, and short?\n"
                        '- Was there a new chat, started after the save, where Hermes used the fact before you '
                        'mentioned it?\n'
                        '- Are the two notes the page listed still there?\n'
                        '- If something was planted to stop or spoil the save, is it fixed, and did your fact land '
                        'afterward?\n'
                        '- Your answer to check 3. Does it name the right kind of memory, with a reason that holds '
                        'up?',
         'profile': {'soul': ''},
         'seed_notes': [{'text': 'Shift plans use 24-hour times, like {shift_example}, and list the earliest shift first.',
                         'key': True},
                        {'text': 'The weekly ops summary goes to the {ops_channel} channel on {summary_day}, as '
                                 '{bullets} bullets or fewer.',
                         'key': True},
                        {'text': "Refunds over {refund} dollars need the owner's yes before they are sent.", 'key': True},
                        {'text': 'The walk-in fridge is logged at {fridge_times}; anything above {fridge_max} C is '
                                 'reported at once.',
                         'key': True},
                        {'text': 'Working files live in the shared folder {folder}; drafts go in {folder}/Drafts '
                                 'until approved.',
                         'key': False},
                        {'text': 'Supplier orders are placed on {order_day} before noon; the produce supplier needs '
                                 "{notice} days' notice.",
                         'key': False},
                        {'text': "Customer replies are signed '{sign_off}', never with a first name, and answered "
                                 'within one working day.',
                         'key': False},
                        {'text': 'The team calendar is the shared one called {calendar}; personal calendars are never '
                                 'edited.',
                         'key': False}],
         # Filled per learner from the attempt's seed (foundations.seed_params_for), so two learners' notes differ in
         # names and numbers as well as in which notes are drawn.
         'seed_params': {'shift_example': ['14:00, never 2 pm', '15:30, never 3:30 pm', '09:00, never 9 am',
                                           '18:00, never 6 pm'],
                         'ops_channel': ['#ops', '#ops-team', '#floor', '#front-desk'],
                         'summary_day': ['Friday', 'Thursday', 'Monday'],
                         'bullets': ['five', 'four', 'six'],
                         'refund': ['150', '200', '250', '300', '400'],
                         'fridge_times': ['7:00 and 15:00', '6:30 and 14:30', '8:00 and 16:00'],
                         'fridge_max': ['4', '5'],
                         'folder': ['Ops/2026', 'Ops-Shared', 'Team/Ops'],
                         'order_day': ['Tuesdays', 'Mondays', 'Wednesdays'],
                         'notice': ['two', 'three'],
                         'sign_off': ['The Ops Team', 'The Front Desk', 'Customer Care'],
                         'calendar': ['Ops Rota', 'Team Rota', 'Shift Board']},
         'seed_draw': {'key': 2, 'other': 3},
         'plants': ['write_approval', 'memory_full'],
         'plants_at': {'beginner': 1, 'intermediate': 2, 'advanced': 2}},
 'live_checks': [{'id': 'memory_line', 'reader': 'memory.line_matching', 'visible': True},
                 {'id': 'fresh_use', 'reader': 'sessions.used_before_said', 'visible': True},
                 {'id': 'notes_kept', 'reader': 'memory.seed_kept', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plant.fixed', 'visible': False},
                 {'id': 'user_line', 'reader': 'memory.user_line', 'visible': True},
                 {'id': 'one_off', 'reader': 'memory.one_off_decision', 'visible': True}],
 'explain': {'lead': 'Think about what tripped you up, or nearly did, in your run:',
             'question': "A friend told Hermes something in one chat, and a new chat didn't know it. Give her the "
                         "likeliest reasons, in the order you'd check them, and how she'd check each one.",
             'rubric': {1: 'Says Hermes is unreliable, with no reason',
                        2: 'Names one real cause, such as the save never happening',
                        3: 'Names three causes, each with a check: the save never happened (row and file), the save '
                           'is waiting for approval, the note went to a different profile, or a full memory cut it',
                        4: 'Adds one reason from your own run, such as saving in the wrong profile or an approval '
                           'still waiting, and puts the checks in a sensible order'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'Two more candidates, and only one should get in:\n'
                      '\n'
                      '- A fact about you, such as your role or how you like answers laid out. Ask Hermes to save '
                      'it. It belongs in `USER.md`; check that it went there.\n'
                      '- Something one job needs once, like "the printer quote came in at noon today." Decide '
                      'whether it earns a line, using the judgment above, and write one sentence on why. If you '
                      "think it doesn't, don't save it.\n"
                      '\n'
                      "Then check how full memory is now, from the last save row's result, and work out how many "
                      'one-line notes still fit.',
              'live_checks': ['user_line', 'one_off']},
 'review': [],
 'revisions': [{'date': '2026-10-21', 'what': 'Built from missions/03-memory.v2.md (Hermes v0.22.4).'},
               {'date': '2026-10-22',
                'what': 'Re-synced after the teaching review; the wrong-profile plant is dropped, one practice '
                        'profile.'},
               {'date': '2026-10-22',
                'what': 'Review 2: two protected notes per seed, shown on the page; the transfer is a USER.md fact '
                        'plus a save-or-skip call.'}]}
