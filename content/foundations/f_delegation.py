"""Capability mission: Hand work to helper agents, and check what each one did.

Placed on the Boundary Keeper trail, Intermediate camp (school.PLACEMENTS): matching each job to the right kind of
agent. Facts read from the Hermes source at v0.23.0: tools/delegate_tool.py, tools/delegate_tool_tasks.py,
tools/delegate_tool_child_run.py, tools/delegate_tool_config.py, hermes_cli/config_defaults.py.
"""

MISSION = {'id': 'f.delegation',
 'title': 'Hand work to helper agents, and check what each one did',
 'order': 12,
 'idea_refs': [],
 'domain': 'D11',
 'level': 'intermediate',
 'minutes': {'read': 25, 'do': 35},
 'cost': {'chats': 3,
          'words': 'a few short chats on your provider, plus one per helper',
          'line': 'Expected cost: two or three short chats on your provider, and each helper is a short chat of its '
                  'own, so three helpers cost about as much as three more short chats.'},
 'as_of': [{'fact': 'Helpers start without memory and without context files such as AGENTS.md',
            'file': 'tools/delegate_tool.py',
            'pattern': 'skip_context_files=True, skip_memory=',
            'since': '0.23.0'},
           {'fact': 'Each helper is saved as a chat of its own, marked subagent and linked to the chat that started it',
            'file': 'tools/delegate_tool_child_run.py',
            'pattern': 'session_id=child.session_id, source="subagent",',
            'since': '0.23.0'},
           {'fact': 'A batch larger than delegation.max_concurrent_children is refused whole: Too many tasks',
            'file': 'tools/delegate_tool_tasks.py',
            'pattern': 'Too many tasks: \\{len\\(tasks\\)\\} provided, but max_concurrent_children is \\{max_children\\}',
            'since': '0.23.0'},
           {'fact': 'An empty delegation.model means helpers use the main model',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"model": "",  # e.g. "google/gemini-3-flash-preview" \\(empty = inherit parent\\)',
            'since': '0.23.0'},
           {'fact': 'Up to 10 helpers run at once unless delegation.max_concurrent_children says otherwise',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"max_concurrent_children": 10,',
            'since': '0.23.0'}],
 'recall': {'lead': 'In an earlier mission you kept two jobs apart in two profiles. Jot down two things:',
            'prompts': ['one thing a new profile starts without', 'how you checked which profile a chat was in'],
            'seconds': 180,
            'from': 'f.profiles'},
 'claim': {'text': 'I can hand parts of a job to helper agents at once, give each one what it needs, and prove from '
                   "Hermes's records what each helper did.",
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'practice_note': 'This practice profile has three client folders under `clients/` in its practice folder, and one '
                  'house rule saved in its memory. Helpers are chats Hermes starts for itself, so each one costs about '
                  'as much as a short chat of your own.',
 'fresh_text': 'This mission builds a new `academy-practice`, with its own practice folder. If the mission page shows '
               "that practice chats don't open in the practice folder, press **Copy** beside the folder, choose it "
               "with the chat's folder picker, and start a new practice chat before you begin.",
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field "
                  "Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': 'One request handed every client to a helper of its own, all at once, and Hermes ran it.',
               'proves_by': 'live:batch'},
              {'id': 's2',
               'text': "Each helper worked in one client's folder and no other.",
               'proves_by': 'live:helpers_ran'},
              {'id': 's3',
               'text': "Every client has a summary with its own figures, no one else's, ending with the house rule.",
               'proves_by': 'live:summaries_right'},
              {'id': 's4',
               'text': 'You can say what a helper starts without, and how you made sure it got what it needed.',
               'proves_by': 'rubric:explain'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.delegation.try.md',
 'idea': 'md/f.delegation.idea.md',
 'expert': 'md/f.delegation.expert.md',
 'expert_lead': 'Nadia Okafor keeps the books for four small charities. Every month she wants one page per charity: '
                "money in, money out, anything odd. She asks Hermes to do all four at once.",
 'expert_note': 'Nadia and her charities are made up.',
 'record_example': 'md/f.delegation.record-example.md',
 'lab': {'body': 'The practice folder holds three client folders under `clients/`, each with a `notes.txt`. The '
                 "profile's memory holds a house rule for client summaries. The job: one `summary.md` in each client's "
                 "folder, written by a helper of that client's own, all three at once. Work only in "
                 '`academy-practice`, and start every chat with **Open practice chat**.\n'
                 '\n'
                 '1. **Read the memory first.** Press **Show memory file** and find the house rule.\n'
                 "2. **Write the request.** Ask for one helper per client, all at once. Give each helper its client's "
                 'folder, by full path, and everything the house rule says. Helpers start without memory.\n'
                 "3. **Check each helper's work.** Open each `summary.md`. Does it quote its own client's budget, and "
                 'only that one? Does it end with the house rule?\n'
                 "4. **If a batch is refused or a helper fails,** find the setting behind it, fix it, and ask again in a "
                 'new chat.\n'
                 '\n'
                 'Field Academy has also set one trap in the profile. At Advanced there are two. If a check fails when '
                 "you thought it should pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the "
                 'Check step.',
         'checks_text': "Field Academy reads the practice profile's chat records, its settings and the client folders "
                        'itself. Nothing needs pasting in.\n'
                        '\n'
                        '- Your chats. Is there one hand-off to helpers that covers every client, and did it run?\n'
                        "- The helpers' own chats. Hermes saves each helper as a chat marked subagent. Did each one "
                        "stay in one client's folder?\n"
                        "- The folders. Does each `summary.md` give its own client's budget, no other, and end with "
                        'the house rule?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted, so you can see where your guess '
                        'was off.',
         'profile': {'soul': ''},
         'setup': 'delegation',
         'folder': True,
         'memory_view': True,
         'panels': ['folder', 'working_folder'],
         'try_fields': [{'id': 'guess_rule', 'label': 'Your guess: will each helper follow the house rule in memory?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}],
                         'required': True},
                        {'id': 'followed', 'label': 'How many of the three summaries ended with the house rule',
                         'kind': 'number', 'required': True}],
         'note_fields': [{'id': 'split', 'label': 'How you split the job between helpers', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 600},
                         {'id': 'passed_on', 'label': 'What you told every helper, and why', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 800},
                         {'id': 't_runs', 'label': 'How many helpers run', 'kind': 'number', 'for': 'transfer',
                          'required': True},
                         {'id': 't_model', 'label': 'Which model the helpers use', 'kind': 'text', 'for': 'transfer',
                          'required': True, 'max': 200},
                         {'id': 't_rule', 'label': 'Do the helpers follow the rule in AGENTS.md?', 'kind': 'choice',
                          'for': 'transfer', 'required': True,
                          'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_change', 'label': "What you'd change, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['one_helper', 'helper_model_typo'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'batch', 'reader': 'delegation.batch', 'visible': True},
                 {'id': 'helpers_ran', 'reader': 'delegation.helpers_ran', 'visible': True},
                 {'id': 'summaries_right', 'reader': 'delegation.summaries_right', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 'reading', 'reader': 'delegation.reading', 'visible': True}],
 'explain': {'lead': 'Draw on the helpers you just ran:',
             'question': 'A helper wrote a summary that broke your house rule, though Hermes knows the rule. Why did '
                         "it happen, and what are two ways to make sure the next helper follows it?",
             'rubric': {1: 'Blames the model, or says the helper "forgot", without saying what a helper starts with',
                        2: "Says helpers don't share the chat, but not that they start without memory and context files",
                        3: 'Says helpers start without memory and context files such as AGENTS.md, and gives two fixes: '
                           "put the rule in each helper's task, or have Hermes check each summary before it reports",
                        4: 'Adds a point from your own run: the summary that missed the rule, a refused batch, or the '
                           'helper chats you found in the records'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Here is someone else's setup. Without running anything, answer:\n"
                      '\n'
                      '- `delegation.max_concurrent_children: 2`\n'
                      '- `delegation.model:` left empty\n'
                      '- The house rule for reports is in the project\'s `AGENTS.md`, not in memory.\n'
                      '- The request: "Give each of my four stores to its own helper and have each write a report."\n'
                      '\n'
                      'How many helpers run? Which model do they use? Do they follow the rule in `AGENTS.md`? What '
                      "would you change, and why?",
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-11-09', 'what': 'Built for the School of Hermes against the Hermes v0.23.0 source.'}]}
