Field Academy has added a connector called `files` to the practice profile. It reads and writes files in the practice
folder, and nowhere else. For this mission, Hermes's own file and terminal tools are switched off in the practice
profile, so the connector is the only way it can touch files. The mission page shows the practice folder's full path,
with a copy button.

1. **Look at what it offers.** Open **Capabilities**, set **Configuring:** to `academy-practice`, and go to the
   **Connectors** tab. Open `files` and read its list of tools. Write down how many there are and how many are on.
2. **Your guess.** You're about to ask Hermes to move a file. Will it check with you first? Write yes or no.
3. **Ask.** Press **Open practice chat**. Paste the folder path into this message where it says `<path>`, then send:
   `Use the files connector to make a folder called archive inside <path>, and move old-flyer.txt from <path> into it.`
   Count how many times Hermes asks your permission.
4. **Put it back.** Send: `Move old-flyer.txt back where it was and remove the empty archive folder.`

Hermes asks before it runs a risky command, so a yes is a fair guess. It didn't ask once. The activity rows show a
folder made and a file moved, start to finish, with nobody consulted.
