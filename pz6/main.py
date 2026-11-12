import argparse
import re
import textwrap

# Правила, хранящиеся в БД (последнее — гипотеза H)
RULES = [
    "X проживает в Y",
    "X является членом партии Z",
    "X имеет возраст T",
    "X является ИП",
    "X будет голосовать за кандидата B",
]
HYPOTHESIS = len(RULES)

DEFAULT_E1 = "1(0.8, 0.3) and 2(0.75, 0.25)"
DEFAULT_E2 = "3(0.4, 0.5) or 4(0.85, 0.2)"

FACT = re.compile(
    r"^\s*(not\s+)?(\d+)\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)\s*$",
    re.IGNORECASE,
)

Fact = tuple[bool, int, float, float]  # (отрицание, номер правила, MD, MND)


class ParseError(Exception):
    pass


def parse(expression: str) -> tuple[list[Fact], str | None]:
    # "N(MD, MND) [and|or [not] N(MD, MND)]"
    parts = re.split(r"\s+(and|or)\s+", expression.strip(), flags=re.IGNORECASE)

    if len(parts) > 3:
        raise ParseError("предположение должно содержать не более двух правил")

    facts: list[Fact] = []

    for part in parts[::2]:
        match = FACT.match(part)

        if not match:
            raise ParseError(f"не удалось разобрать «{part}»")

        neg, rule, md, mnd = match.groups()
        rule, md, mnd = int(rule), float(md), float(mnd)

        if not 1 <= rule < HYPOTHESIS:
            raise ParseError(f"в БД нет правила-условия с номером {rule}")

        if not (0 <= md <= 1 and 0 <= mnd <= 1):
            raise ParseError("меры доверия и недоверия должны лежать в [0; 1]")

        facts.append((neg is not None, rule, md, mnd))

    op = parts[1].lower() if len(parts) == 3 else None

    return facts, op


def negate(fact: Fact) -> tuple[float, float]:
    # Not MD = 1 - MD
    neg, _, md, mnd = fact

    return (1 - md, 1 - mnd) if neg else (md, mnd)


def evaluate(facts: list[Fact], op: str | None) -> tuple[float, float]:
    # MD1 And MD2 = MIN(MD1, MD2), MD1 Or MD2 = MAX(MD1, MD2)
    values = [negate(f) for f in facts]

    if op is None:
        return values[0]

    combine = min if op == "and" else max

    return combine(v[0] for v in values), combine(v[1] for v in values)


def accumulate(first: float, second: float) -> float:
    # M[H:E1, E2] = M[H:E1] + M[H:E2] * (1 - M[H:E1])
    return first + second * (1 - first)


def fmt(v: float) -> str:
    return f"{round(v, 4):g}"


def describe(facts: list[Fact], op: str | None, name: str) -> list[str]:
    lines = [f"{name}: ЕСЛИ"]

    for idx, (neg, rule, md, mnd) in enumerate(facts):
        if idx:
            lines.append("и" if op == "and" else "или")

        text = ("НЕ " if neg else "") + RULES[rule - 1]
        lines.append(f"  {text} (MD = {fmt(md)}, MND = {fmt(mnd)})")

    lines += ["ТО", f"  {RULES[HYPOTHESIS - 1]}"]

    return lines


def explain(facts: list[Fact], op: str | None, measure: int) -> str:
    label = "MD" if measure == 0 else "MND"
    terms = []

    for f in facts:
        value = (f[2], f[3])[measure]
        terms.append(f"1 - {fmt(value)}" if f[0] else fmt(value))

    if op is None:
        expr = terms[0]
    else:
        expr = f"{'MIN' if op == 'and' else 'MAX'}({', '.join(terms)})"

    return f"{label} = {expr} = {fmt(evaluate(facts, op)[measure])}"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pz6",
        usage="%(prog)s [options] [E1] [E2]",
        description= \
            "Принимает на вход не более двух предположений E1, E2 — комбинаций " \
            "правил БД с мерами доверия (MD) и недоверия (MND) из [0; 1]. " \
            "Меры каждого предположения рассчитываются по правилам нечеткой " \
            "логики (And = MIN, Or = MAX, Not = 1 - M), затем объединяются: " \
            "M[H:E1, E2] = M[H:E1] + M[H:E2](1 - M[H:E1]). Итоговый коэффициент " \
            "уверенности считается по формуле Шортлиффа: KU = MD - MND. " \
            "Предположение задается в виде «N(MD, MND) and|or [not] N(MD, MND)», " \
            "где N — номер правила в БД.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            правила в БД:
                1. X проживает в Y
                2. X является членом партии Z
                3. X имеет возраст T
                4. X является ИП
                5. X будет голосовать за кандидата B (гипотеза H)

            пример:
                # предположения из задания
                %(prog)s

                # задать свои предположения
                %(prog)s "1(0.9, 0.1) or 2(0.6, 0.3)" "not 4(0.3, 0.6)"

                # только одно предположение
                %(prog)s -1 "3(0.7, 0.2) and 4(0.5, 0.4)"
        """),
    )

    parser.add_argument("e1", nargs="?", default=DEFAULT_E1)
    parser.add_argument("e2", nargs="?", default=DEFAULT_E2)
    parser.add_argument(
        "-1", "--single", action="store_true", dest="single",
        help="рассчитать только предположение E1",
    )

    args = parser.parse_args()

    expressions = [args.e1] if args.single else [args.e1, args.e2]
    assumptions = []

    for name, expression in zip(["E1", "E2"], expressions):
        try:
            assumptions.append(parse(expression))
        except ParseError as error:
            print(f"{name}: {error}")

            return -1

    print("Правила в БД:")

    for i, rule in enumerate(RULES, 1):
        print(f"{i}. {rule}")

    results = []

    for name, (facts, op) in zip(["E1", "E2"], assumptions):
        print()
        print("\n".join(describe(facts, op, name)))

        md, mnd = evaluate(facts, op)
        results.append((md, mnd))

        print("\n" + explain(facts, op, 0).replace("MD =", f"MD[H:{name}] =", 1))
        print(explain(facts, op, 1).replace("MND =", f"MND[H:{name}] =", 1))
        print(f"KU[H:{name}] = {fmt(md)} - {fmt(mnd)} = {fmt(md - mnd)}")

    if len(results) == 2:
        (md1, mnd1), (md2, mnd2) = results
        md, mnd = accumulate(md1, md2), accumulate(mnd1, mnd2)

        print("\nОбъединение предположений E1, E2:")
        print(
            f"MD[H:E1, E2] = {fmt(md1)} + {fmt(md2)} * (1 - {fmt(md1)}) = {fmt(md)}"
        )
        print(
            f"MND[H:E1, E2] = {fmt(mnd1)} + {fmt(mnd2)} * (1 - {fmt(mnd1)}) = {fmt(mnd)}"
        )
        label = "E1, E2"
    else:
        md, mnd = results[0]
        label = "E1"

    ku = md - mnd

    print(f"\nKU[H:{label}] = {fmt(md)} - {fmt(mnd)} = {fmt(ku)}")

    if ku > 0:
        verdict = "скорее подтверждается"
    elif ku < 0:
        verdict = "скорее опровергается"
    else:
        verdict = "не подтверждается и не опровергается"

    print(f"Гипотеза «{RULES[HYPOTHESIS - 1]}» {verdict}")

    return 0

if __name__ == "__main__":
    main()
