"""Foundations mission 6: Keep two jobs apart in two profiles.

Learner text comes from .planning/field-academy-v3/missions/06-profiles.v2.md, learner sections only (everything from "## Build
notes" down stays in the planning file). Converted unchanged except where the format needs it: the expert run's steps
carry Did, Saw, Noticed and Ruled out lines. Plants live in plants_a.py, checks in foundations_checks_a.py, and every
as_of pattern is checked against the Hermes source by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.profiles',
 'title': 'Keep two jobs apart in two profiles',
 'order': 6,
 'idea_refs': [7],
 'domain': 'D3',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 35},
 'cost': {'chats': 6,
          'words': 'a small charge on your provider',
          'line': 'Expected cost: five or six short chats across two profiles, a small charge on your provider.'},
 'as_of': [{'fact': 'A clone copies both memory files',
            'file': 'hermes_cli/profiles.py',
            'pattern': '_CLONE_SUBDIR_FILES = \\["memories/MEMORY\\.md", "memories/USER\\.md"\\]',
            'since': '0.22'},
           {'fact': 'The New profile dialog says it copies config, skills, and SOUL.md',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': 'Copies config, skills, and SOUL\\.md from the selected source profile',
            'since': '0.22.4'}],
 'recall': {'lead': "In the last mission you turned a repeat job into a skill. What's stuck with you? Two things:",
            'prompts': ['what Hermes reads about a skill before it decides to open it',
                        'the sign that Hermes opened your skill on its own, and the test that would have fooled you'],
            'seconds': 180,
            'from': 'f.skills'},
 'claim': {'text': "I can keep two jobs fully separate in Hermes, and prove from each profile's own records and a "
                   'new chat in each that nothing crosses between them.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'Two fresh practice profiles',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': "This mission builds a new `academy-practice` and a second one, `academy-practice-b`. The mission page also shows whether practice chats open in the practice folder. On a fail, copy the folder's location from the page, pick it in the chat's folder picker, and open a fresh practice chat before you begin.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "The practice profile from an earlier mission is removed when you set up practice, after Field Academy saves its evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': "Each of the two practice profiles holds its own fact in its own memory, and not the other's.",
               'proves_by': 'live:own_facts'},
              {'id': 's2',
               'text': "A new chat in each profile uses its own fact in real work, and never the other's.",
               'proves_by': 'live:own_use+rubric:explain'},
              {'id': 's3',
               'text': "At every step you can say which profile you're in, and how you know.",
               'proves_by': 'rubric:explain'},
              {'id': 's4',
               'text': 'Something in the setup mixes the two jobs. You find it and fix it.',
               'proves_by': 'live:plant_fixed'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.profiles.try.md',
 'try_prompt': '',
 'idea': 'md/f.profiles.idea.md',
 'expert': 'md/f.profiles.expert.md',
 'expert_lead': 'Kwame Asante is a freelance social media manager. He posts for two clients: Spoke & Chain, a bike '
                'shop, and Wren Floral, a flower shop. Last month Hermes wrote a Wren Floral caption that mentioned '
                'a bike tune-up special. The owner, Odile Wren, spotted it in the draft and asked him, politely, '
                'whether he had other clients reading her account.',
 'expert_note': 'Kwame and both shops are made up.',
 'expert_slots': ["How many profiles do you run, and what's the rule you use to decide a job gets its own?",
                  "Have you had one client's details show up in another's work? What caused it?",
                  'Do you ever clone a profile? When is that the right call?',
                  'What do you keep out of a client profile on purpose?'],
 'record_example': 'md/f.profiles.record-example.md',
 'lab': {'body': 'Work only in `academy-practice` and `academy-practice-b`. Pretend each is a different client. '
                 'Start every chat with **Open practice chat A** or **Open practice chat B**.\n'
                 '\n'
                 '1. **Pick one real-sounding fact per client:** a deadline, a preference, a rule. One line each.\n'
                 '2. **Save the first in A and the second in B.**\n'
                 '3. **Prove all four checks.** For check 2, ask each profile for real work that needs its fact. How '
                 'you prove the rest is up to you.\n'
                 '\n'
                 'The setup also hides one mix-up between the two clients, and check 4 is finding it. The counts you '
                 "wrote in Work it out are a good place to start. When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads both practice profiles' memory files and chat records on its own.\n"
                        '\n'
                        "- Each profile's memory. Does it hold its own fact, and nothing from the other client?\n"
                        "- Each profile's chats. Is there a new chat, started after both saves, where Hermes used "
                        "its own fact in real work? Did either chat bring up the other client's fact?\n"
                        '- The planted mix-up. Is it gone?\n'
                        "- Your written answer to check 3. Does it name a real way to tell which profile you're in?\n"
                        '\n'
                        'Your four results appear beside the prediction you wrote before the try.',
         'profile': {'soul': ''},
         'profiles': ['a', 'b'],
         'plants': ['cloned_memory', 'decoy_in_b'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1},
         'held': [{'kind': 'shared_agents_md',
                   'why': "Advanced variant held: whether a desktop chat loads AGENTS.md from a profile's "
                          'terminal.cwd is unconfirmed.'}],
         'note_fields_a': {'first': [{'id': 'fact_a',
                                      'label': 'The fact you saved in academy-practice (A)',
                                      'kind': 'text',
                                      'min': 8,
                                      'max': 300},
                                     {'id': 'key_a', 'label': 'Its key word', 'kind': 'text', 'min': 2, 'max': 60},
                                     {'id': 'fact_b',
                                      'label': 'The fact you saved in academy-practice-b (B)',
                                      'kind': 'text',
                                      'min': 8,
                                      'max': 300},
                                     {'id': 'key_b', 'label': 'Its key word', 'kind': 'text', 'min': 2, 'max': 60},
                                     {'id': 'which_profile',
                                      'label': 'Check 3: how you knew which profile you were in, each time',
                                      'kind': 'textarea',
                                      'min': 20,
                                      'max': 1500}],
                           'transfer': [{'id': 'plan',
                                         'label': 'Your profile plan: for each profile, its name, what it holds, and '
                                                  'what it must never hold',
                                         'kind': 'textarea',
                                         'min': 80,
                                         'max': 4000}],
                           'try': [{'id': 'answer_b1',
                                    'label': "B's answer to step 2",
                                    'kind': 'text',
                                    'min': 2,
                                    'max': 600},
                                   {'id': 'answer_b2',
                                    'label': "B's answer to step 3",
                                    'kind': 'text',
                                    'min': 2,
                                    'max': 600},
                                   {'id': 'count_a',
                                    'label': "Lines in A's memory",
                                    'kind': 'int',
                                    'min': 0,
                                    'max': 500,
                                    'required': False},
                                   {'id': 'count_b',
                                    'label': "Lines in B's memory",
                                    'kind': 'int',
                                    'min': 0,
                                    'max': 500,
                                    'required': False}]}},
 'live_checks': [{'id': 'own_facts', 'reader': 'profiles.own_facts', 'visible': True},
                 {'id': 'own_use', 'reader': 'profiles.own_use', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plant.fixed_a', 'visible': False},
                 {'id': 'plan_written', 'reader': 'profiles.plan_written', 'visible': True}],
 'explain': {'lead': 'Think back to the mix-up you found:',
             'question': "Your Hermes mentions client A's details while working for client B. List the causes in the "
                         "order you'd check them, and how you'd check each one.",
             'rubric': {1: 'Names one cause, or blames the model without checking anything',
                        2: 'Names the wrong profile as a cause, with no way to check it, or no sensible order',
                        3: 'Cheap checks first: which profile the chat belonged to, whether B was cloned from A, '
                           "whether A's files sit somewhere B was asked to read. A real check for each, such as "
                           "`/profile`, a new chat quoting B's memory notes, or the file's location",
                        4: 'Adds what happened in your own run: the mix-up you found and how you found it'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'On paper, plan the profiles for one real client of yours. For each profile, write:\n'
                      '\n'
                      '- its name\n'
                      '- what it holds: which facts, which skills, which keys, which scheduled jobs\n'
                      '- what it must never hold\n'
                      '\n'
                      'Then use mission 5. Pick one procedure this client needs and say which profile its skill '
                      "belongs in. If two profiles need the same skill, say how you'd get it into both without "
                      "bringing memory along. Copying the skill's folder from one profile's `skills` folder into the "
                      "other's is one way.",
              'live_checks': ['plan_written']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/06-profiles.v2.md (Hermes v0.22.4).'}]}
