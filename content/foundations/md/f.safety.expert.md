# Watch it done

## Step 1: She fills in the grid before she lets it touch a file
- **Did:** Filled in the grid for the profile as she found it, on the shared computer in the church office.
- **Saw:** Terminal: approvals on, but `recursive delete` in the always-allow list; checkpoints off. File edits: nothing asks, nothing undoes. Email connector: full trust, and nothing ever undoes a send.
- **Noticed:** Five of six cells were empty or weaker than she'd assumed.
- **Ruled out:** Starting work on a profile she hadn't read.

## Step 2: She removes the old "always"
- **Did:** Looked at where the always-allow entry came from.
- **Saw:** It was months old; someone had answered "always" to save a click.
- **Noticed:** That one answer emptied the terminal's "before" cell for every chat and scheduled job.
- **Ruled out:** Keeping an entry she didn't remember adding. She removed it.

## Step 3: She tests checkpoints where they can work
- **Did:** Turned on checkpoints and tested them with an edit to a spreadsheet sitting loose in her home folder.
- **Saw:** `/rollback` showed nothing.
- **Noticed:** Checkpoints skip the top of the home folder.
- **Ruled out:** Believing the setting worked because it was on. She moved the work into a Donations folder, tried again, and got a snapshot.

## Step 4: She uses the undo for real
- **Did:** Two weeks later, when Hermes merged two months of donor records with the wrong date format, ran `/rollback diff 1`, then `/rollback 1`.
- **Saw:** Every changed line in the diff, then the files put back.
- **Noticed:** Hermes's word that it was restored proved nothing yet.
- **Ruled out:** Trusting the reply. She opened the spreadsheet and checked three rows by hand.

## Step 5: She guards the door nothing can undo
- **Did:** Marked the email connector untrusted.
- **Saw:** Hermes now asks her before it sends a thank-you note.
- **Noticed:** A sent email stays sent, so the only protection is before.
- **Ruled out:** Counting on checkpoints for anything that leaves the computer.
