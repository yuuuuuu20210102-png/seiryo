import copy
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.animation import FuncAnimation

from data.make_students_data import シミュレーション用データを作る
from data.make_seiryo_data import X_MIN, X_MAX, Y_MIN, Y_MAX
from sim.simulation import (
    シミュレーション状態を初期化する,
    一ステップ進める,
    残人数を数える,
    現在の距離マップを得る,
    通れるか,
    候補位置を作る,
    占有表を作る,
    そのマスに入れるか,
    forbiddenを無視してよいか,
)


def 背景グリッドを作る(grid):
    return copy.deepcopy(grid)


def クラス色辞書を作る(students):
    palette = [
        "blue", "green", "orange", "purple",
        "cyan", "magenta", "yellow", "brown",
        "olive", "navy"
    ]

    class_names = sorted(list({s["class_name"] for s in students}))
    class_color = {}

    for i, name in enumerate(class_names):
        class_color[name] = palette[i % len(palette)]

    return class_color


def 本来進みたい候補を確認用に集める(grid, student, occupied, dist_map):
    if student["x"] is None or student["y"] is None:
        return []

    current = (student["x"], student["y"])
    if current not in dist_map:
        return []

    current_dist = dist_map[current]
    all_better = []

    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        if not 通れるか(grid, nx, ny, student):
            continue
        if (nx, ny) not in dist_map:
            continue

        if (not forbiddenを無視してよいか(student, 救済中=False)) and ((nx, ny) in student["forbidden_after_door"]):
            continue

        next_dist = dist_map[(nx, ny)]
        if next_dist >= current_dist:
            continue

        all_better.append((nx, ny, next_dist))

    if not all_better:
        return []

    min_dist = min(d for _, _, d in all_better)
    best_distance_candidates = [(x, y, d) for x, y, d in all_better if d == min_dist]

    enterable = []
    current_pos = (student["x"], student["y"])
    for x, y, d in best_distance_candidates:
        if そのマスに入れるか(occupied, (x, y), current_pos, student["final_goals"]):
            enterable.append((x, y, d))

    return enterable


def 生徒と矢印を描く(ax, grid, students, sim_state, class_color):
    occupied = 占有表を作る(students)

    for s in students:
        if s["exited"]:
            continue
        if s["x"] is None or s["y"] is None:
            continue

        x, y = s["x"], s["y"]
        color = class_color.get(s["class_name"], "blue")

        # 生徒本体
        ax.scatter([x], [y], c=[color], s=18, edgecolors="black", linewidths=0.3, zorder=3)

        # 初期座席からまだ出ていない生徒は、最初の移動方向を矢印表示
        dist_map = 現在の距離マップを得る(s, sim_state)
        candidates = 本来進みたい候補を確認用に集める(grid, s, occupied, dist_map)

        if not candidates:
            continue

        nx, ny, _ = candidates[0]
        dx = nx - x
        dy = ny - y

        ax.arrow(
            x, y,
            dx * 0.6, dy * 0.6,
            head_width=0.18,
            head_length=0.18,
            fc=color,
            ec=color,
            length_includes_head=True,
            zorder=4
        )


def シミュレーションを矢印付きで表示する(max_steps=500, interval=200):
    grid, doors, final_goals, students = シミュレーション用データを作る()
    sim_state = シミュレーション状態を初期化する(grid, students)
    class_color = クラス色辞書を作る(students)

    cmap = ListedColormap([
        "black",   # 壁
        "white",   # 通路
        "red",     # 扉
        "blue",    # 最終出口
        "gray",    # 初期座席
    ])

    fig, ax = plt.subplots(figsize=(16, 9))
    current_step = {"value": 0}

    def update(frame):
        ax.clear()

        if 残人数を数える(students) > 0 and current_step["value"] < max_steps:
            一ステップ進める(grid, students, sim_state)
            current_step["value"] += 1

        view = 背景グリッドを作る(grid)

        ax.imshow(
            view,
            cmap=cmap,
            origin="upper",
            vmin=0,
            vmax=4,
            extent=[X_MIN - 0.5, X_MAX + 0.5, Y_MAX + 0.5, Y_MIN - 0.5]
        )

        生徒と矢印を描く(ax, grid, students, sim_state, class_color)

        ax.set_title(
            f"進みたい方向の矢印表示 step={current_step['value']} 残人数={残人数を数える(students)}"
        )
        ax.set_xticks(range(X_MIN, X_MAX + 1, 2))
        ax.set_yticks(range(Y_MIN, Y_MAX + 1, 1))
        ax.grid(color="gray", linestyle="--", linewidth=0.4)

        handles = []
        for class_name, color in class_color.items():
            handles.append(
                plt.Line2D(
                    [0], [0],
                    marker="o",
                    color="w",
                    markerfacecolor=color,
                    markeredgecolor="black",
                    markersize=6,
                    label=class_name
                )
            )
        ax.legend(handles=handles, title="クラス", bbox_to_anchor=(1.02, 1), loc="upper left")

        if 残人数を数える(students) == 0 or current_step["value"] >= max_steps:
            ani.event_source.stop()

    ani = FuncAnimation(fig, update, frames=max_steps, interval=interval, repeat=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    シミュレーションを矢印付きで表示する()