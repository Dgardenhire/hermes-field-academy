"""Foundations mission 11: Foundations review.

Learner text comes from .planning/field-academy-v3/missions/11-review.md, learner sections only. It is an assessment
(``kind: review``): no try, no worked example. The learner writes the claim and the standard (level advanced). Two
problems are drawn by foundations_b.review_pick: one from what every chat carries, one from what Hermes may do
unwatched, never one met at an earlier Compare, never two connector problems. Field Academy records a Start snapshot
of memory, skills and waiting saves after the plants. The parts the build notes give to the learner's own Hermes
(coverage of account 1, the "how I found it" lines, the learner's own checks) are kept as written in the record,
because the grading flow grades one answer per attempt (Explain it).
"""

MISSION = {'id': 'f.review',
 'kind': 'review',
 'title': 'Foundations review',
 'order': 11,
 'idea_refs': [11, 12],
 'domain': 'D10',
 'level': 'advanced',
 'minutes': {'read': 15, 'do': 60},
 'cost': {'chats': 3,
          'words': "one small job's worth of model use",
          'line': "Expected cost: one small job's worth of model use, plus whatever Hermes runs in the background "
                  'around it. Read your own total with `/usage` at the end of each practice chat.'},
 'as_of': [{'fact': 'Helper agents use the main model unless delegation.model is set',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"model": "",\\s*# e\\.g\\. "google/gemini-3-flash-preview" \\(empty = inherit parent\\)',
            'since': '0.22.4'},
           {'fact': 'Memory approvals are off by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"write_approval":\\s*False,\\s*\\n\\s*"memory_char_limit"',
            'since': '0.22'},
           {'fact': 'Side jobs on provider auto use the main model',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': 'provider "auto" = inherit the main model',
            'since': '0.22.4'}],
 'recall': {'lead': "Write the three things you'd check first in any Hermes profile you didn't set up yourself, and "
                    'why those three.',
            'prompts': ["the three things you'd check first, and why those three"],
            'seconds': 300,
            'from': 'f.diagnose'},
 'claim': {'text': 'I can take a small real job through Hermes in a profile I did not set up, find what is planted '
                   'in it, and account for every claim, model and change, with evidence a stranger can check.',
           'author': 'course'},
 'standard_lead': ('Three to five checks that would prove your claim false. Each one should be something a stranger '
                   'could test from the evidence without asking you. When you press **Start**, they\'re frozen. You can '
                   'add a correction later, and the correction is recorded beside the original.'),
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, five minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': "You've done ten missions with the claim and the standard written for you. This time you write both, "
               'on a job you pick, in a practice profile with two problems planted in it. Nobody tells you what they '
               "are or where. There's no warm-up try and no worked example: go straight from the job to your claim, "
               'your checks and the run, and lean on your own notes from the last ten missions when you\'re stuck.\n'
               '\n'
               "**Pick the job.** Something small and real that you'd hand Hermes anyway, about half an hour of its "
               'work. It should change at least one file, so there\'s something to check afterward. Good sizes: tidy '
               'a folder of notes into one summary, turn a messy export into a clean table, draft three replies from '
               "a list of questions. You'll copy the files it needs into the practice folder once you've started, so "
               "gather them now, and leave out anything you wouldn't want sitting in a practice chat's history.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "This mission builds a new `academy-practice` and replaces the one from an earlier mission. Field Academy saves that one's evidence first and asks you before it removes anything.",
 'standard': [{'id': 's1', 'text': 'Both planted problems are gone, and I can say how I found each one.',
               'proves_by': 'live:plants_fixed'},
              {'id': 's2', 'text': "Every claim in Hermes's final answer is listed and checked against the files.",
               'proves_by': 'live:claims_checked'},
              {'id': 's3', 'text': 'Every model that worked on the job is listed, and the list matches the settings.',
               'proves_by': 'live:models_match'},
              {'id': 's4', 'text': 'Every change Hermes made to its own memory and skills is listed, with who asked for it.',
               'proves_by': 'live:self_edits'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "How many of your checks will pass, and where you'll slip."},
 'idea': 'md/f.review.idea.md',
 'record_example': 'md/f.review.record-example.md',
 'lab': {'memory_view': True,  # the page offers Show memory file on this mission (0.9 persona test)
         'body': '1. Press **Start**. Field Academy freezes your claim, standard and prediction, and starts a timer.\n'
                 '2. Copy the files the job needs into the practice folder. The mission page shows where it is, with a '
                 '**Copy** button for its location. Use copies and leave the originals where they are.\n'
                 '3. Press **Open practice chat** and do the job. Paste the practice folder\'s location from the mission '
                 'page wherever a request needs a path. Use the app the way you would on a real job. The terminal is '
                 "there if you'd rather.\n"
                 '4. Somewhere along the way, find the two planted problems, fix them, and say how you found each '
                 'one.\n'
                 '5. Write the three accounts.\n'
                 '6. Score yourself against your own standard, check by check, with the evidence for each.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's settings, memory, skills, logs, scheduled jobs and "
                        'chat records itself, in the background.\n'
                        '\n'
                        "Each item says who does the checking. Where it's your own words, the record says so on that "
                        'line, because what you wrote is weaker evidence than a file Field Academy read.\n'
                        '\n'
                        '- **The two plants.** Is each one gone? *Field Academy reads the profile.* Your "how I found '
                        'it" lines go into the record as you wrote them.\n'
                        "- **Account 1.** Is each claim marked held or didn't, and do the files agree where Field "
                        'Academy can test them (a file exists, a named path)? *Field Academy reads the files.* '
                        'Coverage of every claim is shown as you wrote it.\n'
                        "- **Account 2.** Does your list match the profile's model settings? *Field Academy reads "
                        'them.* Did the helper agents you say ran actually run? *Field Academy reads the chat '
                        'records.*\n'
                        '- **Account 3.** Does your list match the difference between the Start snapshot and the end, '
                        'including anything still waiting? *Field Academy reads the memory, skills and chat records.*\n'
                        '- **How you\'ll know.** Your own checks and your self-score are shown beside the evidence, as '
                        'you wrote them.\n'
                        '\n'
                        'Your prediction sits beside each result.',
         'profile': {'soul': ''},
         'setup': 'review',
         'folder': True,
         'pick': 'review',
         'panels': ['folder', 'working_folder', 'baseline', 'can_claim'],
         'note_fields': [{'id': 'job', 'label': 'The job, in one line', 'kind': 'text', 'required': True, 'min': 8, 'max': 300},
                         {'id': 'found_1', 'label': 'The first planted problem, and how you found it', 'kind': 'long',
                          'max': 800},
                         {'id': 'found_2', 'label': 'The second planted problem, and how you found it', 'kind': 'long',
                          'max': 800},
                         {'id': 'claims', 'label': "Account 1: each claim in Hermes's final answer, one per line, ending "
                                                   "with held or didn't", 'kind': 'long', 'max': 3000},
                         {'id': 'wrong', 'label': 'Account 1: what was wrong with the result, whether or not Hermes said so',
                          'kind': 'long', 'max': 2000},
                         {'id': 'main_model', 'label': 'Account 2: the main model', 'kind': 'text', 'max': 200},
                         {'id': 'fallback', 'label': 'Account 2: the backup models (or none)', 'kind': 'text', 'max': 300},
                         {'id': 'subagents', 'label': 'Account 2: the helper-agent model', 'kind': 'text', 'max': 200},
                         {'id': 'subagents_ran', 'label': 'Did helper agents run during your job?', 'kind': 'choice',
                          'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'},
                                      {'value': 'cant_tell', 'label': "Can't tell"}]},
                         {'id': 'models_why', 'label': "Account 2: what ran, what you'd change, and anything you can't "
                                                       'tell and why', 'kind': 'long', 'max': 1500},
                         {'id': 'job_model', 'label': "Account 2: the job's own model, if it runs on a schedule (or none)",
                          'kind': 'text', 'max': 200},
                         {'id': 'edits', 'label': 'Account 3: every memory line and skill that is new, changed or gone '
                                                  'since Start, one per line, with asked, on its own or mine, and keep '
                                                  'or remove', 'kind': 'long', 'max': 3000},
                         {'id': 'minutes', 'label': 'How long the run took, in minutes', 'kind': 'number'},
                         {'id': 'claim_review', 'label': "The claim you'd want a reviewer to look at first, and why",
                          'kind': 'long', 'for': 'transfer', 'required': True, 'min': 20, 'max': 800}],
         'plants': ['write_approval', 'memory_full', 'twin_connector', 'open_connector', 'broken_connector'],
         'plants_at': {'beginner': 2, 'intermediate': 2, 'advanced': 2}},
 'live_checks': [{'id': 'plants_fixed', 'reader': 'plants.all_fixed', 'visible': True},
                 {'id': 'claims_checked', 'reader': 'review.claims_checked', 'visible': True},
                 {'id': 'models_match', 'reader': 'review.models_match', 'visible': True},
                 {'id': 'self_edits', 'reader': 'review.self_edits', 'visible': True},
                 {'id': 'claims_read', 'reader': 'review.can_claim_read', 'visible': True}],
 'explain': {'lead': "Write one case for a stranger: someone who wasn't there and doesn't use Hermes.",
             'question': 'The situation, what you asked Hermes to do, what it got wrong or nearly got wrong, how you '
                         "found out, and what you'd do differently. Under 300 words.",
             'rubric': {1: 'Describes the job and says it went well',
                        2: 'Names something that went wrong, with no evidence a stranger could look at',
                        3: 'Names what went wrong, how it was found and the evidence that shows it, in plain words a '
                           'stranger could follow',
                        4: "Also says what the record can't show: a check that was weak, a plant found by luck, or a "
                           "model or self-edit you couldn't account for"},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'Field Academy builds the list of what you can now claim from your record, so no two look alike. '
                      'Read it on the mission page: the claims you passed, the ones not yet, and your own claim last. '
                      "Then name the claim you'd want a reviewer to look at first, and why.",
              'live_checks': ['claims_read']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/11-review.md (Hermes v0.22.4).'}]}
