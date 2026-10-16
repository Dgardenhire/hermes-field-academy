# Troubleshooting

## The page says it failed to render, or stays blank

A component used but never imported is a `ReferenceError` at render. The app's
error boundary replaces the page with "failed to render" and a Retry button, or
the page stays blank when the error comes before the boundary. Run the
preflight:

```bash
python scripts/check_identifiers.py desktop/plugin.js
```

It prints the missing name. `node --check` does not catch this.

## The pane renders but the layout looks wrong

The desktop stylesheet is compiled from app sources at build time and a plugin
file is never scanned, so an arbitrary-value utility can be missing from the
shipped CSS with no error anywhere. Run:

```bash
python scripts/check_plugin_css.py desktop/plugin.js
```

It checks every arbitrary-value class against the app's real stylesheet and
fails with the list. It skips cleanly if the app is not installed; pass
`--css` to point it at a stylesheet.

## "Field Academy is not connected yet"

The desktop half is running and the agent half is not. The desktop half draws the
page; the agent half owns the database. Enable the agent half and restart:

```bash
hermes plugins enable field-academy
```

Check that it landed:

```bash
grep -A16 '^plugins:' ~/.hermes/config.yaml
```

A plugin enabled while the app is running gets its routes the first time
`/api/plugins/field-academy/...` is called: the backend mounts them then. If
that still returns 404, restart the backend.

## A gate will not close

That is the design. Three shapes, and none of them is a checkbox:

- **Desktop gate** — reads live gateway state. If the backend is unreachable the
  gate fails and says so; it does not fall back to a pass.
- **Artifact gate** — reads the file you name, requires its section headings, and
  refuses a stub. It also refuses an empty file, a file over 5 MiB, and anything
  that is not UTF-8 text. Export a PDF or a scan as text or Markdown first.
- **Explain step** — closes only when the agent grades your answer at or above
  the threshold and calls `field_academy_grade_explanation`. A failed attempt
  stays open with the feedback attached and records no evidence.

The state layer refuses `status='done'` on any step a check owns, so this is not
something the interface can work around.

## The grade never arrives

Submitting an explanation writes your answer, then opens a new chat and sends the
grading instruction there, so it never lands in the middle of your own work. Only
on a Hermes too old to let a plugin send into a chat does the instruction go to
the clipboard instead, and the plugin says so: paste it into the new chat and
send it. The answer is saved either way. If the score still never arrives, for
example because you closed that chat, reopen the mission and press **Send for
scoring again**.

## Nothing is offered in chat

`pre_llm_call` offers at most one practice, and only when there is an opportunity
for the level you are currently working. It offers nothing in scheduled jobs,
webhooks or messaging apps (it reads the platform Hermes passes for the turn),
and nothing in a one-shot CLI run. If
offers stopped, check that the agent half is enabled and that `/academy` reports
the level you expect.

## Where the logs are

```bash
hermes logs desktop -f      # the desktop app: boot, renderer errors
hermes logs gui -f          # the backend the app talks to; plugin routes mount here
hermes logs errors -f       # warnings and errors, including plugin import failures
```

A page that fails to render is diagnosed from the desktop log, never by theory:

```bash
grep 'renderer console:main\|error-boundary:contrib:.*field-academy' ~/.hermes/logs/desktop.log | tail
```

`Mounted plugin API routes: /api/plugins/field-academy/` in `gui.log` proves the
**Python half mounted**. It is not evidence that the page renders. Two different
things.

## Verifying a change to the pane

Saving `desktop/plugin.js` is supposed to hot-reload in place. Treat that as a
hypothesis: fingerprint the running pane by reading a string only the new version
contains out of the live window. "I saved the file" is not evidence.

## Running the checks

```bash
python -m unittest discover -s tests        # the full test suite
python scripts/check_identifiers.py desktop/plugin.js
python scripts/check_plugin_css.py desktop/plugin.js
hermes plugins validate . --install-deps    # the catalog admission command, as catalog CI runs it
```
