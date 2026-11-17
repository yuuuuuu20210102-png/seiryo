import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.animation import FuncAnimation

from data.make_seiryo_data import X_MIN, X_MAX, Y_MIN, Y_MAX
from sim.simulation import 一ステップ進める, 残人数を数える, シミュレーション状態を初期化する
from sim.visualization_common import (
    背景グリッドを作る,
    クラス色辞書を作る,
    生徒座標をまとめる,
    凡例ハンドルを作る,
)


def シミュレーションを表示する(
    grid,
    students,
    max_steps=2000,
    interval=100,
    process_steps_per_frame=1,
):
    cmap = ListedColormap([
        "black",
        "white",
        "red",
        "blue",
        "gray",
    ])

    sim_state = シミュレーション状態を初期化する(grid, students)
    class_color = クラス色辞書を作る(students)

    fig, ax = plt.subplots(figsize=(16, 9))
    current_step = {"value": 0}
    result = {
        "completed": False,
        "total_steps": 0,
        "remaining_students": len(students),
    }

    def update(frame):
        ax.clear()

        if 残人数を数える(students) > 0 and current_step["value"] < max_steps:
            for _ in range(process_steps_per_frame):
                if 残人数を数える(students) == 0:
                    break
                if current_step["value"] >= max_steps:
                    break
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

        (
            single_xs, single_ys, single_cs,
            two_xs, two_ys,
            three_xs, three_ys
        ) = 生徒座標をまとめる(students, class_color)

        ax.scatter(single_xs, single_ys, c=single_cs, s=18, edgecolors="black", linewidths=0.3)
        ax.scatter(two_xs, two_ys, c="pink", s=28, edgecolors="black", linewidths=0.4)
        ax.scatter(three_xs, three_ys, c="red", s=36, edgecolors="black", linewidths=0.4)

        ax.set_title(f"退場シミュレーション step={current_step['value']} 残人数={残人数を数える(students)}")
        ax.set_xticks(range(X_MIN, X_MAX + 1, 2))
        ax.set_yticks(range(Y_MIN, Y_MAX + 1, 1))
        ax.grid(color="gray", linestyle="--", linewidth=0.4)

        ax.legend(
            handles=凡例ハンドルを作る(class_color),
            title="表示",
            bbox_to_anchor=(1.02, 1),
            loc="upper left"
        )

        if 残人数を数える(students) == 0 or current_step["value"] >= max_steps:
            result["completed"] = 残人数を数える(students) == 0
            result["total_steps"] = current_step["value"]
            result["remaining_students"] = 残人数を数える(students)
            ani.event_source.stop()

    ani = FuncAnimation(fig, update, frames=max_steps, interval=interval, repeat=False)
    plt.tight_layout()
    plt.show()

    result["completed"] = 残人数を数える(students) == 0
    result["total_steps"] = current_step["value"]
    result["remaining_students"] = 残人数を数える(students)
    return result