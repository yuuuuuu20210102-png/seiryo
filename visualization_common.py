import copy
import matplotlib.pyplot as plt


plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


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


def 占有人数を集計する(students):
    counts = {}
    for s in students:
        if s["exited"]:
            continue
        if s["x"] is None or s["y"] is None:
            continue
        pos = (s["x"], s["y"])
        counts[pos] = counts.get(pos, 0) + 1
    return counts


def 生徒座標をまとめる(students, class_color):
    single_xs = []
    single_ys = []
    single_cs = []

    two_xs = []
    two_ys = []

    three_xs = []
    three_ys = []

    counts = 占有人数を集計する(students)
    added_multi = set()

    for s in students:
        if s["exited"]:
            continue
        if s["x"] is None or s["y"] is None:
            continue

        x = s["x"]
        y = s["y"]
        pos = (x, y)
        count = counts.get(pos, 1)

        if count == 1:
            single_xs.append(x)
            single_ys.append(y)
            single_cs.append(class_color.get(s["class_name"], "blue"))
        elif count == 2:
            if pos not in added_multi:
                two_xs.append(x)
                two_ys.append(y)
                added_multi.add(pos)
        else:
            if pos not in added_multi:
                three_xs.append(x)
                three_ys.append(y)
                added_multi.add(pos)

    return single_xs, single_ys, single_cs, two_xs, two_ys, three_xs, three_ys


def 凡例ハンドルを作る(class_color):
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

    handles.append(
        plt.Line2D(
            [0], [0],
            marker="o",
            color="w",
            markerfacecolor="pink",
            markeredgecolor="black",
            markersize=7,
            label="2人マス"
        )
    )
    handles.append(
        plt.Line2D(
            [0], [0],
            marker="o",
            color="w",
            markerfacecolor="red",
            markeredgecolor="black",
            markersize=7,
            label="3人マス"
        )
    )

    return handles