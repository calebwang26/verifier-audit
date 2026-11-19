# EXPLAIN: how verifier-audit works

Written for someone who knows neural networks & the basics of RL but is new to reading research code. Part 1 walks through the idea & the files. Part 2 answers the "defend it" questions.

## Part 1: the idea in one page

In RL for coding, a model writes code, a **verifier** (usually a test suite) says pass or fail, & that pass/fail is the **reward**. The model is trained to get more reward. So whatever the verifier accepts is, quite literally, what the model learns to do.

A verifier can be wrong in two directions:

- **False negative:** it fails correct code. Annoying, but the model just loses some reward it deserved.
- **False positive:** it passes wrong code. This one is dangerous, because the model gets rewarded for being wrong.

This project measures false positives. To measure them you need a supply of wrong solutions whose wrongness you're sure of. It uses three supplies:

1. **Mutants.** Take a correct solution & make one small change (`<` becomes `<=`, a `+ 1` becomes `+ 2`, a line is deleted). Most such changes are bugs. They're cheap & automatic: 444 of them across 12 tasks.
2. **Reward hacks.** Hand-written "solutions" that don't solve the task but try to pass the tests anyway (memorise the test answers, return an object that claims to equal anything).
3. **Real model-written wrong code,** from the public EvalPlus project.

For each supply the question is the same: **what share of the wrong solutions does the test suite pass?** That share is the verifier's false-positive rate.

### The measuring chain, step by step

```
reference solution ──mutate.py──▶ 444 mutants
                                     │
                     equivalence.py  │  drop the ones that aren't really bugs (19)
                                     ▼
                                425 real bugs
                                     │
                        run_suite.py │  each bug × each of 5 suites, in a sandbox
                                     ▼
                         pass / fail table  ──audit.py──▶  false-positive rate per suite
```

### Words you'll need

| word | meaning |
|---|---|
| reference solution | the known-correct answer to a task |
| mutant | the reference with one small change |
| equivalent mutant | a mutant whose change makes no difference to behaviour, so it isn't a bug |
| killed / survived | a mutant is *killed* when a suite fails it, & *survives* when the suite passes it |
| mutation score | share of real bugs a suite kills |
| false-positive rate (FPR) | share of real bugs a suite passes = 1 − mutation score |
| oracle | a slow, obviously-correct second implementation used to check answers |
| AST | "abstract syntax tree": Python's parsed, structured form of source code |
| sandbox | an isolated place to run untrusted code so it can't affect anything else |

## The files, in the order the data flows

### `tasks/<name>/` (12 folders)

Each task is a small coding problem. Take `tasks/merge_intervals/`:

- **`solution.py`**: the reference. Sorts the intervals, then sweeps once, merging as it goes.
- **`spec.py`**: three things the audit needs to know about the task.
  - `oracle()`: a second, deliberately different way to compute the answer (keep merging any two overlapping intervals until nothing changes). Slow, but hard to get wrong.
  - `gen_input(rng)`: makes one random input. Inputs are kept small on purpose, because small inputs hit the awkward cases (empty, one item, ties) more often.
  - `EDGE_INPUTS`: hand-picked tricky inputs.
- **`suite_weak.py`**: one happy-path test.
- **`suite_medium.py`**: starts with `from suite_weak import *`, then adds the tests a typical repo would have.
- **`suite_strong.py`**: starts with `from suite_medium import *`, then adds edge cases & a test that compares the solution with the oracle on 200 random inputs.
- **`hacks/`**: the four reward hacks for this task.

Because each suite imports the one below it, weak ⊂ medium ⊂ strong is guaranteed, not just intended.

### `tasks/_shared/`

- **`suite_empty.py`**: a suite with no assertions. Its right answer is known: it must pass everything.
- **`suite_oracle.py`**: compares the solution with the oracle on 500 random inputs. Its right answer is also known: it must pass (almost) nothing that's wrong.
- **`harness.py`**: the few lines that actually run a suite inside the sandbox.
- **`checks.py`**: the strict comparison. A result only counts if it's plain built-in data (numbers, strings, lists). This is what stops the "object that equals anything" trick.
- **`equiv_child.py`**: the in-sandbox half of the equivalence check.

### `mutate.py`: making the bugs

Python can parse source code into a tree (`ast.parse`). In that tree, `a < b` is a `Compare` node with an `Lt` operator, `x + 1` is a `BinOp` node with an `Add`, & so on. `mutate.py` walks the tree, & at every node where one of its seven operators applies it makes a copy of the tree with just that node changed, then turns the copy back into source code (`ast.unparse`).

| operator | example |
|---|---|
| `cmp_swap` | `start <= end` → `start < end` |
| `const_offby1` | `ordered[1:]` → `ordered[2:]` |
| `bool_swap` | `a and b` → `a or b` |
| `stmt_delete` | a line removed |
| `cond_negate` | `if x:` → `if not x:` |
| `arith_swap` | `i + 1` → `i - 1` |
| `return_const` | `return merged` → `return []` |

Working on the tree instead of the text is what makes this safe. A text search for `<` would also match inside strings & comments.

Try it: `python mutate.py tasks/merge_intervals/solution.py` lists all 37 mutants of that task, & adding an id like `m021` prints that one's change.

### `run_suite.py`: asking "does this candidate pass this suite?"

1. Make a fresh temporary folder.
2. Write the candidate there as `solution.py` & copy in the suite files.
3. Start a **separate Python process** that imports the suite & calls every `test_*` function.
4. Wait at most 4 seconds. If the process hasn't answered, kill it & call it a fail.

The separate process & the timeout exist because mutants do things like turn `i += 1` into `i += 0`, which loops forever. About 2% of the audit's runs end in a timeout.

### `equivalence.py`: throwing out mutants that aren't bugs

Example: in `if end > last[1]: last[1] = end`, changing `>` to `>=` only adds the case "end equals last[1]", where the assignment sets a value to itself. Nothing changes. No test could ever fail that mutant, so counting it as "a bug the tests missed" would be unfair.

The check runs the mutant & the reference on the edge inputs plus 3,000 random inputs. If they never differ, the mutant is flagged "likely equivalent" & left out. If they differ, the input that showed it is saved as a **witness**.

### `audit.py`: the main loop

For each task: mutate, check equivalence, run every mutant on every suite, count. It also checks two rules that must never break (a mutant killed by a weaker suite must be killed by the stronger one; a mutant flagged equivalent must pass everything). Output: `outputs/audit.json` & a table.

### `hacks_eval.py` & `demos/verifier_attacks/`

`hacks_eval.py` runs the 48 hand-written hacks through the same `run_suite`. The demo goes one step further & attacks the verifier itself, to show which verifier designs hold up.

### `review/`

`sample.py` draws 30 random mutants. `hand_labels.json` is my judgement of each from reading the code. `compare.py` checks those against the audit & writes `mutant_sample.md`.

### `evalplus_check.py` & `evalplus_worker.py`: the realism check

Same idea as the audit, pointed at a public benchmark. HumanEval's original tests (about 10 per problem) are the verifier under audit. HumanEval+'s much larger test set (about 750 per problem) is the ground truth. For each of 164 problems it computes two numbers & asks whether they move together:

- **predicted:** the share of mutants that slip past the original tests,
- **real:** the share of wrong *model-written* solutions that slip past the original tests.

`evalplus_worker.py` is the part that runs model-written code, so it's the most defensive file in the repo: every candidate gets its own process, time limits, & a list of dangerous functions switched off. On a Mac it also runs inside the system sandbox with no network & no file writes.

### `report.py`

Reads the JSON files in `outputs/` & draws the four plots in `figures/`.

### `tests/`

About 140 tests. The most important file is `tests/test_known_answers.py`, which runs the whole audit & checks that the empty suite scores ~100% & the oracle suite ~0%.

## Part 2: defend it

Short answers to the questions a researcher or a data buyer is likely to ask. Numbers are from the run recorded in the README.

### 1. How do you know the audit itself is correct? Walk through the checks.

Four checks, each catching a different kind of mistake.

1. **Known answers.** Two suites were added whose right score is known before running anything. The empty suite asserts nothing, so it must pass every real bug: it passed 425 of 425. The oracle suite compares against a brute-force oracle on 500 random inputs, so it must pass almost none: it passed 1 of 425. If the runner were secretly testing the reference instead of the mutant, the oracle suite would have passed everything. If timeouts or crashes were being miscounted, the empty suite would have dropped below 100%.
2. **Rules that can't be broken.** Weak ⊂ medium ⊂ strong, so a mutant killed by a weaker suite must be killed by the stronger one. And a mutant flagged "equivalent" must pass every suite. Zero violations in 2,220 runs.
3. **Hand-checked sample.** I read 30 randomly drawn mutants & judged each without the audit's label in front of me. 30 of 30 agreed. Because that draw happened to contain no equivalent mutants, I also reviewed all 19 that the audit flagged. All 19 hold up, though 6 only because of a promise in the task description (for example "the inputs are integers").
4. **Cross-check with the hacks.** Suites that pass more mutants also pass more hacks (empty 100% & 100%, weak 33% & 100%, medium 16% & 77%). The one mismatch is informative rather than a fault: the strong suite passes 0% of mutants but 23% of hacks, almost all of it one hack (question 7).

One thing these checks did *not* confirm, & the fifth check (EvalPlus) is why I know: that a good mutation score means real model errors get caught. See the next question.

### 2. Why are mutants not the same as the mistakes a real model makes, & how did the EvalPlus check test that? What did the correlation show?

A mutant is the *correct* solution with one token changed. A model's wrong answer is usually a *different program*: a different reading of the spec, or an edge case nobody thought about. Those are different kinds of wrong.

The test: for each of 164 HumanEval problems, compute (a) the share of mutants that slip past HumanEval's original tests & (b) the share of wrong model-written solutions that slip past them, using 196,800 released samples from six models, with HumanEval+ deciding what counts as wrong. If mutants were a good stand-in, problems with a high (a) should have a high (b).

**They don't. Spearman rank correlation 0.07, 95% interval −0.10 to 0.24, over 162 problems.** That's indistinguishable from no relationship. Removing duplicate samples gives 0.06. A second full run from a fresh clone gave 0.08, with 0.06% of sample verdicts differing because slow samples hit time limits differently under load.

Where it goes wrong, concretely:

- The audit found **no** surviving mutant on 125 problems. On 109 of those, real wrong solutions got through anyway. 59% of all real false positives (5,786 of 9,815) sit in problems the audit called clean.
- `filter_integers` is the clearest case. The reference is one line, `type(x) == int`. All its mutants die. But 97% of the wrong model solutions pass the original tests, because models write `isinstance(x, int)`, which lets `True` & `False` through, & the original tests contain no booleans. No single-token change to the reference produces that mistake.
- The reverse also happens. `numerical_letter_grade` has 22 surviving mutants, all of them nudged grade boundaries like `> 3.7` → `>= 3.7`. Real false positives there: zero out of 993 wrong samples. The boundaries are written out in the prompt, so models copy them correctly. Mutants attack exactly the part a model gets right for free.

There's one weak positive signal. Against a different measure, "of the solutions the original tests accept, what share are wrong", the correlation is 0.20 (interval 0.01 to 0.37). That's one of three secondary analyses with no correction for trying several, so I wouldn't lean on it.

**What I take from it:** mutation score tells you whether the tests exercise the code that's *there*. It says little about inputs & behaviours the reference never had to think about, & that's where models actually fail.

### 3. Why can HumanEval+ serve as ground truth here, & what's the weakness of that assumption?

Because it's far stronger than what it's judging: about 750 inputs per problem against about 10, built by combining LLM-suggested seed inputs with automated mutation of those inputs, & checked against reference solutions the EvalPlus authors re-verified.

The weakness is that "passes HumanEval+" is still not "correct". It's a bigger test suite, not a proof. Two consequences:

- Some wrong solutions pass HumanEval+ too. Those are counted as correct here, so every false-positive rate in the realism check is an **underestimate**.
- 229 mutants pass both test sets. I treated them as equivalent & left them out, but some are surely real bugs HumanEval+ can't see. It's the same problem as the equivalent-mutant check in the main audit: the ground truth is only as good as its inputs.

A third caveat: "wrong" sometimes means "disagrees with the reference about something the prompt left open". `is_palindrome` solutions that ignore upper & lower case are counted wrong, which is debatable.

### 4. What's a mutant, & why does "the tests still pass on a mutant" mean the verifier is weak?

A mutant is the correct solution with one small deliberate change, such as `<` to `<=`. If that change alters the program's behaviour, the mutant is a buggy program, & I know it's buggy because I broke it myself.

A verifier's whole job is to tell correct from buggy. If it gives the mutant a pass, it has just failed at that job on a case where the answer is known. Count how often that happens & you have a measured false-positive rate instead of a feeling that "the tests look thorough".

### 5. What's an equivalent mutant, & why must it be excluded?

A mutant whose change makes no difference on any input. Example from `merge_intervals`: in `if end > last[1]: last[1] = end`, changing `>` to `>=` only adds the case where `end` already equals `last[1]`, & then the assignment changes nothing.

It has to be excluded because it isn't a bug. No test could fail it, not even a perfect one. If it stayed in, every suite would be charged with "missing" something that was never wrong, & the false-positive rates would be inflated by a fixed amount unrelated to test quality.

The catch, which the hand review made concrete: equivalence can't be proven by testing, only suggested. The audit calls a mutant equivalent if it matches the reference on 3,000 random inputs plus hand-picked edge cases. Six of the 19 it flagged are equivalent only on the inputs the task allows.

### 6. Why does a weak verifier make RL training data worse, not just evaluation worse?

In evaluation, a false positive inflates a score. The number is wrong, but the model is unchanged.

In RL training, the verifier's verdict **is the reward**, & the gradient pushes the model toward whatever earned it. A false positive means a wrong solution got reward 1, so the update makes that wrong behaviour more likely next time. In GRPO terms, the wrong sample's reward lands above the group average exactly when it should be below, so the sign of its update is flipped.

It's worse than random label noise, because it isn't random. The model is searching for whatever gets reward, so it finds the verifier's specific blind spots & concentrates there. That's reward hacking. The gallery shows how little it takes: memorising the tests beat every suite built only from fixed examples, on all 12 tasks.

### 7. Which hack was hardest to catch, & what kind of test catches it?

**`always_equal`:** return an object whose `==` always answers True. It beat the *strong* suite on 10 of 12 tasks, the same suite that caught every one of the 425 real bugs. No amount of extra test cases helps, because every `assert f(x) == expected` hands the decision to the object being judged.

What catches it is a different *kind* of check, not more of the same:

- insist that the result is plain data of the expected type before comparing (the oracle suite does this & caught it 12 of 12), or better,
- run the candidate in its own process & compare only its serialised output from outside (the third verifier in `demos/verifier_attacks/`, which also stops a forged "all tests passed" message).

Runner-up: the `special_case` hack for `is_valid_parentheses`, which counts brackets without tracking order. It survived the 500-input oracle suite because inputs that expose it (like `[(])`) turn up about once in 3,000 draws from my generator. More random inputs is the weak fix. A generator aimed at that case, or simply trying every string up to length 6, is the strong one.

### 8. How would an AI training-data broker use this on a seller's real repo before pricing an RL environment?

As one stage of a quality report on the verifier, done before a price is set. In order:

1. **Mutation audit as a floor test.** Mutate the functions each task touches & run the repo's own tests. This is cheap & fully automatic. A suite that lets a third of mutants through (like the weak suites here) is plainly inadequate, & the environment is rejected or marked down. But passing is **not** proof of quality: the EvalPlus result shows a clean mutation score coexists with lots of real false positives.
2. **Real model attempts, judged by something stronger than the repo's tests.** Run three or more models on each task. For solutions the verifier accepts, check them a second way: differential testing against the reference on generated inputs (the HumanEval+ recipe), or hand review of a stratified sample. Report the share of accepted solutions that are wrong, with an interval. This is the number a buyer actually feels.
3. **Hack resistance checklist.** Can the agent edit the test files? Do the candidate & the checker share a process? Are outputs compared as plain data? Are there any checks the agent can't see or predict? Each "no" is a known exploit from the gallery & the demo.
4. **Put the numbers on the delivery.** Per environment: mutation score, measured false-positive share, checklist result. Buyers reportedly discard much of what they buy for exactly these failures, so a seller's data that arrives with them measured is worth more than data that arrives with a claim.

What I would not do is quote mutation score alone as "verifier quality". This project is the evidence for why not.
