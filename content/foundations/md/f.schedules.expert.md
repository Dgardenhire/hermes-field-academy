# Watch it done

## Step 1: She works back from a late morning
- **Did:** Friday at 6:30 a.m. her phone stayed quiet. The parts list arrived at 7:10, the minute she opened her laptop.
- **Saw:** A job that ran, late, with nothing to say why.
- **Noticed:** Most of her setup could still be right; something else held the run back.
- **Ruled out:** Rewriting the request before finding out what happened.

## Step 2: She checks the request was written for a stranger
- **Did:** Read the request again: the Dispatch folder, the two files, what the list should show, Telegram as the place it goes, and `[CRON_FAILURE]` if either file is missing or empty.
- **Saw:** "Like we did yesterday" was crossed out of her first draft. What memory already held, 12-hour times and vans written as "Van 1," was left out.
- **Noticed:** The request named everything a stranger would need.
- **Ruled out:** The request as the cause.

## Step 3: She checks the model
- **Did:** Opened the job's **Model** field.
- **Saw:** A model pinned, because she planned to try a cheaper main model the next week.
- **Noticed:** A change to her main model couldn't reach this job.
- **Ruled out:** A moved main model.

## Step 4: She remembers what the test caught
- **Did:** Went back over her first **Trigger now**.
- **Saw:** It had pulled two of yesterday's jobs, so she'd added "only rows dated today." While she fixed it, the status flipped from paused to active, and she paused it again before the top of the hour.
- **Noticed:** Testing paused had caught a real bug, and Trigger now had switched the job back on.
- **Ruled out:** A half-fixed job firing on its own.

## Step 5: She looks at the machine
- **Did:** Checked where the job runs.
- **Saw:** Her laptop sleeps with the lid closed. The job caught up once, late, when it woke.
- **Noticed:** Nothing runs while the computer sleeps.
- **Ruled out:** A fault in Hermes. She moved the job to the office computer, which stays on, with the gateway installed as a service.

## Step 6: She reads the record before she stops checking
- **Did:** Opened **Run history** after Monday's run and compared its list with the parts file.
- **Saw:** Monday's run on time, and a list that matched the file.
- **Noticed:** An on-time run she'd checked herself is worth more than a feeling it's set up right.
- **Ruled out:** Trusting "ok" without reading the result.
