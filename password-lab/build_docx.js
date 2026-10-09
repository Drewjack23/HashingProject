const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, ImageRun,
} = require('docx');

const RESULTS = path.join(__dirname, 'results');
const BLUE = '2E74B5';
const BODY_FONT = 'Times New Roman';
const HEAD_FONT = 'Calibri Light';

// ---- helpers ---------------------------------------------------------------
function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text, font: BODY_FONT, size: 22, ...opts })],
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, font: HEAD_FONT, size: 32, color: BLUE, bold: true })],
  });
}
function titlePara(text) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text, font: BODY_FONT, size: 40, bold: true })],
  });
}
function subtitlePara(text) {
  return new Paragraph({
    spacing: { after: 240 },
    children: [new TextRun({ text, font: BODY_FONT, size: 24, italics: true, color: '404040' })],
  });
}
function caption(boldLabel, rest) {
  return new Paragraph({
    spacing: { before: 60, after: 240 },
    children: [
      new TextRun({ text: boldLabel, font: BODY_FONT, size: 20, bold: true }),
      new TextRun({ text: rest, font: BODY_FONT, size: 20 }),
    ],
  });
}
function figure(file, ratio) {
  const widthIn = 6.3;
  const emuW = Math.round(widthIn * 914400);
  const emuH = Math.round(widthIn * ratio * 914400);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 40 },
    children: [new ImageRun({
      type: 'png',
      data: fs.readFileSync(path.join(RESULTS, file)),
      transformation: { width: Math.round(widthIn * 96), height: Math.round(widthIn * ratio * 96) },
    })],
  });
}

// ---- tables ----------------------------------------------------------------
function cell(text, { bold = false, width, align = AlignmentType.LEFT, shade = null } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: align,
      spacing: { after: 0 },
      children: [new TextRun({ text, font: BODY_FONT, size: 20, bold })],
    })],
  });
}
function makeTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) =>
      cell(h, { bold: true, width: widths[i], shade: 'DEEAF6' })),
  });
  const bodyRows = rows.map(r => new TableRow({
    children: r.map((c, i) => cell(c, { width: widths[i] })),
  }));
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: border, bottom: border, left: border, right: border,
      insideHorizontal: border, insideVertical: border,
    },
    rows: [headerRow, ...bodyRows],
  });
}

// ---- document --------------------------------------------------------------
const children = [];
children.push(titlePara('Two Extra Characters and the Hash That Guards Them: What I Measured About Password Cracking'));
children.push(subtitlePara('A small, local experiment on how password length and the choice of hashing algorithm change how hard a password is to guess'));

children.push(body('I wanted to test something people repeat all the time, which is that you should just make your password a couple characters longer. It sounds obvious, but I never had a feel for how much those extra characters actually buy you. So I built a small experiment to measure it myself. The question I started with was simple. How much do two extra characters change how hard a password is to guess, and does the hashing algorithm behind it change that answer?'));
children.push(body('Everything I tested was generated on my own machine. There were no real passwords, no leaked data, no accounts, and nothing touching a network. I made up synthetic passwords, hashed them locally, and then tried to guess them back. What I found is that length and the hashing algorithm are two different kinds of defense, and they help in different ways. Length controls how many guesses an attacker has to make. The hashing algorithm controls how much each guess costs. You really want both.'));

children.push(h1('The Setup'));
children.push(body('The core of the experiment is a brute-force search, which just means trying every possible password in order until you hit the right one. The catch is that trying every password gets slow fast, so to keep things finishable I used a deliberately tiny alphabet of just the four letters a, b, c, and d. I want to be upfront that this is a toy search space. Real passwords come from a much bigger set of characters, and I deal with that later using estimates. The toy alphabet is there so the brute-force part actually completes in a reasonable amount of time and I can watch how the numbers grow.'));
children.push(body('I tested three password lengths, 4, 6, and 8 characters, so each step adds two characters. For each length I generated 10 random target passwords using a fixed seed, which just means the random choices are reproducible and anyone running the code gets the same targets I did. The search walks candidates in a fixed order, basically counting through them like an odometer where the last character changes fastest. Because the order is fixed, every password has a known position in line, and that position is what decides how many guesses it takes to reach it.'));
children.push(body('For timing I used a monotonic clock, which is a timer that only moves forward and does not jump around if the system clock gets adjusted. I also put a time budget on each search so a run that took too long would be marked incomplete instead of being counted as a success. In this demo none of the searches hit that limit, but the guardrail matters because I never wanted a timed-out search showing up as a crack.'));
children.push(body('The second experiment looked at hashing cost, and I will explain hashing in that section. The whole thing ran on an Intel Xeon processor at about 2.8 GHz with 4 logical CPUs, on Linux, using Python 3.13. The password hashing used the bcrypt library version 5.0.0 and argon2-cffi version 25.1.0. I kept the benchmark to a single process and a single worker on purpose, so the numbers are a clean per-core baseline instead of whatever my machine could do flat out.'));

children.push(h1('What Two Extra Characters Changed'));
children.push(body('The number of possible passwords is just the alphabet size raised to the power of the length. With my four-letter alphabet, a length-4 password has 4 to the 4th power, which is 256 possibilities. Length 6 has 4,096. Length 8 has 65,536. The thing to notice is the jump. Each time I add two characters, the number of possibilities multiplies by 16, not adds. Going from length 4 all the way to length 8 multiplies the search space by 256. That multiplying behavior is the whole point. Two extra characters do not add a little work for an attacker, they multiply it.'));
children.push(body('That shows up in the guesses too. One thing I had to be careful about is that a single password’s cracking time does not mean much on its own. Since the search goes in a fixed order, a target that happens to sit near the front gets found almost instantly, and one near the back takes nearly the whole space. The position of a random password is itself random, so one run can look lucky or unlucky. That is exactly why I used 10 targets per length and looked at the middle of the pack instead of any single result.'));

children.push(h1('What the Numbers Showed'));
children.push(body('Here are the measured results from the brute-force search. These are real measurements from the run, not estimates.'));
children.push(makeTable(
  ['Length', 'Possible passwords', 'Targets', 'Median guesses', 'Guesses range (min–max)', 'Median time'],
  [
    ['4', '256', '10', '148', '41–255', '0.027 ms'],
    ['6', '4,096', '10', '2,942', '315–3,938', '0.489 ms'],
    ['8', '65,536', '10', '35,571', '11,470–64,346', '6.931 ms'],
  ],
  [1000, 2000, 1000, 1700, 2200, 1460],
));
children.push(caption('Table 1. ', 'Measured brute-force results over the toy alphabet “abcd” (seed 1234, 10 targets per length). All 30 searches completed; none timed out.'));
children.push(body('The median number of guesses climbs from 148 at length 4 to 2,942 at length 6 to 35,571 at length 8. Roughly a 16-fold jump each time I add two characters, which lines up with the possibility counts. The spread in each row is wide, which is the position effect I mentioned. At length 8 one target was found after about 11,000 guesses and another took over 64,000, and both are totally normal depending on where the password landed in line.'));
children.push(body('Figure 1 shows the same thing visually. Each dot is one password, and the bar is the median for that length.'));
children.push(figure('fig1_search_times.png', 0.7114));
children.push(caption('Figure 1. ', 'Measured time to find each target by password length, in seconds on a log scale. Each dot is one of the 10 targets; the horizontal bar is the median. Notice both the upward jump with length and the wide spread within each length, which comes from where each target sits in the search order. This shows measurements.'));
children.push(body('The measured guessing rate on my machine was about 5.38 million guesses per second for this simple Python search loop. That number is slow compared to a real cracking tool, but it is a real measurement from my hardware, and I use it later to project out to bigger alphabets.'));

children.push(h1('Why the Hashing Algorithm Mattered'));
children.push(body('Up to here I was only counting guesses. The second experiment is about how expensive each guess is, and that comes down to hashing. A hash function takes an input and scrambles it into a fixed-size string of characters in a way that cannot be reversed. This is not encryption. Encryption is meant to be undone with a key. Hashing is a one-way street with no key to undo it. When a service stores your password, it should store the hash, not the password itself, so that if the database leaks, the attacker gets scrambled values instead of the actual passwords.'));
children.push(body('Two more terms matter here. A salt is a random value mixed into the password before hashing, so that two people with the same password still get different stored hashes, and an attacker cannot precompute one big table and crack everyone at once. A work factor is a setting that deliberately makes the hash slow to compute. A slow hash sounds like a bad thing, but for passwords it is the point. If each guess is expensive, the attacker can only make a few guesses per second instead of millions.'));
children.push(body('I compared three algorithms by measuring how many candidate verifications per second a single CPU core could do. A verification is just checking one guess against a stored hash. I timed hash creation separately from verification, ran a few warm-up rounds first, and then measured 5 batches of 20 verifications each, 100 total per algorithm, and reported the median. Here is what I got.'));
children.push(makeTable(
  ['Algorithm', 'Role', 'Cost settings', 'Salt', 'Median verif./sec', 'Range (min–max)'],
  [
    ['SHA-256', 'Fast-hash baseline (not for password storage)', 'sha256(salt + password)', '16 bytes', '1,019,316', '877,462–1,034,661'],
    ['bcrypt', 'Password hash', 'cost 8 (2^8 = 256 rounds)', '16 bytes', '57.9', '57.1–58.8'],
    ['Argon2id', 'Memory-hard password hash', 'time 2, memory 64 MiB, parallelism 1, 32-byte output', '16 bytes', '7.3', '7.0–7.7'],
  ],
  [1150, 1950, 2250, 900, 1400, 1710],
));
children.push(caption('Table 2. ', 'Measured verification throughput, single process and single worker, 100 timed verifications per algorithm (5 batches of 20) after 3 warm-up rounds.'));
children.push(body('SHA-256 is a fast, general-purpose hash. I included it only as a baseline, and I want to be clear that it is not an appropriate way to store passwords. I used a salted construction, hashing the salt joined with the password, with a 16-byte salt. It managed about 1,019,316 verifications per second. That speed is exactly the problem. A fast hash lets an attacker try enormous numbers of guesses cheaply.'));
children.push(body('bcrypt is a password hashing function built to be slow, with an adjustable work factor called the cost. I set the cost to 8, which means 2 to the 8th, or 256 rounds of internal work. It did about 57.9 verifications per second, which is roughly 17,600 times slower per guess than SHA-256. Argon2id is a newer function that is also memory-hard, meaning it deliberately uses a chunk of memory on every computation so that specialized hardware cannot cheaply run thousands of copies in parallel. I ran it with a time cost of 2, 64 MiB of memory, and a parallelism of 1, with a 16-byte salt and a 32-byte output. It did about 7.3 verifications per second, around 140,000 times slower than SHA-256 and about 8 times slower than my bcrypt setting.'));
children.push(body('Figure 2 shows this gap. The y-axis is on a log scale, meaning each gridline is 10 times the one below it, because otherwise the slow algorithms would be invisible next to SHA-256.'));
children.push(figure('fig2_hash_throughput.png', 0.7058));
children.push(caption('Figure 2. ', 'Measured verification throughput by algorithm, in verifications per second on a log scale, with each algorithm’s cost settings shown. Higher bars mean cheaper guessing for an attacker. Notice SHA-256 sits about five orders of magnitude above the two slow hashes. This shows measurements.'));
children.push(body('The takeaway is that the same brute-force attack that is cheap against a fast hash becomes painfully slow against bcrypt or Argon2id. One honest note on the comparison. All three verified the same work, one correct password checked against that algorithm’s own stored hash using its own verification function. The functions do different internal work, so I read the SHA-256 number as a floor on cost per check rather than a perfectly matched race.'));

children.push(h1('Why Length Alone Wasn’t Enough'));
children.push(body('I ran one more small test to push back on the idea that longer is automatically safer. I built a transparent, made-up guess list out of common-looking words and suffixes, the kind of thing a simple guessing tool would try first, and I placed two targets in the picture. One was “dragon2024,” which is 10 characters long but follows a predictable word-plus-year pattern. The other was “cbad,” which is only 4 characters but random over my toy alphabet.'));
children.push(body('The long one got found at position 22 out of a 100-entry list. The short random one was never in the word list at all, so that kind of attack would never find it, though a brute-force search would eventually reach it at position 148. So the longer password was the easier one to guess here, because its length came from a predictable pattern. I want to keep this conclusion small. This is a demonstration of guess ordering, not a measurement of real-world strength, and real guessing tools use far bigger and smarter lists. All it shows is that length by itself does not tell you how strong a password is. A longer password is not always stronger.'));

children.push(h1('What the Estimates Mean'));
children.push(body('My brute-force search used a four-letter alphabet, which no one actually uses. To say anything about realistic passwords I switched from measuring to estimating. I took the 5.38 million guesses per second I measured and projected how long an exhaustive search would take for bigger alphabets, using the expected number of guesses, which is about half the total search space for a randomly chosen target. These are estimates, clearly separate from the measurements above.'));
children.push(makeTable(
  ['Alphabet', 'Length', 'Search space', 'Estimated expected time'],
  [
    ['26 (lowercase)', '6', '308,915,776', '28.7 seconds'],
    ['26 (lowercase)', '8', '208,827,064,576', '5.4 hours'],
    ['26 (lowercase)', '12', '95,428,956,661,682,176', '281 years'],
    ['62 (letters + digits)', '8', '218,340,105,584,896', '234.8 days'],
    ['62 (letters + digits)', '12', '3,226,266,762,397,899,821,056', '9.5 million years'],
    ['95 (full keyboard)', '8', '6,634,204,312,890,625', '19.5 years'],
    ['95 (full keyboard)', '12', '540,360,087,662,636,962,890,625', '1.6 billion years'],
  ],
  [2300, 1000, 3660, 2400],
));
children.push(caption('Table 3. ', 'Projected, not measured. Expected time assumes a uniformly random password and the measured rate of about 5.38 million guesses per second on this machine’s CPU. These are not GPU numbers and not a guarantee.'));
children.push(body('A couple of things to notice. With a 26-letter lowercase alphabet, length 8 comes out to about 5.4 hours and length 12 to about 281 years on my machine. With a 95-character alphabet, roughly what you get from a full keyboard, length 8 jumps to about 19.5 years and length 12 to about 1.6 billion years. Figure 3 plots these, again on a log scale, with a line marking one year for reference.'));
children.push(figure('fig3_estimates.png', 0.7121));
children.push(caption('Figure 3. ', 'Projected expected time to crack by password length for three alphabet sizes, in seconds on a log scale, with a dashed one-year reference line. Notice the straight lines on a log axis, which means each added character multiplies the time. This shows estimates, not measurements.'));
children.push(body('The big warning is that these numbers are tied to my specific CPU running a slow Python loop. A real attacker with optimized software, many cores, or a GPU, which can run thousands of hash computations at once, would be far faster. So these estimates are not universal cracking times and they are not GPU numbers. They assume the password is truly random and that the attacker searches every candidate without repeating. They are useful for seeing the shape of the growth, not for promising that any particular password is safe for a particular number of years.'));

children.push(h1('What I’d Do Differently'));
children.push(body('If I ran this again, the first thing I would change is the alphabet. The toy four-letter set made the search finish, but it means my only real brute-force measurements are on an unrealistic space. I would like to push to a slightly larger alphabet and shorter lengths so I can still measure real cracking times on something closer to reality instead of relying entirely on projections.'));
children.push(body('I would also want to measure instead of estimate the effect of hardware. Right now my cracking rate is one slow Python number. Writing the inner search loop in a faster way, or testing on a GPU, would let me compare real rates instead of guessing at the multiplier. And on the hashing side, I only tested one setting per algorithm. It would be more useful to sweep the bcrypt cost and the Argon2 memory and time settings to show how throughput drops as you turn the work factor up, since that is the exact dial a real system tunes. These are all future experiments, not things I have done yet.'));

children.push(h1('Final Thoughts'));
children.push(body('The clearest lesson from my results is that password length and the hashing algorithm are solving two different halves of the same problem. Length decides how many guesses an attacker needs, and in my measurements each pair of extra characters multiplied that count rather than nudging it. The hashing algorithm decides how much each of those guesses costs, and the gap between a fast hash and a slow, memory-hard one was five orders of magnitude in my benchmark. Neither one is enough on its own. A long password stored behind a fast hash is still cheap to attack in bulk, and a slow hash cannot save a password that a word list guesses in the first 22 tries.'));
children.push(body('So the practical version is short. Use a long, unpredictable password, and rely on services that store passwords with a slow algorithm like bcrypt or Argon2id rather than a bare fast hash. That combination is what actually makes guessing expensive, and it held up in everything I measured.'));

children.push(h1('References'));
const refs = [
  '[1] National Institute of Standards and Technology. (2017, updated 2020). Digital Identity Guidelines: Authentication and Lifecycle Management (NIST Special Publication 800-63B). https://doi.org/10.6028/NIST.SP.800-63b',
  '[2] Biryukov, A., Dinu, D., Khovratovich, D., & Josefsson, S. (2021). Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work Applications (RFC 9106). Internet Engineering Task Force. https://doi.org/10.17487/RFC9106',
  '[3] Provos, N., & Mazières, D. (1999). A Future-Adaptable Password Scheme. Proceedings of the 1999 USENIX Annual Technical Conference, FREENIX Track, 81–91. https://www.usenix.org/legacy/events/usenix99/provos.html',
  '[4] National Institute of Standards and Technology. (2015). Secure Hash Standard (SHS) (FIPS Publication 180-4). https://doi.org/10.6028/NIST.FIPS.180-4',
  '[5] OWASP Foundation. Password Storage Cheat Sheet. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html',
];
for (const r of refs) {
  children.push(new Paragraph({
    spacing: { after: 120, line: 264 },
    children: [new TextRun({ text: r, font: BODY_FONT, size: 20 })],
  }));
}

const doc = new Document({
  styles: { default: { document: { run: { font: BODY_FONT, size: 22 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(__dirname, 'Password_Hashing_Article_Andrew_Jackson.docx');
  fs.writeFileSync(out, buf);
  console.log('wrote', out, buf.length, 'bytes');
});
