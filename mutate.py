"""AST-based mutation engine.

A *mutant* is a copy of a program with one small change, the kind of slip a
programmer (or a model) could plausibly make. This module parses Python
source into a syntax tree with the standard `ast` module, finds every place
one of seven mutation operators applies, & returns one mutant per place.

Operators:
    cmp_swap      swap a comparison: <  <->  <=,  >  <->  >=,  ==  <->  !=
    const_offby1  add or subtract 1 from a numeric constant
    bool_swap     swap `and` & `or`
    stmt_delete   delete one statement
    cond_negate   negate the condition of an if / while / conditional expression
    arith_swap    swap + & - (including += & -=)
    return_const  replace a returned value with a constant

Only code inside functions is mutated. Module-level constants, imports &
docstrings are left alone.

Command line:
    python mutate.py tasks/merge_intervals/solution.py        # list mutants
    python mutate.py tasks/merge_intervals/solution.py m007   # print one
"""
from __future__ import annotations

import ast
import copy
import difflib
import sys
from dataclasses import dataclass

OPERATORS = ["cmp_swap", "const_offby1", "bool_swap", "stmt_delete",
             "cond_negate", "arith_swap", "return_const"]

_CMP_SWAPS = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
              ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_CMP_SYMBOL = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
_NEVER_DELETED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import,
                  ast.ImportFrom, ast.Global, ast.Nonlocal, ast.Pass)
_STATEMENT_LISTS = ("body", "orelse", "finalbody")


@dataclass(frozen=True)
class Mutant:
    id: str           # "m001", "m002", ... in source order
    operator: str     # one of OPERATORS
    lineno: int       # line of the change in the original source
    description: str  # e.g. "`if start <= last[1]:`  ->  `if start < last[1]:`"
    source: str       # the full mutated program


@dataclass(frozen=True)
class _Site:
    """One place where one operator can make one change."""
    operator: str
    lineno: int
    col: int
    index: int        # position of the node in ast.walk(tree) order
    payload: tuple    # operator-specific details


def normalize(source: str) -> str:
    """Source code as `ast` prints it back: comments gone, formatting uniform."""
    return ast.unparse(ast.parse(source))


def _owners(tree: ast.AST) -> dict[int, ast.AST | None]:
    """For every node, the function it sits inside (None for module-level code)."""
    owner: dict[int, ast.AST | None] = {}

    def visit(node: ast.AST, func: ast.AST | None) -> None:
        owner[id(node)] = func
        inner = node if isinstance(node, _FUNCTIONS) else func
        for child in ast.iter_child_nodes(node):
            visit(child, inner)

    visit(tree, None)
    return owner


def _is_docstring(stmt: ast.stmt) -> bool:
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _is_number(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool))


def _returns_booleans(func: ast.AST, owner: dict[int, ast.AST | None]) -> bool:
    """Guess whether a function returns True/False, from how its returns look."""
    for node in ast.walk(func):
        if isinstance(node, ast.Return) and owner[id(node)] is func and node.value is not None:
            value = node.value
            if isinstance(value, (ast.Compare, ast.BoolOp)):
                return True
            if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not):
                return True
            if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                return True
    return False


def _find_sites(tree: ast.AST) -> list[_Site]:
    owner = _owners(tree)
    sites: list[_Site] = []

    def add(operator: str, node: ast.AST, index: int, *payload) -> None:
        sites.append(_Site(operator, getattr(node, "lineno", 0), getattr(node, "col_offset", 0),
                           index, payload))

    for index, node in enumerate(ast.walk(tree)):
        func = owner[id(node)]
        inside = func is not None

        # stmt_delete: statements in the body of a function, or of anything inside one.
        if inside or isinstance(node, _FUNCTIONS):
            for field in _STATEMENT_LISTS:
                statements = getattr(node, field, None)
                if not isinstance(statements, list):
                    continue
                for position, stmt in enumerate(statements):
                    if not isinstance(stmt, ast.stmt) or isinstance(stmt, _NEVER_DELETED):
                        continue
                    if _is_docstring(stmt):
                        continue
                    if isinstance(stmt, ast.Return) and stmt.value is not None:
                        continue  # same behaviour as return_const's `return None`
                    sites.append(_Site("stmt_delete", stmt.lineno, stmt.col_offset, index,
                                       (field, position)))
        if not inside:
            continue

        if isinstance(node, ast.Compare):
            for k, op in enumerate(node.ops):
                if type(op) in _CMP_SWAPS:
                    add("cmp_swap", node, index, k)
        if _is_number(node):
            add("const_offby1", node, index, +1)
            add("const_offby1", node, index, -1)
        if isinstance(node, ast.BoolOp):
            add("bool_swap", node, index)
        if isinstance(node, (ast.If, ast.While, ast.IfExp)):
            test = node.test
            # `x == y` & `x != y` are already negated by cmp_swap; don't make a twin.
            twin = (isinstance(test, ast.Compare) and len(test.ops) == 1
                    and isinstance(test.ops[0], (ast.Eq, ast.NotEq)))
            if not twin:
                add("cond_negate", node, index, "test")
        if isinstance(node, ast.comprehension):
            for k in range(len(node.ifs)):
                sites.append(_Site("cond_negate", node.ifs[k].lineno, node.ifs[k].col_offset,
                                   index, ("ifs", k)))
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, (ast.Add, ast.Sub)):
            add("arith_swap", node, index)
        if isinstance(node, ast.Return) and node.value is not None:
            pair = (True, False) if _returns_booleans(func, owner) else (0, 1)
            for constant in (None, pair[0], pair[1], "", []):
                add("return_const", node, index, constant)

    order = {name: rank for rank, name in enumerate(OPERATORS)}
    sites.sort(key=lambda s: (s.lineno, s.col, order[s.operator]))  # stable: keeps variant order
    return sites


def _negate(test: ast.expr) -> ast.expr:
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return test.operand
    return ast.UnaryOp(op=ast.Not(), operand=test)


def _short(node: ast.AST, limit: int = 70) -> str:
    text = ast.unparse(node).split("\n")[0]
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _apply(tree: ast.AST, site: _Site) -> str:
    """Make the change described by `site` in `tree` (in place). Returns a description."""
    node = list(ast.walk(tree))[site.index]
    op = site.operator

    if op == "stmt_delete":
        field, position = site.payload
        statements = getattr(node, field)
        described = f"delete `{_short(statements[position])}`"
        del statements[position]
        if not statements and field == "body":
            statements.append(ast.Pass())
        return described

    before = _short(node)
    if op == "cmp_swap":
        (k,) = site.payload
        old = type(node.ops[k])
        node.ops[k] = _CMP_SWAPS[old]()
        return f"`{before}`  ->  `{_short(node)}`"
    if op == "const_offby1":
        (delta,) = site.payload
        new_value = node.value + delta
        node.value = new_value
        return f"constant {before} -> {new_value}"
    if op == "bool_swap":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return f"`{before}`  ->  `{_short(node)}`"
    if op == "cond_negate":
        if site.payload[0] == "test":
            old = _short(node.test)
            node.test = _negate(node.test)
            return f"condition `{old}`  ->  `{_short(node.test)}`"
        k = site.payload[1]
        old = _short(node.ifs[k])
        node.ifs[k] = _negate(node.ifs[k])
        return f"condition `{old}`  ->  `{_short(node.ifs[k])}`"
    if op == "arith_swap":
        node.op = ast.Sub() if isinstance(node.op, ast.Add) else ast.Add()
        return f"`{before}`  ->  `{_short(node)}`"
    if op == "return_const":
        (constant,) = site.payload
        node.value = ast.List(elts=[], ctx=ast.Load()) if constant == [] and isinstance(constant, list) \
            else ast.Constant(value=constant)
        return f"`{before}`  ->  `{_short(node)}`"
    raise ValueError(f"unknown operator {op}")


def generate_mutants(source: str) -> list[Mutant]:
    """Every single-point mutant of `source`, in source order, without duplicates."""
    tree = ast.parse(source)
    original = ast.unparse(tree)
    seen = {original}
    mutants: list[Mutant] = []
    for site in _find_sites(tree):
        mutated_tree = copy.deepcopy(tree)
        description = _apply(mutated_tree, site)
        ast.fix_missing_locations(mutated_tree)
        mutated = ast.unparse(mutated_tree)
        if mutated in seen:
            continue  # no real change, or the same program as an earlier mutant
        try:
            compile(mutated, "<mutant>", "exec")
        except (SyntaxError, ValueError):
            continue
        seen.add(mutated)
        mutants.append(Mutant(f"m{len(mutants) + 1:03d}", site.operator, site.lineno,
                              _describe(original, mutated, description), mutated + "\n"))
    return mutants


def _describe(original: str, mutated: str, fallback: str) -> str:
    """Prefer "old line  ->  new line" when exactly one line changed."""
    before, after = original.splitlines(), mutated.splitlines()
    if len(before) == len(after):
        changed = [(a.strip(), b.strip()) for a, b in zip(before, after) if a != b]
        if len(changed) == 1:
            return f"`{changed[0][0]}`  ->  `{changed[0][1]}`"
    return fallback


def diff(original_source: str, mutant: Mutant) -> str:
    """The changed lines only, as a small unified diff."""
    before = normalize(original_source).splitlines()
    after = mutant.source.splitlines()
    lines = difflib.unified_diff(before, after, lineterm="", n=1)
    return "\n".join(line for line in lines if not line.startswith(("---", "+++")))


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = open(sys.argv[1]).read()
    mutants = generate_mutants(source)
    if len(sys.argv) > 2:
        chosen = next(m for m in mutants if m.id == sys.argv[2])
        print(f"# {chosen.id} [{chosen.operator}] line {chosen.lineno}: {chosen.description}")
        print(diff(source, chosen))
        return
    for m in mutants:
        print(f"{m.id}  {m.operator:13s} line {m.lineno:3d}  {m.description}")
    print(f"{len(mutants)} mutants")


if __name__ == "__main__":
    main()
