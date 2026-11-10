"""Teaching mission: Write a walkthrough someone can follow on their own.

Placed on the Guide trail, Verify camp (school.PLACEMENTS). The profile is already set up for a person, with one skill
that does their weekly job. A colleague's draft walkthrough is in the folder. The learner writes `walkthrough.md`
that names only what the profile really has, ends with how to check the result, and follows it once in a new chat.
"""

MISSION = {'id': 'f.teach-walkthrough',
 'title': 'Write a walkthrough someone can follow on their own',
 'order': 15,
 'idea_refs': [],
 'domain': 'D14',
 'level': 'advanced',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 2,
          'words': 'small change on most providers',
          'line': 'Expected cost: one or two short chats on your provider.'},
 'as_of': [{'fact': 'The Capabilities page lists a profile\'s skills on its Skills tab',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "tabSkills: 'Skills'",
            'since': '0.23.0'},
           {'fact': "A skill's name and description come from the front matter at the top of its SKILL.md",
            'file': 'agent/skill_utils.py',
            'pattern': 'def parse_frontmatter\\(content: str\\)',
            'since': '0.23.0'}],
 'recall': {'lead': 'In the last mission you set Hermes up for someone. Jot down two things:',
            'prompts': ['where their rule went, and why there', 'how a new chat proved it'],
            'seconds': 180,
            'from': 'f.teach-profile'},
 'claim': {'text': 'I can write a walkthrough another person can follow on their own, naming only what their Hermes '
                   'really has, and prove it by following it once myself.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'practice_note': "The practice profile is already set up for the person in `brief.txt`, with one skill for their "
                  "weekly orders. A colleague's draft walkthrough is `draft-walkthrough.md`.",
 'fresh_text': 'This mission builds a new `academy-practice`, with its own practice folder. If the mission page shows '
               "that practice chats don't open in the practice folder, press **Copy** beside the folder, choose it "
               "with the chat's folder picker, and start a new practice chat before you begin.",
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field "
                  "Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1', 'text': 'The walkthrough names the skill the profile really has, and nothing that isn\'t there.', 'proves_by': 'live:names_real'},
              {'id': 's2', 'text': 'It ends with where the result lands and how to check it.', 'proves_by': 'live:has_check'},
              {'id': 's3', 'text': 'You followed it once, word for word, in a new chat, and it worked.', 'proves_by': 'live:tested'},
              {'id': 's4', 'text': 'No step tells them to switch a safeguard off.', 'proves_by': 'live:plant_fixed'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.teach-walkthrough.try.md',
 'idea': 'md/f.teach-walkthrough.idea.md',
 'expert': 'md/f.teach-walkthrough.expert.md',
 'expert_lead': 'Priya Nair set up Hermes for her uncle Sanjay, who runs a corner shop. She lives two hours away and '
                'wants him to run his Monday stock list without phoning her.',
 'expert_note': 'Priya and Sanjay are made up.',
 'record_example': 'md/f.teach-walkthrough.record-example.md',
 'lab': {'body': "The profile is set up for the person in `brief.txt`. A colleague wrote `draft-walkthrough.md`. The "
                 'job: write `walkthrough.md` in the practice folder that they can follow on their own. Work only in '
                 '`academy-practice`.\n'
                 '\n'
                 '1. **Look at what the profile really has.** Open **Capabilities**, set **Configuring:** to '
                 '`academy-practice`, and read the **Skills** tab. Note the skill\'s exact name.\n'
                 '2. **Read the draft as a stranger would.** Every name, every step. Anything that isn\'t in the '
                 'profile, or isn\'t safe, comes out.\n'
                 '3. **Write walkthrough.md.** Short numbered steps. Exact names. The last step says where the result '
                 'lands and how to check it.\n'
                 '4. **Follow it yourself,** word for word, in a new practice chat. If a step doesn\'t work as written, '
                 'fix the step.\n'
                 '\n'
                 'Field Academy has also set one trap. At Advanced there are two. If a check fails when you thought it '
                 "should pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the "
                 'Check step.',
         'checks_text': "Field Academy reads the walkthrough, the profile's skills, its chat records and the practice "
                        'folder itself.\n'
                        '\n'
                        '- The walkthrough. Does every skill it names exist? Does it name the real one?\n'
                        '- The last step. Does it say where the result lands and how to check it?\n'
                        '- Your chats. After you wrote it, did a chat follow it and write the result?\n'
                        '- Safety. Does any step switch a safeguard off?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted.',
         'profile': {'soul': ''},
         'setup': 'teach_walkthrough',
         'folder': True,
         'memory_view': True,
         'panels': ['folder', 'working_folder'],
         'try_fields': [{'id': 'guess_works', 'label': "Your guess: would the colleague's draft work, followed word for word?",
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}],
                         'required': True}],
         'note_fields': [{'id': 'changed', 'label': 'What you changed from the draft, and why', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 800},
                         {'id': 't_stranger', 'label': 'Could someone new follow it on their own?', 'kind': 'choice',
                          'for': 'transfer', 'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_done', 'label': "Would they know when it's worked?", 'kind': 'choice', 'for': 'transfer',
                          'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_change', 'label': "What you'd change, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['stale_skill_name', 'unsafe_tip'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'names_real', 'reader': 'walkthrough.names_real', 'visible': True},
                 {'id': 'has_check', 'reader': 'walkthrough.has_check', 'visible': True},
                 {'id': 'tested', 'reader': 'walkthrough.tested', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': True},
                 {'id': 'reading', 'reader': 'walkthrough.reading', 'visible': True}],
 'explain': {'lead': 'Draw on the walkthrough you just wrote:',
             'question': "A walkthrough worked when you wrote it and fails for them a month later. Name two reasons that "
                         "happen, and what in a walkthrough guards against each.",
             'rubric': {1: 'Blames the person for not following it',
                        2: 'Names one reason (a renamed skill, a changed setting) with no guard',
                        3: 'Names two (a name that changed or never existed, a step that only worked on your screen, a '
                           'missing check), and the guard for each: exact names read from the profile, following it '
                           'yourself in a new chat, a last step that checks the result',
                        4: 'Adds a point from your own run: the stale name or the unsafe step you found'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Someone's walkthrough for a new hire says:\n"
                      '\n'
                      '1. Open Hermes.\n'
                      '2. Use the usual skill for the invoices.\n'
                      '3. You\'re done.\n'
                      '\n'
                      "Could someone new follow it on their own? Would they know when it's worked? What would you "
                      'change, and why?',
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-11-09', 'what': 'Built for the School of Hermes, Guide trail.'}]}
