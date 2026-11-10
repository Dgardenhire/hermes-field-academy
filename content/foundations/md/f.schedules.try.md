Field Academy filled in this practice profile's memory as if it belonged to Yusuf Demir, who runs the front desk at a
tile and flooring showroom. Yusuf is made up. One of the notes says he wants every summary to start with "For Yusuf:".

1. Press **Open practice chat**. The mission page shows the practice folder's full location; paste it where it says
   *folder*:

   `Look at orders-week.csv in` *folder*`. How many orders are marked late?`

   Let it answer.

2. Open **Scheduled jobs** from the left side of the app. Jobs belong to one profile, and this page works on the
   profile of the chat you last sent in, which is now `academy-practice`. The mission page shows a pass line when the
   app is pointed there; if it shows a fail, follow its fix first. Then press **New cron** and fill it in:
   - **Name:** `late-orders`
   - **Prompt:** `Check the file we just looked at and tell me how many orders are late.`
   - **Frequency:** Hourly
   - **Deliver to:** This desktop
   - **Model:** leave it on Default

   Press **Create cron**.

   > No Scheduled jobs on the left? The app is in Simple mode. Switch to Advanced in **Settings → Appearance → Window &
   > layout**. (As of Hermes 0.22.)

3. Write two guesses. Will the job's answer start with "For Yusuf:"? Will it know which file you meant?

4. Press **Trigger now**. The app waits for the run to finish, usually within a minute. Press **Show runs** and open
   the run. Then press **Pause**, so it doesn't fire every hour while you read.

The obvious guesses are "yes and yes," since it's the same Hermes, or "no and no," since it's a robot on a timer.
Usually it's yes, then no. The run greets Yusuf and has no idea which file you meant. Some runs say so. Some pick the
wrong file and answer confidently anyway.
