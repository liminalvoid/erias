import argparse
import csv
import textwrap
from pathlib import Path

Matrix = list[list[float | int]]


def find_max(matrix: Matrix) -> tuple[float, int, int]:
    max_val = float("-inf")
    i_max, j_max = -1, -1

    for i in range(len(matrix)):
        for j in range(i + 1, len(matrix)):
            if matrix[i][j] > max_val:
                max_val = matrix[i][j]
                i_max, j_max = i, j

    return max_val, i_max, j_max


def print_matrix(matrix: Matrix, labels: list[str] | None = None) -> None:
    if labels is None:
        labels = [f"U{i + 1}" for i in range(len(matrix))]

    cells = [[f"{v:g}" for v in row] for row in matrix]
    width = max(len(s) for s in labels + [c for row in cells for c in row])
    label_width = max(len(s) for s in labels)

    print(" " * label_width + " | " + " ".join(s.rjust(width) for s in labels))
    print("-" * label_width + "-+-" + "-".join("-" * width for _ in labels))

    for label, row in zip(labels, cells):
        print(label.ljust(label_width) + " | " + " ".join(c.rjust(width) for c in row))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pz2",
        usage="%(prog)s [options]",
        description= \
            "Принимает на вход двумерную матрицу расстояний и находит максимум. " \
            "Если флаг --csv отсутствует, на вход подается двумерная матрица, " \
            "разделенная запятыми между строками и пробелом между столбцами.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            пример:
                # считать матрицу из CSV-файла
                %(prog)s -c example.csv --cluster-size 0.74

                # передать матрицу как аргумент
                %(prog)s "1 0 2, 2 3 1, 2 3 1" --cluster-size 0.74

                # передать только элементы над главной диагональю
                # (для упрощения ручного ввода матрицы, в примере
                # матрица размерностью 5x5)
                %(prog)s -s "1 3 4 3, 5 5 3, 5 8, 2" --cluster-size 0.74
        """),
    )

    parser.add_argument("input_matrix", nargs="?")
    parser.add_argument("-c", "--csv")
    parser.add_argument("-s", "--simplified")
    parser.add_argument("--cluster-size")

    args = parser.parse_args()

    input_matrix: Matrix = []

    if not args.cluster_size:
        print("no cluster size given")

        return -1

    try:
        cluster_size = float(args.cluster_size)
    except ValueError:
        print("incorrect cluster size value")

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
    elif args.simplified:
        rows = [[float(c) for c in r.split()] for r in args.simplified.split(",")]
        n, m = len(rows) + 1, len(rows[0]) + 1
        input_matrix = [[0] * m for _ in range(m)]

        for i in range(n):
            for j in range(i + 1, m):
                input_matrix[i][j] = rows[i][j - (i + 1)]
    else:
        rows = args.input_matrix.split(",")

        for r in rows:
            input_matrix.append(list(map(float, r.split())))

    labels = [[f"U{k + 1}"] for k in range(len(input_matrix))]

    while len(input_matrix) > 1:
        max_val, i, j = find_max(input_matrix)
        if max_val < cluster_size:
            break

        for k in range(len(input_matrix)):
            if k not in (i, j):
                a, b = sorted((i, k))
                c, d = sorted((j, k))
                input_matrix[a][b] = max(input_matrix[a][b], input_matrix[c][d])

        for row in input_matrix:
            row.pop(j)
        input_matrix.pop(j)
        labels[i] += labels.pop(j)

    print_matrix(input_matrix, [", ".join(l) for l in labels])

    return 0

if __name__ == "__main__":
    main()

