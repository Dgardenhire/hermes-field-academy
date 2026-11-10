Ingrid's entry, from her run:

> **Claim:** I can connect an outside tool with only the access a job needs, and prove it asks before it changes
> anything.
>
> **Prediction:** 4 of 4. I thought the log was the only hard part.
>
> **Result:** 3 of 4, one short of my guess.
>
> - Check 1, one folder and an allow list: missed first time, pass after the fix. *Field Academy read it.*
> - Check 2, untrusted: pass first time. *Field Academy read it.*
> - Check 3, a write that asked and was turned down: missed. *Field Academy read it.*
> - Check 4, a clean start in the log: pass first time. *Field Academy read it.*
>
> **Evidence:** the connector's settings block, dated; the chat where the write went through, with Hermes's message
> quoted; the start line from the connector log.
>
> **What I missed:** I fixed `files` and the first write still went through without a question. There was a second
> connector, `docs`, pointed at the same folder at full trust, and Hermes used that one. I deleted `docs`, saw the
> settings were right, and scored myself 4. I never asked for a write again, so the only write on record is the one
> that didn't ask.
>
> **Transfer:** the other setup was untrusted with no allow list. Four tools would ask; I'd cut it to the two the job
> uses and keep untrusted.
