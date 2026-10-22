import argparse
import csv
import textwrap
from pathlib import Path

Matrix = list[list[float | int]]

DEFAULT_MATRIX = "5 4 5 0 5, 5 5 5 0 5, 5 4 4 0 5, 4 3 4 0 3, 0 0 0 0 0, 4 5 5 0 1"


def mid(row: list[float | int]) -> float:
    rated = [v for v in row if v != 0]

    return sum(rated) / len(rated) if rated else 0


def filter_matrix(
    matrix: Matrix,
    products: list[str],
    users: list[str],
    min_rating: float,
) -> tuple[Matrix, list[str], list[str]]:
    active = [j for j in range(len(users)) if any(row[j] != 0 for row in matrix)]
    keep = [i for i, row in enumerate(matrix) if any(row) and mid(row) >= min_rating]

    return (
        [[matrix[i][j] for j in active] for i in keep],
        [products[i] for i in keep],
        [users[j] for j in active],
    )


def to_coo(matrix: Matrix) -> tuple[list, list[int], list[int]]:
    value, row, col = [], [], []

    for i, r in enumerate(matrix):
        for j, v in enumerate(r):
            if v != 0:
                value.append(v)
                row.append(i)
                col.append(j)

    return value, row, col


def to_csr(matrix: Matrix) -> tuple[list, list[int], list[int]]:
    value, col, row_index = [], [], [0]

    for r in matrix:
        for j, v in enumerate(r):
            if v != 0:
                value.append(v)
                col.append(j)
        row_index.append(len(value))

    return value, col, row_index


def to_ellpack(matrix: Matrix) -> tuple[Matrix, Matrix]:
    nonzero = [[(j, v) for j, v in enumerate(r) if v != 0] for r in matrix]
    width = max((len(r) for r in nonzero), default=0)

    value = [[v for _, v in r] + [0] * (width - len(r)) for r in nonzero]
    column: Matrix = [[float(j) for j, _ in r] + [0] * (width - len(r)) for r in nonzero]

    return value, column


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


def print_array(name: str, values: list) -> None:
    print(f"{name:<9}: " + " ".join(f"{v:g}" for v in values))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pz3",
        usage="%(prog)s [options]",
        description= \
            "Принимает на вход матрицу предпочтений (строки — товары, " \
            "столбцы — пользователи), исключает товары с «нулевым» и низким " \
            "рейтингом, «неактивных» пользователей и выводит результат " \
            "в форматах хранения разреженных матриц COO, CSR и ELLPACK. " \
            "Если флаг --csv отсутствует, на вход подается двумерная матрица, " \
            "разделенная запятыми между строками и пробелом между столбцами.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            пример:
                # матрица предпочтений из задания
                %(prog)s

                # считать матрицу из CSV-файла
                %(prog)s -c example.csv --min-rating 4

                # передать матрицу как аргумент
                %(prog)s "5 4 0, 0 0 0, 3 5 0" --min-rating 4
        """),
    )

    parser.add_argument("input_matrix", nargs="?", default=DEFAULT_MATRIX)
    parser.add_argument("-c", "--csv")
    parser.add_argument("--min-rating", default="4")

    args = parser.parse_args()

    input_matrix: Matrix = []

    try:
        min_rating = float(args.min_rating)
    except ValueError:
        print("incorrect min rating value")

        return -1

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

    products = [f"P{i + 1}" for i in range(len(input_matrix))]
    users = [f"U{j + 1}" for j in range(len(input_matrix[0]))]

    print("Матрица предпочтений 0:")
    print_matrix(
        [row + [round(mid(row), 2)] for row in input_matrix],
        products,
        users + ["MID"],
    )

    matrix, products, users = filter_matrix(input_matrix, products, users, min_rating)

    print("\nМатрица предпочтений 1:")
    if not matrix:
        print("после фильтрации матрица пуста")

        return 0
    print_matrix(matrix, products, users)

    value, row, col = to_coo(matrix)
    print("\nCOO:")
    print_array("Value", value)
    print_array("Row", row)
    print_array("Col", col)

    value, col, row_index = to_csr(matrix)
    print("\nCSR:")
    print_array("Value", value)
    print_array("Col", col)
    print_array("RowIndex", row_index)

    value, column = to_ellpack(matrix)
    print("\nELLPACK:")
    print("Value:")
    print_matrix(value, products)
    print("Column:")
    print_matrix(column, products)

    return 0

if __name__ == "__main__":
    main()
