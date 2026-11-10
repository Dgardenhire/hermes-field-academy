# Watch it done

## Step 1: She lists the job first
- **Did:** Wrote the job's actions: read the meeting notes, write one page.
- **Saw:** Two actions, both on files in one folder.
- **Noticed:** Nothing in the job runs a program, browses or searches the web.
- **Ruled out:** Starting from the list of toolsets and asking which ones might come in handy.

## Step 2: She switches off what the job doesn't use
- **Did:** In **Capabilities**, set **Configuring:** to the practice's profile and opened the **Tools** tab. Switched off terminal, code execution, browser and web.
- **Saw:** The count of toolsets on dropped, and file stayed on.
- **Noticed:** The tab saves its list in the profile's `config.yaml`, under `platform_toolsets`.
- **Ruled out:** Switching off everything, file included, which would stop the job itself.

## Step 3: She tests it the way an attacker would
- **Did:** In a new chat, asked Hermes to run `date` in the terminal.
- **Saw:** Hermes said it had no terminal tool. No tool call in the activity.
- **Noticed:** A settings screen is a claim. A refused request is proof.
- **Ruled out:** Trusting the switch without trying it.

## Step 4: She looks for other ways in
- **Did:** Read the profile's connectors and its plugins.
- **Saw:** A filesystem connector, set up a year ago for a scanner, pointed at her whole home folder.
- **Noticed:** Switching toolsets off doesn't touch a connector. That one could read and change patient files.
- **Ruled out:** Leaving it because "it's only the scanner's." She pointed it at the scanner's own folder.

## Step 5: She does the job and reads the result
- **Did:** Asked for the page in a new chat.
- **Saw:** Read-file calls, one write, and a page with every meeting on it.
- **Noticed:** The job never noticed the tools were gone.
- **Ruled out:** Putting a toolset back "to be safe."
