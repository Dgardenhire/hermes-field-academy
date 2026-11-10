"""Foundations mission 5: Turn a repeat job into a skill.

Learner text comes from .planning/field-academy-v3/missions/05-skills.v2.md, learner sections only (everything from "## Build
notes" down stays in the planning file). Converted unchanged except where the format needs it: the expert run's steps
carry Did, Saw, Noticed and Ruled out lines. Plants live in plants_a.py, checks in foundations_checks_a.py, and every
as_of pattern is checked against the Hermes source by scripts/check_foundations.py when HERMES_SOURCE is set.
"""

MISSION = {'id': 'f.skills',
 'title': 'Turn a repeat job into a skill',
 'order': 5,
 'idea_refs': [6, 11],
 'domain': 'D4',
 'level': 'beginner',
 'minutes': {'read': 20, 'do': 35},
 'cost': {'chats': 5,
          'words': 'usually a few cents',
          'line': 'Expected cost: four or five short chats in the practice profile. Mission 2 showed you where to '
                  'read the real figure.'},
 'as_of': [{'fact': 'The skills list shows 60 characters of each description, else it cuts at the last whole word and adds three dots',
            'file': 'agent/skill_utils.py',
            'pattern': 'SKILL_PROMPT_DESC_LIMIT = 60[\\s\\S]*def clip_skill_description[\\s\\S]*head = desc\\[:SKILL_PROMPT_DESC_LIMIT - 2\\][\\s\\S]*_CLIP_TRAIL_RE\\.sub\\("", head\\[:boundary\\.start\\(\\)\\]\\) \\+ "\\.\\.\\."',
            'since': '0.22.6'},
           {'fact': "Hermes refuses a new or changed skill description over 60 characters, and keeps an unchanged long one",
            'file': 'tools/skill_manager_tool.py',
            'pattern': 'len\\(desc\\) <= SKILL_PROMPT_DESC_LIMIT or \\(before is not None and desc == _description_of\\(before\\)\\)',
            'since': '0.22.6'},
           {'fact': 'A background review of skills runs about every ten trips',
            'file': 'agent/agent_init.py',
            'pattern': '"creation_nudge_interval", 10',
            'since': '0.22.4'},
           {'fact': 'The curator marks unused skills stale at 14 days and archives them at 30',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"stale_after_days": 14,[^\\n]*\\n\\s*"archive_after_days": 30',
            'since': '0.22.4'},
           {'fact': "The app's row reads Loaded skill",
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "loaded: 'Loaded skill'",
            'since': '0.22.4'}],
 'recall': {'lead': "In the last mission you changed Hermes's instructions and watched when the change took hold. "
                    'From memory, write two things:',
            'prompts': ['why a chat that was already open kept behaving the old way',
                        "the moment you'd start a new chat on purpose"],
            'seconds': 180,
            'from': 'f.new-chats'},
 'claim': {'text': 'I can turn a job I repeat into a skill that Hermes finds and uses on its own, and prove it from '
                   'the skill file and a brand-new chat.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': 'This mission builds a new `academy-practice` when you set up practice.',
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "The one from an earlier mission is removed first, after Field Academy saves its evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': 'The skill file has four parts: when to use it, the steps, the pitfalls, and a way to check '
                       'the result. Name the headings however you like, as long as all four parts are there.',
               'proves_by': 'live:four_parts'},
              {'id': 's2',
               'text': "Its description starts with the words you'd actually say when you ask for this job.",
               'proves_by': 'live:description_words+rubric:explain'},
              {'id': 's3',
               'text': 'In a brand-new chat, Hermes loads the skill without you naming it.',
               'proves_by': 'live:loaded_unnamed'},
              {'id': 's4',
               'text': "None of the job's steps are left sitting in memory.",
               'proves_by': 'live:steps_out'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.skills.try.md',
 'try_prompt': '',
 'idea': 'md/f.skills.idea.md',
 'expert': 'md/f.skills.expert.md',
 'expert_lead': "Bernadette Kowalczyk runs a dental office's front desk. Each Friday she reports unpaid insurance "
                'claims by insurer. Twice she corrected Hermes for totaling the billed column instead of the paid '
                'one. Then a skill appeared she\'d never asked for, `insurance-claims-reporting`: "Use when '
                'summarizing aged insurance receivables by payer." The next Friday she asked for "the Friday claims '
                'report." No **Loaded skill** row, and the billed column again. Dr. Halvorsen caught a total $3,100 '
                'too high before it reached the accountant.',
 'expert_note': 'Bernadette and her office are made up; the numbers are illustrative.',
 'expert_slots': ["What's the first job you turned into a skill, and what made you decide it was worth it?",
                  'Have you found a skill Hermes wrote on its own? Did you keep it, rewrite it, or throw it out?',
                  "How do you know a skill's description is good before you test it?",
                  'Do you install community skills? What do you read first?'],
 'record_example': 'md/f.skills.record-example.md',
 'lab': {'memory_view': True,  # the page offers Show memory file on this mission (0.9 persona test)
         'body': 'Work only in `academy-practice`. Start every chat with **Open practice chat**.\n'
                 '\n'
                 '1. **Pick a real job you repeat,** with at least three steps: a weekly report, a standard reply, a '
                 "checklist. Leave the try's pantry job alone; it doesn't count here.\n"
                 '2. **Do it once with Hermes,** correcting it as you go. Write down how you asked.\n'
                 '3. **Make it a skill.** Ask Hermes to save it, type `/learn` and describe what to learn from, or '
                 'use `/refine` as in the try.\n'
                 '4. **Fix the description.** Read it in **Capabilities → Skills** and rewrite it using the judgment '
                 'above.\n'
                 '5. **Prove all four checks.** How you prove them is up to you.\n'
                 '\n'
                 'One more thing in the practice profile may trip your proof. Field Academy put it there, and '
                 "finding it is part of the job. If the evidence doesn't add up, work out why before you move on.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's skills, memory and chat records itself. There's "
                        'nothing for you to paste in.\n'
                        '\n'
                        '- Your `SKILL.md`. Does it have all four parts, each with real content, whatever you named '
                        'the headings?\n'
                        '- Its description. Does the part Hermes shows, cut at a whole word before 60 characters, share words with how you asked for the job in '
                        'your test chat?\n'
                        '- Your chat records. Is there a chat, started after the skill was last saved, where Hermes '
                        'loaded the skill before you typed its name or its slash command?\n'
                        "- The memory file. Are this job's steps gone from it? If something was planted, is it "
                        'fixed?\n'
                        '\n'
                        'Each check comes back pass or miss, next to the number you predicted at the start.',
         'profile': {'soul': ''},
         'plants': ['steps_in_memory', 'greedy_neighbor'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2},
         'try_lists_a': [{'label': 'Week 1',
                          'text': 'Ana Ruiz, 8-10, canned beans\n'
                                  'Tom Pike (maybe), 10-12, rice\n'
                                  'Lena Ortiz, 8-10, pasta\n'
                                  'Raj Patel, 10-12, peanut butter\n'
                                  'Mia Chen (maybe), 8-10, cereal\n'
                                  'Owen Hart, 10-12, canned soup\n'
                                  'Zoe Brooks, 8-10, diapers\n'
                                  'Sam Okoro, 10-12, oatmeal\n'
                                  'Ivy Lane (maybe), 10-12, tuna'},
                         {'label': 'Week 2',
                          'text': 'Ana Ruiz, 10-12, rice\n'
                                  'Ben Ford, 8-10, canned corn\n'
                                  'Raj Patel, 8-10, cereal\n'
                                  'Nora Diaz (maybe), 10-12, pasta sauce\n'
                                  'Owen Hart, 8-10, flour\n'
                                  'Kai Wong, 10-12, canned beans\n'
                                  'Tom Pike (maybe), 8-10, soap\n'
                                  'Lena Ortiz, 10-12, apples'},
                         {'label': 'Week 3',
                          'text': 'Zoe Brooks, 10-12, rice\n'
                                  'Sam Okoro, 8-10, pasta\n'
                                  'Mia Chen (maybe), 10-12, canned fruit\n'
                                  'Ben Ford, 10-12, oatmeal\n'
                                  'Kai Wong, 8-10, toothpaste\n'
                                  'Ivy Lane (maybe), 8-10, crackers\n'
                                  'Raj Patel, 10-12, canned tuna\n'
                                  'Nora Diaz, 8-10, milk powder\n'
                                  'Ana Ruiz, 8-10, lentils\n'
                                  'Owen Hart, 10-12, cereal'}],
         'note_fields_a': {'first': [{'id': 'job',
                                      'label': 'The job you repeat',
                                      'kind': 'text',
                                      'min': 4,
                                      'max': 200},
                                     {'id': 'asked',
                                      'label': 'How you asked for it in your test chat, word for word',
                                      'kind': 'text',
                                      'min': 4,
                                      'max': 600},
                                     {'id': 'skill_name',
                                      'label': "Your skill's name, as Capabilities shows it",
                                      'kind': 'text',
                                      'min': 3,
                                      'max': 80}],
                           'transfer': [{'id': 'original',
                                         'label': 'The description you read, word for word',
                                         'kind': 'textarea',
                                         'required': False,
                                         'max': 1100},
                                        {'id': 'survives',
                                         'label': 'What survives the cut',
                                         'kind': 'text',
                                         'required': False,
                                         'max': 200},
                                        {'id': 'better',
                                         'label': 'Your better line, 60 characters or fewer',
                                         'kind': 'text',
                                         'min': 8,
                                         'max': 120},
                                        {'id': 'edit_choice',
                                         'label': 'Would you change a built-in skill from its file? And would an '
                                                  'open chat see the change?',
                                         'kind': 'textarea',
                                         'min': 20,
                                         'max': 1500}],
                           'try': [{'id': 'description',
                                    'label': "The try skill's description, word for word",
                                    'kind': 'text',
                                    'min': 5,
                                    'max': 1100},
                                   {'id': 'loaded', 'label': 'Did a Loaded skill row appear?', 'kind': 'bool'}]}},
 'live_checks': [{'id': 'four_parts', 'reader': 'skills.four_parts', 'visible': True},
                 {'id': 'description_words', 'reader': 'skills.description_words', 'visible': True},
                 {'id': 'loaded_unnamed', 'reader': 'skills.loaded_unnamed', 'visible': True},
                 {'id': 'steps_out', 'reader': 'skills.steps_out', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plant.fixed_a', 'visible': False},
                 {'id': 'better_line', 'reader': 'skills.better_line', 'visible': True}],
 'explain': {'lead': 'Use what happened in your own chats:',
             'question': 'Hermes keeps asking how you like your reports formatted. Does the answer belong in memory '
                         "or in a skill? Say why, and how you'd prove Hermes is using it.",
             'rubric': {1: "Picks memory or skill with no reason, or a reason that doesn't hold",
                        2: 'Picks sensibly and says why, with no way to prove it worked',
                        3: 'Splits the fact ("I want reports as PDFs") from the steps (the layout), puts each in its '
                           'place, and names a fair test: a new chat, no hints, a **Loaded skill** row',
                        4: "Adds a point from your own run, such as a description in Hermes's words that you "
                           'rewrote, or a step you found in memory'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Find a skill in your everyday profile that you didn't write. In **Capabilities**, set "
                      '**Configuring:** to your everyday profile and look through its **Skills** tab. Look only; '
                      'change nothing there.\n'
                      '\n'
                      "- Pick one from the hub, or one marked **Learned** that you don't remember asking for. Read "
                      'its description as Hermes would. If it runs past 60 characters, what survives the cut at the last whole word?\n'
                      "- If it fits, does it start with words you'd actually say? Write a better one in 60 "
                      'characters or less.\n'
                      "- Built-in skills have no **Edit** button in the app. Say whether you'd change one anyway "
                      'from its file, knowing Hermes keeps your edit but stops updating that skill for you from then '
                      'on.\n'
                      '\n'
                      "Then use mission 4: if you did change a description, would a chat that's already open see it? "
                      'Why?',
              'live_checks': ['better_line']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/05-skills.v2.md (Hermes v0.22.4).'}]}
