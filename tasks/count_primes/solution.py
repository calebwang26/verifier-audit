"""Count the prime numbers strictly less than n."""


def count_primes(n):
    if n < 3:
        return 0
    is_prime = [True] * n
    is_prime[0] = False
    is_prime[1] = False
    i = 2
    while i * i < n:
        if is_prime[i]:
            for multiple in range(i * i, n, i):
                is_prime[multiple] = False
        i += 1
    count = 0
    for flag in is_prime:
        if flag:
            count += 1
    return count
