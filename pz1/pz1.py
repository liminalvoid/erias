import argparse
import csv
import textwrap
from pathlib import Path


class VectorsDifferentLengthError(Exception):
    pass


Matrix = list[list[float | int]]


def calculate_cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise VectorsDifferentLengthError("Переданные векторы разные по размеру")

    sum_product = sum([a[i] * b[i] for i in range(len(a))])
    sqrt_sum_a = sum([a[i] ** 2 for i in range(len(a))]) ** 0.5
    sqrt_sum_b = sum([b[i] ** 2 for i in range(len(b))]) ** 0.5

    return sum_product / (sqrt_sum_a * sqrt_sum_b)


def transpose_matrix(matrix: Matrix):
    n = len(matrix)
    m = len(matrix[n - 1])
    transposed: Matrix = [[0] * n for i in range(m)]

    for i in range(m):
        for j in range(n):
            transposed[i][j] = matrix[j][i]

    return transposed


def get_closest_vectors_and_similarity(matrix: Matrix) -> tuple[tuple[int, int], float]:
    highest_similarity = 0
    closest_vectors = (0, 0)
    n = len(matrix)

    for i in range(n):
        for j in range(i + 1, n):
            current_similarity = calculate_cosine_similarity(matrix[i], matrix[j])

            if current_similarity > highest_similarity:
                highest_similarity = current_similarity
                closest_vectors = (i, j)

    return (closest_vectors, highest_similarity)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pz1",
        usage="%(prog)s [options]",
        description= \
            "Принимает на вход двумерную матрицу и находит самые близкие вектора. " \
            "Если флаг --csv отсутствует, на вход подается двумерная матрица, " \
            "разделенная запятыми между строками и пробелом между столбцами.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            пример:
                # считать матрицу из CSV-файла
                %(prog)s -c example.csv

                # передать матрицу как аргумент
                %(prog)s "1 0 2, 2 3 1, 2 3 1"
        """),
    )

    parser.add_argument("input_matrix", nargs="?")
    parser.add_argument("-c", "--csv")

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
                input_matrix.append(list(map(int, row)))
    else:
        rows = args.input_matrix.split(",")

        for r in rows:
            input_matrix.append(list(map(int, r.split())))

    closest_products, highest_product_similarity = get_closest_vectors_and_similarity(input_matrix)

    transposed: Matrix = transpose_matrix(input_matrix)
    closest_users, highest_user_similarity = get_closest_vectors_and_similarity(transposed)

    print(
        f"Самые близкие продукты – {closest_products[0] + 1} и {closest_products[1] + 1}",
        f"с подобием, равным {highest_product_similarity:.4f}",
    )

    print(
        f"Самые близкие пользователи – {closest_users[0] + 1} и {closest_users[1] + 1}",
        f"с подобием, равным {highest_user_similarity:.4f}",
    )

    return 0


if __name__ == "__main__":
    main()
