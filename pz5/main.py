import argparse
import csv
import textwrap
from pathlib import Path

Matrix = list[list[float | int]]

DEFAULT_MATRIX = "5 5 4 5 4, 5 5 3 0 3, 5 5 5 5 0, 5 0 5 5 5, 0 5 1 0 2"
DEFAULT_SIMILARITY = "0.8 0.85 0.82 0.7, 0.78 0.75 0.9, 0.95 0.72, 0.68"
DEFAULT_THRESHOLD = 0.85


def mid(values: list[float | int]) -> float:
    rated = [v for v in values if v != 0]

    return sum(rated) / len(rated) if rated else 0


def column(matrix: Matrix, j: int) -> list[float | int]:
    return [row[j] for row in matrix]


def neighbours(
    matrix: Matrix,
    similarity: Matrix,
    a: int,
    i: int,
    threshold: float,
) -> list[int]:
    # K — товары, похожие на i (сходство не ниже порога) и оцененные пользователем a
    return [
        j
        for j in range(len(matrix))
        if j != i and similarity[i][j] >= threshold and matrix[j][a] != 0
    ]


def predict(matrix: Matrix, similarity: Matrix, a: int, i: int, k: list[int]) -> float:
    # Pr(a, i) = Σ r(a, j) * cos(i, j) / Σ |cos(i, j)|, j ∈ K
    num = sum(matrix[j][a] * similarity[i][j] for j in k)
    den = sum(abs(similarity[i][j]) for j in k)

    return num / den if den else 0


def recommend(
    matrix: Matrix,
    similarity: Matrix,
    a: int,
    threshold: float,
) -> list[tuple[int, float, list[int]]]:
    items = []

    for i, row in enumerate(matrix):
        if row[a] != 0:
            continue

        k = neighbours(matrix, similarity, a, i, threshold)

        if k:
            items.append((i, predict(matrix, similarity, a, i, k), k))

    return sorted(items, key=lambda p: -p[1])


def best_rated(matrix: Matrix) -> int:
    return max(range(len(matrix)), key=lambda i: mid(matrix[i]))


def print_matrix(
    matrix: Matrix,
    row_labels: list[str] | None = None,
    col_labels: list[str] | None = None,
) -> None:
    if row_labels is None:
        row_labels = [str(i) for i in range(len(matrix))]
    if col_labels is None:
        col_labels = [str(j) for j in range(len(matrix[0]) if matrix else 0)]

    cells = [[f"{v:g}" for v in row] for row in matrix]
    width = max(len(s) for s in col_labels + [c for row in cells for c in row])
    label_width = max(len(s) for s in row_labels)

    print(" " * label_width + " | " + " ".join(s.rjust(width) for s in col_labels))
    print("-" * label_width + "-+-" + "-".join("-" * width for _ in col_labels))

    for label, row in zip(row_labels, cells):
        print(label.ljust(label_width) + " | " + " ".join(c.rjust(width) for c in row))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pz5",
        usage="%(prog)s [options]",
        description= \
            "Принимает на вход матрицу предпочтений (строки — товары, " \
            "столбцы — пользователи) и матрицу косинусного сходства товаров, " \
            "для каждого пользователя прогнозирует рейтинг неоцененных товаров " \
            "по похожим товарам (ITEM-BASED): " \
            "Pr(a, i) = Σ r(a, j) * cos(i, j) / Σ |cos(i, j)|, где K — товары " \
            "со сходством с i не ниже порога, оцененные пользователем a. " \
            "Новому пользователю рекомендуется товар с наибольшим средним " \
            "рейтингом. Матрица сходства задается элементами над главной " \
            "диагональю.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            пример:
                # матрицы из задания
                %(prog)s

                # считать матрицу предпочтений из CSV-файла
                %(prog)s -c example.csv -s "0.9 0.7, 0.6"

                # передать матрицу предпочтений как аргумент и задать порог
                %(prog)s "5 5 0, 5 0 3, 0 5 1" -s "0.9 0.7, 0.6" -t 0.7
        """),
    )

    parser.add_argument("input_matrix", nargs="?", default=DEFAULT_MATRIX)
    parser.add_argument("-c", "--csv")
    parser.add_argument("-s", "--similarity", default=DEFAULT_SIMILARITY)
    parser.add_argument("-t", "--threshold", type=float, default=DEFAULT_THRESHOLD)

    args = parser.parse_args()

    input_matrix: Matrix = []

    if args.csv:
        csv_path = Path(args.csv)

        if not csv_path.exists():
            print("there's no such csv file")

            return -1

        with open(args.csv, newline="") as file:
            reader = csv.reader(file)

            for row in reader:
                input_matrix.append(list(map(float, row)))
    else:
        rows = args.input_matrix.split(",")

        for r in rows:
            input_matrix.append(list(map(float, r.split())))

    try:
        rows = [[float(c) for c in r.split()] for r in args.similarity.split(",")]
    except ValueError:
        print("incorrect similarity matrix")

        return -1

    m = len(rows) + 1

    if m != len(input_matrix) or any(len(rows[i]) != m - 1 - i for i in range(m - 1)):
        print("similarity matrix doesn't match the number of products")

        return -1

    similarity: Matrix = [[0] * m for _ in range(m)]

    for i in range(m - 1):
        for j in range(i + 1, m):
            similarity[i][j] = similarity[j][i] = rows[i][j - (i + 1)]

    products = [f"P{i + 1}" for i in range(len(input_matrix))]
    users = [f"U{j + 1}" for j in range(len(input_matrix[0]))]

    print("Матрица предпочтений:")
    print_matrix(
        [row + [round(mid(row), 2)] for row in input_matrix],
        products,
        users + ["MID"],
    )

    print("\nМатрица сходства товаров:")
    print_matrix(similarity, products, products)

    pairs = [
        (similarity[i][j], i, j)
        for i in range(m)
        for j in range(i + 1, m)
        if similarity[i][j] >= args.threshold
    ]

    print(f"\nПохожие товары (сходство >= {args.threshold:g}):")

    if not pairs:
        print("нет")

    for sim, i, j in sorted(pairs, reverse=True):
        print(f"{products[i]} - {products[j]}: {sim:g}")

    best = best_rated(input_matrix)
    popular = f"{products[best]} (средний рейтинг {mid(input_matrix[best]):g})"

    print(f"\nНовый пользователь: рекомендовать {popular}")

    for a in range(len(users)):
        print()

        if not any(column(input_matrix, a)):
            print(f"{users[a]} — новый пользователь, рекомендовать {popular}")

            continue

        items = recommend(input_matrix, similarity, a, args.threshold)

        if not items:
            print(f"{users[a]}: нечего рекомендовать")

            continue

        for i, rating, k in items:
            terms = " + ".join(
                f"{input_matrix[j][a]:g}*{similarity[i][j]:g}" for j in k
            )
            sims = " + ".join(f"{similarity[i][j]:g}" for j in k)

            print(
                f"{users[a]}, {products[i]}: K = {{{', '.join(products[j] for j in k)}}}, "
                f"Pr = ({terms}) / ({sims}) = {rating:.2f}"
            )
            print(f"{users[a]} рекомендовать {products[i]} (прогноз рейтинга {rating:.2f})")

    return 0

if __name__ == "__main__":
    main()
