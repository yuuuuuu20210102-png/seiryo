from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt

X_MIN = -4
X_MAX = 42
Y_MIN = 0
Y_MAX = 30

WIDTH = X_MAX - X_MIN + 1
HEIGHT = Y_MAX - Y_MIN + 1

WALL = 0
ROAD = 1
DOOR = 2
FINAL_EXIT = 3
START_SEAT = 4


def wx(x):
    return x - X_MIN


def in_bounds(x, y):
    return X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX


def set_cell(grid, x, y, value):
    if in_bounds(x, y):
        grid[y][wx(x)] = value


def get_cell(grid, x, y):
    if in_bounds(x, y):
        return grid[y][wx(x)]
    return None


def create_hall_model():
    base_width = 43
    base_height = 31
    base = [[0 for _ in range(base_width)] for _ in range(base_height)]

    # ホール内部
    for y in range(1, 26):
        for x in range(1, 42):
            base[y][x] = ROAD

    # 左ブロック
    for y in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
        for x in range(1, 7):
            base[y][x] = WALL
    for x in range(1, 6):
        base[24][x] = WALL

    # 中央左ブロック
    for y in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
        for x in range(9, 18):
            base[y][x] = WALL
    for x in range(9, 17):
        base[24][x] = WALL

    # 中央右ブロック
    for y in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
        for x in range(20, 29):
            base[y][x] = WALL
    for x in range(20, 28):
        base[24][x] = WALL

    # 右ブロック下段
    for x in [31, 32]:
        base[16][x] = WALL
    for x in range(31, 35):
        base[18][x] = WALL
    for x in range(31, 37):
        base[20][x] = WALL
    for x in range(31, 39):
        base[22][x] = WALL
    for x in range(32, 38):
        base[24][x] = WALL

    # 右ブロック上段
    for y in range(1, 8):
        for x in [32, 34, 36, 38]:
            base[y][x] = WALL
    for y in range(9, 13):
        base[y][32] = WALL
    for y in range(9, 14):
        base[y][34] = WALL
    for y in range(9, 16):
        base[y][36] = WALL
    for y in range(9, 19):
        base[y][38] = WALL

    # 下側の壁
    for x in range(0, 42):
        base[25][x] = WALL

    # 下側外通路
    for x in range(2, 42):
        base[26][x] = ROAD
        base[27][x] = ROAD

    # 拡張グリッドへコピー
    grid = [[WALL for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for y in range(base_height):
        for x in range(base_width):
            set_cell(grid, x, y, base[y][x])

    # 外側通路
    for y in range(1, 7):
        set_cell(grid, 0, y, ROAD)

    for y in range(5, 10):
        set_cell(grid, 0, y, WALL)

    for y in range(1, 9):
        set_cell(grid, -1, y, ROAD)

    for y in range(2, 8):
        set_cell(grid, -2, y, ROAD)

    set_cell(grid, -2, 8, ROAD)
    set_cell(grid, -2, 9, ROAD)
    set_cell(grid, -2, 10, ROAD)

    for y in range(10, 28):
        set_cell(grid, -3, y, ROAD)

    for y in range(1, 6):
        set_cell(grid, -3, y, ROAD)
    set_cell(grid, -2, 1, ROAD)

    for x in range(-3, 43):
        set_cell(grid, x, 26, ROAD)
        set_cell(grid, x, 27, ROAD)

    # (-3,6~8) を通路化
    for y in range(6, 9):
        set_cell(grid, -3, y, ROAD)

    # (-2,11~25) を通路化
    for y in range(11, 26):
        set_cell(grid, -2, y, ROAD)

    # (-1,5~8) に壁を設置
    for y in range(5, 9):
        set_cell(grid, -1, y, WALL)

    # 今回追加: (-3,9) の壁を削除して通路化
    set_cell(grid, -3, 9, ROAD)

    # final exit
    final_goals = [(-4, 10), (-4, 9)]

    # x=-4 は final_goals 以外壁
    for y in range(Y_MIN, Y_MAX + 1):
        set_cell(grid, -4, y, WALL)
    for gx, gy in final_goals:
        set_cell(grid, gx, gy, FINAL_EXIT)

    # 同じ名前の扉は1つの扉として扱う
    doors = {
        "1": [(7, 25), (8, 25)],
        "2": [(18, 25), (19, 25)],
        "3": [(29, 25), (30, 25)],
        "4": [(41, 25), (40, 25)],
        "5": [(-3, 8), (-2, 8)],
    }

    # 扉を反映
    for door_cells in doors.values():
        for x, y in door_cells:
            set_cell(grid, x, y, DOOR)

    return grid, doors, final_goals


def plot_grid_only(grid, title="Hall Model"):
    cmap = ListedColormap(["black", "white", "red", "blue", "gray"])

    plt.figure(figsize=(16, 9))
    plt.imshow(
        grid,
        cmap=cmap,
        origin="upper",
        extent=[X_MIN - 0.5, X_MAX + 0.5, Y_MAX + 0.5, Y_MIN - 0.5]
    )
    plt.title(title)
    plt.xticks(range(X_MIN, X_MAX + 1, 2))
    plt.yticks(range(Y_MIN, Y_MAX + 1, 1))
    plt.grid(color="gray", linestyle="--", linewidth=0.4)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    grid, doors, final_goals = create_hall_model()
    plot_grid_only(grid, "Hall Only")