## What's going on

You typed one message. Hermes didn't answer it in one go. It ran a loop.

Each time around the loop is one **trip** to the model, the AI that does the thinking:

1. Hermes sends the model everything it needs: its instructions, the tools it's allowed to use, and the chat so far.
2. The model either writes an answer in plain words, or asks Hermes to use one or more tools: read a file, run a command, search the web.
3. If it asked for tools, Hermes runs them, adds what came back to the chat, and goes around again.
4. When the model answers in plain words and asks for nothing, the loop stops. That's the answer you read.

When the model asks for several reads or searches in one trip, Hermes usually runs them together. Commands, and edits to the same file, run one after another. As of Hermes 0.22 there's no limit on the number of trips by default. The loop runs until the model stops asking for tools, or until you stop it.

### Reading the rows

The rows are the record of that loop. Each one has two parts worth reading:

- **The title** says what the step set out to do. A failed save can still be titled **Edited file**.
- **The small icon** beside it says how it went: a check mark when the tool reported success, a warning sign when it failed.

Click a row to expand it and see what went in and what came back.

### The answer is a claim

When the loop ends, the model writes a summary. The same model wrote every step, and it writes the summary from what it believes happened. It doesn't go back and look.

Tools fail. Files turn out empty. A read of an empty file succeeds, so it gets a check mark, and it brings back nothing. The summary can still say "read all four files and counted every date."

So there are three layers of evidence, and each one is stronger than the last:

1. **The answer** tells you what Hermes believes it did.
2. **The rows** tell you what it tried, and whether each tool reported success.
3. **The real thing** tells you what happened: the file on disk, the rows in the sheet, the folder's contents.

### Changing course mid-turn

Type `/steer` and a note, like `/steer only use this week's folder`, and Hermes adds it once the current step finishes. Nothing already done is lost. Press **Stop**, or `Esc`, to end the turn. That throws away the reply in progress and undoes nothing: a file already written stays written.

## Work it out

Use your own count from the Practice step.

Each trip, the model can ask for one tool or several at once. So if you counted 5 rows, the model was asked at most 6 times: once per row, plus once for the answer. If some rows popped up together, it was fewer. After your check, Field Academy shows you the real number from Hermes's own record.

Now take the sentence you wrote down and write the rows that prove it beside it. "I read all four files" needs four reads, each with a check mark, each bringing back real text. Find only three, or one empty, and the sentence is a claim with nothing behind it.

## Check yourself

Answer in the box, then show the answer.

**1. Hermes says "Saved the report to summary.md." Which row backs that up, and what would you still check?**

> A step on `summary.md` with a check mark. Then open the file itself: is the new content there, and did it change just now? The row shows the tool reported success. The file shows what's actually saved.

**2. A row is titled Edited file and has a warning sign. Was the file edited?**

> Don't assume so. The title names the step. The warning sign says it failed. Expand the row to see what came back.

**3. You press Stop after Hermes wrote two of the four files it planned. What's on disk?**

> Two files. Stopping ends the turn and throws away the reply in progress. It doesn't take back steps already done.

## What people get wrong

- **"If it says done, it's done."** The summary is the model's account of its own work, written at the end. To see for yourself, open the output and compare it with one sentence of the summary.
- **"No warning signs means the job came out right."** A tool can succeed and still bring back the wrong thing: an empty file, last week's folder, an old copy. The check mark covers the step. Only the real output covers the job.
- **"Asking 'are you sure?' is a check."** Hermes answers from the same chat it just wrote. It may agree, apologize, or invent a correction. Asking it to open the file and quote the row count is closer. Opening it yourself is the check.

## The judgment: which claims to check

You can't check every word, and you don't need to. Put your checking where a mistake would hide.

1. **Counts and totals.** "38 jobs," "112 hours," "20 rows." A wrong number looks just like a right one.
2. **Words like "all," "every" and "none."** "Read all five sheets" is false if one was empty, and nothing in the answer will tell you.
3. **Anything that leaves the building.** A report you'll send, a file someone else will open. Check those before they go.
4. **Saves and sends.** "Saved," "sent," "updated." Check that the thing exists and changed when Hermes says it did.

Stop checking when each claim the job depends on has one real check behind it.

When it heads the wrong way, steer if the finished steps are still good. Stop if it's about to do something you don't want, like writing in the wrong place, because `/steer` waits for the current step to finish.

A number you pass on to someone else should have a check behind it. When something's wrong, find the cause before you rerun. A rerun on the same bad input gives the same wrong answer, just as confidently.

## Also good to know

- **In a terminal,** each step prints as a line with the tool's name and a short preview. `/verbose` changes how much you see. `Ctrl+C` with an empty prompt stops the turn; if you've started typing, the first press clears your text and the turn keeps going.
- **Queue instead of steer.** `/queue` and a message waits and sends it as the next turn, after this one ends.
- **A quick recap.** In a terminal or a messaging app, `/status` lists the tools used most and the last few files touched.
