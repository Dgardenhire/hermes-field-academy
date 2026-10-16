# The learning science behind Field Academy 0.5

This page says what each feature rests on, which parts are Field Academy's own
choices, and which claims could not be verified. Plain statement first: Field
Academy has not been tested on learners, so nothing here says it works. It says
what the design borrows from research, and where it guesses.

## How this page was checked

Every reference below was looked up in the Crossref index on 3 October 2026, and
its title, journal, volume, pages and year matched the entry. That confirms the
paper exists and the citation is right. It does not confirm what the paper found.
The one-line summaries come from the author's reading and memory of the field, and
no effect size is quoted anywhere because none was checked against the paper.
Two items could not be confirmed that way and are marked.

## 1. Spaced review

**What we do.** A passed mission comes back two days later for three short
questions, then after 7, 21 and 60 days when it goes well, and the next day when
it goes badly. Each mission keeps a strength from 0 to 100.

**What it rests on.** Retrieving something from memory strengthens it more than
rereading it (Roediger and Karpicke, 2006; Karpicke and Roediger, 2008). Spreading
practice over time beats cramming it, across many studies (Cepeda and others, 2006).
How long to wait depends on how long you want to remember (Cepeda and others,
2008). Dunlosky and others (2013) reviewed ten study techniques and rated practice
testing and spaced practice highest in usefulness. Mixing topics inside a session
helps learners tell ideas apart (Rohrer and Taylor, 2007), so a session draws one
question from each of up to three different missions.

**Our own choices, not findings.** The gaps of 2, 7, 21 and 60 days, the ceiling of
90, the pass line of 70, the line of 85 for moving up a rung, the rule that a miss
drops two rungs, the 40/60 weighting that makes strength lean on the latest answer,
and the slow fading of strength when a review is overdue are all Field Academy's own
design. The Cepeda 2008 paper supports gaps that grow with the time you want to
remember. It does not support these particular numbers, and we could not check the
paper's own rule of thumb for the ratio, so we do not quote one.

**Practice early.** Answers given before a review is due change strength and leave
the schedule alone, because an early answer says little about whether the wait
held. That is a design judgment, not a result.

**No streaks.** Nothing counts days of use. A mission comes back when its schedule
says so. This is a product decision about honesty, in the spirit of the critique of
manipulative interface patterns (Gray and others, 2018). It is not a claim that
streaks harm learning.

## 2. Stronger checks

**What we do.** Every check needs something the learner made: a typed answer
compared with what Hermes reports, a skill or job or chat that carries a
mission-specific marker, or a document whose every section holds real content
(docs/checks.md has the full audit).

**What it rests on.** Assessment that asks learners to produce something, not to
recognize it, supports retrieval and transfer. Short-answer testing has been found
to beat multiple choice for later retention in some conditions (Kang, McDermott and
Roediger, 2007). The placement check uses multiple choice on purpose, because it
only decides where to start and never certifies anything.

**Limits.** A check finds the parts a real document has. It cannot judge quality.
docs/checks.md lists every check that cannot be made fully strong and why.

## 3. Feedback on a miss

**What we do.** A miss says exactly what was missing. The first miss adds one hint
about the first missing item. The second adds a worked example for that same item.
The learner can always retry.

**What it rests on.** Feedback helps most when it says where the learner is, where
they are going and what to do next, at the level of the task (Hattie and Timperley,
2007). Tutors help most by supporting only the part a learner can't yet do and
fading as they improve (Wood, Bruner and Ross, 1976). The worked-example effect
supports showing a finished example when a learner is stuck (Sweller and Cooper,
1985).

**Our own choice.** The exact ladder (what, then a hint, then an example) and the
rule of one focus at a time are ours. We found no study of this particular ladder
for a learning plugin. One focus at a time is a guess about working-memory load.

## 4. Worked examples and fading

**What we do.** Each mission runs a lesson, a finished worked example, a
half-finished one with gaps, then the learner alone. The page shows the support
fading. Each worked example is a real case with its steps labelled by the sub-goal
each one meets, and each worked document passes the very check the learner faces.
Since 0.8.0 the steps carry plain names (the story, the takeaway, your turn, try
it, explain it, prove it), and every mission opens story-first: the
worked example comes first as a short story about what happened to someone, and
the lesson follows as a three-line takeaway, with a labelled picture where one
helps. Reading and video links moved to the end of each mission, closed, under Go
deeper, so everything needed to pass is on the page.

**Our own choice.** Putting the story before the takeaway, the three-line limit and
moving the reading to the end are ours. The studies below compare studying
examples with solving problems; we found none that tests this order for a learning
plugin.

**What it rests on.** Studying worked examples beats solving problems for a
beginner (Sweller and Cooper, 1985; Atkinson, Derry, Renkl and Wortham, 2000).
Moving gradually from example to problem, by blanking out steps, helps further
(Renkl, Atkinson, Maier and Staley, 2002; Renkl and Atkinson, 2003). The benefit
reverses for experts, who gain from solving and lose time on examples (Kalyuga,
Ayres, Chandler and Sweller, 2003), which is why the placement check exists. Overall
design draws on cognitive load theory (Sweller, van Merriënboer and Paas, 1998).

**Trying before seeing.** The half-finished example makes the learner write each gap
before the model answer shows. After two failed tries the answers can be shown, and
the step stays open. That follows the general finding that producing an answer
first helps, but the two-try rule is ours.

## 5. Self-explanation

The explain step asks the learner to put the idea in their own words, and Hermes
scores it against named points. Students who explain examples to themselves learn
more (Chi, Bassok, Lewis, Reimann and Glaser, 1989), and prompting them to do it
helps (Chi, de Leeuw, Chiu and LaVancher, 1994).

**Limit.** The scorer is the learner's own Hermes. We have not measured how well
it agrees with a human grader, so a score is a guide, and the page says the
learner can retry as often as they like.

## 6. Placement

**What we do.** A short scenario check per path. Both questions right on a level
skips that level's reading and practice. The question and the check on real work
still count on every mission, and the Field Record says which missions had their
reading skipped.

**What it rests on.** Diagnostic assessment lets instruction match what a learner
knows (Black and Wiliam, 1998, not confirmed by lookup, see below), and the
expertise reversal effect says needless instruction can hurt an expert (Kalyuga and
others, 2003). Mastery learning requires that a learner show the learning before
moving on (Bloom, 1968, not confirmed by lookup; Kulik, Kulik and Bangert-Drowns,
1990, a meta-analysis). Our rule that a skipped level still needs real work is a
mastery rule: a skip changes what you read, not what you must show.

**Our own choices.** Two questions per level and the both-right rule have not been
checked for reliability. A level is easy to guess past with two questions, which is
why a guess gains only the reading and never the check.

## 7. Transfer and the capstone

**What we do.** A final mission per path where the learner works on their own
problem, states criteria first and reports against them. The question Hermes scores
puts them in a situation unlike any earlier mission.

**What it rests on.** Transfer to new situations is hard and varies by how far the
new situation is from the old (Barnett and Ceci, 2002). Comparing and abstracting
across cases helps schemas form (Gick and Holyoak, 1983). Stating criteria before
the work makes the evidence checkable. That last point is a design choice.

## 8. After the summit

A versioned changelog flags a passed mission whose check or lesson changed. The
learner can re-verify. A re-verify that misses leaves the mission passed. That is
a fairness rule of ours: a Field Record states what was checked at the time, and it
records which version of each check was passed.

## 9. Motivation

**What we do.** One question on first run, "What do you want Hermes to do for
you?", woven into each mission's "why this matters to you" line and every practice
prompt. Every mission says how long it takes, honestly.

**What it rests on.** Helping learners see how material matters to their own lives
raised interest and performance in one field study (Hulleman and Harackiewicz,
2009). Autonomy and relevance are central in self-determination theory (Deci and
Ryan, 2000).

**Limit.** We use the learner's words as they typed them. We do not know whether
the effect holds for adults learning software on their own time.

## What we could not verify

- **Black and Wiliam (1998), "Assessment and classroom learning," Assessment in
  Education 5(1).** The Crossref lookup returned a different, later chapter by the
  same authors, so the 1998 article's details come from memory only.
- **Bloom (1968), "Learning for mastery," Evaluation Comment 1(2).** It is not in
  the index the lookup used, so it is cited from memory.
- **Bloom (1984), "The 2 sigma problem," Educational Researcher 13(6).** It exists
  (confirmed). We cite no effect size from it, and we do not rely on it.
- **Every effect size and every claim about what a paper found.** Checked against
  nothing but the author's memory.
- **Whether any of this helps people learn Hermes.** Not tested.

## References

Atkinson, R. K., Derry, S. J., Renkl, A., and Wortham, D. (2000). Learning from
examples: Instructional principles from the worked examples research. *Review of
Educational Research*, 70(2), 181-214.

Barnett, S. M., and Ceci, S. J. (2002). When and where do we apply what we learn? A
taxonomy for far transfer. *Psychological Bulletin*, 128(4), 612-637.

Black, P., and Wiliam, D. (1998). Assessment and classroom learning. *Assessment in
Education*, 5(1), 7-74. (Not confirmed by lookup.)

Bloom, B. S. (1968). Learning for mastery. *Evaluation Comment*, 1(2). (Not
confirmed by lookup.)

Bloom, B. S. (1984). The 2 sigma problem: The search for methods of group instruction
as effective as one-to-one tutoring. *Educational Researcher*, 13(6), 4-16.

Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., and Rohrer, D. (2006).
Distributed practice in verbal recall tasks: A review and quantitative synthesis.
*Psychological Bulletin*, 132(3), 354-380.

Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., and Pashler, H. (2008). Spacing
effects in learning: A temporal ridgeline of optimal retention. *Psychological
Science*, 19(11), 1095-1102.

Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P., and Glaser, R. (1989).
Self-explanations: How students study and use examples in learning to solve
problems. *Cognitive Science*, 13(2), 145-182.

Chi, M. T. H., de Leeuw, N., Chiu, M.-H., and LaVancher, C. (1994). Eliciting
self-explanations improves understanding. *Cognitive Science*, 18(3), 439-477.

Deci, E. L., and Ryan, R. M. (2000). The "what" and "why" of goal pursuits: Human
needs and the self-determination of behavior. *Psychological Inquiry*, 11(4),
227-268.

Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., and Willingham, D. T.
(2013). Improving students' learning with effective learning techniques: Promising
directions from cognitive and educational psychology. *Psychological Science in the
Public Interest*, 14(1), 4-58.

Gick, M. L., and Holyoak, K. J. (1983). Schema induction and analogical transfer.
*Cognitive Psychology*, 15(1), 1-38.

Gray, C. M., Kou, Y., Battles, B., Hoggatt, J., and Toombs, A. L. (2018). The dark
(patterns) side of UX design. *Proceedings of the 2018 CHI Conference on Human
Factors in Computing Systems*, 1-14.

Hattie, J., and Timperley, H. (2007). The power of feedback. *Review of Educational
Research*, 77(1), 81-112.

Hulleman, C. S., and Harackiewicz, J. M. (2009). Promoting interest and performance
in high school science classes. *Science*, 326(5958), 1410-1412.

Kalyuga, S., Ayres, P., Chandler, P., and Sweller, J. (2003). The expertise reversal
effect. *Educational Psychologist*, 38(1), 23-31.

Kang, S. H. K., McDermott, K. B., and Roediger, H. L. (2007). Test format and
corrective feedback modify the effect of testing on long-term retention. *European
Journal of Cognitive Psychology*, 19(4-5), 528-558.

Karpicke, J. D., and Roediger, H. L. (2008). The critical importance of retrieval for
learning. *Science*, 319(5865), 966-968.

Kulik, C.-L. C., Kulik, J. A., and Bangert-Drowns, R. L. (1990). Effectiveness of
mastery learning programs: A meta-analysis. *Review of Educational Research*, 60(2),
265-299.

Renkl, A., and Atkinson, R. K. (2003). Structuring the transition from example study
to problem solving in cognitive skill acquisition: A cognitive load perspective.
*Educational Psychologist*, 38(1), 15-22.

Renkl, A., Atkinson, R. K., Maier, U. H., and Staley, R. (2002). From example study to
problem solving: Smooth transitions help learning. *Journal of Experimental
Education*, 70(4), 293-315.

Roediger, H. L., and Karpicke, J. D. (2006). Test-enhanced learning: Taking memory
tests improves long-term retention. *Psychological Science*, 17(3), 249-255.

Rohrer, D., and Taylor, K. (2007). The shuffling of mathematics problems improves
learning. *Instructional Science*, 35(6), 481-498.

Sweller, J., and Cooper, G. A. (1985). The use of worked examples as a substitute for
problem solving in learning algebra. *Cognition and Instruction*, 2(1), 59-89.

Sweller, J., van Merriënboer, J. J. G., and Paas, F. G. W. C. (1998). Cognitive
architecture and instructional design. *Educational Psychology Review*, 10(3),
251-296.

Wood, D., Bruner, J. S., and Ross, G. (1976). The role of tutoring in problem
solving. *Journal of Child Psychology and Psychiatry*, 17(2), 89-100.
