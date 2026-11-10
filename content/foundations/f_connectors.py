"""Foundations mission 7: Connect an outside tool safely.

Learner text comes from .planning/field-academy-v3/missions/07-connectors.v2.md, learner sections only. Changed from
it on purpose: the pinned connector (@modelcontextprotocol/server-filesystem 2026.8.31, read Oct 22) registers 14
tools, the README's 13 plus a deprecated read_file alias, so "Work it out" counts 14, 10 read-only and 4 that change
things. The build notes became the setup, the plants, the live checks and the "as of Hermes" facts below.
"""

MISSION = {'id': 'f.connectors',
 'title': 'Connect an outside tool safely',
 'order': 7,
 'idea_refs': [10],
 'domain': 'D5',
 'level': 'beginner',
 'minutes': {'read': 25, 'do': 40},
 'cost': {'chats': 4,
          'words': 'small change on most providers',
          'line': 'Expected cost: three or four short chats on your provider. The connector itself runs on your own '
                  "computer and costs nothing; its first start downloads it, so you'll need to be online."},
 'as_of': [{'fact': 'A connector with no trust setting runs at full trust; an unknown word counts as untrusted',
            'file': 'tools/mcp_tool_registration.py',
            'pattern': "None -> ``full`` \\(compat default\\); unrecognized -> ``untrusted`` \\(fail closed\\)",
            'since': '0.22.4'},
           {'fact': "An untrusted connector's write tool asks: MCP tool '<tool>' on UNTRUSTED server '<server>' wants to run",
            'file': 'tools/mcp_tool_handlers.py',
            'pattern': "MCP tool '\\{tool_name\\}' on UNTRUSTED server '\\{server_name\\}' wants to run\\.",
            'since': '0.22.4'},
           {'fact': 'A turned-down write is recorded in the chat as not approved and not run',
            'file': 'tools/mcp_tool_handlers.py',
            'pattern': 'The user did not approve running write-capable MCP tool',
            'since': '0.22.4'},
           {'fact': 'tools.include is an allow list, and an empty one registers nothing',
            'file': 'tools/mcp_tool_registration.py',
            'pattern': '``tools.include`` is a whitelist \\(``\\[\\]`` = register',
            'since': '0.22.4'},
           {'fact': "Each connector start writes ===== starting MCP server '<name>' ===== to mcp-stderr.log",
            'file': 'tools/mcp_tool_config.py',
            'pattern': "===== starting MCP server '\\{server_name\\}' =====",
            'since': '0.22.4'},
           {'fact': 'Saving the connector box says MCP server saved; a bad paste says Invalid MCP JSON',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "invalidJson: 'Invalid MCP JSON'(?:.|\\n){0,400}savedTitle: 'MCP server saved'",
            'since': '0.22.4'},
           {'fact': 'The Capabilities profile picker is labeled Configuring:',
            'file': 'apps/desktop/src/i18n/en.ts',
            'pattern': "configuringProfile: 'Configuring:'",
            'since': '0.22.4'},
           {'fact': "The app's chats honour agent.disabled_toolsets, which switches off Hermes's own file and terminal tools here",
            'file': 'tui_gateway/agent_factory.py',
            'pattern': 'def _load_disabled_toolsets\\(\\)',
            'since': '0.22.4'}],
 'recall': {'lead': 'In the last mission you kept two jobs in two profiles. Jot down two things:',
            'prompts': ["one thing a profile keeps separate, and one thing it doesn't",
                        'how you knew which profile you were in'],
            'seconds': 180,
            'from': 'f.profiles'},
 'claim': {'text': 'I can connect an outside tool to Hermes with only the access a job needs, and prove from its '
                   'settings and a real attempt that it asks me before it changes anything.',
           'author': 'course'},
 'standard_lead': "Four checks. Miss one and you can't do it yet. They won't change after you start.",
 'labels': {'fresh': 'A fresh practice profile',
            'recall': 'Recall, three minutes, no looking back',
            'claim': "What you'll be able to do",
            'standard': "How you'll know",
            'predict': 'Your guess'},
 # Shown on the Practice and Your turn steps, before the first chat (0.9 persona test).
 'practice_note': "This practice profile has a filesystem connector. When a practice chat opens, Hermes starts it with `npx`, which downloads a pinned package from npm and keeps it running while the chat is open. It can reach one folder, inside the practice profile. Hermes's own file and terminal tools are off here.",
 'fresh_text': "This mission builds a new `academy-practice`, with its own practice folder. The mission page also shows whether practice chats open in the practice folder. If it shows a fail, the fix takes a minute: press **Copy** beside the practice folder, choose that folder with the chat's folder picker, and start a new practice chat before you begin.",
 # Shown only when a practice profile from an earlier mission is still there (0.9 persona test).
 'fresh_replace': "The practice profiles from an earlier mission are removed when you set up practice, after Field Academy saves their evidence to your record. You'll be asked to confirm first.",
 'standard': [{'id': 's1',
               'text': 'The connector reaches only the practice folder, and an allow list names only the tools this '
                       'job needs.',
               'proves_by': 'live:connector_scoped'},
              {'id': 's2',
               'text': 'Its trust is set so any tool that can change things asks first.',
               'proves_by': 'live:connector_untrusted'},
              {'id': 's3',
               'text': 'A real attempt to change something stopped and asked you, and you turned it down.',
               'proves_by': 'live:write_refused'},
              {'id': 's4',
               'text': "The connector started cleanly, and you can show where that's recorded.",
               'proves_by': 'live:clean_start'}],
 'predict': {'per_check': True,
             'ask_step': True,
             'lead': "Write down how many checks you expect to pass, and where you think you'll slip. You'll see it "
                     'beside the result.'},
 'try': 'md/f.connectors.try.md',
 'idea': 'md/f.connectors.idea.md',
 'expert': 'md/f.connectors.expert.md',
 'expert_lead': 'Farid Haddad runs a two-person print shop. Customers email order sheets, and he saves each one as a '
                'text file in an `orders` folder. He wants Hermes to read the week\'s orders and write a short '
                'summary. Nothing else.',
 'expert_note': 'Farid and his shop are made up.',
 'expert_slots': ['Which connectors do you run every day, and which have you removed? Why?',
                  "Have you seen a connector's output try to steer Hermes? What happened?",
                  'How do you decide whether a connector gets trust: untrusted?',
                  "What's the first thing you check when a connector's tools don't show up?"],
 'record_example': 'md/f.connectors.record-example.md',
 'lab': {'body': 'The practice folder holds a week of sample orders. The job: read them and write one summary file in '
                 'the same folder. Work only in `academy-practice`, and start every chat with **Open practice '
                 'chat**. When a message needs the folder, paste its full path from the mission page.\n'
                 '\n'
                 "1. **List the job's actions** before you change anything.\n"
                 '2. **Fit the `files` connector to the job,** using the settings text from the mission page and the '
                 'tools list.\n'
                 '3. **Watch the gate work.** The first time Hermes asks to write, read the card and turn it down. '
                 'Seeing it stop is your proof that the setting holds, and Hermes writes the refusal into the chat. '
                 'Then ask again and approve, so the summary gets written.\n'
                 '4. **Prove the other checks.** How is up to you.\n'
                 '\n'
                 'Field Academy has also set one trap, in the profile or in the folder. At Advanced there are two, '
                 'one in each place. If a check '
                 "fails when you thought it should pass, that's your lead.\n"
                 '\n'
                 "When you're done, press **Save what I did** below. Then score yourself, and run the checks on the Check step.",
         'checks_text': "Field Academy reads the practice profile's settings, connector log and chat records, and the "
                        'practice folder, itself. Nothing needs pasting in.\n'
                        '\n'
                        '- The connector settings. Does exactly one connector reach the practice folder? Does its '
                        'allow list hold only tools this job needs? Is it untrusted?\n'
                        '- Your chats. Is there a turned-down write? Hermes records the refusal in the chat.\n'
                        '- The connector log. Did it start cleanly after your last change, and did a tool call '
                        'succeed?\n'
                        '- The folder. Is there a summary file, and is every order still where it started?\n'
                        '\n'
                        'Field Academy lines up each result with what you predicted, so you can see where your guess '
                        'was off.',
         'profile': {'soul': ''},
         'setup': 'connectors',
         'folder': True,
         'panels': ['folder', 'working_folder', 'connector_text'],
         # The try's own note (0.9 persona test): what the learner counted and guessed before the lesson, kept with the attempt.
         'try_fields': [{'id': 'tools_total', 'label': 'How many tools the files connector offers', 'kind': 'number', 'required': True},
                        {'id': 'tools_on', 'label': 'How many of them are on', 'kind': 'number', 'required': True},
                        {'id': 'guess_asks', 'label': 'Your guess: will Hermes check with you before it moves the file?',
                         'kind': 'choice', 'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}], 'required': True},
                        {'id': 'times_asked', 'label': 'How many times Hermes asked your permission', 'kind': 'number'}],
         'note_fields': [{'id': 'actions', 'label': "The job's actions, listed before you changed anything", 'kind': 'long',
                          'required': True, 'min': 10, 'max': 600},
                         {'id': 'server', 'label': 'The connector you fitted to the job', 'kind': 'text',
                          'placeholder': 'files', 'max': 60},
                         {'id': 'injection', 'label': 'Anything in the folder that tried to give Hermes orders',
                          'kind': 'long', 'max': 600},
                         {'id': 't_free', 'label': 'How many tools run without asking', 'kind': 'number', 'for': 'transfer',
                          'required': True},
                         {'id': 't_ask', 'label': 'Which tools ask first', 'kind': 'long', 'for': 'transfer', 'required': True,
                          'max': 600},
                         {'id': 't_blocked', 'label': "Which tools can't run at all", 'kind': 'long', 'for': 'transfer',
                          'max': 600},
                         {'id': 't_change', 'label': "What you'd change, and why", 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800},
                         {'id': 't_profile', 'label': 'Which profile this connector belongs in, and what would happen in '
                                                      'their main profile', 'kind': 'long', 'for': 'transfer',
                          'required': True, 'min': 10, 'max': 800}],
         'plants': ['twin_connector', 'order_injection'],
         'plants_at': {'beginner': 1, 'intermediate': 1, 'advanced': 2}},
 'live_checks': [{'id': 'connector_scoped', 'reader': 'connectors.one_scoped', 'visible': True},
                 {'id': 'connector_untrusted', 'reader': 'connectors.untrusted', 'visible': True},
                 {'id': 'write_refused', 'reader': 'connectors.refusal_seen', 'visible': True},
                 {'id': 'clean_start', 'reader': 'connectors.clean_start', 'visible': True},
                 {'id': 'folder_outcome', 'reader': 'connectors.folder_outcome', 'visible': True},
                 {'id': 'plant_fixed', 'reader': 'plants.all_fixed', 'visible': False},
                 {'id': 'reading', 'reader': 'connectors.reading', 'visible': True}],
 'explain': {'lead': 'Draw on the connector you just fitted:',
             'question': 'A connector deleted a file without asking. Name two settings that would have stopped it, and '
                         "say what each one does that the other doesn't.",
             'rubric': {1: 'Says "turn on approvals," or blames the model, without naming a connector setting',
                        2: "Names untrusted or an allow list, but not both, or can't say how they differ",
                        3: "Names both: the allow list removes the delete tool so it can't run; untrusted makes tools "
                           "that can change things ask. Notes that Hermes's terminal approvals don't cover connectors",
                        4: 'Adds a point from your own run: the refusal you saw, a planted problem you found, or why '
                           "the read-only label alone isn't enough"},
             'pass_level': 3,
             'after': ''},
 'transfer': {'body': 'Field Academy shows you a connector setup someone else wrote, as a short settings block. '
                      'Without running anything, answer:\n'
                      '\n'
                      '- Which tools can Hermes use without asking?\n'
                      '- Which only after asking?\n'
                      "- Which can't it use at all?\n"
                      '- What would you change, and why?\n'
                      '\n'
                      'Then use mission 6: the person works for two clients. Say which profile this connector belongs '
                      'in, and what would happen if it sat in their main profile instead.',
              'example': {'command': 'npx',
                          'args': ['-y', '@modelcontextprotocol/server-filesystem@2026.8.31', '~/Clients'],
                          'trust': 'untrusted',
                          'tools': {'exclude': ['move_file']}},
              'live_checks': ['reading']},
 'review': [],
 'revisions': [{'date': '2026-10-22', 'what': 'Built from missions/07-connectors.v2.md (Hermes v0.22.4); the tool '
                                               'count follows the pinned connector, 14.'}]}
