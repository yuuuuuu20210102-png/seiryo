import random
from collections import deque
from data.make_seiryo_data import X_MIN, X_MAX, WALL, ROAD, DOOR, FINAL_EXIT, START_SEAT


def 通れるか(grid, x, y, student=None):
    if y < 0 or y >= len(grid):
        return False
    if x < X_MIN or x > X_MAX:
        return False

    gx = x - X_MIN
    cell = grid[y][gx]

    if cell in [ROAD, DOOR, FINAL_EXIT]:
        return True

    if cell == START_SEAT and student is not None and (x, y) == (student["x"], student["y"]):
        return True

    return False


def 候補位置を作る(x, y):
    return [
        (x, y - 1),
        (x - 1, y),
        (x + 1, y),
        (x, y + 1),
    ]


def 占有表を作る(students):
    occupied = {}
    for s in students:
        if s["exited"]:
            continue
        pos = (s["x"], s["y"])
        occupied[pos] = occupied.get(pos, 0) + 1
    return occupied


def そのマスに入れるか(occupied, pos, current_pos):
    if pos == current_pos:
        return True
    return occupied.get(pos, 0) < 3


def 残人数を数える(students):
    return sum(1 for s in students if not s["exited"])


def 距離マップを作る(grid, goal):
    dist = {}
    q = deque()

    dist[goal] = 0
    q.append(goal)

    while q:
        x, y = q.popleft()
        current_d = dist[(x, y)]

        for nx, ny in 候補位置を作る(x, y):
            if ny < 0 or ny >= len(grid):
                continue
            if nx < X_MIN or nx > X_MAX:
                continue
            if (nx, ny) in dist:
                continue

            cell = grid[ny][nx - X_MIN]
            if cell in [ROAD, DOOR, FINAL_EXIT, START_SEAT]:
                dist[(nx, ny)] = current_d + 1
                q.append((nx, ny))

    return dist


def シミュレーション状態を初期化する(grid, students):
    door_goals = sorted({tuple(s["target_door"]) for s in students})
    door_distance_maps = {}

    for door in door_goals:
        door_distance_maps[door] = 距離マップを作る(grid, door)

    final_goal = tuple(students[0]["final_goal"]) if students else None
    final_distance_map = 距離マップを作る(grid, final_goal) if final_goal else {}

    return {
        "door_distance_maps": door_distance_maps,
        "final_distance_map": final_distance_map,
        "current_step": 0,
    }


def 現在の距離マップを得る(student, sim_state):
    if student["passed_door"]:
        return sim_state["final_distance_map"]
    return sim_state["door_distance_maps"][tuple(student["target_door"])]


def 扉前履歴を記録する(student):
    pos = (student["x"], student["y"])
    if not student["passed_door"]:
        if pos not in student["path_history_before_door"]:
            student["path_history_before_door"].append(pos)


def 扉通過処理(student):
    student["passed_door"] = True
    forbidden = set(student["path_history_before_door"])
    forbidden.discard(tuple(student["target_door"]))
    student["forbidden_after_door"] = forbidden


def 現在地を離れたら座席を壁にする(grid, student, old_pos):
    if old_pos == tuple(student["start_pos"]) and (not student["left_start_pos"]):
        ox, oy = old_pos
        grid[oy][ox - X_MIN] = WALL
        student["left_start_pos"] = True


def 混雑停止確率(occupied_count):
    if occupied_count >= 3:
        return 1 / 2
    if occupied_count == 2:
        return 1 / 5
    return 0.0


def 停止するか(student, occupied, current):
    if random.random() < student["stay_prob"]:
        return True

    count_here = occupied.get(current, 1)
    p = 混雑停止確率(count_here)
    if p > 0 and random.random() < p:
        return True

    return False


def 初期移動先を決める(student):
    x, y = student["x"], student["y"]

    # 11Rだけは最初に左へ出る
    if student["class_name"] == "11R":
        return (x - 1, y)

    # それ以外は上へ
    return (x, y - 1)


def 初期座席から出す(grid, student, occupied):
    x, y = student["x"], student["y"]
    current = (x, y)

    gx = x - X_MIN
    if grid[y][gx] != START_SEAT:
        return False

    student["steps_since_start"] += 1

    if student["steps_since_start"] < student["start_wait_steps"] and (not student["must_leave_start"]):
        return False

    if student["steps_since_start"] >= 5:
        student["must_leave_start"] = True

    next_pos = 初期移動先を決める(student)

    if not 通れるか(grid, next_pos[0], next_pos[1], student):
        return False

    if not そのマスに入れるか(occupied, next_pos, current):
        return False

    occupied[current] = occupied.get(current, 0) - 1
    if occupied[current] <= 0:
        occupied.pop(current, None)

    student["x"], student["y"] = next_pos
    occupied[next_pos] = occupied.get(next_pos, 0) + 1

    現在地を離れたら座席を壁にする(grid, student, current)
    return True


def 停滞カウンタを更新する(student, old_pos):
    new_pos = (student["x"], student["y"])
    if new_pos == old_pos:
        student["stuck_steps"] += 1
    else:
        student["stuck_steps"] = 0
    student["last_position"] = new_pos


def 五ステップ以上停滞したときに動かす(grid, student, occupied, dist_map):
    current = (student["x"], student["y"])

    movable = []
    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        if not 通れるか(grid, nx, ny, student):
            continue
        if not そのマスに入れるか(occupied, (nx, ny), current):
            continue

        # 扉を出た後だけ、来た道を使わない
        if student["passed_door"] and (nx, ny) in student["forbidden_after_door"]:
            continue

        if (nx, ny) in dist_map:
            d = dist_map[(nx, ny)]
        else:
            d = 10**9

        movable.append((nx, ny, d))

    if not movable:
        return False

    min_dist = min(d for _, _, d in movable)
    best_candidates = [(x, y) for x, y, d in movable if d == min_dist]
    next_pos = random.choice(best_candidates)

    occupied[current] = occupied.get(current, 0) - 1
    if occupied[current] <= 0:
        occupied.pop(current, None)

    old_pos = current
    student["x"], student["y"] = next_pos
    occupied[next_pos] = occupied.get(next_pos, 0) + 1

    現在地を離れたら座席を壁にする(grid, student, old_pos)
    return True


def 本来進みたい候補を集める(grid, student, occupied, dist_map):
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

        # 扉を出た後だけ、来た道を使わない
        if student["passed_door"] and (nx, ny) in student["forbidden_after_door"]:
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
    for x, y, d in best_distance_candidates:
        if そのマスに入れるか(occupied, (x, y), current):
            enterable.append((x, y, d))

    return enterable


def 本来進みたいマスが三人で満員か(grid, student, occupied, dist_map):
    current = (student["x"], student["y"])
    if current not in dist_map:
        return False

    current_dist = dist_map[current]
    has_better = False
    all_full = True

    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        if not 通れるか(grid, nx, ny, student):
            continue
        if (nx, ny) not in dist_map:
            continue

        # 扉を出た後だけ、来た道を使わない
        if student["passed_door"] and (nx, ny) in student["forbidden_after_door"]:
            continue

        next_dist = dist_map[(nx, ny)]
        if next_dist >= current_dist:
            continue

        has_better = True
        if occupied.get((nx, ny), 0) < 3:
            all_full = False

    return has_better and all_full


def 最終出口到達処理(student, occupied):
    current = (student["x"], student["y"])
    student["exited"] = True

    if current in occupied:
        occupied[current] -= 1
        if occupied[current] <= 0:
            occupied.pop(current, None)


def 一ステップ進める(grid, students, sim_state):
    sim_state["current_step"] += 1

    occupied = 占有表を作る(students)
    active_students = [s for s in students if not s["exited"]]
    random.shuffle(active_students)

    for s in active_students:
        if s["exited"]:
            continue

        if sim_state["current_step"] < s["start_step"]:
            continue

        old_pos_for_stuck = (s["x"], s["y"])
        current = (s["x"], s["y"])

        if 初期座席から出す(grid, s, occupied):
            停滞カウンタを更新する(s, old_pos_for_stuck)
            current = (s["x"], s["y"])
        else:
            if not s["passed_door"]:
                扉前履歴を記録する(s)

            if (not s["passed_door"]) and current == tuple(s["target_door"]):
                扉通過処理(s)

            if s["passed_door"] and current == tuple(s["final_goal"]):
                最終出口到達処理(s, occupied)
                停滞カウンタを更新する(s, old_pos_for_stuck)
                continue

            gx = s["x"] - X_MIN
            current_cell = grid[s["y"]][gx]
            dist_map = 現在の距離マップを得る(s, sim_state)

            did_move = False
            if current_cell != START_SEAT:
                if not 停止するか(s, occupied, current):
                    candidates = 本来進みたい候補を集める(grid, s, occupied, dist_map)

                    if candidates:
                        min_dist = min(p[2] for p in candidates)
                        best_candidates = [(x, y) for x, y, d in candidates if d == min_dist]
                        next_pos = random.choice(best_candidates)

                        occupied[current] = occupied.get(current, 0) - 1
                        if occupied[current] <= 0:
                            occupied.pop(current, None)

                        s["x"], s["y"] = next_pos
                        occupied[next_pos] = occupied.get(next_pos, 0) + 1

                        現在地を離れたら座席を壁にする(grid, s, current)
                        did_move = True

            停滞カウンタを更新する(s, old_pos_for_stuck)

            if (not did_move) and s["stuck_steps"] >= 5:
                current_after = (s["x"], s["y"])
                if not 本来進みたいマスが三人で満員か(grid, s, occupied, dist_map):
                    if 五ステップ以上停滞したときに動かす(grid, s, occupied, dist_map):
                        停滞カウンタを更新する(s, current_after)

            new_current = (s["x"], s["y"])

            if (not s["passed_door"]) and new_current == tuple(s["target_door"]):
                扉通過処理(s)

            if s["passed_door"] and new_current == tuple(s["final_goal"]):
                最終出口到達処理(s, occupied)


def シミュレーションを実行する(grid, students, max_steps=200):
    sim_state = シミュレーション状態を初期化する(grid, students)
    history = [残人数を数える(students)]

    for _ in range(max_steps):
        if 残人数を数える(students) == 0:
            break
        一ステップ進める(grid, students, sim_state)
        history.append(残人数を数える(students))

    return history