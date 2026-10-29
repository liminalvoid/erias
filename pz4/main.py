import argparse
import csv
import textwrap
from pathlib import Path

Matrix = list[list[float | int]]

DEFAULT_MATRIX = "5 5 4 5, 5 5 3 0, 5 5 5 5, 5 0 2 0, 0 5 1 0"
DEFAULT_SIMILARITY = "0.9 0.7, 0.6"


def mid(values: list[float | int]) -> float:
    rated = [v for v in values if v != 0]

    return sum(rated) / len(rated) if rated else 0


def column(matrix: Matrix, j: int) -> list[float | int]:
    return [row[j] for row in matrix]


def find_max(similarity: Matrix, a: int) -> tuple[float, int]:
    max_val, u_max = float("-inf"), -1

    for u in range(len(similarity)):
        if u != a and similarity[a][u] > max_val:
            max_val, u_max = similarity[a][u], u

    return max_val, u_max


def predict(matrix: Matrix, a: int, u: int, i: int, sim: float) -> float:
    # r(a, i) = r̄a + sim(a, u) * (r(u, i) - r̄u) / |sim(a, u)|
    ra, ru = mid(column(matrix, a)), mid(column(matrix, u))

    return ra + sim * (matrix[i][u] - ru) / abs(sim)


def recommend(
    matrix: Matrix,
    similarity: Matrix,
    a: int,
) -> tuple[int, float, list[tuple[int, float]]]:
    sim, u = find_max(similarity, a)
    items = [
        (i, predict(matrix, a, u, i, sim))
        for i, row in enumerate(matrix)
        if row[a] == 0 and row[u] != 0
    ]

    return u, sim, sorted(items, key=lambda p: -p[1])


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
        prog="pz4",
        usage="%(prog)s [options]",
        description= \
            "Принимает на вход матрицу предпочтений (строки — товары, " \
            "столбцы — пользователи) и матрицу сходства пользователей, " \
            "для каждого пользователя находит наиболее похожего и рекомендует " \
            "товары, которые оценил похожий пользователь (USER-BASED). " \
            "Новому пользователю (все рейтинги == 0) рекомендуется товар " \
            "с наибольшим средним рейтингом. Пользователи, отсутствующие " \
            "в матрице сходства, исключаются. Матрица сходства задается " \
            "элементами над главной диагональю.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            пример:
                # матрицы из задания
                %(prog)s

                # считать матрицу предпочтений из CSV-файла
                %(prog)s -c example.csv -s "0.9 0.7, 0.6"

                # передать матрицу предпочтений как аргумент
                %(prog)s "5 5 0, 5 0 3, 0 5 1" -s "0.9 0.7, 0.6"
        """),
    )

    parser.add_argument("input_matrix", nargs="?", default=DEFAULT_MATRIX)
    parser.add_argument("-c", "--csv")
    parser.add_argument("-s", "--similarity", default=DEFAULT_SIMILARITY)

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
    similarity: Matrix = [[0] * m for _ in range(m)]

    for i in range(m - 1):
        for j in range(i + 1, m):
            similarity[i][j] = similarity[j][i] = rows[i][j - (i + 1)]

    products = [f"P{i + 1}" for i in range(len(input_matrix))]
    users = [f"U{j + 1}" for j in range(len(input_matrix[0]))]

    if m > len(users):
        print("similarity matrix is larger than the number of users")

        return -1

    print("Матрица предпочтений:")
    print_matrix(
        input_matrix + [[round(mid(column(input_matrix, j)), 2) for j in range(len(users))]],
        products + ["MID"],
        users,
    )

    print("\nМатрица сходства пользователей:")
    print_matrix(similarity, users[:m], users[:m])

    if m < len(users):
        print("\nИсключить: " + ", ".join(users[m:]))

    averages = [mid(row) for row in input_matrix]
    best = max(range(len(products)), key=lambda i: averages[i])

    for a in range(len(users)):
        print()

        if not any(column(input_matrix, a)):
            print(
                f"{users[a]} — новый пользователь, рекомендовать "
                f"{products[best]} (средний рейтинг {averages[best]:g})"
            )

            continue
        if a >= m:
            continue

        u, sim, items = recommend(input_matrix, similarity, a)

        print(f"{users[a]}: наиболее похожий пользователь {users[u]} (сходство {sim:g})")
        print_matrix(
            [[row[a], row[u]] for row in input_matrix],
            products,
            [users[a], users[u]],
        )
        print(
            f"r{users[a]} = {mid(column(input_matrix, a)):g}, "
            f"r{users[u]} = {mid(column(input_matrix, u)):g}"
        )

        if not items:
            print(f"{users[a]}: нечего рекомендовать")

            continue

        for i, rating in items:
            print(f"{users[a]} рекомендовать {products[i]} (прогноз рейтинга {rating:g})")

    return 0

if __name__ == "__main__":
    main()
