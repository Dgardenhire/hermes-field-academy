"""Capability mission: Give Hermes only the tools a job needs.

Placed on the Crossroads trail, Intermediate camp (school.PLACEMENTS): connect a client's tools safely. Facts read from
the Hermes source at v0.23.0: hermes_cli/web_routers/tools.py (the Tools tab writes platform_toolsets.cli),
tui_gateway/agent_factory.py (desktop chats honour agent.disabled_toolsets), hermes_cli/tools_config.py (plugin
toolsets on a saved list), toolsets.py (what each toolset holds).
"""

MISSION = {'id': 'f.toolsets',
 'title': 'Give Hermes only the tools a job needs',
 'order': 13,
 'idea_refs': [],
 'domain': 'D12',
 'level': 'intermediate',
 'minutes': {'read': 25, 'do': 30},
 'cost': {'chats': 3,
          'words': 'small change on most providers',
          'line': 'Expected cost: three short chats on your provider. The connector in this profile runs on your own '
                  "computer; its first start downloads it, so you'll need to be online."},
 'as_of': [{'fact': 'Switching a toolset in the Tools tab saves the list as platform_toolsets.cli',
            'file': 'hermes_cli/web_routers/tools.py',
            'pattern': '\\(``platform_toolsets\\.cli`` for most',
            'since': '0.23.0'},
           {'fact': "The app's chats also honour agent.disabled_toolsets",
            'file': 'tui_gateway/agent_factory.py',
            'pattern': 'def _load_disabled_toolsets\\(\\)',
            'since': '0.23.0'},
           {'fact': 'A plugin can add a toolset of its own, which goes on the same list',
            'file': 'hermes_cli/tools_config.py',
            'pattern': 'Plugin toolsets are first-class on a saved list',
            'since': '0.23.0'},
           {'fact': 'The terminal toolset holds the terminal and process tools',
            'file': 'toolsets.py',
            'pattern': '"terminal": _ts\\("Terminal/command execution and process management tools", \\["terminal", "process_manage"\\]\\)',
            'since': '0.23.0'},
           {'fact': 'The Capabilities page has a Tools tab',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "tabToolsets: 'Tools'",
            'since': '0.23.0'}],
 'recall': {'lead': 'In an earlier mission you connected an outside tool safely. Jot down two things:',
            'prompts': ["what a connector's folder decides", 'how you saw it ask before it changed something'],
            'seconds': 180,
            'from': 'f.connectors'},
 'claim': {'text': 'I can give Hermes only the tools a job needs, and prove from its settings and a real attempt that '
                   'the rest are gone.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'practice_note': 'This practice profile starts with every toolset Hermes ships switched on, and three meeting notes in '
                  'its practice folder under `meetings/`.',
 'fresh_text': 'This mission builds a new `academy-practice`, with its own practice folder. If the mission page shows '
               "that practice chats don't open in the practice folder, press **Copy** beside the folder, choose it "
               "with the chat's folder picker, and start a new practice chat before you begin.",
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field "
                  "Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': 'A chat in the profile gets the file tools and none of terminal, code, browser or web.',
               'proves_by': 'live:trimmed'},
              {'id': 's2',
               'text': 'A real attempt to run a program, after your last change, ran nothing.',
               'proves_by': 'live:probe_refused'},
              {'id': 's3',
               'text': 'The job still gets done: a brief that names every meeting.',
               'proves_by': 'live:job_done'},
              {'id': 's4',
               'text': "Nothing else in the profile gives back what you switched off.",
               'proves_by': 'live:plant_fixed'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.toolsets.try.md',
 'idea': 'md/f.toolsets.idea.md',
 'expert': 'md/f.toolsets.expert.md',
 'expert_lead': 'Ruth Abara runs the office for a dental practice. She wants Hermes to read the week\'s meeting notes '
                'and write one page for the partners. She has heard Hermes can run programs and browse the web, and '
                'she wants none of that near patient files.',
 'expert_note': 'Ruth and her practice are made up.',
 'record_example': 'md/f.toolsets.record-example.md',
 'lab': {'body': 'The practice folder holds three meeting notes under `meetings/`. The job: read them and write '
                 '`brief.md` in the practice folder, one line per meeting. Work only in `academy-practice`, and start '
                 'every chat with **Open practice chat**.\n'
                 '\n'
                 "1. **List the job's actions** before you change anything.\n"
                 '2. **Switch off what the job doesn\'t need.** Open **Capabilities**, set **Configuring:** to '
                 '`academy-practice`, and go to the **Tools** tab.\n'
                 '3. **Test it.** In a new practice chat, send: `Run the command date in the terminal.` Hermes should '
                 'tell you it can\'t.\n'
                 '4. **Do the job** in a new practice chat, and read the brief.\n'
                 '\n'
                 'Field Academy has also set one trap in the profile. If a check fails when you thought it should '
                 "pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the "
                 'Check step.',
         'checks_text': "Field Academy reads the practice profile's settings, chat records and practice folder itself. "
                        'Nothing needs pasting in.\n'
                        '\n'
                        '- The settings. Which toolsets does a chat get, after the Tools tab list and '
                        '`agent.disabled_toolsets`?\n'
                        '- Your chats. After your last change, did a request for the terminal run any program?\n'
                        '- The folder. Is there a `brief.md` that names every meeting?\n'
                        '- The rest of the profile. Can anything else still reach what you switched off?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted, so you can see where your guess '
                        'was off.',
         'profile': {'soul': ''},
         'setup': 'toolsets',
         'folder': True,
         'panels': ['folder', 'working_folder'],
         'try_fields': [{'id': 'toolsets_on', 'label': 'How many toolsets the Tools tab shows as on', 'kind': 'number',
                         'required': True},
                        {'id': 'guess_ran', 'label': 'Your guess: will Hermes run a terminal command if you ask?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}],
                         'required': True}],
         'note_fields': [{'id': 'actions', 'label': "The job's actions, listed before you changed anything", 'kind': 'long',
                          'required': True, 'min': 10, 'max': 600},
                         {'id': 'switched_off', 'label': 'What you switched off, and why', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 600},
                         {'id': 't_on', 'label': 'The toolsets a chat gets', 'kind': 'text', 'for': 'transfer',
                          'required': True, 'max': 200},
                         {'id': 't_run', 'label': 'Can a chat run a program?', 'kind': 'choice', 'for': 'transfer',
                          'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_home', 'label': 'Can a chat change files anywhere in their home folder?', 'kind': 'choice',
                          'for': 'transfer', 'required': True,
                          'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_change', 'label': "What you'd change, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['wide_connector'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1}},
 'live_checks': [{'id': 'trimmed', 'reader': 'toolsets.trimmed', 'visible': True},
                 {'id': 'probe_refused', 'reader': 'toolsets.probe_refused', 'visible': True},
                 {'id': 'job_done', 'reader': 'toolsets.job_done', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': True},
                 {'id': 'reading', 'reader': 'toolsets.reading', 'visible': True}],
 'explain': {'lead': 'Draw on the profile you just trimmed:',
             'question': 'You switched off the terminal toolset, and Hermes still changed a settings file it should '
                         "never touch. Name two ways that can happen, and how you'd check for each.",
             'rubric': {1: 'Says "the setting didn\'t save" or blames the model, without naming another way in',
                        2: 'Names one other way in (a connector, a plugin), with no way to check it',
                        3: 'Names a connector that reaches the folder and a plugin or second list that adds a toolset '
                           "back, and says where to look for each: the connector's folder in its settings, and the "
                           'Tools tab list beside `agent.disabled_toolsets`',
                        4: 'Adds a point from your own run: the connector you found, the probe that ran nothing, or the '
                           'count of toolsets before and after'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Here is someone else's setup. Without running anything, answer:\n"
                      '\n'
                      '- The Tools tab list (`platform_toolsets.cli`): `file`, `web`, `terminal`\n'
                      '- `agent.disabled_toolsets`: `terminal`\n'
                      '- One connector, `disk`, the filesystem connector pointed at their home folder, `~`\n'
                      '\n'
                      'Which toolsets does a chat get? Can it run a program? Can it change files anywhere in their home '
                      "folder? What would you change, and why?",
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-11-09', 'what': 'Built for the School of Hermes against the Hermes v0.23.0 source.'}]}
