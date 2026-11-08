import random
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from data.make_seiryo_data import (
    START_SEAT,
    set_cell,
    create_hall_model,
    X_MIN, X_MAX, Y_MIN, Y_MAX
)


def make_rectangle_cells(x1, x2, y1, y2):
    cells = []
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            cells.append((x, y))
    return cells


def combine_rectangles(rectangles):
    cells = []
    for x1, x2, y1, y2 in rectangles:
        cells += make_rectangle_cells(x1, x2, y1, y2)
    return cells


def デフォルト扉割り当てを作る(doors):
    return {
        "11R": doors["5"],
        "12R": doors["5"],
        "13R": doors["5"],
        "14R": doors["5"],
        "15R": doors["5"],
        "16R": doors["5"],
        "17R": doors["5"],
        "18R": doors["5"],
    }


def デフォルト退場開始ステップを作る():
    return {
        "11R": 0,
        "12R": 0,
        "13R": 0,
        "14R": 0,
        "15R": 0,
        "16R": 0,
        "17R": 0,
        "18R": 0,
    }


def クラスブロック定義を作る():
    return {
        "11R": combine_rectangles([
            (32, 32, 3, 7), (34, 34, 3, 7), (36, 36, 3, 7), (38, 38, 3, 7),
            (32, 32, 9, 12), (34, 34, 9, 13), (36, 36, 9, 15), (38, 38, 9, 15)
        ]),
        "12R": combine_rectangles([
            (22, 28, 2, 2), (22, 28, 4, 4), (22, 28, 6, 6), (22, 28, 8, 8),
            (22, 28, 10, 10), (22, 28, 12, 12), (22, 28, 14, 14)
        ]),
        "13R": combine_rectangles([
            (20, 22, 2, 2), (20, 22, 4, 4), (20, 22, 6, 6), (20, 22, 8, 8),
            (20, 22, 10, 10), (20, 22, 12, 12), (20, 22, 14, 14),
            (15, 17, 2, 2), (15, 17, 4, 4), (15, 17, 6, 6), (15, 17, 8, 8),
            (15, 17, 10, 10), (15, 17, 12, 12), (15, 17, 14, 14)
        ]),
        "14R": combine_rectangles([
            (9, 14, 2, 2), (9, 14, 4, 4), (9, 14, 6, 6), (9, 14, 8, 8),
            (9, 14, 10, 10), (9, 14, 12, 12), (9, 14, 14, 14)
        ]),
        "15R": combine_rectangles([
            (1, 6, 6, 6), (1, 6, 8, 8), (1, 6, 10, 10), (1, 6, 12, 12),
            (1, 6, 14, 14), (1, 6, 16, 16), (1, 6, 18, 18)
        ]),
        "16R": combine_rectangles([
            (1, 6, 20, 20), (1, 6, 22, 22), (1, 5, 24, 24),
            (9, 13, 16, 16), (9, 13, 18, 18), (9, 13, 20, 20),
            (9, 13, 22, 22), (9, 13, 24, 24)
        ]),
        "17R": combine_rectangles([
            (14, 17, 16, 16), (14, 17, 18, 18), (14, 17, 20, 20), (14, 17, 22, 22),
            (20, 24, 16, 16), (20, 24, 18, 18), (20, 24, 20, 20),
            (20, 24, 22, 22), (20, 24, 24, 24)
        ]),
        "18R": combine_rectangles([
            (25, 28, 16, 16), (25, 28, 18, 18), (25, 28, 20, 20), (25, 28, 22, 22),
            (31, 32, 16, 16), (31, 34, 18, 18), (31, 36, 20, 20), (31, 38, 22, 22),
            (32, 37, 24, 24)
        ])
    }


def 個体停止確率を作る():
    候補 = [
        1 / 100,
        1 / 80,
        1 / 60,
        1 / 40,
        1 / 30,
        1 / 20,
        1 / 10,
        1 / 8,
        1 / 5,
    ]
    return random.choice(候補)


def add_students(students, grid, cells, target_door, final_goals, class_name, start_step, start_id):
    sid = start_id
    for x, y in cells:
        set_cell(grid, x, y, START_SEAT)

        students.append({
            "id": sid,
            "x": x,
            "y": y,
            "start_pos": (x, y),
            "left_start_pos": False,
            "target_door": target_door,
            "final_goals": final_goals,
            "passed_door": False,
            "class_name": class_name,
            "exited": False,
            "start_step": start_step,
            "path_history_before_door": [(x, y)],
            "forbidden_after_door": set(),
            "stay_prob": 個体停止確率を作る(),
            "start_wait_steps": random.randint(1, 5),
            "steps_since_start": 0,
            "must_leave_start": False,
            "last_position": (x, y),
            "stuck_steps": 0,
        })
        sid += 1
    return sid


def create_students(grid, doors, final_goals, assignment=None, start_steps=None):
    if assignment is None:
        assignment = デフォルト扉割り当てを作る(doors)

    if start_steps is None:
        start_steps = デフォルト退場開始ステップを作る()

    students = []
    sid = 0
    class_blocks = クラスブロック定義を作る()

    for class_name, cells in class_blocks.items():
        target_door = assignment[class_name]
        start_step = start_steps.get(class_name, 0)

        sid = add_students(
            students,
            grid,
            cells,
            target_door,
            final_goals,
            class_name,
            start_step,
            sid
        )

    return students


def シミュレーション用データを作る(assignment=None, start_steps=None):
    grid, doors, final_goals = create_hall_model()

    if assignment is None:
        assignment = デフォルト扉割り当てを作る(doors)

    if start_steps is None:
        start_steps = デフォルト退場開始ステップを作る()

    students = create_students(grid, doors, final_goals, assignment, start_steps)
    return grid, doors, final_goals, students


def plot_students_on_grid(grid, students, title="Student Placement"):
    cmap = ListedColormap(["black", "white", "red", "blue", "gray"])

    plt.figure(figsize=(16, 9))
    plt.imshow(
        grid,
        cmap=cmap,
        origin="upper",
        extent=[X_MIN - 0.5, X_MAX + 0.5, Y_MAX + 0.5, Y_MIN - 0.5]
    )

    palette = ["blue", "green", "orange", "purple", "cyan", "magenta", "yellow", "brown"]
    class_color = {}
    color_idx = 0

    xs, ys, cs = [], [], []
    for s in students:
        xs.append(s["x"])
        ys.append(s["y"])
        cname = s["class_name"]
        if cname not in class_color:
            class_color[cname] = palette[color_idx % len(palette)]
            color_idx += 1
        cs.append(class_color[cname])

    plt.scatter(xs, ys, c=cs, s=20, edgecolors="black")
    plt.title(title)
    plt.xticks(range(X_MIN, X_MAX + 1, 2))
    plt.yticks(range(Y_MIN, Y_MAX + 1, 1))
    plt.grid(color="gray", linestyle="--", linewidth=0.4)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    grid, doors, final_goals = create_hall_model()
    assignment = デフォルト扉割り当てを作る(doors)
    start_steps = デフォルト退場開始ステップを作る()
    students = create_students(grid, doors, final_goals, assignment, start_steps)
    plot_students_on_grid(grid, students, "Students Only")