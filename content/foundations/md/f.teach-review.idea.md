## What's going on

A Field Record is a folder anyone can check without Hermes. That's what makes it worth more than a screenshot, and it's
also why judging one is a skill: the checks prove some things and not others, and a reviewer has to know which.

Your try showed the trap. The record looked finished: a number, a verdict, evidence lines. A quick read says yes. A
check says something else: a file changed after saving, or the holder's own words claiming more than the result lines
show.

Think of it as a sealed envelope with a signed letter inside. An unbroken seal tells you nobody opened it on the way.
It doesn't tell you the letter is true.

### What the folder proves

- **MANIFEST.sha256** lists a fingerprint (SHA-256) for every other file in the folder. Run
  `shasum -a 256 -c MANIFEST.sha256` inside the folder and each line says OK or FAILED. OK means that file is byte for
  byte what was saved. FAILED means it changed after saving.
- **The record number** is made from `record.json` itself. Change anything in it and the number no longer matches. The
  README in the folder says how to check it.
- **Each evidence file** is a short excerpt Field Academy read from a practice profile, with its own fingerprint in the
  record. Secrets were removed before saving.

So a clean check proves the folder is as it was saved. That's all it proves.

### What it leaves open

- **Whether the claims are true.** The holder's case and limits are their own words. The record keeps them as written.
  If the case says "first time" and the result says "after a fix," the record is honest and the words aren't.
- **Who did the work.** Everything ran on the holder's computer. Nobody watched.
- **How hard it was.** Each mission was practice in a profile Field Academy made, at a level the holder picked.

The record says these things about itself in its own words ("What this record doesn't show"). Read that section.
It's the holder's limits, and good holders write them plainly.

### How to read one

1. **Check the fingerprints first.** Know which files you can trust before you read any of them.
2. **Read the result lines under the verdict.** First run, after the fix, which checks missed.
3. **Read their words against those lines.** The case, the limits, the "what I missed."
4. **Write to them.** The record number, what checked out, what didn't, what you can vouch for, and one question that
   would settle what the record can't.

## Work it out

Fill in this table from the folder in your practice profile.

| | What you found | What it proves |
|---|---|---|
| The fingerprint check | Your result | Which files are as saved |
| The result lines | Your result | How the work really passed |
| Their own words | Your result | Whether they describe it fairly |

Now the hard one. Every fingerprint says OK, the number checks, and the case says "I passed every check the first
time." The result line says 2 of 4 first, 4 of 4 after the fix. Is the record tampered with?

> No. Nothing was changed after saving, so every check passes. The words claim more than the record shows. That's a
> question for the holder. The folder itself is fine.

## Check yourself

Answer in the box, then show the answer.

**1. One line of the fingerprint check says FAILED. What do you know?**

> That file changed after the record was saved. Don't trust what it says now.

**2. Every line says OK. Can you vouch for the person?**

> You can vouch that the folder is as it was saved. Whether the claims are true and who did the work, you still have to
> read for, and ask.

**3. What's the one thing a review should end with?**

> A question to the holder, by name, that would settle what the record can't show.

## What people get wrong

- **"It has a number, so it's verified."** The number proves the file wasn't changed. Anyone can make a record.
- **"One bad file means it's all fake."** Ask first. One changed file is a question to put to them.
- **"The verdict line is the summary."** It's counted from the record. Read the result lines it's counted from.

## The judgment: what you vouch for

1. **Vouch only for what you checked.** "The folder is intact and shows one mission passed after a fix" is a sentence
   you can stand behind.
2. **Say what you can't see.** Practice profiles, self-graded answers, no one watching.
3. **Ask for a live run when it matters.** Twenty minutes watching them do one mission settles who did the work.
4. **Be fair in public, firm in private.** Write the review to them first.

## Also good to know

- **Your own record works the same way.** Before you send yours to anyone, run the check on it yourself.
- **A reviewer's signature is a different thing.** The Guide trail's record can carry a reviewer's signed review;
  a self-issued record says plainly that nobody outside reviewed it.
