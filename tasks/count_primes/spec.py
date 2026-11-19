"""Oracle & input generator for count_primes."""


def apply(solution, args):
    return solution.count_primes(*args)


def oracle(n):
    """Brute force: test every number below n by trying every possible divisor."""
    count = 0
    for candidate in range(2, n):
        if all(candidate % divisor != 0 for divisor in range(2, candidate)):
            count += 1
    return count


def gen_input(rng):
    roll = rng.random()
    if roll < 0.4:
        return (rng.randint(-2, 12),)
    if roll < 0.8:
        return (rng.randint(0, 60),)
    return (rng.randint(0, 130),)


EDGE_INPUTS = [(n,) for n in (-5, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 25, 26, 49, 50, 100, 121, 122, 170)]
