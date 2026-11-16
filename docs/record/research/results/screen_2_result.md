# Screen #2 result (2026-10-16): STOP (no headroom)

The run used screen `626f8037…` and code `4565ff61…` (unchanged since `b250c7f`). Its 6 synthetic tests, including the no-leak test, passed first.
- **Archive:** MD5 `11d66d59…` matched; 3,350,124,833 rows streamed; 100,084,561 kept (local 13–24 Sep, the 3,225 KFZ signal groups). Rows from 25 Sep on were read and discarded, never kept.
- **Groups:** 2,838 eligible, 40 drawn (seed 7,421,001).
- **Fixed margins:** median 8 s; 10 groups at 0 s, 11 at the 20-s cap.
- **Memory:** peak 40.8 GB, from concatenating the kept rows. Stream to per-group files next time.

| cell | approaches | no forecast | loss F | loss O | loss H | pass F | pass O | pass H | P = O − F [95 % CI] | H − F |
|---|---|---|---|---|---|---|---|---|---|---|
| weekday 18–22 | 192,000 | 12.5 % | 4.5 % | 4.1 % | 4.3 % | 21.0 % | 19.0 % | 21.7 % | −1.96 pts [−2.73, −1.26] | +0.68 pts |
| weekend 23–24 | 76,800 | 8.9 % | 4.9 % | 4.7 % | 4.8 % | 24.1 % | 18.3 % | 24.5 % | −5.76 pts [−7.92, −3.94] | +0.39 pts |

## Reading (main session)

- **Validity is no problem here.** All arms stay valid: losses 4.1–4.9 % against the 5 % target.
- **Per-group margins fitted on 14–17 Sep transfer well** to the next week, including the weekend.
- **There is no headroom.** Even the hindsight-fitted fixed margin beats the fixed one by under 1 pass point. So no online margin can win by the pre-registered 2 points.
- **The online margin loses** 2–6 points, as expected when there is no drift: it pays for its own variability.
- **This STOP does not come from the tracker's step size.** The headroom is measured without the tracker.
- **Limit:** the headroom is for a per-group *constant* margin. A time-varying hindsight margin was not measured, and the screen did not ask for it.
