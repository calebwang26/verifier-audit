"""Oracle & input generator for spiral_order."""


def apply(solution, args):
    return solution.spiral_order(*args)


def oracle(matrix):
    """Brute force: walk cell by cell, turning right whenever the way ahead is blocked."""
    if not matrix or not matrix[0]:
        return []
    rows, cols = len(matrix), len(matrix[0])
    seen = set()
    out = []
    r, c, dr, dc = 0, 0, 0, 1
    for _ in range(rows * cols):
        out.append(matrix[r][c])
        seen.add((r, c))
        nr, nc = r + dr, c + dc
        if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in seen:
            dr, dc = dc, -dr
            nr, nc = r + dr, c + dc
        r, c = nr, nc
    return out


def grid(rows, cols):
    """A rows x cols matrix filled with 1, 2, 3, ... so every cell is different."""
    return [[r * cols + c + 1 for c in range(cols)] for r in range(rows)]


def gen_input(rng):
    return (grid(rng.randint(0, 5), rng.randint(0, 5)),)


EDGE_INPUTS = [([],), ([[]],), ([[], []],), (grid(1, 1),), (grid(1, 4),), (grid(4, 1),), (grid(2, 2),),
               (grid(3, 3),), (grid(3, 4),), (grid(4, 3),), (grid(4, 4),), (grid(2, 5),), (grid(5, 2),),
               (grid(5, 5),), (grid(1, 2),), (grid(2, 1),)]
