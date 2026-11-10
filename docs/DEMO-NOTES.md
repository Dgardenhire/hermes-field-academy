# Demo notes: Field Academy 0.9 in 60 seconds

Private. Left out of the public package (`.public-exclude`). For the hackathon video and any live walk-through.

## The hook

**"Prove what you can do with Hermes."** Open on the Field Academy home page, the mountain banner and the
Foundations card right under it, and say it over the three parts.

Keep Hermes the hero. The planted problems are the kind every real setup runs into (a full memory, saves waiting
for approval, a job pointed at a typo), and Hermes is the one that tells you about them when you know where to look.
Don't frame any beat as Hermes failing or forgetting. The story is a person getting good at Hermes, and having proof.

## The moments, in order (about 10 seconds each)

1. **The first screen.** Banner, then the card: *A problem is planted first. The check reads Hermes itself. The
   record opens anywhere.* Let the file names show: `memories/MEMORY.md`, `state.db`, `MANIFEST.sha256`.
   Line: "Eleven missions. Each one runs in its own practice profile, so my own Hermes stays as it was."
2. **The practice profile appears.** Press the button in mission 3; cut to Settings, Profiles, where
   `academy-practice` shows up. Line: "Field Academy asks Hermes to make a fresh profile and sets up one snag in it."
3. **Your turn.** The two notes the owner can't lose, then **Open practice chat**. In the chat, ask Hermes to remember
   one fact. The app shows the memory row. Line: "Hermes tells me what it did. Now let's see it on disk."
4. **The check.** Press **Check my work**. The cards fill in with what Field Academy read: `MEMORY.md` 479 of 2,200
   characters, the held save in `pending/`. Line: "The check reads Hermes's own files. Not my word, not a quiz."
   Then the fix: approve the held save in Hermes, check again, and it passes.
5. **Compare.** Guess, self-score and result side by side. Line: "It also tracks whether my judgment is getting
   better."
6. **The record.** Open the Field Record, scroll to **Every excerpt**, tick **Keep this excerpt out** on one.
   Save, open the folder, run `shasum -a 256 -c MANIFEST.sha256`, every line `OK`. Line: "Anyone I send this to
   can check it, without Hermes."

Close on the Foundations card again, or the mountain.

## After the persona test (November 8)

- The home page now has one **Start here**, on the Foundations card. Open on it.
- In moment 4, after the miss, the **Fixed it? Check again** panel sits right under the result. Use it on camera
  instead of jumping to Fix and transfer.
- In moment 6, open `record.md` too: the **Verdict** line on top, an excerpt captioned "Backs check 2", and **Ask the
  holder** under the entry. That's the hiring-manager beat.
- Mission 7's settings text hides passwords and tokens on screen, so it's safe to show; still, don't scroll a real
  profile's connectors on a recording.
- Don't pan across Check yourself answers: they open only after an answer is typed.

## Shots worth having in the can

- Mission 8: **Two scheduled runs have landed** on the page the morning after. Shows checks that wait for the real
  world, which a prompt can't do.
- Mission 7: Hermes stopping to ask before an untrusted connector writes, then the check finding the refusal in the
  chat record.
- The page in light mode with a green accent, and in a narrow window, to show it follows the user's own theme.

## Say carefully

- Field Academy is a community plugin, not made or endorsed by Nous Research. Say it once, on screen or in the
  description.
- A Field Record is self-issued. "Anyone can check the files didn't change", not "it proves I'm certified".
- Practice chats run on your own provider. Each mission states its expected cost.
