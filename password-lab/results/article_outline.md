# Medium article outline

*Grounded in the completed run. Expected outcomes are kept separate from findings; nothing surprising is manufactured.*

## Three possible titles

1. "Two Extra Characters: What Actually Happens When You Make a Password Longer"
2. "Length Helps, But the Hash Decides the Price: A Small Password-Cracking Experiment"
3. "I Benchmarked Password Cracking on a Toy Alphabet — Here's What the Numbers Say"

## Opening hook

Start with the plain claim people repeat — "just add a couple more characters" — then show, with the measured numbers, that adding two characters doesn't add work, it multiplies it, and that the hashing algorithm quietly sets how much each guess even costs.

## Methods section

- Toy alphabet `abcd`, lengths [4, 6, 8], 10 seeded targets each, fixed enumeration order.
- Exhaustive search with a monotonic timer and a time budget; timed-out runs marked incomplete, never counted as cracks.
- Verification-throughput benchmark for SHA-256 (baseline), bcrypt, and Argon2id, hash creation timed separately, warm-up plus several batches, single process / single worker.
- A transparent dictionary illustration for length-vs-predictability.
- A projection module labeled clearly as estimates from this machine's rate.

## Results section

- Length: search space grows ~256x from length 4 to 8 on the toy alphabet; show the median guess counts and the spread.
- Measured search rate ~5,381,435 guesses/sec (this machine, Python loop).
- Hashing: Argon2id was ~140,084x slower per verification than the SHA-256 baseline on this machine.
- Predictability: the long predictable target was reached early in the word list while the short random one wasn't in the list at all.

## Suggested chart placement

- Figure 1 (`fig1_search_times`) right after the length results, to show both the growth and the per-target variability.
- Figure 2 (`fig2_hash_throughput`) in the hashing section, with the cost settings visible on the bars.
- Figure 3 (`fig3_estimates`) in a clearly separated "projections" box so readers don't mistake estimates for measurements.

## Practical takeaway

Use a long, unpredictable password AND rely on services that store passwords with a slow hash like bcrypt or Argon2id. Length raises the number of guesses; the hash raises the price of each guess; you want both.

## Topic tags

`Cybersecurity`, `Passwords`, `Cryptography`, `Python`, `Security`

