"""Foundations mission 8: Set up a job that runs on a schedule.

Learner text comes from .planning/field-academy-v3/missions/08-schedules.v2.md, learner sections only. The draft job
the planted problems live in is made by Hermes itself: the page sends cron.manage (add, then pause) through
host.requestProfile, and Field Academy reads the job list afterwards. jobs.json is never written. Check 1 is read by
Field Academy from the job's request (the five parts and the conversation phrases); the record tags it that way.
"""

MISSION = {'id': 'f.schedules',
 'title': 'Set up a job that runs on a schedule',
 'order': 8,
 'idea_refs': [9],
 'domain': 'D7',
 'level': 'beginner',
 'minutes': {'read': 25, 'do': 50, 'wait': 180},
 'cost': {'chats': 3,
          'words': 'small change on most providers',
          'line': 'Expected cost: a handful of short runs, small change on most providers. A job that fires every few '
                  'minutes on an expensive model is how a bill grows, so keep practice jobs to once an hour and stop '
                  "them when you're done."},
 'as_of': [{'fact': 'Each run records its scheduled instant; a run you start by hand has none',
            'file': 'cron/executions.py',
            'pattern': 'add_column_if_missing\\(conn, "executions", "scheduled_instant"',
            'since': '0.22.4'},
           {'fact': 'Runs the schedule fires are recorded with source builtin',
            'file': 'cron/scheduler.py',
            'pattern': 'source="builtin", scheduled_instant=job.get\\("_scheduled_instant"\\)',
            'since': '0.22.4'},
           {'fact': 'A run within 300 seconds of its slot counts as on time',
            'file': 'cron/jobs.py',
            'pattern': '_LATE_DISPATCH_TOLERANCE_SECONDS = 300',
            'since': '0.22.4'},
           {'fact': 'Trigger now switches a paused job back on',
            'file': 'hermes_cli/web_routers/cron.py',
            'pattern': 'force = not job.get\\("enabled", True\\) or job.get\\("state"\\) == "paused"',
            'since': '0.22.4'},
           {'fact': 'Scheduled jobs refuse risky commands by default',
            'file': 'hermes_cli/config_defaults.py',
            'pattern': '"cron_mode": "deny"',
            'since': '0.22'},
           {'fact': 'A misspelled delivery place blocks the run before any model call',
            'file': 'cron/scheduler.py',
            'pattern': 'BLOCKED by pre-dispatch config validation',
            'since': '0.22.4'},
           {'fact': 'Hourly fires at the top of every hour',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "hourly: 'At the top of every hour'",
            'since': '0.22.4'},
           {'fact': 'The gateway keeps running after you quit the app',
            'file': 'website/docs/user-guide/desktop.md',
            'pattern': 'it keeps running after you quit and has no idle shutdown',
            'since': '0.22.4'}],
 'recall': {'lead': 'Last mission you connected an outside tool to Hermes. Note two things about it:',
            'prompts': ['what that tool could do without asking you first, before you changed anything',
                        'the setting that made its write tools ask'],
            'seconds': 180,
            'from': 'f.connectors'},
 'claim': {'text': 'I can set up a scheduled job that runs right with nobody watching, and prove from Hermes\'s own '
                   'records that it ran on time and delivered.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 'fresh_text': "This mission builds a new `academy-practice`, with its own practice folder and a few notes already in its memory. The mission page also shows whether practice chats open in the practice folder. If that check fails, set the folder yourself before you begin: copy it from the page, choose it in the chat's folder picker, then open a new practice chat.\n\n**How long this takes.** The lesson and the setup take under an hour. The last check takes longer: it needs your job to run twice on its own, an hour apart. Plan for the computer to stay awake for two to three hours after you set the job up. You can quit the app in the meantime. Field Academy tells you when two scheduled runs have landed, and if the app was closed, you'll see it the next time you open Field Academy. The waiting doesn't count toward the hours in your record. When it's over, you'll pause or delete the job, so it stops costing you every hour.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "The practice profile from an earlier mission is removed when you set up practice, after Field Academy saves its evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': "The job's request names where to work, what to read, what a good result looks like, where it "
                       'goes, and what to do if it fails.',
               'proves_by': 'live:request_parts'},
              {'id': 's2',
               'text': 'You tested it while it was paused, before it ever ran on its own.',
               'proves_by': 'live:tested_paused'},
              {'id': 's3',
               'text': "The job has its own model set, so a change to your main model can't change it.",
               'proves_by': 'live:model_pinned'},
              {'id': 's4',
               'text': 'The run history shows at least two runs the schedule fired on its own, and the result arrived '
                       'where you said.',
               'proves_by': 'live:two_runs'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.schedules.try.md',
 'idea': 'md/f.schedules.idea.md',
 'expert': 'md/f.schedules.expert.md',
 'expert_lead': 'Colleen Brady dispatches for a heating and cooling company with three vans. Her scheduled job was '
                "supposed to text her the day's jobs waiting on parts before the techs called in.",
 'expert_note': 'Colleen and the company are made up; the times are illustrative.',
 'expert_slots': ["What's the first scheduled job you'd tell a new user to build, and which one would you tell them to "
                  'wait on?',
                  'How do you decide a job is trustworthy enough to stop checking it every morning? How many clean '
                  'runs?',
                  'Has a job of yours ever "succeeded" while doing the wrong thing? What gave it away?',
                  "Do you pin every job, or only some? What's your rule?",
                  'Where do your own jobs run: laptop, office machine, server? What made you move them?'],
 'record_example': 'md/f.schedules.record-example.md',
 'lab': {'memory_view': True,  # the page offers Show memory file on this mission (0.9 persona test)
         'body': 'The practice profile holds a draft job called `academy-draft-summary`, paused, and a folder of '
                 'sample files. Expect one problem in the profile that will make a job fail or land in the wrong '
                 'place.\n'
                 '\n'
                 "1. Pick a small job you'd really want on a schedule, using the sample files: a summary, a list or a "
                 "check. Start from the draft or make your own. The mission page shows the folder's full location to "
                 'paste into the request.\n'
                 '2. Set it up to meet all four checks in your standard, in the **Scheduled jobs** view, with the '
                 'mission page showing a pass for `academy-practice`.\n'
                 '3. Schedule it hourly and resume it. Then keep the computer awake: plugged in, lid open, and set not '
                 'to sleep.\n'
                 '   - **Windows 11:** Settings → System → Power & battery → Screen and sleep. Set "When plugged in, '
                 "put my device to sleep after\" to Never. On Windows 10 it's Settings → System → Power & sleep.\n"
                 '   - **Mac:** System Settings → Battery → Options, then turn on "Prevent automatic sleeping on power '
                 'adapter when the display is off." On a desktop Mac, look under System Settings → Energy.\n'
                 '   - **Linux:** in most desktops, Settings → Power, and turn off automatic suspend.\n'
                 '\n'
                 '   Write down what the setting was, so you can put it back. You can quit the app. Field Academy tells '
                 'you when two scheduled runs have landed. If the computer sleeps anyway, the run that fires when it '
                 'wakes still counts toward check 4, because the schedule fired it, not you. Your record marks it '
                 'late.\n'
                 '4. **Stop it.** After the second run lands, pause or delete the job in **Scheduled jobs** '
                 '(**Pause**, or **Delete**). An hourly job keeps costing you every hour until you do. Then put your '
                 'sleep setting back.\n'
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's job list and run history itself, in the background. "
                        "You don't copy anything anywhere.\n"
                        '\n'
                        "- Your job's request: does it cover the five parts, and does it still lean on a "
                        'conversation?\n'
                        '- The run history: was the job run by hand, while you were testing, before its first '
                        'scheduled run?\n'
                        "- The job's own record: does it have a model set?\n"
                        '- The run history again: at least two completed runs the schedule fired, with the result '
                        'delivered? A catch-up run after sleep counts, marked late.\n'
                        '- The planted problem: is it fixed?\n'
                        '\n'
                        'Your prediction sits beside each result.',
         'profile': {'soul': ''},
         'setup': 'schedules',
         'folder': True,
         'panels': ['folder', 'working_folder', 'jobs', 'scheduled_page', 'watch'],
         'try_fields': [{'id': 'guess_greets', 'label': 'Your guess: will the job\'s answer start with "For Yusuf:"?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'guess_file', 'label': 'Your guess: will it know which file you meant?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'run_greets', 'label': 'The run: did its answer start with "For Yusuf:"?', 'kind': 'choice',
                         'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
                        {'id': 'run_file', 'label': 'The run: did it know which file you meant?', 'kind': 'choice',
                         'choices': [{'value': 'knew', 'label': 'Yes, the right file'},
                                     {'value': 'said_so', 'label': 'No, and it said so'},
                                     {'value': 'guessed', 'label': 'No, it picked a file anyway'}]}],
         'note_fields': [{'id': 'job_name', 'label': "Your job's name, as it shows in Scheduled jobs", 'kind': 'text',
                          'required': True, 'max': 80},
                         {'id': 'sleep_setting', 'label': 'Your sleep setting before you changed it, so you can put it back',
                          'kind': 'text', 'max': 200},
                         {'id': 'first_job', 'label': 'The first job, whose output this one reads', 'kind': 'text',
                          'for': 'transfer', 'required': True, 'max': 80},
                         {'id': 'job_name', 'label': "The second job's name", 'kind': 'text', 'for': 'transfer',
                          'required': True, 'max': 80},
                         {'id': 'covered', 'label': "Which of the five parts the first job's output now covers, and which "
                                                    'this job still has to say for itself', 'kind': 'long',
                          'for': 'transfer', 'required': True, 'min': 10, 'max': 800}],
         'plants': ['vague_request', 'bad_delivery'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'request_parts', 'reader': 'schedules.request_parts', 'visible': True},
                 {'id': 'tested_paused', 'reader': 'schedules.tested_paused', 'visible': True},
                 {'id': 'model_pinned', 'reader': 'schedules.model_pinned', 'visible': True},
                 {'id': 'two_runs', 'reader': 'schedules.two_runs', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 'chained', 'reader': 'schedules.chained', 'visible': True}],
 'explain': {'lead': 'From your own run, answer this:',
             'question': 'A job works every time you run it by hand, and it fails every night. Give three likely '
                         "causes, in the order you'd check them, and how you'd check each one.",
             'rubric': {1: 'Names causes that don\'t fit a job that works by hand, such as "the request is wrong"',
                        2: 'Names causes that fit, with no way to check them',
                        3: 'Three fitting causes in a sensible order, each with a check someone could do',
                        4: 'Adds a point from your own run: a sleeping computer, a job on Default whose main model '
                           'moved, a risky step refused with nobody there, or Trigger now switching a paused job '
                           'back on'},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': "Build a second job that uses the first job's latest result. Hermes can pass one job's output to "
                      'another; ask it in a practice chat to set that up.\n'
                      '\n'
                      '- Send it somewhere different from the first job.\n'
                      "- Before it runs, write down which of the five parts the first job's output now covers, and "
                      'which this job still has to say for itself.\n'
                      '\n'
                      'Test it the same way: paused first, run by hand, then the run history.',
              'live_checks': ['chained']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/08-schedules.v2.md (Hermes v0.22.4).'}]}
