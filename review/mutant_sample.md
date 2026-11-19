# Hand-checked mutant sample

30 mutants drawn at random from all 444 (seed 2026, `review/sample.py`). Each was judged by reading the change next to the original code & reasoning about whether any input could behave differently. The hand labels were committed before the comparison script was written.

- **hand:** my label from reading the code
- **audit:** the audit's label (differs from the reference on at least one of 3,000 random inputs or an edge input = bug, otherwise likely equivalent)

**Agreement: 30 of 30 (100%).**

| # | mutant | change | hand | audit | agree | one-line reason |
|---|---|---|---|---|---|---|
| 1 | `binary_search/m002` | `low = 0`  ->  `low = 1` | bug | bug | yes | Search starts at index 1, so a target at index 0 is never found: ([3], 3) gives -1. |
| 2 | `count_primes/m006` | `return 0`  ->  `return None` | bug | bug | yes | For n below 3 it returns None instead of 0. |
| 3 | `count_primes/m017` | `is_prime[1] = False`  ->  `is_prime[0] = False` | bug | bug | yes | Index 1 is never cleared, so 1 is counted as a prime: every n >= 3 is one too high. |
| 4 | `count_primes/m021` | delete `while i * i < n:` | bug | bug | yes | The sieve loop is gone, so composites are counted: n=10 gives 8, not 4. |
| 5 | `count_primes/m025` | `if is_prime[i]:`  ->  `if not is_prime[i]:` | bug | bug | yes | Multiples are only crossed off for non-primes, but nothing ever becomes non-prime, so composites stay: n=10 gives 8. |
| 6 | `longest_common_prefix/m009` | `first = strs[0]`  ->  `first = strs[-1]` | bug | bug | yes | Uses the last string as the yardstick & never looks at the first: ['b','a'] gives 'a', not ''. |
| 7 | `longest_common_prefix/m017` | `if i >= len(other) or other[i] != first[i]:`  ->  `if i >= len(other) and other[i] != first[i]:` | bug | bug | yes | With `and` the early return never fires (or it crashes on a short string): ['ab','ac'] gives 'ab', not 'a'. |
| 8 | `lru_cache/m014` | `return self.items[key]`  ->  `return 0` | bug | bug | yes | get() returns 0 instead of the stored value: put(1,10) then get(1) gives 0. |
| 9 | `max_subarray_sum/m005` | `return 0`  ->  `return ''` | bug | bug | yes | Empty list returns '' instead of 0. |
| 10 | `merge_intervals/m024` | delete `if end > last[1]:` | bug | bug | yes | An overlapping interval no longer extends the end: [[1,3],[2,6]] gives [[1,3]]. |
| 11 | `merge_intervals/m034` | `return merged`  ->  `return 0` | bug | bug | yes | Returns 0 instead of the merged list for any non-empty input. |
| 12 | `parse_duration/m023` | `if position < next_allowed:`  ->  `if not position < next_allowed:` | bug | bug | yes | The order check is inverted, so the very first unit is rejected: '45s' raises. |
| 13 | `parse_duration/m029` | delete `next_allowed = position + 1` | bug | bug | yes | next_allowed never advances, so repeats & wrong order are accepted: '1h2h' gives 10800 instead of raising. |
| 14 | `parse_duration/m034` | delete `if digits:` | bug | bug | yes | A trailing number with no unit is silently ignored: '15' gives 0 instead of raising. |
| 15 | `rle_encode/m011` | delete `count = 1` | bug | bug | yes | `count` is never initialised, so any non-empty string crashes when it's first used. |
| 16 | `rle_encode/m015` | `for ch in s[1:]:`  ->  `for ch in s[2:]:` | bug | bug | yes | The second character is skipped: 'ab' gives 'a'. |
| 17 | `rle_encode/m024` | `parts.append(current + (str(count) if count > 1 else ''))`  ->  `parts.append(current - (str(count) if count > 1 else ''))` | bug | bug | yes | Subtracting a string from a string raises TypeError as soon as a run ends: 'ab' crashes. |
| 18 | `rle_encode/m031` | `count = 1`  ->  `count = 2` | bug | bug | yes | Later runs start counting at 2: 'ab' gives 'ab2'. |
| 19 | `rle_encode/m038` | `parts.append(current + (str(count) if count > 1 else ''))`  ->  `parts.append(current + (str(count) if count > 0 else ''))` | bug | bug | yes | A final run of length 1 gets a count: 'a' gives 'a1'. |
| 20 | `roman_to_int/m002` | `total = 0`  ->  `total = 1` | bug | bug | yes | Total starts at 1, so every answer is one too high. |
| 21 | `roman_to_int/m006` | delete `if i + 1 < len(s) and value < VALUES[s[i + 1]]:` | bug | bug | yes | Nothing is ever added: every numeral gives 0. |
| 22 | `roman_to_int/m019` | delete `total += value` | bug | bug | yes | Values are only ever subtracted, never added: 'III' gives 0. |
| 23 | `spiral_order/m037` | `result.append(matrix[top][col])`  ->  `pass` | bug | bug | yes | The top row of every ring is never read: [[1]] gives []. |
| 24 | `spiral_order/m047` | delete `right -= 1` | bug | bug | yes | The right edge never moves in, so cells are read twice: [[1,2],[3,4]] repeats the 4. |
| 25 | `spiral_order/m056` | `for col in range(right, left - 1, -1):`  ->  `for col in range(right, left - 2, -1):` | bug | bug | yes | The bottom row runs one column too far & wraps to index -1: a 2x2 gives [1,2,4,3,4]. |
| 26 | `spiral_order/m058` | `for col in range(right, left - 1, -1):`  ->  `for col in range(right, left - 1, -2):` | bug | bug | yes | The bottom row is read in steps of 2, so a 3x3 misses the 7. |
| 27 | `spiral_order/m060` | `result.append(matrix[bottom][col])`  ->  `pass` | bug | bug | yes | The bottom row of every ring is never read: a 2x2 misses the 3. |
| 28 | `spiral_order/m064` | `bottom -= 1`  ->  `bottom -= 0` | bug | bug | yes | The bottom edge never moves up, so cells are read twice: a 2x2 gives [1,2,4,3,3]. |
| 29 | `top_k_frequent/m011` | `if k <= 0:`  ->  `if not k <= 0:` | bug | bug | yes | The guard is inverted: every positive k returns []. |
| 30 | `top_k_frequent/m020` | `return ranked[:k]`  ->  `return 0` | bug | bug | yes | Returns 0 instead of a list for every positive k. |

To see any of these in full: `python mutate.py tasks/<task>/solution.py <id>`.

## Every mutant the audit flagged as likely equivalent

The random sample above happened to contain no equivalent mutants (only 19 of 444 are flagged, so a 30-mutant draw misses them about a quarter of the time). That leaves the audit's *equivalent* label untested, so all of the flagged mutants were reviewed too. This part was not blind: I knew the audit had flagged them. Each verdict is an argument you can check yourself.

| mutant | change | hand | equivalence holds | reason |
|---|---|---|---|---|
| `count_primes/m005` | `if n < 3:`  ->  `if n < 2:` | equivalent | always | n=2 builds [True, True], clears both & counts 0, the same as returning 0 early. |
| `count_primes/m020` | `i = 2`  ->  `i = 1` | equivalent | always | The extra pass with i=1 does nothing because is_prime[1] is already False. |
| `count_primes/m023` | `while i * i < n:`  ->  `while i * i <= n:` | equivalent | always | The extra pass happens only when i*i == n, & then range(i*i, n, i) is empty. |
| `longest_common_prefix/m013` | `for other in strs[1:]:`  ->  `for other in strs[0:]:` | equivalent | always | Comparing the first string with itself can never find a mismatch. |
| `max_subarray_sum/m019` | `if current < 0:`  ->  `if current <= 0:` | equivalent | always | When current is exactly 0, `0 + value` & `value` are the same number. |
| `max_subarray_sum/m020` | `if current < 0:`  ->  `if current < 1:` | equivalent | only for integer inputs | For integers `current < 1` means `current <= 0` (see m019). With fractions it's a real bug: [0.5, 1] would give 1 instead of 1.5. The task says integers. |
| `max_subarray_sum/m027` | `if current > best:`  ->  `if current >= best:` | equivalent | always | Re-assigning best to an equal value changes nothing. |
| `merge_intervals/m015` | `for start, end in ordered[1:]:`  ->  `for start, end in ordered[0:]:` | equivalent | only if start <= end | The first interval is compared with a copy of itself & absorbed. An invalid interval like [5,1] would be duplicated, but the task promises start <= end. |
| `merge_intervals/m026` | `if end > last[1]:`  ->  `if end >= last[1]:` | equivalent | always | Re-assigning the end to an equal value changes nothing. |
| `parse_duration/m010` | `next_allowed = 0`  ->  `next_allowed = -1` | equivalent | always | A position is never negative, so `position < -1` & `position < 0` are both always false. |
| `parse_duration/m020` | `elif ch in UNIT_SECONDS and digits:`  ->  `elif ch in UNIT_SECONDS or digits:` | equivalent | same result or same error type; the error message differs | Every input the reference rejects still raises ValueError, but from int('') or str.index() with a different message. A test that checked the message text would tell them apart. |
| `spiral_order/m006` | `if not matrix or not matrix[0]:`  ->  `if not matrix or not matrix[-1]:` | equivalent | only for rectangular matrices | Checks whether the last row is empty instead of the first. Same thing when all rows have equal length; differs for ragged input like [[1], []]. |
| `spiral_order/m011` | `return result`  ->  `return []` | equivalent | always | At that early return `result` is still the empty list. |
| `spiral_order/m025` | `right = len(matrix[0]) - 1`  ->  `right = len(matrix[-1]) - 1` | equivalent | only for rectangular matrices | Takes the width from the last row instead of the first. |
| `top_k_frequent/m005` | `counts[value] = counts.get(value, 0) + 1`  ->  `counts[value] = counts.get(value, 1) + 1` | equivalent | always | Every count is one higher, which doesn't change the ranking. Counts are never returned. |
| `top_k_frequent/m006` | `counts[value] = counts.get(value, 0) + 1`  ->  `counts[value] = counts.get(value, -1) + 1` | equivalent | always | Every count is one lower, which doesn't change the ranking. |
| `top_k_frequent/m007` | `counts[value] = counts.get(value, 0) + 1`  ->  `counts[value] = counts.get(value, 0) + 2` | equivalent | always | Every count is doubled, which doesn't change the ranking. |
| `top_k_frequent/m012` | `if k <= 0:`  ->  `if k < 0:` | equivalent | always | k=0 falls through to ranked[:0], which is [] anyway. |
| `top_k_frequent/m014` | `if k <= 0:`  ->  `if k <= -1:` | equivalent | only for whole-number k | For integers `k <= -1` means `k < 0` (see m012). |

**All 19 agree with the audit: none is a bug on the inputs the task allows.** 13 are equivalent on any input at all. The other 6 are equivalent only because of something the task's description promises (whole numbers, rectangular matrices, start <= end) or because only the error *type* is compared, not its message. So "equivalent" always means "equivalent on the inputs you're allowed to send". If a task's promises were loosened, those mutants would become real bugs that this audit never counted.
