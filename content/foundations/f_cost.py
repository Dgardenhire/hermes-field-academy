"""Foundations mission 2: See what a chat costs, and cut it.

Learner text comes from .planning/field-academy-v3/missions/02-cost.v2.md, learner sections only (everything from "## Build
notes" down stays in the planning file). Converted unchanged except where the format needs it: the expert run's steps
carry Did, Saw, Noticed and Ruled out lines. Plants live in plants_a.py, checks in foundations_checks_a.py, and every
as_of pattern is checked against the Hermes source by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.cost',
 'title': "See what a chat costs, and cut it",
 'order': 2,
 'idea_refs': [2, 3, 12],
 'domain': 'D2',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 30},
 'cost': {'chats': 4,
          'words': 'usually a few cents',
          'line': 'Expected cost: four short chats in the practice profile. This mission shows you where to read '
                  'what they cost.'},
 'as_of': [{'fact': 'Helper agents use the main model unless you set one',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"model":\\s*"",\\s*# e\\.g\\..*empty = inherit parent',
            'since': '0.22.4'},
           {'fact': 'Hermes asks before a model switch once a chat passes 100,000 tokens',
            'file': 'hermes_cli/model_selection_guards.py',
            'pattern': 'DEFAULT_CONTEXT_CACHE_SWITCH_THRESHOLD = 100_000',
            'since': '0.22'},
           {'fact': 'Risky commands are judged by a side model by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"mode":\\s*"smart"',
            'since': '0.22.4'}],
 'recall': {'lead': 'In the last mission, one message turned into a loop of tool calls. From memory, write two '
                    'things:',
            'prompts': ['roughly how many trips around the loop your job took',
                        "the claim you caught that wasn't true"],
            'seconds': 180,
            'from': 'f.loop'},
 'claim': {'text': 'I can see what makes a chat cost what it does, and cut the cost without breaking the job.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 # Shown on the Practice and Your turn steps, before the first chat (0.9 persona test). True whatever was planted:
 # the connector is in the settings either way, on or off, so the note names neither problem (Nov 8).
 'practice_note': "This practice profile's settings include a filesystem connector. While it's on, Hermes starts it with "
                  '`npx` each time a practice chat opens. That downloads a pinned package from npm and keeps it running '
                  'while the chat is open. It can reach one folder, inside the practice profile.',
 'fresh_text': 'When you set up practice, Field Academy builds a new `academy-practice` for this mission, with its own practice folder and its own setup.',
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': 'The one from an earlier mission goes away, after Field Academy saves its evidence to your record and you confirm.',
 'standard': [{'id': 's1',
               'text': 'You can name the parts of what Hermes sends on every trip, and which part is biggest in your '
                       'setup.',
               'proves_by': 'rubric:explain'},
              {'id': 's2',
               'text': 'You decide what to cut by looking at what the job actually used.',
               'proves_by': 'live:cost_decision+rubric:explain'},
              {'id': 's3',
               'text': 'The part sent on every trip shrinks, and the share you write down is within 5 points of the '
                       'real drop.',
               'proves_by': 'live:fixed_part_drop'},
              {'id': 's4',
               'text': 'The same job still comes out right afterward.',
               'proves_by': 'live:job_still_right'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside your result at the end.'},
 'try': 'md/f.cost.try.md',
 'try_prompt': '',
 'idea': 'md/f.cost.idea.md',
 'expert': 'md/f.cost.expert.md',
 'expert_lead': 'Aisha Bello coordinates operations for a food bank with 12 staff and a few hundred volunteers. '
                'Every Monday, Hermes turns the volunteer sign-up sheet into a shift plan. Her model bill has crept '
                'up.',
 'expert_note': 'Aisha is made up, and her figures are only for illustration.',
 'expert_slots': ["When a client says their AI bill went up, what's the first thing you look at, and what's the "
                  'mistake you see most?'],
 'record_example': 'md/f.cost.record-example.md',
 'lab': {'body': "A small job is waiting. Its request card is on this page, with the practice folder's full location "
                 'already filled in. The practice setup is carrying more than this job needs, and finding it is part '
                 'of the work.\n'
                 '\n'
                 '**Working folder.** After your first practice chat, the page shows a **Working folder** check. If '
                 'it fails, press **Copy** beside the practice folder on this page, choose that folder with the '
                 "chat's folder picker, then press **Open practice chat** for a fresh chat before you measure. A "
                 'project file only loads in a chat that starts in its folder.\n'
                 '\n'
                 '1. **Before.** Press **Open practice chat**, send `hello`, and note the fixed part from Context '
                 'Usage. Then paste the request from the card into that chat and let the job finish.\n'
                 '2. **Decide.** Using the activity rows and the Context Usage panel, decide what to cut. Write down '
                 "what you'll cut and why, before you change anything.\n"
                 '3. **Cut.** Open **Capabilities**, choose `academy-practice` in the **Configuring:** picker, and '
                 'switch off what you decided on in the **Skills**, **Tools** and **Connectors** tabs. If your cut is in the '
                 "project file, the page shows the file's full location with a **Copy** button. In Notepad, choose "
                 '**File → Open** and paste the location into the file name box. In TextEdit, choose **File → '
                 'Open**, press `Cmd+Shift+G` and paste it. Delete the block you decided on, then save.\n'
                 '4. **After.** Press **Open practice chat** again, send `hello`, and note the fixed part. Write '
                 'down how much it shrank, in tokens and as a share of the "before" number. Then paste the same '
                 'request and check the result is right.\n'
                 '5. **Count the models.** Open **Settings → Model**, choose `academy-practice` under **Applies '
                 'to**, and write down which model each row under **Main model**, **Auxiliary models** and '
                 '**Subagents** would use.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's settings and chat records itself. You don't need "
                        'to copy numbers anywhere.\n'
                        '\n'
                        "- What's still switched on in the practice profile. Is the planted extra gone, and is "
                        'everything the job used still there?\n'
                        '- The first trip of your "before" and "after" chats, which shows the fixed part. How much '
                        'did it shrink, and is the share you wrote down within 5 points of it?\n'
                        '- Hermes\'s own record of the "after" job. Did it finish without a tool error? Is the '
                        'result right?\n'
                        '- What Hermes recorded each job cost, where your provider reports prices.\n'
                        '- Your written decision from step 2. Does it name what the job used and what you cut?',
         'profile': {'soul': ''},
         'plants': ['extra_connector', 'unused_skills'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1},
         'held': [{'kind': 'extra_toolsets',
                   'why': 'Held. The Capabilities Tools tab writes platform_toolsets.cli, not agent.disabled_toolsets '
                          '(hermes_cli/web_routers/tools.py toggle_toolset, tools_config._save_platform_tools, v0.22.4). '
                          'A plant on platform_toolsets.cli waits for a live app to confirm desktop chats read it.'},
                  {'kind': 'agents_md_big', 'why': 'Held until the working-folder check passes in a live app.'}],
         'note_fields_a': {'first': [{'id': 'decision',
                                      'label': "Step 2: what you'll cut, and why, from what the job used",
                                      'kind': 'textarea',
                                      'min': 20,
                                      'max': 2000},
                                     {'id': 'before_tokens',
                                      'label': 'Before: the fixed part, in tokens',
                                      'kind': 'int',
                                      'min': 1,
                                      'max': 10000000},
                                     {'id': 'after_tokens',
                                      'label': 'After: the fixed part, in tokens',
                                      'kind': 'int',
                                      'min': 1,
                                      'max': 10000000},
                                     {'id': 'share',
                                      'label': 'How much it shrank, as a share of before (percent)',
                                      'kind': 'int',
                                      'min': 0,
                                      'max': 100},
                                     {'id': 'main', 'label': 'Main model', 'kind': 'text', 'min': 2, 'max': 200},
                                     {'id': 'auxiliary',
                                      'label': 'Auxiliary models',
                                      'kind': 'text',
                                      'min': 2,
                                      'max': 600},
                                     {'id': 'subagents', 'label': 'Subagents', 'kind': 'text', 'min': 2, 'max': 200}],
                           'transfer': [{'id': 'sentences',
                                         'label': 'What it will save and on which jobs; what could get worse and how '
                                                  "you'd notice",
                                         'kind': 'textarea',
                                         'min': 40,
                                         'max': 2000},
                                        {'id': 'one_model',
                                         'label': 'My provider offers only one model',
                                         'kind': 'bool',
                                         'required': False}],
                           'try': [{'id': 'total',
                                    'label': 'The total the panel shows for this chat',
                                    'kind': 'int',
                                    'min': 1,
                                    'max': 10000000},
                                   {'id': 'hello',
                                    'label': 'How much of it is the word you typed',
                                    'kind': 'int',
                                    'min': 0,
                                    'max': 1000}]}},
 'live_checks': [{'id': 'fixed_part_drop', 'reader': 'cost.fixed_part_drop', 'visible': True},
                 {'id': 'job_still_right', 'reader': 'cost.job_still_right', 'visible': True},
                 {'id': 'cost_decision', 'reader': 'cost.decision', 'visible': True},
                 {'id': 'models_counted', 'reader': 'cost.models_counted', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plant.fixed_a', 'visible': False},
                 {'id': 'subagent_model', 'reader': 'cost.subagent_model', 'visible': True}],
 'explain': {'lead': 'Your before-and-after numbers are the evidence here:',
             'question': "A friend's bill doubled the month she connected three new services. Explain why to her, "
                         'and tell her what to check and what to keep.',
             'rubric': {'1': 'Says connectors cost money, without saying why',
                        '2': 'Explains that their tool descriptions are sent on every trip',
                        '3': 'Adds how she can see it (the Context Usage panel) and a fix that keeps what she uses',
                        '4': 'Adds why the fix belongs in a new chat (the cache, and tools loading at the start), '
                             'using numbers from your own run'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'Helper agents are separate agents Hermes starts for side jobs, like researching three things '
                      "at once. Hermes calls them subagents. Hermes's docs say they usually burn most of the tokens "
                      'in a big parallel job. Unless you set one, they use your main model.\n'
                      '\n'
                      'Set a cheaper model for them in the practice profile: open **Settings → Model**, choose '
                      '`academy-practice` in the **Applies to** row at the top, and set the model under '
                      '**Subagents**. Then answer in two or three sentences:\n'
                      '\n'
                      '- What will this save, and on which jobs?\n'
                      '- What could get worse, and how would you notice?\n'
                      '\n'
                      "If your provider offers only one model, say which kind you'd choose and why.",
              'live_checks': ['subagent_model']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/02-cost.v2.md (Hermes v0.22.4).'},
               {'date': '2026-11-08', 'what': 'Two possible planted problems instead of one; the note before the first '
                                             'practice chat reworded to be true for either.'}]}
