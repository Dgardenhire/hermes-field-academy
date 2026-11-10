"""Foundations mission 10: Find out why Hermes failed, and fix it.

Learner text comes from .planning/field-academy-v3/missions/10-diagnose.v2.md, learner sections only. Round one (the
model name with one letter changed) is the setup every learner gets; it is shown for comparison, never graded. Round
two draws one break: a connector whose command isn't there, or a scheduled job Hermes can't deliver (cron.manage has
no working-folder field, so the build notes' missing-folder job is replaced by a misspelled delivery place, which
Hermes also logs as a WARNING and still marks the run). The transfer round, after Reset, plants the other one.

The app's Run doctor and Create backup act on the app's own selected profile and the plugin SDK has no door to aim
them at another, so the page gives the terminal commands with Copy and lists backups it reads itself.
"""

LAYERS = [{'value': v, 'label': v.capitalize()} for v in ('model', 'connector', 'scheduled job', 'tool', 'app')]

MISSION = {'id': 'f.diagnose',
 'title': 'Find out why Hermes failed, and fix it',
 'order': 10,
 'idea_refs': [],
 'domain': 'D9',
 'level': 'beginner',
 'minutes': {'read': 25, 'do': 45},
 'cost': {'chats': 4,
          'words': 'small change on most providers',
          'line': "Expected cost: a few short chats and one scheduled run on your provider; `/usage` in a chat shows that "
                  "chat's share. The doctor, the logs and backups don't call a model, so they cost nothing."},
 'as_of': [{'fact': "A connector that can't start logs Failed to connect to MCP server as a WARNING",
            'file': 'tools/mcp_tool_discovery.py',
            'pattern': 'logger\\.warning\\("Failed to connect to MCP server',
            'since': '0.22.4'},
           {'fact': 'Log lines start with the local date and time, the level, then the source',
            'file': 'hermes_logging.py',
            'pattern': '_LOG_FORMAT = "%\\(asctime\\)s %\\(levelname\\)s%\\(session_tag\\)s %\\(name\\)s: %\\(message\\)s"',
            'since': '0.22.4'},
           {'fact': 'errors.log takes warnings and up and rotates at 2 MB, keeping two old files',
            'file': 'hermes_logging.py',
            'pattern': '\\("errors\\.log", logging\\.WARNING, 2 \\* 1024 \\* 1024, 2, None\\)',
            'since': '0.22.4'},
           {'fact': 'A refused request logs Non-retryable client error',
            'file': 'agent/turn_recovery.py',
            'pattern': 'Non-retryable client error',
            'since': '0.22.4'},
           {'fact': 'A model the provider doesn\'t know sends the chat to the backup models, if any',
            'file': 'agent/error_classifier.py',
            'pattern': 'model_not_found triggers fallback',
            'since': '0.22.4'},
           {'fact': "The app's Create backup writes into the profile's own backups folder",
            'file': 'hermes_cli/web_routers/ops.py',
            'pattern': '``<profile home>/backups``',
            'since': '0.22.4'},
           {'fact': 'A job with a misspelled delivery place is blocked before any model call, with a WARNING',
            'file': 'cron/scheduler.py',
            'pattern': 'BLOCKED by pre-dispatch config validation',
            'since': '0.22.4'}],
 'recall': {'lead': 'Last mission you set up guardrails and undo. Two things, straight from memory:',
            'prompts': ['one thing a checkpoint can undo, and one thing nothing can undo',
                        'where an "Always allow" answer gets saved, and what else it reaches'],
            'seconds': 180,
            'from': 'f.safety'},
 'claim': {'text': "I can find why Hermes failed within ten minutes using its own diagnostics, fix it, and show the fix "
                   'holds.',
           'author': 'course'},
 'standard_lead': ("These four checks apply to round two, the break you aren't told about. They would prove the claim "
                   "false, and they won't change after you start."),
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': "This mission builds a new `academy-practice`. It arrives already broken, on purpose.\n\nThis mission has two rounds. In the first, everyone gets the same break and the lesson walks you through it. In the second, the practice profile has a break picked for you, and you're on your own.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "It replaces the one from an earlier mission. Field Academy saves its evidence first and asks you before it removes anything.",
 'standard': [{'id': 's1', 'text': 'You named the layer that failed: the model, a connector, a scheduled job, a tool, '
                                   'or the app.', 'proves_by': 'live:layer_named'},
              {'id': 's2', 'text': 'You found the log or report line that proves it, and you can quote it.',
               'proves_by': 'live:line_quoted'},
              {'id': 's3', 'text': 'You made a backup, then fixed it.', 'proves_by': 'live:backup_first'},
              {'id': 's4', 'text': "A new chat, or the job's next run, works.", 'proves_by': 'live:works_after'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.diagnose.try.md',
 'idea': 'md/f.diagnose.idea.md',
 'expert': 'md/f.diagnose.expert.md',
 'expert_lead': 'Odessa Pruitt coordinates a property management office with 40 rental units. Her Monday, from her '
                'own notes.',
 'expert_note': 'Odessa is made up for this lesson, and so are her times. The cards, buttons and log lines are real '
                'Hermes.',
 'expert_slots': ["What's the most confusing failure you've had, where the obvious layer wasn't the real one?",
                  'When Hermes breaks for you, what\'s the very first thing you look at, honestly?',
                  "Do you back up before every change, or only some? Where's your line?",
                  'What should a client try before they call you, and what should they never touch?',
                  "Have you seen a log or debug report that held something it shouldn't have? What was it?"],
 'record_example': 'md/f.diagnose.record-example.md',
 'lab': {'body': "Round two. The practice profile's model works now, and a second break has been sitting behind the "
                 "first. It's in a different layer. Finding which one is the round.\n"
                 '\n'
                 "One kind of line is worth knowing before you start, because it's easy to scroll past. When a "
                 "connector can't start, `errors.log` gets a WARNING like this one (the name, path and reason here "
                 'are made up; yours will differ):\n'
                 '\n'
                 '```\n'
                 "2026-10-22 14:03:51,207 WARNING tools.mcp_tool: Failed to connect to MCP server 'notes-reader' "
                 '(command=C:\\Tools\\notes-server.exe): ...\n'
                 '```\n'
                 '\n'
                 'The words to look for are "Failed to connect to MCP server". After them come the connector\'s name, '
                 "the command Hermes tried to run, and the reason. It's a WARNING, so it doesn't stop your chat. The "
                 "chat just goes on without that connector's tools.\n"
                 '\n'
                 '### Your turn\n'
                 '\n'
                 '1. Start a timer.\n'
                 '2. Use the profile the way you normally would: press **Open practice chat** and ask for something '
                 'real. Then open **Scheduled jobs** and look at the job there. The page works on the profile of the '
                 'chat you last sent in, which is now `academy-practice`. The mission page shows a pass line when the '
                 'app is pointed there; if it shows a fail, follow its fix first.\n'
                 '3. Find the layer that failed and the line that proves it. Under **The practice profile\'s tools**, '
                 "the mission page has the practice profile's logs folder and the doctor command to copy into a "
                 'terminal.\n'
                 '4. Copy the backup command from the same place and run it, then fix the break and show the fix '
                 'holds.\n'
                 '5. Stop the timer and write down how long it took.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's settings, logs, scheduled jobs and backups itself, "
                        'in the background.\n'
                        '\n'
                        '- Is the planted fault gone? *Field Academy reads this.*\n'
                        "- Does the line you quoted appear in the practice profile's logs or the job's records, and "
                        'does it point at the layer you named? *Field Academy reads this.*\n'
                        '- Was a backup made before the fix? *Field Academy reads this.*\n'
                        "- Did a new chat, or the job's next run, succeed after the fix? *Field Academy reads this.*\n"
                        '\n'
                        'Your Explain it answer, below, is the one part your own Hermes grades.\n'
                        '\n'
                        'Your prediction sits beside each result, with your time from both rounds.',
         'profile': {'soul': ''},
         'setup': 'diagnose',
         'folder': True,
         'transfer_swap': True,
         'panels': ['folder', 'ops', 'jobs', 'scheduled_page'],
         'try_fields': [{'id': 'card_part', 'label': 'The part of Hermes the card says failed', 'kind': 'text',
                         'required': True, 'max': 200},
                        {'id': 'guess_doctor', 'label': 'Your guess: will the doctor find the problem?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'doctor_found', 'label': 'What the doctor said: did it find the problem?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]}],
         'note_fields': [{'id': 'round_one_minutes', 'label': 'Round one: how long it took, in minutes', 'kind': 'number'},
                         {'id': 'layer', 'label': 'The layer that failed', 'kind': 'choice', 'choices': LAYERS, 'required': True},
                         {'id': 'quote', 'label': 'The line that proves it, copied from the log', 'kind': 'long',
                          'required': True, 'min': 12, 'max': 800},
                         {'id': 'minutes', 'label': 'Round two: how long it took, in minutes', 'kind': 'number'},
                         {'id': 'first_check', 'label': "Which layer you'll check first, and why", 'kind': 'long',
                          'for': 'transfer', 'required': True, 'min': 10, 'max': 600},
                         {'id': 'layer', 'label': 'The layer that failed', 'kind': 'choice', 'choices': LAYERS,
                          'for': 'transfer', 'required': True},
                         {'id': 'quote', 'label': 'The line that proves it', 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 12, 'max': 800},
                         {'id': 'minutes', 'label': 'How long it took, in minutes', 'kind': 'number', 'for': 'transfer'}],
         'plants': ['broken_connector', 'job_blocked'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 1}},
 'live_checks': [{'id': 'layer_named', 'reader': 'diagnose.layer_named', 'visible': True},
                 {'id': 'line_quoted', 'reader': 'diagnose.line_quoted', 'visible': True},
                 {'id': 'backup_first', 'reader': 'diagnose.backup_first', 'visible': True},
                 {'id': 'works_after', 'reader': 'diagnose.works_after', 'visible': True},
                 {'id': 'round_one', 'reader': 'diagnose.round_one', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 't_layer', 'reader': 'diagnose.layer_named', 'visible': True},
                 {'id': 't_line', 'reader': 'diagnose.line_quoted', 'visible': True},
                 {'id': 't_fixed', 'reader': 'plants.all_fixed', 'visible': True}],
 'explain': {'lead': 'Draw on what happened in your own two rounds:',
             'question': 'Walk someone through what you check first when Hermes "stops working," and why that order.',
             'rubric': {1: 'Starts with reinstalling, retrying, or changing settings before looking',
                        2: 'Names some of the right places, with no order or reason',
                        3: "A clear order (the card's layer, the doctor, the logs at that minute, the job's records), a "
                           'reason for each, and a backup before any change',
                        4: 'Adds a point from your own run: what the doctor passed that was still broken, a log line '
                           "that pointed somewhere you didn't expect, or a folder that turned out to be the wrong "
                           "profile's"},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'Press **Reset practice profile**. Field Academy rebuilds it with a different break, in a '
                      'different layer. No hints this time.\n'
                      '\n'
                      "- Before you start, write which layer you'll check first and why.\n"
                      '- Find it, fix it, and quote the line.\n'
                      '- Compare your time with round two.',
              'live_checks': ['t_layer', 't_line', 't_fixed']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/10-diagnose.v2.md (Hermes v0.22.4); the job break '
                                               'is a misspelled delivery place, since cron.manage sets no working '
                                               'folder.'}]}
