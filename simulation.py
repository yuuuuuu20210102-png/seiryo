import random
from collections import deque, defaultdict
from data.make_seiryo_data import X_MIN, X_MAX, WALL, ROAD, DOOR, FINAL_EXIT, START_SEAT


def 扉座標集合(student):
    target = student["target_door"]
    if isinstance(target, list):
        return {tuple(p) for p in target}
    if isinstance(target, tuple):
        return {tuple(target)}
    return {tuple(target)}


def 通れるか(grid, x, y, student=None):
    if x is None or y is None:
        return False

    if y < 0 or y >= len(grid):
        return False
    if x < X_MIN or x > X_MAX:
        return False

    gx = x - X_MIN
    cell = grid[y][gx]

    if cell == WALL:
        return False

    if cell == START_SEAT:
        if student is not None and student["x"] is not None and student["y"] is not None:
            return (x, y) == (student["x"], student["y"])
        return False

    if cell == FINAL_EXIT:
        return True

    if cell == ROAD:
        return True

    if cell == DOOR:
        if student is None:
            return True

        if student["passed_door"]:
            return True

        return (x, y) in 扉座標集合(student)

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
        if s["x"] is None or s["y"] is None:
            continue
        pos = (s["x"], s["y"])
        occupied[pos] = occupied.get(pos, 0) + 1
    return occupied


def 残人数を数える(students):
    return sum(1 for s in students if not s["exited"])


def そのマスに入れるか(occupied, pos, current_pos, final_goals=None):
    if pos == current_pos:
        return True

    if final_goals is not None and pos in set(final_goals):
        return True

    return occupied.get(pos, 0) < 3


def 複数ゴール距離マップを作る(grid, goals, allowed_doors=None):
    dist = {}
    q = deque()

    goal_set = set(tuple(g) for g in goals)
    allowed_door_set = set(tuple(d) for d in allowed_doors) if allowed_doors is not None else None

    for goal in goal_set:
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

            if cell == WALL:
                continue

            if cell == START_SEAT:
                dist[(nx, ny)] = current_d + 1
                q.append((nx, ny))
                continue

            if cell in [ROAD, FINAL_EXIT]:
                dist[(nx, ny)] = current_d + 1
                q.append((nx, ny))
                continue

            if cell == DOOR:
                if (nx, ny) in goal_set:
                    dist[(nx, ny)] = current_d + 1
                    q.append((nx, ny))
                    continue

                if allowed_door_set is not None and (nx, ny) in allowed_door_set:
                    dist[(nx, ny)] = current_d + 1
                    q.append((nx, ny))
                    continue

    return dist


def シミュレーション状態を初期化する(grid, students):
    door_goal_sets = {tuple(sorted(扉座標集合(s))) for s in students}
    door_distance_maps = {}

    for door_set in door_goal_sets:
        door_cells = [tuple(p) for p in door_set]
        door_distance_maps[door_set] = 複数ゴール距離マップを作る(
            grid,
            door_cells,
            allowed_doors=door_cells
        )

    final_goals = students[0]["final_goals"] if students else []
    all_door_cells = []
    for door_set in door_goal_sets:
        all_door_cells.extend(list(door_set))

    final_distance_map = 複数ゴール距離マップを作る(
        grid,
        final_goals,
        allowed_doors=all_door_cells
    ) if final_goals else {}

    return {
        "door_distance_maps": door_distance_maps,
        "final_distance_map": final_distance_map,
        "current_step": 0,
        "entry_seq_counter": 0,
    }


def 現在の距離マップを得る(student, sim_state):
    if student["passed_door"]:
        return sim_state["final_distance_map"]
    key = tuple(sorted(扉座標集合(student)))
    return sim_state["door_distance_maps"][key]


def 扉前履歴を記録する(student):
    if student["x"] is None or student["y"] is None:
        return
    pos = (student["x"], student["y"])
    if not student["passed_door"] and pos not in student["path_history_before_door"]:
        student["path_history_before_door"].append(pos)


def 扉通過処理(student):
    student["passed_door"] = True
    forbidden = set(student["path_history_before_door"])
    for p in 扉座標集合(student):
        forbidden.discard(p)
    student["forbidden_after_door"] = forbidden


def 現在地を離れたら座席を壁にする(grid, student, old_pos):
    if old_pos is None:
        return

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
    if student["class_name"] == "11R":
        return (x - 1, y)
    return (x, y - 1)


def 停滞カウンタを更新する(student, old_pos):
    if student["x"] is None or student["y"] is None:
        student["stuck_steps"] = 0
        student["last_position"] = (None, None)
        return

    new_pos = (student["x"], student["y"])
    if new_pos == old_pos:
        student["stuck_steps"] += 1
    else:
        student["stuck_steps"] = 0
    student["last_position"] = new_pos


def 最終出口近傍か(student):
    if student["x"] is None or student["y"] is None:
        return False

    x = student["x"]
    y = student["y"]

    for gx, gy in student["final_goals"]:
        if abs(x - gx) <= 2 and abs(y - gy) <= 2:
            return True
    return False


def forbiddenを無視してよいか(student, 救済中=False):
    if not student["passed_door"]:
        return True
    if 救済中:
        return True
    if 最終出口近傍か(student):
        return True
    return False


def 範囲内(x, y, x1, x2, y1, y2):
    return x1 <= x <= x2 and y1 <= y <= y2


def 優先方向を返す(x, y):
    if 範囲内(x, y, -1, 42, 26, 27):
        return "left"

    if 範囲内(x, y, 1, 6, 5, 23):
        return "right"

    if 範囲内(x, y, -3, -2, 11, 25):
        return "up"

    if 範囲内(x, y, -3, -2, 7, 8):
        return "down"
    if 範囲内(x, y, 33, 41, 1, 7):
        return "down"
    if 範囲内(x, y, 7, 8, 2, 24):
        return "down"
    if 範囲内(x, y, 18, 19, 2, 24):
        return "down"
    if 範囲内(x, y, 29, 30, 2, 24):
        return "down"

    return None


def 右上絶対一方通行エリアか(x, y):
    return 33 <= x <= 41 and 1 <= y <= 7


def 方向差分を文字にする(dx, dy):
    if dx == 0 and dy == -1:
        return "up"
    if dx == 0 and dy == 1:
        return "down"
    if dx == -1 and dy == 0:
        return "left"
    if dx == 1 and dy == 0:
        return "right"
    return None


def 逆方向か(dir1, dir2):
    return (dir1, dir2) in {
        ("up", "down"),
        ("down", "up"),
        ("left", "right"),
        ("right", "left"),
    }


def 戻り禁止位置か(student, pos):
    if student.get("swap_block_return_steps", 0) <= 0:
        return False
    return pos == student.get("swap_block_return_pos", None)


def 一本道か(grid, x, y):
    up_blocked = not 通れるか(grid, x, y - 1, None)
    down_blocked = not 通れるか(grid, x, y + 1, None)
    left_blocked = not 通れるか(grid, x - 1, y, None)
    right_blocked = not 通れるか(grid, x + 1, y, None)

    if up_blocked and down_blocked and (not left_blocked) and (not right_blocked):
        return True

    if left_blocked and right_blocked and (not up_blocked) and (not down_blocked):
        return True

    return False


def 一本道お見合いか(grid, proposal_a, proposal_b):
    ax, ay = proposal_a["from"]
    bx, by = proposal_b["from"]
    return 一本道か(grid, ax, ay) or 一本道か(grid, bx, by)


def 絶対一方通行違反か(current_pos, next_pos, student=None):
    cx, cy = current_pos
    nx, ny = next_pos

    if student is not None:
        if (
            student.get("class_name") == "11R"
            and not student.get("left_start_pos", False)
            and current_pos == tuple(student.get("start_pos", current_pos))
            and next_pos == (cx - 1, cy)
        ):
            return False

    current_in = 右上絶対一方通行エリアか(cx, cy)
    next_in = 右上絶対一方通行エリアか(nx, ny)

    if not current_in and not next_in:
        return False

    dx = nx - cx
    dy = ny - cy
    move_dir = 方向差分を文字にする(dx, dy)

    return move_dir != "down"


def 優先通路で逆走衝突しそうか(student, next_pos, students, dist_map):
    if student["x"] is None or student["y"] is None:
        return False

    if student.get("swap_grace_steps", 0) > 0:
        return False

    nx, ny = next_pos
    preferred_dir = 優先方向を返す(nx, ny)
    if preferred_dir is None:
        return False

    dx = nx - student["x"]
    dy = ny - student["y"]
    my_dir = 方向差分を文字にする(dx, dy)
    if my_dir is None:
        return False

    if my_dir == preferred_dir:
        return False

    if not 逆方向か(my_dir, preferred_dir):
        return False

    for other in students:
        if other["exited"]:
            continue
        if other["x"] is None or other["y"] is None:
            continue
        if other["id"] == student["id"]:
            continue

        ox, oy = other["x"], other["y"]
        other_pref = 優先方向を返す(ox, oy)
        if other_pref != preferred_dir:
            continue

        if (ox, oy) not in dist_map:
            continue

        current_dist = dist_map[(ox, oy)]
        for tx, ty in 候補位置を作る(ox, oy):
            if (tx, ty) not in dist_map:
                continue
            if dist_map[(tx, ty)] >= current_dist:
                continue

            odx = tx - ox
            ody = ty - oy
            other_dir = 方向差分を文字にする(odx, ody)

            if other_dir == preferred_dir:
                if preferred_dir in ("up", "down"):
                    if abs(ox - nx) <= 1 and abs(oy - ny) <= 2:
                        return True
                else:
                    if abs(oy - ny) <= 1 and abs(ox - nx) <= 2:
                        return True

    return False


def 最終出口か(student):
    if student["x"] is None or student["y"] is None:
        return False
    return (student["x"], student["y"]) in set(student["final_goals"])


def 最終出口到達処理(student):
    student["exited"] = True
    student["x"] = None
    student["y"] = None
    student["last_position"] = (None, None)
    student["stuck_steps"] = 0
    student["swap_grace_steps"] = 0
    student["swap_block_return_steps"] = 0
    student["swap_block_return_pos"] = None


def 生徒の補助状態を初期化する(students, sim_state):
    for s in students:
        if "cell_entry_step" not in s:
            s["cell_entry_step"] = 0
        if "cell_entry_seq" not in s:
            s["cell_entry_seq"] = sim_state["entry_seq_counter"]
            sim_state["entry_seq_counter"] += 1
        if "swap_grace_steps" not in s:
            s["swap_grace_steps"] = 0
        if "swap_block_return_steps" not in s:
            s["swap_block_return_steps"] = 0
        if "swap_block_return_pos" not in s:
            s["swap_block_return_pos"] = None


def マス内優先キー(student):
    return (
        0 if student.get("swap_grace_steps", 0) > 0 else 1,
        student.get("cell_entry_step", 10**9),
        student.get("cell_entry_seq", 10**9),
        random.random(),
    )


def 提案優先度を計算する(student, from_pos, to_pos):
    fx, fy = from_pos
    tx, ty = to_pos
    dx = tx - fx
    dy = ty - fy
    move_dir = 方向差分を文字にする(dx, dy)
    preferred = 優先方向を返す(tx, ty)

    priority = 0

    if preferred is not None and move_dir == preferred:
        priority += 100

    priority += min(student.get("stuck_steps", 0), 20)

    if student["passed_door"]:
        priority += 10

    if student.get("swap_grace_steps", 0) > 0:
        priority += 200

    return priority


def 初期座席からの提案を作る(grid, student, occupied):
    x, y = student["x"], student["y"]
    current = (x, y)

    gx = x - X_MIN
    if grid[y][gx] != START_SEAT:
        return None

    student["steps_since_start"] += 1

    if student["steps_since_start"] < student["start_wait_steps"] and (not student["must_leave_start"]):
        return None

    if student["steps_since_start"] >= 5:
        student["must_leave_start"] = True

    next_pos = 初期移動先を決める(student)

    if 戻り禁止位置か(student, next_pos):
        return None

    if 絶対一方通行違反か(current, next_pos, student):
        return None

    if not 通れるか(grid, next_pos[0], next_pos[1], student):
        return None

    if not そのマスに入れるか(occupied, next_pos, current, student["final_goals"]):
        return None

    return {
        "student": student,
        "from": current,
        "to": next_pos,
        "priority": 提案優先度を計算する(student, current, next_pos),
        "kind": "start_leave",
    }


def 通常移動候補を集める(grid, student, occupied, dist_map, students):
    current = (student["x"], student["y"])
    if current not in dist_map:
        return []

    current_dist = dist_map[current]
    candidates = []

    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue

        if 絶対一方通行違反か(current, next_pos, student):
            continue

        if not 通れるか(grid, nx, ny, student):
            continue
        if (nx, ny) not in dist_map:
            continue

        if (not forbiddenを無視してよいか(student, 救済中=False)) and ((nx, ny) in student["forbidden_after_door"]):
            continue

        if 優先通路で逆走衝突しそうか(student, next_pos, students, dist_map):
            continue

        next_dist = dist_map[(nx, ny)]
        if next_dist >= current_dist:
            continue

        if not そのマスに入れるか(occupied, next_pos, current, student["final_goals"]):
            continue

        candidates.append((nx, ny, next_dist))

    if not candidates:
        return []

    min_dist = min(d for _, _, d in candidates)
    return [(x, y, d) for x, y, d in candidates if d == min_dist]


def 救済移動候補を集める(grid, student, occupied, dist_map, students):
    current = (student["x"], student["y"])
    previous = student.get("last_position", None)

    movable = []
    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue

        if 絶対一方通行違反か(current, next_pos, student):
            continue

        if not 通れるか(grid, nx, ny, student):
            continue

        if not そのマスに入れるか(occupied, next_pos, current, student["final_goals"]):
            continue

        if 優先通路で逆走衝突しそうか(student, next_pos, students, dist_map):
            continue

        forbidden_hit = (nx, ny) in student["forbidden_after_door"]
        is_previous = (previous is not None) and ((nx, ny) == previous)

        d = dist_map[(nx, ny)] if (nx, ny) in dist_map else 10**9

        movable.append({
            "pos": (nx, ny),
            "dist": d,
            "is_previous": is_previous,
            "forbidden_hit": forbidden_hit,
        })

    if not movable:
        return []

    candidates = [m for m in movable if not m["is_previous"]]
    if not candidates:
        candidates = movable

    non_forbidden = [m for m in candidates if not m["forbidden_hit"]]
    if non_forbidden:
        candidates = non_forbidden

    min_dist = min(m["dist"] for m in candidates)
    best = [m for m in candidates if m["dist"] == min_dist]
    return [m["pos"] for m in best]


def 本来進みたいマスが三人で満員か(grid, student, occupied, dist_map, students):
    current = (student["x"], student["y"])
    if current not in dist_map:
        return False

    current_dist = dist_map[current]
    has_better = False
    all_full = True

    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue

        if 絶対一方通行違反か(current, next_pos, student):
            continue

        if not 通れるか(grid, nx, ny, student):
            continue
        if (nx, ny) not in dist_map:
            continue

        if (not forbiddenを無視してよいか(student, 救済中=False)) and ((nx, ny) in student["forbidden_after_door"]):
            continue

        if 優先通路で逆走衝突しそうか(student, next_pos, students, dist_map):
            continue

        next_dist = dist_map[(nx, ny)]
        if next_dist >= current_dist:
            continue

        has_better = True
        if そのマスに入れるか(occupied, next_pos, current, student["final_goals"]):
            all_full = False

    return has_better and all_full


def 進みたいマスの先が満員詰まりか(grid, student, occupied, dist_map, students):
    current = (student["x"], student["y"])
    if current not in dist_map:
        return False

    current_dist = dist_map[current]
    candidates = []

    for nx, ny in 候補位置を作る(student["x"], student["y"]):
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue

        if 絶対一方通行違反か(current, next_pos, student):
            continue

        if not 通れるか(grid, nx, ny, student):
            continue
        if (nx, ny) not in dist_map:
            continue

        if (not forbiddenを無視してよいか(student, 救済中=False)) and ((nx, ny) in student["forbidden_after_door"]):
            continue

        if 優先通路で逆走衝突しそうか(student, next_pos, students, dist_map):
            continue

        next_dist = dist_map[(nx, ny)]
        if next_dist >= current_dist:
            continue

        candidates.append((nx, ny, next_dist))

    if not candidates:
        return False

    min_dist = min(d for _, _, d in candidates)
    best_candidates = [(x, y) for x, y, d in candidates if d == min_dist]

    checked_any = False

    for bx, by in best_candidates:
        if (bx, by) not in dist_map:
            continue

        base_dist = dist_map[(bx, by)]
        next_steps = []

        for tx, ty in 候補位置を作る(bx, by):
            if not 通れるか(grid, tx, ty, student):
                continue
            if (tx, ty) not in dist_map:
                continue
            if dist_map[(tx, ty)] < base_dist:
                next_steps.append((tx, ty))

        if not next_steps:
            continue

        checked_any = True

        if any(そのマスに入れるか(occupied, p, (bx, by), student["final_goals"]) for p in next_steps):
            return False

    return checked_any


def 前方に長時間停滞中の相手がいるか(student, students):
    x, y = student["x"], student["y"]

    check_positions = [
        (x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1),
        (x, y - 2), (x - 2, y), (x + 2, y), (x, y + 2),
    ]

    for cx, cy in check_positions:
        for other in students:
            if other["exited"]:
                continue
            if other["id"] == student["id"]:
                continue
            if other["x"] == cx and other["y"] == cy:
                if other.get("stuck_steps", 0) >= 1:
                    return True
    return False


def 提案を作る(grid, student, occupied, sim_state, students):
    if student["exited"] or student["x"] is None or student["y"] is None:
        return None

    current = (student["x"], student["y"])

    if not student["passed_door"]:
        扉前履歴を記録する(student)

    if (not student["passed_door"]) and current in 扉座標集合(student):
        扉通過処理(student)

    if student["passed_door"] and 最終出口か(student):
        return {
            "student": student,
            "from": current,
            "to": current,
            "priority": 9999,
            "kind": "exit_now",
        }

    gx = student["x"] - X_MIN
    current_cell = grid[student["y"]][gx]

    if current_cell == START_SEAT:
        return 初期座席からの提案を作る(grid, student, occupied)

    if 停止するか(student, occupied, current):
        return None

    dist_map = 現在の距離マップを得る(student, sim_state)

    normal_candidates = 通常移動候補を集める(grid, student, occupied, dist_map, students)
    if normal_candidates:
        nx, ny, _ = random.choice(normal_candidates)
        return {
            "student": student,
            "from": current,
            "to": (nx, ny),
            "priority": 提案優先度を計算する(student, current, (nx, ny)),
            "kind": "normal",
        }

    if student["stuck_steps"] >= 1:
        if 進みたいマスの先が満員詰まりか(grid, student, occupied, dist_map, students):
            return None

        if (
            not 本来進みたいマスが三人で満員か(grid, student, occupied, dist_map, students)
            or 前方に長時間停滞中の相手がいるか(student, students)
        ):
            rescue_candidates = 救済移動候補を集める(grid, student, occupied, dist_map, students)
            if rescue_candidates:
                nx, ny = random.choice(rescue_candidates)
                return {
                    "student": student,
                    "from": current,
                    "to": (nx, ny),
                    "priority": 提案優先度を計算する(student, current, (nx, ny)) + 80,
                    "kind": "rescue",
                }

    return None


def 正面衝突か(proposal_a, proposal_b):
    return proposal_a["from"] == proposal_b["to"] and proposal_a["to"] == proposal_b["from"]


def 長時間お見合いか(proposal_a, proposal_b):
    sa = proposal_a["student"]
    sb = proposal_b["student"]

    if sa.get("stuck_steps", 0) < 1:
        return False
    if sb.get("stuck_steps", 0) < 1:
        return False

    return proposal_a["from"] == proposal_b["to"] and proposal_a["to"] == proposal_b["from"]


def 同じマス内で誰が動くかを選ぶ(proposals):
    if not proposals:
        return []

    sorted_props = sorted(proposals, key=lambda p: マス内優先キー(p["student"]))
    best_student = sorted_props[0]["student"]

    best_main_key = (
        0 if best_student.get("swap_grace_steps", 0) > 0 else 1,
        best_student.get("cell_entry_step", 10**9),
        best_student.get("cell_entry_seq", 10**9),
    )

    top = []
    for p in sorted_props:
        s = p["student"]
        k = (
            0 if s.get("swap_grace_steps", 0) > 0 else 1,
            s.get("cell_entry_step", 10**9),
            s.get("cell_entry_seq", 10**9),
        )
        if k == best_main_key:
            top.append(p)

    return [random.choice(top)]


def 同一到着先競合を解決する(proposals):
    if not proposals:
        return []

    by_dest = defaultdict(list)
    for p in proposals:
        by_dest[p["to"]].append(p)

    winners = []
    for dest, plist in by_dest.items():
        if len(plist) == 1:
            winners.append(plist[0])
            continue

        max_priority = max(p["priority"] for p in plist)
        top = [p for p in plist if p["priority"] == max_priority]
        winners.append(random.choice(top))

    return winners


def 正面衝突を解決する(grid, proposals):
    if not proposals:
        return [], []

    used = set()
    swaps = []
    normal = []

    for i in range(len(proposals)):
        if i in used:
            continue

        found_swap = False
        for j in range(i + 1, len(proposals)):
            if j in used:
                continue

            if 正面衝突か(proposals[i], proposals[j]):
                if 一本道お見合いか(grid, proposals[i], proposals[j]) or 長時間お見合いか(proposals[i], proposals[j]):
                    swaps.append((proposals[i], proposals[j]))
                    used.add(i)
                    used.add(j)
                    found_swap = True
                    break

                swaps.append((proposals[i], proposals[j]))
                used.add(i)
                used.add(j)
                found_swap = True
                break

        if not found_swap:
            normal.append(proposals[i])

    return swaps, normal


def 提案を解決する(grid, proposals, occupied):
    by_source = defaultdict(list)
    for p in proposals:
        by_source[p["from"]].append(p)

    source_filtered = []
    for src, plist in by_source.items():
        if len(plist) == 1:
            source_filtered.append(plist[0])
        else:
            chosen_list = 同じマス内で誰が動くかを選ぶ(plist)
            source_filtered.extend(chosen_list)

    swaps, others = 正面衝突を解決する(grid, source_filtered)
    winners = 同一到着先競合を解決する(others)

    final_actions = []

    for a, b in swaps:
        final_actions.append({"kind": "swap", "a": a, "b": b})

    final_count = defaultdict(int)
    for pos, count in occupied.items():
        final_count[pos] += count

    random.shuffle(winners)

    for p in winners:
        src = p["from"]
        dst = p["to"]
        student = p["student"]

        if p["kind"] == "exit_now":
            final_actions.append({"kind": "exit_now", "proposal": p})
            continue

        if dst in set(student["final_goals"]):
            final_actions.append({"kind": "move", "proposal": p})
            final_count[src] -= 1
            final_count[dst] += 1
            continue

        if final_count[dst] < 3:
            final_actions.append({"kind": "move", "proposal": p})
            final_count[src] -= 1
            final_count[dst] += 1

    return final_actions


def 生徒を新しいマスへ置く(student, new_pos, sim_state):
    student["x"], student["y"] = new_pos
    student["cell_entry_step"] = sim_state["current_step"]
    student["cell_entry_seq"] = sim_state["entry_seq_counter"]
    sim_state["entry_seq_counter"] += 1


def 提案を適用する(grid, actions, sim_state):
    for action in actions:
        if action["kind"] == "exit_now":
            student = action["proposal"]["student"]
            最終出口到達処理(student)
            continue

        if action["kind"] == "move":
            p = action["proposal"]
            student = p["student"]
            old_pos = p["from"]
            new_pos = p["to"]

            if old_pos != new_pos:
                生徒を新しいマスへ置く(student, new_pos, sim_state)
                現在地を離れたら座席を壁にする(grid, student, old_pos)

            current = (student["x"], student["y"])
            if (not student["passed_door"]) and current in 扉座標集合(student):
                扉通過処理(student)

            if student["passed_door"] and 最終出口か(student):
                最終出口到達処理(student)

        if action["kind"] == "swap":
            a = action["a"]
            b = action["b"]

            sa = a["student"]
            sb = b["student"]

            old_a = a["from"]
            old_b = b["from"]

            new_a = a["to"]
            new_b = b["to"]

            生徒を新しいマスへ置く(sa, new_a, sim_state)
            生徒を新しいマスへ置く(sb, new_b, sim_state)

            sa["swap_grace_steps"] = 1
            sb["swap_grace_steps"] = 1

            sa["swap_block_return_steps"] = 1
            sb["swap_block_return_steps"] = 1
            sa["swap_block_return_pos"] = old_a
            sb["swap_block_return_pos"] = old_b

            現在地を離れたら座席を壁にする(grid, sa, old_a)
            現在地を離れたら座席を壁にする(grid, sb, old_b)

            current_a = (sa["x"], sa["y"])
            current_b = (sb["x"], sb["y"])

            if (not sa["passed_door"]) and current_a in 扉座標集合(sa):
                扉通過処理(sa)
            if (not sb["passed_door"]) and current_b in 扉座標集合(sb):
                扉通過処理(sb)

            if sa["passed_door"] and 最終出口か(sa):
                最終出口到達処理(sa)
            if sb["passed_door"] and 最終出口か(sb):
                最終出口到達処理(sb)


def 補助カウンタを減らす(students):
    for s in students:
        if s.get("swap_grace_steps", 0) > 0:
            s["swap_grace_steps"] -= 1

        if s.get("swap_block_return_steps", 0) > 0:
            s["swap_block_return_steps"] -= 1
            if s["swap_block_return_steps"] <= 0:
                s["swap_block_return_pos"] = None


def 一ステップ進める(grid, students, sim_state):
    sim_state["current_step"] += 1

    生徒の補助状態を初期化する(students, sim_state)

    occupied = 占有表を作る(students)
    active_students = [s for s in students if (not s["exited"]) and s["x"] is not None and s["y"] is not None]
    random.shuffle(active_students)

    old_positions = {}
    proposals = []

    for s in active_students:
        old_positions[s["id"]] = (s["x"], s["y"])

        if sim_state["current_step"] < s["start_step"]:
            continue

        proposal = 提案を作る(grid, s, occupied, sim_state, students)
        if proposal is not None:
            proposals.append(proposal)

    actions = 提案を解決する(grid, proposals, occupied)
    提案を適用する(grid, actions, sim_state)

    for s in students:
        if s["exited"]:
            停滞カウンタを更新する(s, old_positions.get(s["id"], None))
            continue

        if s["x"] is None or s["y"] is None:
            停滞カウンタを更新する(s, old_positions.get(s["id"], None))
            continue

        old_pos = old_positions.get(s["id"], (s["x"], s["y"]))
        停滞カウンタを更新する(s, old_pos)

    補助カウンタを減らす(students)


def シミュレーションを実行する(grid, students, max_steps=200):
    sim_state = シミュレーション状態を初期化する(grid, students)
    history = [残人数を数える(students)]

    for _ in range(max_steps):
        if 残人数を数える(students) == 0:
            break
        一ステップ進める(grid, students, sim_state)
        history.append(残人数を数える(students))

    return history