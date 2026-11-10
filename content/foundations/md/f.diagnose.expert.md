# Watch it done

## Step 1: 8:15, she keeps the card's details
- **Did:** Every message to Hermes ended in an error card naming the provider or model. She pressed **Copy error details** and pasted them into a note before touching anything else.
- **Saw:** A card that names the layer.
- **Noticed:** The card says where, and stops there.
- **Ruled out:** Pressing Retry until something changed.

## Step 2: 8:17, she runs the doctor
- **Did:** Ran the doctor.
- **Saw:** Clean on her provider and key.
- **Noticed:** That rules out an expired key. It doesn't touch the model name.
- **Ruled out:** A missing or rejected key.

## Step 3: 8:20, she reads errors.log at the minute
- **Did:** Opened `errors.log` at 8:15.
- **Saw:** An ERROR showing the provider refusing the request, with the model from her settings. It had a stray letter. Her nephew had changed models for her on Saturday.
- **Noticed:** The log held what the doctor couldn't see.
- **Ruled out:** The network: something had answered.

## Step 4: 8:22, she backs up and changes one thing
- **Did:** Made a quick backup, corrected the model name in **Settings → Model**, and started a new chat.
- **Saw:** It answered.
- **Noticed:** One change, one test, so she knew which change fixed it.
- **Ruled out:** Changing several settings at once.

## Step 5: 8:24, she doesn't assume the job had the same problem
- **Did:** Opened the overnight rent-reminder job's run history instead of assuming the model fix covered it.
- **Saw:** The run finished, and its reply said it couldn't find the rent folder. In `errors.log`, a warning from Saturday night: the job's working folder no longer existed, running without it. Someone had renamed "Rent 2026" to "Rent."
- **Noticed:** A different layer: the scheduled job.
- **Ruled out:** "Same problem, now fixed."

## Step 6: 8:31, she fixes the job and watches it work
- **Did:** Asked Hermes to point the job at the new folder, and watched the next run.
- **Saw:** The next run did the work.
- **Noticed:** A finished run isn't proof; a run that did the work is.
- **Ruled out:** Calling it fixed before the next run.

## Step 7: Later, she reads the report before sharing it
- **Did:** Ran `hermes debug share --local` before posting a debug report in the Hermes Discord.
- **Saw:** Tenant names in the log lines.
- **Noticed:** Keys are hidden in a debug report; names and chat pieces aren't.
- **Ruled out:** A public upload. She used **Send diagnostics** instead.
