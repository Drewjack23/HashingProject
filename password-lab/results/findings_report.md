# Password length, hashing cost, and cracking difficulty

*An automatically generated findings report. Every number below comes from the run that produced this file. All passwords and hashes are synthetic and generated locally.*

- Run seed: `1234`
- Toy alphabet: `abcd` (size 4)
- Lengths tested: [4, 6, 8]
- Targets per length: 10
- Captured: 2026-10-09T05:36:12.481281+00:00
- Machine: Linux-6.18.44-fc-v80-x86_64-with-glibc2.39 / x86_64 (4 logical CPUs)
- Python: 3.13.16 (CPython)
- Libraries: bcrypt 5.0.0, argon2-cffi 25.1.0, matplotlib 3.11.2

## The question

How much do two extra characters change how hard a password is to crack, and how does the choice of hashing algorithm change that answer? To keep the brute-force part finishable on a normal CPU, the search runs over a deliberately tiny toy alphabet. The point isn't the exact seconds, it's how the numbers grow and how the algorithm multiplies the cost.

## What I expected before running it

I expected adding two characters to multiply the number of possible passwords by the alphabet size squared, so each step from 4 to 6 to 8 should jump by a fixed factor, not a small amount. I also expected SHA-256 to be fast enough that it barely slows an attacker down, while bcrypt and Argon2id should be much slower per guess on purpose. I kept these expectations separate from the results so I wouldn't talk myself into seeing them.

## Experiment 1: length vs exhaustive search

Using the toy alphabet `abcd`, the number of possible passwords is alphabet-size to the power of the length. With this alphabet that is:

| Length | Total candidates | Targets | Found | Incomplete | Median time | Median guesses |
|---|---|---|---|---|---|---|
| 4 | 256 | 10 | 10 | 0 | 0.0 ms | 148 |
| 6 | 4,096 | 10 | 10 | 0 | 0.5 ms | 2,942 |
| 8 | 65,536 | 10 | 10 | 0 | 6.9 ms | 35,571 |

Going from length 4 to length 8 multiplies the search space by about 256x. That is the whole idea of the experiment: two extra characters don't add a little, they multiply.

One thing worth being honest about: the time to crack a single password bounces around a lot. That's because the search walks candidates in a fixed order, so a target near the front is found almost instantly and one near the back takes nearly the whole space. The position of a random target is itself random, so a single password's time doesn't mean much. That's why there are many targets per length and the table reports the median instead of one lucky or unlucky run.

The median measured rate on this machine was about **5,381,435 guesses/second** for this simple Python search loop. That number feeds the projections below.

## Experiment 2: hashing algorithm cost

Here the question flips from *how many* guesses to *how expensive each guess is*. I measured how many candidate verifications per second a single CPU worker can do against each stored hash. Hash creation was timed separately from verification, with warm-up runs and several timed batches so I could report a median and the spread.

| Algorithm | Cost settings | Salt bytes | Median verifications/sec | Min–Max |
|---|---|---|---|---|
| SHA-256 (salted baseline, NOT for password storage) | sha256(salt || password) | 16 | 1,019,316 | 877,462–1,034,661 |
| bcrypt | log2 rounds = 8 (cost 256) | 16 | 58 | 57–59 |
| Argon2id | t=2, m=64.0 MiB, p=1 | 16 | 7 | 7–8 |

On this machine, bcrypt was about 17,615x slower per guess than the SHA-256 baseline; Argon2id was about 140,084x slower per guess than the SHA-256 baseline. 

The SHA-256 row is labeled a baseline on purpose. It is not a recommended way to store passwords. It's here to show the floor: a fast hash lets an attacker try huge numbers of guesses cheaply, which is exactly what a slow password hash is designed to stop. bcrypt and Argon2id spend real work (and, for Argon2id, real memory) on every single check, so the same brute-force attack that is cheap against SHA-256 becomes painfully slow against them.

A fair-measurement note: all three verify the same workload (one correct password, checked against that algorithm's own stored hash with its own verification API). The APIs do different internal work, so the SHA-256 number is best read as a lower bound on cost per check rather than a head-to-head race on identical operations. Everything is single-process and single-worker so the numbers are a clean per-core baseline.

## Experiment 3: length is not the same as predictability

This small illustration uses a transparent, made-up guess list of fictional words plus common suffixes. It compares a long-but-predictable target against a short-but-random one.

| Target | Length | In word list? | Word-list rank | Brute-force rank | Note |
|---|---|---|---|---|---|
| `dragon2024` | 10 | yes | 22 | — | 10 characters long, but it is word+year, so a dictionary guesser reaches it very early. Length did not protect it. |
| `cbad` | 4 | no | not found | 148 | Only 4 characters, but it is not in the dictionary at all, so a word-list attack never finds it. A brute-force attack would, but only by walking the enumeration order. |

The takeaway from this one is narrow and I want to be careful about it: it only shows guess *ordering*, not real-world strength. A longer password that follows a predictable pattern can be guessed before a shorter random one. Length alone doesn't tell you how strong a password is.

## Projections (estimates, not measurements)

These take the measured guesses/second from experiment 1 and project how long an exhaustive search would take for bigger, more realistic alphabets. **These are estimates based on this one machine's CPU rate.** They are not GPU numbers, not universal cracking times, and not a guarantee. They assume uniformly random passwords and an exhaustive search with no repeats.

| Alphabet | Length | Search space | Expected guesses | Estimated expected time |
|---|---|---|---|---|
| 26 | 4 | 456,976 | 228,488 | 42.5 ms |
| 26 | 6 | 308,915,776 | 154,457,888 | 28.7 seconds |
| 26 | 8 | 208,827,064,576 | 104,413,532,288 | 5.4 hours |
| 26 | 10 | 141,167,095,653,376 | 70,583,547,826,688 | 151.8 days |
| 26 | 12 | 95,428,956,661,682,176 | 47,714,478,330,841,088 | 281.0 years |
| 62 | 4 | 14,776,336 | 7,388,168 | 1.4 seconds |
| 62 | 6 | 56,800,235,584 | 28,400,117,792 | 1.5 hours |
| 62 | 8 | 218,340,105,584,896 | 109,170,052,792,448 | 234.8 days |
| 62 | 10 | 839,299,365,868,340,224 | 419,649,682,934,170,112 | 2.5 thousand years |
| 62 | 12 | 3,226,266,762,397,899,821,056 | 1,613,133,381,198,949,908,480 | 9.5 million years |
| 95 | 4 | 81,450,625 | 40,725,313 | 7.6 seconds |
| 95 | 6 | 735,091,890,625 | 367,545,945,313 | 19.0 hours |
| 95 | 8 | 6,634,204,312,890,625 | 3,317,102,156,445,313 | 19.5 years |
| 95 | 10 | 59,873,693,923,837,890,625 | 29,936,846,961,918,947,328 | 176.3 thousand years |
| 95 | 12 | 540,360,087,662,636,962,890,625 | 270,180,043,831,318,495,100,928 | 1.6 billion years |

## What the results support

The length numbers back up the main point cleanly: two extra characters multiply the work rather than adding to it, and you can see that both in the measured guess counts and in the projections. The hashing numbers show the second half of the answer. The algorithm sets the price per guess, and a slow, memory-hard algorithm like Argon2id makes the same brute-force attack far more expensive than a fast hash does. Put together, a longer password and a slow hash each help, and they help in different ways that stack.

## What's still uncertain

The single-password times are noisy because of where the target lands in the order, so I lean on medians and distributions, not individual runs. The hashing comparison isn't an identical-operation race, so I treat SHA-256 as a floor. And the projections inherit all the assumptions of the formula, so they should be read as rough scale, not promises.

## Practical takeaways

- Longer passwords help a lot, because each extra character multiplies the attacker's work, but only when the password isn't predictable.
- A slow password hash (bcrypt or Argon2id) matters just as much as length, because it sets how many guesses per second are even possible.
- A fast hash like plain SHA-256 is the wrong tool for storing passwords.
- Length without randomness is a weak defense, as experiment 3 shows.

## Limitations

- The brute-force search uses a tiny toy alphabet so it can finish; real alphabets are far larger, which is why the projection section exists.
- Everything is CPU-only and single-worker. Real attackers use many cores, GPUs, or specialized hardware, so real guess rates are higher.
- Sample sizes are small by design (a handful of targets per length).
- Experiment 3 is an illustration of ordering, not a strength measurement.
- Python loop overhead means the raw guess rate is lower than an optimized cracker would get; the shape of the growth is the point, not the absolute speed.

