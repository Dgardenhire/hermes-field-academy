"""Foundations mission 4: Start a new chat at the right time.

Learner text comes from .planning/field-academy-v3/missions/04-new-chats.v2.md, learner sections only (everything from "## Build
notes" down stays in the planning file). Converted unchanged except where the format needs it: the expert run's steps
carry Did, Saw, Noticed and Ruled out lines. Plants live in plants_a.py, checks in foundations_checks_a.py, and every
as_of pattern is checked against the Hermes source by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.new-chats',
 'title': 'Start a new chat at the right time',
 'order': 4,
 'idea_refs': [5],
 'domain': 'D3',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 5,
          'words': 'usually a few cents',
          'line': 'Expected cost: four or five short chats in the practice profile, each only a question or two '
                  'long.'},
 'as_of': [{'fact': 'Compaction starts at half full by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"threshold":\\s*0\\.50',
            'since': '0.22'},
           {'fact': 'Windows under 512,000 tokens compact at three quarters',
            'file': 'agent/context_compressor.py',
            'pattern': '_SMALL_CTX_WINDOW_LIMIT = 512_000\\n_SMALL_CTX_THRESHOLD_PERCENT = 0\\.75',
            'since': '0.22.4'},
           {'fact': 'Compaction keeps the same chat',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"in_place":\\s*True',
            'since': '0.22.4'}],
 'recall': {'lead': 'Last mission you got a fact into memory and proved it stuck. Write two things:',
            'prompts': ['why asking in the chat where you saved the fact proved nothing',
                        'what Hermes does when memory is full and you ask it to save one more note'],
            'seconds': 180,
            'from': 'f.memory'},
 'claim': {'text': 'I can change how Hermes behaves and know exactly when the change takes effect.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': 'Like every mission, this one builds its own `academy-practice` when you set up practice. Your own profiles stay as they are.',
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "The practice profile from an earlier mission is replaced once Field Academy has saved its evidence to your record and you've confirmed.",
 'standard': [{'id': 's1',
               'text': "Your new rule is in the practice profile's `SOUL.md`.",
               'proves_by': 'live:rule_in_soul'},
              {'id': 's2',
               'text': 'A chat started before the edit still behaves the old way.',
               'proves_by': 'live:before_chat'},
              {'id': 's3',
               'text': 'A chat started after the edit behaves the new way.',
               'proves_by': 'live:after_chat'},
              {'id': 's4',
               'text': 'You can explain when a chat that never ends would pick up the rule, and what to do instead '
                       'of waiting.',
               'proves_by': 'rubric:explain'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside your result at the end.'},
 'try': 'md/f.new-chats.try.md',
 'try_prompt': '',
 'idea': 'md/f.new-chats.idea.md',
 'expert': 'md/f.new-chats.expert.md',
 'expert_lead': "Kenji Mori owns a picture-framing shop. Customers text the shop's Telegram bot for quotes, and "
                'Hermes drafts the replies from a profile called `shop`. Kenji wants the drafts plainer: no '
                'exclamation marks, and every quote ending with "Mori Framing, open Tuesday to Saturday."',
 'expert_note': 'Kenji is made up; his shop and its dates are illustrative.',
 'expert_slots': ["How often do you start a new chat on a messaging bot, and what tells you it's time?",
                  'What goes in your SOUL.md, and what do you keep out of it?',
                  'Has a project file ever fought your SOUL.md? How did you find out?'],
 'record_example': 'md/f.new-chats.record-example.md',
 'lab': {'memory_view': True,  # the page offers Show memory file on this mission (0.9 persona test)
         'body': 'The mission screen offers three rules. Each makes a visible change, such as ending every reply '
                 'with a set line. Pick one.\n'
                 '\n'
                 '1. **Before you edit anything,** press **Open practice chat** and ask a short question. Leave the '
                 'tab open.\n'
                 "2. Add your rule to the practice profile's `SOUL.md` (right-click its square, **Edit SOUL.md…**) "
                 'and save it.\n'
                 '3. Go back to the open chat and ask another short question. Note whether the rule shows.\n'
                 '4. Press **Open practice chat** again and ask the same question in the fresh chat.\n'
                 '5. Write two or three sentences: when would a messaging chat that never ends pick up your rule, '
                 'and what would you do instead of waiting?\n'
                 '\n'
                 'Hermes names the chats on its own, and Field Academy tells them apart by when they started, so you '
                 "don't need to name them.\n"
                 '\n'
                 '**Working folder.** After your first practice chat, the page shows a **Working folder** check. A '
                 "fail means the chat opened somewhere else. Copy the practice folder's location from the page, pick "
                 "that folder with the chat's folder picker, open a new practice chat, and start over from step 1. A "
                 'project file in the practice folder only loads when the chat starts there.\n'
                 '\n'
                 "The setup may get between your rule and the reply. If the fresh chat doesn't follow your rule, run "
                 'down the three setup questions from the judgment section before you press Check.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's files and Hermes's chat records itself, "
                        "including the copy of the instructions each chat started with. You don't need to copy "
                        'anything out of Hermes.\n'
                        '\n'
                        "- Is your rule in the practice profile's `SOUL.md`?\n"
                        '- The chat you started before the edit: does its saved copy lack the rule, and did it '
                        'answer after your edit without following it?\n'
                        '- The chat you started after the edit: does its saved copy include the rule, and does its '
                        'first reply follow it?\n'
                        '- If something was planted to get in the way, is it fixed?\n'
                        '- Your answer to check 4. Does it name compaction, with a fair idea of when that happens, '
                        'and say what to do instead?',
         'profile': {'soul': ''},
         'profiles': ['a'],
         'profiles_after_try': ['b'],  # made after the try, so the try always lands in academy-practice
         'plants': ['soul_wrong_profile'],
         'plants_after_try': ['soul_wrong_profile'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1},
         'held': [{'kind': 'agents_md_contradicts',
                   'why': 'Held until the working-folder check passes in a live app.'}],
         'rules_a': [{'id': 'end_line',
                      'label': 'End every reply with a set line',
                      'text': 'End every reply with the line: Field notes closed.',
                      'marker': 'ends_with',
                      'value': 'Field notes closed.'},
                     {'id': 'first_word',
                      'label': 'Start every reply with a set word',
                      'text': 'Start every reply with the word Noted.',
                      'marker': 'starts_with',
                      'value': 'Noted'},
                     {'id': 'no_comma',
                      'label': 'Never use a comma',
                      'text': 'Never use a comma in a reply.',
                      'marker': 'no_char',
                      'value': ','}],
         'note_fields_a': {'first': [{'id': 'rule',
                                      'label': 'The rule you added',
                                      'kind': 'choice',
                                      'choices_from': 'rules_a'},
                                     {'id': 'when_text',
                                      'label': 'When would a messaging chat that never ends pick up your rule, and '
                                               'what would you do instead of waiting?',
                                      'kind': 'textarea',
                                      'min': 40,
                                      'max': 2000}],
                           'transfer': [{'id': 'fact',
                                         'label': 'The line you saved about when to start fresh',
                                         'kind': 'text',
                                         'min': 8,
                                         'max': 300},
                                        {'id': 'key_term',
                                         'label': 'Its key word',
                                         'kind': 'text',
                                         'min': 2,
                                         'max': 60}],
                           'try': [{'id': 'predicted',
                                    'label': 'Did you predict the open chat would follow it?',
                                    'kind': 'bool'},
                                   {'id': 'window',
                                    'label': 'The second number in the panel header (the window), in thousands',
                                    'kind': 'int',
                                    'min': 1,
                                    'max': 100000,
                                    'required': False}]}},
 'live_checks': [{'id': 'rule_in_soul', 'reader': 'soul.rule_present', 'visible': True},
                 {'id': 'before_chat', 'reader': 'soul.before_chat', 'visible': True},
                 {'id': 'after_chat', 'reader': 'soul.after_chat', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plant.fixed_a', 'visible': False},
                 {'id': 'fresh_line', 'reader': 'memory.line_matching', 'visible': True},
                 {'id': 'fresh_use', 'reader': 'sessions.used_before_said', 'visible': True}],
 'explain': {'lead': 'Lean on your own two chats for this one:',
             'question': "You changed Hermes's tone and it ignored you for an hour. Why?",
             'rubric': {1: 'Says the model ignored the change, with no reason',
                        2: 'Explains that the chat runs on instructions read when it started',
                        3: 'Adds how to make the change apply now: a new chat',
                        4: 'Adds a second cause from your own run (wrong profile, a project file that disagrees) and '
                           'when a chat that never ends would catch up (compaction), with your own numbers'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Pick a messaging chat you use, or picture one if you don't have one yet. Decide when it "
                      'should start fresh: after each finished job, once a week, when the topic changes, or '
                      'something else that fits how you use it.\n'
                      '\n'
                      'Write that decision as one short line and save it to memory, the way you did in mission 3. '
                      'Then prove it landed: the line is in the memory file, and a new chat knows it without being '
                      'told.',
              'live_checks': ['fresh_line', 'fresh_use']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/04-new-chats.v2.md (Hermes v0.22.4).'}]}
