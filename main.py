from data.make_students_data import シミュレーション用データを作る
from sim.visualization import シミュレーションを表示する, 残人数グラフを表示する


def 実行する():
    start_steps = {
        "11R": 0,
        "12R": 0,
        "13R": 0,
        "14R": 0,
        "15R": 0,
        "16R": 0,
        "17R": 0,
        "18R": 0,
    }

    grid, doors, final_goal, students = シミュレーション用データを作る(
        start_steps=start_steps
    )

    print("シミュレーション開始")
    print(f"グリッドサイズ: {len(grid)}行 x {len(grid[0])}列")
    print(f"扉数: {len(doors)}")
    print(f"生徒数: {len(students)}")
    print(f"最終出口: {final_goal}")

    history = シミュレーションを表示する(
        grid,
        students,
        max_steps=2000,
        interval=100
    )

    残人数グラフを表示する(history)


if __name__ == "__main__":
    実行する()