# Streamlining to save usage (the user, 28 November 2026, 19:04 Brussels)

The user: "Let's go with your suggestions and rework the steps. We don't need to release check constantly if it takes so much. Let's streamline this, do the less important things for next week, and the things that save a lot, let's simplify those. And each step doesn't need one quick test. And let's keep the pick pages a little bit more simple. Let's streamline this a little bit more and use less usage."

The goal is to use less usage (a run out of usage stops everything), not raw speed.

## How every task works from now on (S1 to S5)
- **S1 Release check less often.** The scheduling chat fires the release gate about twice a day (around 12:00 and 23:00 Brussels) or when 10 or more releases wait for it, never after every burst. Lanes keep releasing to main (the dev channel) between gate runs.
- **S2 No re-publishing after every step.** Do NOT publish index.html to the artifact and do NOT rewrite the project doc after each step. Once a day at most (the first release of a lane after 20:00 Brussels), or when the user asks.
- **S3 Lighter testing per step.** No dedicated test file and no long test run per step. Before a push run only the lint and the quick start-up smoke test of docs/release-gate.md (these stay: they stop a broken app like v0.250 from reaching main). Add a test only where a step changes audio, saving or a shared hook. The full suite runs in the release gate.
- **S4 Short logs.** One short backlog-log entry and one short notification per step; no long write-ups, no screenshots unless the user asks.
- **S5 Simple pick pages.** Few options, one short line each, the real-place mock-ups the user likes; no long text.

## Moved to next week (L1 to L7), do NOT build now
- **L1 Extensions (lane H):** everything about scripts and sharing: DL12 (sandbox), DL13, DL14, DL15, EX6 (script devices), EX9 (import card), EX10 (script instruments), DL11 (CSS snippets). Lane H finishes only what is not script-related (DL5 to DL8, DL10 without the console, EX2, EX3, EX5, EX7 if they need no scripts), then logs 'extensions paused for next week'.
- **L2 Lessons / Learn mode (lane M):** the whole task waits. Lane F still builds LM1 to LM3 only if they are already started; otherwise they wait too.
- **L3 Ideas (lane D):** the Assistant ideas (I17, I18, I31, I32) and the Time Machine ideas (I22, I23) wait.
- **L4 Sounds (lane L):** the new devices N3 FM6, N4 Comb and Resonator, N6 Clouds, wavetable import (B11, B14) and IR import (B33) wait. Improvements to existing devices continue.
- **L5 Controllers (lane C):** Push 1 stays; Mackie Control, HUI, Launchpad and APC wait.
- **L6 Science look (lane G):** the remaining decorative steps wait; finish the step in hand, then log 'science look paused for next week'.
- **L7 Features (lane C):** only the starred cards of docs/research-features-gap.md and Push 1 this week; the other cards wait.

A lane whose remaining work is all moved logs '<lane> paused for next week'; the scheduling chat counts that as done for this week's final builds.
