"""Teaching mission: Set Hermes up for someone else.

Placed on the Guide trail, Build camp (school.PLACEMENTS). The learner prepares a practice profile for a person from
their brief: who Hermes works for and the rule it keeps (SOUL.md), the one fact it must always know (memory), and a
safe setup for someone who doesn't want programs run (approvals on, terminal off). Facts read from the Hermes source at
v0.23.0; the SOUL.md, memory, approvals and Tools tab facts are the ones missions 3, 4, 7 and 9 and f.toolsets check.
"""

MISSION = {'id': 'f.teach-profile',
 'title': 'Set Hermes up for someone else',
 'order': 14,
 'idea_refs': [],
 'domain': 'D13',
 'level': 'advanced',
 'minutes': {'read': 20, 'do': 35},
 'cost': {'chats': 3,
          'words': 'small change on most providers',
          'line': 'Expected cost: two or three short chats on your provider.'},
 'as_of': [{'fact': 'A new profile can be told who it works for in SOUL.md, from Edit SOUL.md on its square',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "editSoul: 'Edit SOUL\\.md…'",
            'since': '0.23.0'},
           {'fact': 'Switching a toolset in the Tools tab saves the list as platform_toolsets.cli',
            'file': 'hermes_cli/web_routers/tools.py',
            'pattern': '\\(``platform_toolsets\\.cli`` for most',
            'since': '0.23.0'}],
 'recall': {'lead': 'In an earlier mission you gave Hermes only the tools a job needs. Jot down two things:',
            'prompts': ['where the Tools tab saves its list', 'how you proved a toolset was really off'],
            'seconds': 180,
            'from': 'f.toolsets'},
 'claim': {'text': "I can set Hermes up for another person from what they tell me, and prove from its files and a first "
                   "chat that it works for them and keeps their rules.",
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'practice_note': 'The practice profile stands in for the person you are setting Hermes up for. Their brief is '
                  '`brief.txt` in its practice folder.',
 'fresh_text': 'This mission builds a new `academy-practice`, with its own practice folder. If the mission page shows '
               "that practice chats don't open in the practice folder, press **Copy** beside the folder, choose it "
               "with the chat's folder picker, and start a new practice chat before you begin.",
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field "
                  "Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1', 'text': "SOUL.md says who Hermes works for and keeps their one rule.", 'proves_by': 'live:soul'},
              {'id': 's2', 'text': 'The one thing Hermes must always know about their work is in memory.', 'proves_by': 'live:memory'},
              {'id': 's3', 'text': 'Approvals are on and Hermes can\'t run programs, as they asked.', 'proves_by': 'live:safe'},
              {'id': 's4', 'text': 'A brand-new chat answers as their Hermes without being told who they are.', 'proves_by': 'live:first_chat'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.teach-profile.try.md',
 'idea': 'md/f.teach-profile.idea.md',
 'expert': 'md/f.teach-profile.expert.md',
 'expert_lead': "Kwame Mensah sets Hermes up for people in his building who've never used it. This week it's Elena, who "
                'runs a flower stall and wants help with orders.',
 'expert_note': 'Kwame and Elena are made up.',
 'record_example': 'md/f.teach-profile.record-example.md',
 'lab': {'body': "`brief.txt` in the practice folder is from the person you're setting Hermes up for. The job: make "
                 '`academy-practice` theirs. Work only in `academy-practice`.\n'
                 '\n'
                 '1. **Read the brief.** Note who they are, the one fact, the one rule and what they asked you to keep away.\n'
                 '2. **Write SOUL.md for them.** Right-click the practice profile\'s square, **Edit SOUL.md…**. Say who '
                 'Hermes works for and keep their rule in their words.\n'
                 '3. **Put the fact in memory.** In a practice chat, ask Hermes to remember it. Then press **Show memory '
                 'file** and see it there.\n'
                 '4. **Make it safe for them.** Approvals on. In **Capabilities**, **Tools**, switch off what runs programs.\n'
                 '5. **Meet their Hermes.** In a new practice chat, without saying their name, ask: "Who do you work for, '
                 'and what should you never do?"\n'
                 '\n'
                 'Field Academy has also set one trap in the profile. At Advanced there are two. If a check fails when '
                 "you thought it should pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the "
                 'Check step.',
         'checks_text': "Field Academy reads the practice profile's SOUL.md, memory file, settings and chat records itself.\n"
                        '\n'
                        '- SOUL.md. Does it name who Hermes works for, and keep their rule?\n'
                        '- Memory. Is their fact a line in MEMORY.md?\n'
                        '- Settings. Are approvals on, and is the terminal toolset off?\n'
                        '- A new chat. Did it answer as their Hermes without being told?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted.',
         'profile': {'soul': ''},
         'setup': 'teach_profile',
         'folder': True,
         'memory_view': True,
         'panels': ['folder', 'working_folder'],
         'try_fields': [{'id': 'guess_knows', 'label': 'Your guess: will a new chat know who it works for?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}],
                         'required': True}],
         'note_fields': [{'id': 'from_brief', 'label': 'What you took from the brief, and where you put each thing', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 800},
                         {'id': 't_knows', 'label': 'Does a new chat start with the rule?', 'kind': 'choice', 'for': 'transfer',
                          'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_asks', 'label': 'Does anything check with them before a risky command?', 'kind': 'choice',
                          'for': 'transfer', 'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_change', 'label': "What you'd change, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['approvals_off', 'wide_connector'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'soul', 'reader': 'teach.soul_for_them', 'visible': True},
                 {'id': 'memory', 'reader': 'teach.memory_for_them', 'visible': True},
                 {'id': 'safe', 'reader': 'teach.safe_for_them', 'visible': True},
                 {'id': 'first_chat', 'reader': 'teach.first_chat_knows', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 'reading', 'reader': 'teach.profile_reading', 'visible': True}],
 'explain': {'lead': 'Draw on the profile you just set up:',
             'question': "Someone's rule went into a chat you had with their Hermes, and a week later Hermes broke it. "
                         'Why, and where should the rule have gone?',
             'rubric': {1: 'Blames the model, or says Hermes "forgot", without saying where the rule lived',
                        2: 'Says chats end, but not where a rule lasts',
                        3: 'Says a chat is gone when it ends; a rule that must hold every time goes in SOUL.md, and a '
                           'fact in memory, and a new chat proves both',
                        4: 'Adds a point from your own run: the trap you found, or what the first chat said'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "A friend set up Hermes for their mum. Without running anything, answer:\n"
                      '\n'
                      '- SOUL.md is empty.\n'
                      '- In the first chat they typed: "Never pay a bill without asking me."\n'
                      '- Approvals are off, "so she isn\'t bothered by questions".\n'
                      '\n'
                      'Does a new chat start with the rule? Does anything check with her before a risky command? What '
                      "would you change, and why?",
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-11-09', 'what': 'Built for the School of Hermes, Guide trail.'}]}
