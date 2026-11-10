Tomasz's entry, from his run:

> **Claim:** I can hand parts of a job to helper agents at once, give each one what it needs, and prove from Hermes's
> records what each helper did.
>
> **Prediction:** 4 of 4. I thought the rule would be the only hard part, and I'd already seen it fail in the try.
>
> **Result:** 3 of 4, one short of my guess.
>
> - Check 1, one hand-off for every client: missed first time, pass after the fix. *Field Academy read it.*
> - Check 2, each helper in its own folder: pass. *Field Academy read it.*
> - Check 3, every summary right: pass. *Field Academy read it.*
> - Check 4, the explanation: pass, level 3. *His own Hermes graded it.*
>
> **Evidence:** the tool result that refused the first batch; the three helper chats, each marked subagent; the last
> line of each `summary.md`.
>
> **What I missed:** my first request was refused with "Too many tasks: 3 provided, but max_concurrent_children is 1."
> Hermes then ran the helpers one at a time without telling me why, and I scored the hand-off as a pass. The setting was
> in the practice profile's config. I raised it to 3 and asked again in a new chat.
>
> **Transfer:** none of their four helpers would run, because four is over the cap of two. They'd use the main model,
> and they'd never see the rule in `AGENTS.md`.
