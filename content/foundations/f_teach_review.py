"""Teaching mission: Judge someone's work from their Field Record.

Placed on the Guide trail, Verify camp (school.PLACEMENTS). A saved Field Record folder from another learner is in the
practice folder, built from a real record with its number and fingerprints made again. The learner has Hermes run the
fingerprint check, reads the record against the holder's own words, and writes `review.md` to them. The facts are
Field Academy's own: what MANIFEST.sha256 and the record number prove (field_record.py, check_folder and verify).
"""

MISSION = {'id': 'f.teach-review',
 'title': "Judge someone's work from their Field Record",
 'order': 16,
 'idea_refs': [],
 'domain': 'D15',
 'level': 'advanced',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 2,
          'words': 'small change on most providers',
          'line': 'Expected cost: one or two short chats on your provider.'},
 'recall': {'lead': 'In the last mission you wrote a walkthrough. Jot down two things:',
            'prompts': ['the step you changed after following it yourself', 'how the last step says it worked'],
            'seconds': 180,
            'from': 'f.teach-walkthrough'},
 'claim': {'text': "I can judge someone's Hermes work from their Field Record: check that it wasn't changed, see what "
                   'it really shows, and tell them plainly what I can vouch for.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'practice_note': "Another learner's saved Field Record is in the practice folder under `their-record/`. Field Academy "
                  'made it from a real record; the name on it is made up.',
 'fresh_text': 'This mission builds a new `academy-practice`, with its own practice folder. If the mission page shows '
               "that practice chats don't open in the practice folder, press **Copy** beside the folder, choose it "
               "with the chat's folder picker, and start a new practice chat before you begin.",
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field "
                  "Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1', 'text': "You had the record's fingerprints checked, file by file.", 'proves_by': 'live:ran_check'},
              {'id': 's2', 'text': 'Your review gives the record number and says how their work really passed.', 'proves_by': 'live:judged'},
              {'id': 's3', 'text': 'Your review finds whatever in the folder or their words shouldn\'t be trusted.', 'proves_by': 'live:plant_fixed'},
              {'id': 's4', 'text': 'It ends with a question to them, by name.', 'proves_by': 'live:question'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.teach-review.try.md',
 'idea': 'md/f.teach-review.idea.md',
 'expert': 'md/f.teach-review.expert.md',
 'expert_lead': 'Owen Price is hiring someone to run Hermes for his small agency. A candidate sends a Field Record folder '
                'with her application.',
 'expert_note': 'Owen and the candidate are made up.',
 'record_example': 'md/f.teach-review.record-example.md',
 'lab': {'body': "`their-record/` in the practice folder is another learner's saved Field Record. The job: judge it, "
                 'and write `review.md` in the practice folder, to them. Work only in `academy-practice`.\n'
                 '\n'
                 '1. **Check the fingerprints.** In a practice chat, ask Hermes to run `shasum -a 256 -c '
                 'MANIFEST.sha256` inside `their-record` and show you every line.\n'
                 '2. **Read record.md.** Their claim, the result the first time and after any fix, the evidence lines.\n'
                 '3. **Read their own words** (the case and the limits) against what the record shows.\n'
                 '4. **Write review.md.** The record number. Whether every file matched. How their mission really '
                 'passed. What you can vouch for and what you can\'t. One question for them, by name.\n'
                 '\n'
                 'Field Academy has set one problem in the folder or the record. At Advanced there are two. If a check '
                 "fails when you thought it should pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the "
                 'Check step.',
         'checks_text': "Field Academy reads the record folder, your review and the practice profile's chat records itself.\n"
                        '\n'
                        '- Your chats. Did Hermes run the fingerprint check on their folder?\n'
                        '- Your review. Does it give the record number and say how the work really passed?\n'
                        '- The folder and their words. Does your review catch what shouldn\'t be trusted?\n'
                        '- The end. Is there a question to them, by name?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted.',
         'profile': {'soul': ''},
         'setup': 'teach_review',
         'folder': True,
         'panels': ['folder', 'working_folder'],
         'try_fields': [{'id': 'guess_trust', 'label': 'Your guess, from the record alone: can you vouch for it?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}],
                         'required': True}],
         'note_fields': [{'id': 'vouch', 'label': 'What you can vouch for, and what you can\'t', 'kind': 'long',
                          'required': True, 'min': 10, 'max': 800},
                         {'id': 't_unchanged', 'label': 'Does every line OK prove the files are as they were saved?', 'kind': 'choice',
                          'for': 'transfer', 'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_true', 'label': 'Does it prove their claims are true?', 'kind': 'choice', 'for': 'transfer',
                          'required': True, 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                         {'id': 't_change', 'label': "What you'd ask for before you vouched, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['edited_excerpt', 'overclaim'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'ran_check', 'reader': 'review.ran_check', 'visible': True},
                 {'id': 'judged', 'reader': 'review.judged', 'visible': True},
                 {'id': 'question', 'reader': 'review.question', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': True},
                 {'id': 'reading', 'reader': 'review.reading', 'visible': True}],
 'explain': {'lead': 'Draw on the record you just judged:',
             'question': 'Every line of the fingerprint check says OK. What does that prove, what does it leave open, '
                         "and what would you still ask before you vouched for the person?",
             'rubric': {1: 'Says OK means the work is good',
                        2: 'Says OK means nothing was changed, but not what it leaves open',
                        3: 'Says OK proves the files are as they were saved; it leaves open whether the claims are true '
                           'and who did the work, so you read the result lines against their words and ask about the '
                           'part you can\'t see',
                        4: 'Adds a point from your own run: the file that failed, or the words that claimed too much'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'A candidate sends a record folder. You run the fingerprint check and every line says OK. Without '
                      'running anything else, answer:\n'
                      '\n'
                      'Does that prove every file is as it was saved? Does it prove their claims are true? What would you '
                      'ask for before you vouched for them, and why?',
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-11-09', 'what': 'Built for the School of Hermes, Guide trail.'}]}
