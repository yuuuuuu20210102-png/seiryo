import random
from collections import deque
from data.make_seiryo_data import X_MIN, X_MAX, WALL, ROAD, DOOR, FINAL_EXIT, START_SEAT


NEIGHBOR_DELTAS = ((0, -1), (-1, 0), (1, 0), (0, 1))

# True にすると各ステップでルール破綻チェックを行う
DEBUG_VALIDATE_SIMULATION = False


def 扉座標集合(student):
    target_set = student.target_door_set
    if target_set is not None:
        return target_set

    target = student.target_door
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
        if student is not None and student.x is not None and student.y is not None:
            return (x, y) == (student.x, student.y)
        return False

    if cell == FINAL_EXIT:
        return True

    if cell == ROAD:
        return True

    if cell == DOOR:
        if student is None:
            return True
        if student.passed_door:
            return True
        return (x, y) in 扉座標集合(student)

    return False


def 候補位置を作る(x, y):
    return [(x + dx, y + dy) for dx, dy in NEIGHBOR_DELTAS]


def 位置索引と占有表を作る(students):
    pos_index = {}
    occupied = {}

    for s in students:
        if s.exited:
            continue
        if s.x is None or s.y is None:
            continue

        pos = (s.x, s.y)
        lst = pos_index.get(pos)
        if lst is None:
            pos_index[pos] = [s]
            occupied[pos] = 1
        else:
            lst.append(s)
            occupied[pos] += 1

    return pos_index, occupied


def 占有表を作る(students):
    occupied = {}
    for s in students:
        if s.exited:
            continue
        if s.x is None or s.y is None:
            continue
        pos = (s.x, s.y)
        occupied[pos] = occupied.get(pos, 0) + 1
    return occupied


def 残人数を数える(students):
    return sum(1 for s in students if not s.exited)


def 現在残人数を得る(students, sim_state=None):
    if sim_state is not None and "remaining_count" in sim_state:
        return sim_state["remaining_count"]
    return 残人数を数える(students)


def そのマスに入れるか(occupied, pos, current_pos, final_goals=None):
    if pos == current_pos:
        return True

    if final_goals is not None:
        if isinstance(final_goals, set):
            if pos in final_goals:
                return True
        else:
            if pos in set(final_goals):
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

        for dx, dy in NEIGHBOR_DELTAS:
            nx = x + dx
            ny = y + dy

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

            if cell in (ROAD, FINAL_EXIT):
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
    if student.swap_block_return_steps <= 0:
        return False
    return pos == student.swap_block_return_pos


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


def 一本道セルか(pos, sim_state):
    return sim_state["one_path_map"].get(pos, False)


def 下側ボトルネック帯か(x, y):
    return (
        範囲内(x, y, 13, 31, 23, 25)
        or 範囲内(x, y, 14, 24, 16, 22)
        or 範囲内(x, y, 25, 31, 16, 22)
    )


def 下側ボトルネック混雑ペナルティ(pos, occupied):
    x, y = pos
    if not 下側ボトルネック帯か(x, y):
        return 0

    count = occupied.get(pos, 0)
    penalty = 2

    if count >= 1:
        penalty += 2
    if count >= 2:
        penalty += 4

    return penalty


def 候補評価スコア(next_pos, next_dist, occupied):
    score = next_dist * 100

    count = occupied.get(next_pos, 0)
    if count == 1:
        score += 6
    elif count == 2:
        score += 16
    elif count >= 3:
        score += 40

    score += 下側ボトルネック混雑ペナルティ(next_pos, occupied)
    return score


def 静的マップを作る(grid):
    preferred_dir_map = {}
    one_path_map = {}

    height = len(grid)
    for y in range(height):
        for x in range(X_MIN, X_MAX + 1):
            pos = (x, y)
            preferred_dir_map[pos] = 優先方向を返す(x, y)
            one_path_map[pos] = 一本道か(grid, x, y)

    return preferred_dir_map, one_path_map


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

    final_goals = students[0].final_goals if students else []
    all_door_cells = []
    for door_set in door_goal_sets:
        all_door_cells.extend(list(door_set))

    final_distance_map = 複数ゴール距離マップを作る(
        grid,
        final_goals,
        allowed_doors=all_door_cells
    ) if final_goals else {}

    preferred_dir_map, one_path_map = 静的マップを作る(grid)

    return {
        "door_distance_maps": door_distance_maps,
        "final_distance_map": final_distance_map,
        "current_step": 0,
        "entry_seq_counter": 0,
        "remaining_count": len(students),
        "preferred_dir_map": preferred_dir_map,
        "one_path_map": one_path_map,
        "active_students": list(students),
        "active_dirty": False,
    }


def 現在の距離マップを得る(student, sim_state):
    if student.passed_door:
        return sim_state["final_distance_map"]
    key = tuple(sorted(扉座標集合(student)))
    return sim_state["door_distance_maps"][key]


def 扉前履歴を記録する(student):
    x = student.x
    y = student.y
    if x is None or y is None:
        return

    pos = (x, y)
    if (not student.passed_door) and (pos not in student.path_history_before_door_set):
        student.path_history_before_door.append(pos)
        student.path_history_before_door_set.add(pos)


def 扉通過処理(student):
    student.passed_door = True
    forbidden = set(student.path_history_before_door_set)
    for p in student.target_door_set:
        forbidden.discard(p)
    student.forbidden_after_door = forbidden


def 現在地を離れたら座席を壁にする(grid, student, old_pos):
    if old_pos is None:
        return

    if old_pos == student.start_pos and (not student.left_start_pos):
        ox, oy = old_pos
        grid[oy][ox - X_MIN] = WALL
        student.left_start_pos = True


def 混雑停止確率(occupied_count):
    if occupied_count >= 3:
        return 1 / 2
    if occupied_count == 2:
        return 1 / 5
    return 0.0


def 停止するか(student, occupied, current):
    if random.random() < student.stay_prob:
        return True

    count_here = occupied.get(current, 1)
    p = 混雑停止確率(count_here)
    if p > 0 and random.random() < p:
        return True

    return False


def 初期移動先を決める(student):
    x = student.x
    y = student.y
    if student.class_name == "11R":
        return (x - 1, y)
    return (x, y - 1)


def 停滞カウンタを更新する(student, old_pos):
    if student.x is None or student.y is None:
        student.stuck_steps = 0
        student.last_position = (None, None)
        return

    new_pos = (student.x, student.y)
    if new_pos == old_pos:
        student.stuck_steps += 1
    else:
        student.stuck_steps = 0
    student.last_position = new_pos


def 最終出口近傍か(student):
    x = student.x
    y = student.y
    if x is None or y is None:
        return False

    for gx, gy in student.final_goals:
        if abs(x - gx) <= 2 and abs(y - gy) <= 2:
            return True
    return False


def forbiddenを無視してよいか(student, 救済中=False):
    if not student.passed_door:
        return True
    if 救済中:
        return True
    if 最終出口近傍か(student):
        return True
    return False


def 絶対一方通行違反か(current_pos, next_pos, student=None):
    cx, cy = current_pos
    nx, ny = next_pos

    if student is not None:
        if (
            student.class_name == "11R"
            and not student.left_start_pos
            and current_pos == student.start_pos
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


def 優先通路で逆走衝突しそうか(student, next_pos, position_index, dist_map, sim_state):
    sx = student.x
    sy = student.y
    if sx is None or sy is None:
        return False

    if student.swap_grace_steps > 0:
        return False

    nx, ny = next_pos
    preferred_dir = sim_state["preferred_dir_map"].get((nx, ny))
    if preferred_dir is None:
        return False

    dx = nx - sx
    dy = ny - sy
    my_dir = 方向差分を文字にする(dx, dy)
    if my_dir is None:
        return False

    if my_dir == preferred_dir:
        return False

    if not 逆方向か(my_dir, preferred_dir):
        return False

    if preferred_dir in ("up", "down"):
        xs = range(nx - 1, nx + 2)
        ys = range(ny - 2, ny + 3)
    else:
        xs = range(nx - 2, nx + 3)
        ys = range(ny - 1, ny + 2)

    preferred_dir_map = sim_state["preferred_dir_map"]
    sid = student.id

    for ox in xs:
        for oy in ys:
            others = position_index.get((ox, oy))
            if not others:
                continue

            for other in others:
                if other.id == sid:
                    continue

                other_pref = preferred_dir_map.get((ox, oy))
                if other_pref != preferred_dir:
                    continue

                other_pos = (ox, oy)
                if other_pos not in dist_map:
                    continue

                current_dist = dist_map[other_pos]

                for dx2, dy2 in NEIGHBOR_DELTAS:
                    tx = ox + dx2
                    ty = oy + dy2
                    tpos = (tx, ty)

                    if tpos not in dist_map:
                        continue
                    if dist_map[tpos] >= current_dist:
                        continue

                    other_dir = 方向差分を文字にする(dx2, dy2)

                    if other_dir == preferred_dir:
                        if preferred_dir in ("up", "down"):
                            if abs(ox - nx) <= 1 and abs(oy - ny) <= 2:
                                return True
                        else:
                            if abs(oy - ny) <= 1 and abs(ox - nx) <= 2:
                                return True

    return False


def 最終出口か(student):
    x = student.x
    y = student.y
    if x is None or y is None:
        return False
    return (x, y) in student.final_goal_set


def 最終出口到達処理(student, sim_state=None):
    if student.exited:
        return

    student.exited = True
    student.x = None
    student.y = None
    student.last_position = (None, None)
    student.stuck_steps = 0
    student.swap_grace_steps = 0
    student.swap_block_return_steps = 0
    student.swap_block_return_pos = None

    if sim_state is not None:
        if "remaining_count" in sim_state:
            sim_state["remaining_count"] -= 1
        sim_state["active_dirty"] = True


def 生徒の補助状態を初期化する(students, sim_state):
    entry_seq_counter = sim_state["entry_seq_counter"]

    for s in students:
        if s.cell_entry_seq == 0 and s.cell_entry_step == 0 and s.id != 0:
            s.cell_entry_seq = entry_seq_counter
            entry_seq_counter += 1

    sim_state["entry_seq_counter"] = entry_seq_counter


def マス内優先キー(student):
    return (
        0 if student.swap_grace_steps > 0 else 1,
        student.cell_entry_step,
        student.cell_entry_seq,
        random.random(),
    )


def 提案優先度を計算する(student, from_pos, to_pos, sim_state):
    fx, fy = from_pos
    tx, ty = to_pos
    dx = tx - fx
    dy = ty - fy
    move_dir = 方向差分を文字にする(dx, dy)
    preferred = sim_state["preferred_dir_map"].get((tx, ty))

    priority = 0

    if preferred is not None and move_dir == preferred:
        priority += 100

    priority += min(student.stuck_steps, 20)

    if student.passed_door:
        priority += 10

    if student.swap_grace_steps > 0:
        priority += 200

    return priority


def 初期座席からの提案を作る(grid, student, occupied, sim_state):
    x = student.x
    y = student.y
    current = (x, y)

    gx = x - X_MIN
    if grid[y][gx] != START_SEAT:
        return None

    student.steps_since_start += 1

    if student.steps_since_start < student.start_wait_steps and (not student.must_leave_start):
        return None

    if student.steps_since_start >= 5:
        student.must_leave_start = True

    next_pos = 初期移動先を決める(student)

    if 戻り禁止位置か(student, next_pos):
        return None

    if 絶対一方通行違反か(current, next_pos, student):
        return None

    if not 通れるか(grid, next_pos[0], next_pos[1], student):
        return None

    if not そのマスに入れるか(occupied, next_pos, current, student.final_goal_set):
        return None

    return {
        "student": student,
        "from": current,
        "to": next_pos,
        "priority": 提案優先度を計算する(student, current, next_pos, sim_state),
        "kind": "start_leave",
    }


def 通常移動候補を集める(grid, student, occupied, dist_map, position_index, sim_state):
    sx = student.x
    sy = student.y
    current = (sx, sy)

    if current not in dist_map:
        return []

    current_dist = dist_map[current]
    candidates = []
    forbidden_after_door = student.forbidden_after_door
    final_goal_set = student.final_goal_set
    ignore_forbidden = forbiddenを無視してよいか(student, 救済中=False)

    for dx, dy in NEIGHBOR_DELTAS:
        nx = sx + dx
        ny = sy + dy
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue
        if 絶対一方通行違反か(current, next_pos, student):
            continue
        if not 通れるか(grid, nx, ny, student):
            continue
        if next_pos not in dist_map:
            continue
        if (not ignore_forbidden) and (next_pos in forbidden_after_door):
            continue
        if 優先通路で逆走衝突しそうか(student, next_pos, position_index, dist_map, sim_state):
            continue

        next_dist = dist_map[next_pos]
        if next_dist >= current_dist:
            continue

        if not そのマスに入れるか(occupied, next_pos, current, final_goal_set):
            continue

        score = 候補評価スコア(next_pos, next_dist, occupied)
        candidates.append((nx, ny, next_dist, score))

    if not candidates:
        return []

    min_score = min(score for _, _, _, score in candidates)
    return [(x, y, d) for x, y, d, score in candidates if score == min_score]


def 救済移動候補を集める(grid, student, occupied, dist_map, position_index, sim_state):
    sx = student.x
    sy = student.y
    current = (sx, sy)
    previous = student.last_position
    forbidden_after_door = student.forbidden_after_door
    final_goal_set = student.final_goal_set

    movable = []
    for dx, dy in NEIGHBOR_DELTAS:
        nx = sx + dx
        ny = sy + dy
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue
        if 絶対一方通行違反か(current, next_pos, student):
            continue
        if not 通れるか(grid, nx, ny, student):
            continue
        if not そのマスに入れるか(occupied, next_pos, current, final_goal_set):
            continue
        if 優先通路で逆走衝突しそうか(student, next_pos, position_index, dist_map, sim_state):
            continue

        forbidden_hit = next_pos in forbidden_after_door
        is_previous = (previous is not None) and (next_pos == previous)
        d = dist_map[next_pos] if next_pos in dist_map else 10**9
        score = 候補評価スコア(next_pos, d, occupied)

        movable.append({
            "pos": next_pos,
            "dist": d,
            "score": score,
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

    min_score = min(m["score"] for m in candidates)
    return [m["pos"] for m in candidates if m["score"] == min_score]


def 一本道で対向停滞が起きていそうか(student, position_index, sim_state):
    sx = student.x
    sy = student.y
    if sx is None or sy is None:
        return False

    current = (sx, sy)
    if not 一本道セルか(current, sim_state):
        return False

    if student.stuck_steps < 2:
        return False

    sid = student.id
    for dx, dy in NEIGHBOR_DELTAS:
        pos = (sx + dx, sy + dy)
        others = position_index.get(pos)
        if not others:
            continue

        for other in others:
            if other.id == sid:
                continue
            if other.exited:
                continue
            if other.x is None or other.y is None:
                continue
            if other.stuck_steps < 1:
                continue
            if 一本道セルか((other.x, other.y), sim_state):
                return True

    return False


def 一本道退避候補を集める(grid, student, occupied, dist_map, position_index, sim_state):
    sx = student.x
    sy = student.y
    current = (sx, sy)
    previous = student.last_position
    final_goal_set = student.final_goal_set

    if not 一本道セルか(current, sim_state):
        return []

    movable = []

    for dx, dy in NEIGHBOR_DELTAS:
        nx = sx + dx
        ny = sy + dy
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue
        if 絶対一方通行違反か(current, next_pos, student):
            continue
        if not 通れるか(grid, nx, ny, student):
            continue
        if not そのマスに入れるか(occupied, next_pos, current, final_goal_set):
            continue

        is_previous = (previous is not None) and (next_pos == previous)
        is_one_path = 一本道セルか(next_pos, sim_state)
        d = dist_map[next_pos] if next_pos in dist_map else 10**9
        score = 候補評価スコア(next_pos, d, occupied)

        movable.append({
            "pos": next_pos,
            "dist": d,
            "score": score,
            "is_previous": is_previous,
            "is_one_path": is_one_path,
        })

    if not movable:
        return []

    off_path = [m for m in movable if not m["is_one_path"]]
    if off_path:
        candidates = off_path
    else:
        candidates = movable

    non_previous = [m for m in candidates if not m["is_previous"]]
    if non_previous:
        candidates = non_previous

    min_score = min(m["score"] for m in candidates)
    return [m["pos"] for m in candidates if m["score"] == min_score]


def 本来進みたいマスが三人で満員か(grid, student, occupied, dist_map, position_index, sim_state):
    sx = student.x
    sy = student.y
    current = (sx, sy)

    if current not in dist_map:
        return False

    current_dist = dist_map[current]
    has_better = False
    all_full = True
    forbidden_after_door = student.forbidden_after_door
    final_goal_set = student.final_goal_set
    ignore_forbidden = forbiddenを無視してよいか(student, 救済中=False)

    for dx, dy in NEIGHBOR_DELTAS:
        nx = sx + dx
        ny = sy + dy
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue
        if 絶対一方通行違反か(current, next_pos, student):
            continue
        if not 通れるか(grid, nx, ny, student):
            continue
        if next_pos not in dist_map:
            continue
        if (not ignore_forbidden) and (next_pos in forbidden_after_door):
            continue
        if 優先通路で逆走衝突しそうか(student, next_pos, position_index, dist_map, sim_state):
            continue

        next_dist = dist_map[next_pos]
        if next_dist >= current_dist:
            continue

        has_better = True
        if そのマスに入れるか(occupied, next_pos, current, final_goal_set):
            all_full = False

    return has_better and all_full


def 進みたいマスの先が満員詰まりか(grid, student, occupied, dist_map, position_index, sim_state):
    sx = student.x
    sy = student.y
    current = (sx, sy)

    if current not in dist_map:
        return False

    current_dist = dist_map[current]
    candidates = []
    forbidden_after_door = student.forbidden_after_door
    ignore_forbidden = forbiddenを無視してよいか(student, 救済中=False)

    for dx, dy in NEIGHBOR_DELTAS:
        nx = sx + dx
        ny = sy + dy
        next_pos = (nx, ny)

        if 戻り禁止位置か(student, next_pos):
            continue
        if 絶対一方通行違反か(current, next_pos, student):
            continue
        if not 通れるか(grid, nx, ny, student):
            continue
        if next_pos not in dist_map:
            continue
        if (not ignore_forbidden) and (next_pos in forbidden_after_door):
            continue
        if 優先通路で逆走衝突しそうか(student, next_pos, position_index, dist_map, sim_state):
            continue

        next_dist = dist_map[next_pos]
        if next_dist >= current_dist:
            continue

        candidates.append((nx, ny, next_dist))

    if not candidates:
        return False

    min_dist = min(d for _, _, d in candidates)
    best_candidates = [(x, y) for x, y, d in candidates if d == min_dist]

    checked_any = False
    final_goal_set = student.final_goal_set

    for bx, by in best_candidates:
        base_pos = (bx, by)
        if base_pos not in dist_map:
            continue

        base_dist = dist_map[base_pos]
        next_steps = []

        for dx, dy in NEIGHBOR_DELTAS:
            tx = bx + dx
            ty = by + dy
            tpos = (tx, ty)

            if not 通れるか(grid, tx, ty, student):
                continue
            if tpos not in dist_map:
                continue
            if dist_map[tpos] < base_dist:
                next_steps.append(tpos)

        if not next_steps:
            continue

        checked_any = True

        if any(そのマスに入れるか(occupied, p, base_pos, final_goal_set) for p in next_steps):
            return False

    return checked_any


def 前方に長時間停滞中の相手がいるか(student, position_index):
    x = student.x
    y = student.y

    check_positions = (
        (x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1),
        (x, y - 2), (x - 2, y), (x + 2, y), (x, y + 2),
    )

    sid = student.id
    for pos in check_positions:
        others = position_index.get(pos)
        if not others:
            continue
        for other in others:
            if other.id == sid:
                continue
            if other.stuck_steps >= 1:
                return True
    return False


def 提案を作る(grid, student, occupied, sim_state, position_index):
    x = student.x
    y = student.y

    if student.exited or x is None or y is None:
        return None

    current = (x, y)
    passed_door = student.passed_door

    if not passed_door:
        扉前履歴を記録する(student)

    if (not passed_door) and (current in student.target_door_set):
        扉通過処理(student)
        passed_door = True

    if passed_door and ((x, y) in student.final_goal_set):
        return {
            "student": student,
            "from": current,
            "to": current,
            "priority": 9999,
            "kind": "exit_now",
        }

    gx = x - X_MIN
    current_cell = grid[y][gx]

    if current_cell == START_SEAT:
        return 初期座席からの提案を作る(grid, student, occupied, sim_state)

    if 停止するか(student, occupied, current):
        return None

    dist_map = 現在の距離マップを得る(student, sim_state)

    normal_candidates = 通常移動候補を集める(
        grid, student, occupied, dist_map, position_index, sim_state
    )
    if normal_candidates:
        nx, ny, _ = random.choice(normal_candidates)
        next_pos = (nx, ny)
        return {
            "student": student,
            "from": current,
            "to": next_pos,
            "priority": 提案優先度を計算する(student, current, next_pos, sim_state),
            "kind": "normal",
        }

    if student.stuck_steps >= 1:
        if 進みたいマスの先が満員詰まりか(
            grid, student, occupied, dist_map, position_index, sim_state
        ):
            return None

        if (
            not 本来進みたいマスが三人で満員か(
                grid, student, occupied, dist_map, position_index, sim_state
            )
            or 前方に長時間停滞中の相手がいるか(student, position_index)
        ):
            rescue_candidates = 救済移動候補を集める(
                grid, student, occupied, dist_map, position_index, sim_state
            )
            if rescue_candidates:
                next_pos = random.choice(rescue_candidates)
                return {
                    "student": student,
                    "from": current,
                    "to": next_pos,
                    "priority": 提案優先度を計算する(student, current, next_pos, sim_state) + 80,
                    "kind": "rescue",
                }

    if student.stuck_steps >= 2 and 一本道で対向停滞が起きていそうか(student, position_index, sim_state):
        retreat_candidates = 一本道退避候補を集める(
            grid, student, occupied, dist_map, position_index, sim_state
        )
        if retreat_candidates:
            next_pos = random.choice(retreat_candidates)
            return {
                "student": student,
                "from": current,
                "to": next_pos,
                "priority": 提案優先度を計算する(student, current, next_pos, sim_state) + 140,
                "kind": "one_path_retreat",
            }

    return None


def 正面衝突か(proposal_a, proposal_b):
    return proposal_a["from"] == proposal_b["to"] and proposal_a["to"] == proposal_b["from"]


def 同じマス内で誰が動くかを選ぶ(proposals):
    if not proposals:
        return []

    best_key = None
    tied = []

    for p in proposals:
        s = p["student"]
        key = (
            0 if s.swap_grace_steps > 0 else 1,
            s.cell_entry_step,
            s.cell_entry_seq,
        )

        if best_key is None or key < best_key:
            best_key = key
            tied = [p]
        elif key == best_key:
            tied.append(p)

    if len(tied) == 1:
        return tied

    return [random.choice(tied)]


def 同一到着先競合を解決する(proposals):
    if not proposals:
        return []

    by_dest = {}
    for p in proposals:
        dest = p["to"]
        lst = by_dest.get(dest)
        if lst is None:
            by_dest[dest] = [p]
        else:
            lst.append(p)

    winners = []
    for plist in by_dest.values():
        if len(plist) == 1:
            winners.append(plist[0])
            continue

        max_priority = max(p["priority"] for p in plist)
        top = [p for p in plist if p["priority"] == max_priority]
        winners.append(random.choice(top))

    return winners


def 正面衝突を解決する(proposals):
    if not proposals:
        return [], []

    used = set()
    swaps = []
    normal = []

    for i in range(len(proposals)):
        if i in used:
            continue

        pi = proposals[i]
        found_swap = False

        for j in range(i + 1, len(proposals)):
            if j in used:
                continue

            pj = proposals[j]
            if 正面衝突か(pi, pj):
                swaps.append((pi, pj))
                used.add(i)
                used.add(j)
                found_swap = True
                break

        if not found_swap:
            normal.append(pi)

    return swaps, normal


def 提案を解決する(proposals, occupied):
    by_source = {}
    for p in proposals:
        src = p["from"]
        lst = by_source.get(src)
        if lst is None:
            by_source[src] = [p]
        else:
            lst.append(p)

    source_filtered = []
    for plist in by_source.values():
        if len(plist) == 1:
            source_filtered.append(plist[0])
        else:
            source_filtered.extend(同じマス内で誰が動くかを選ぶ(plist))

    swaps, others = 正面衝突を解決する(source_filtered)
    winners = 同一到着先競合を解決する(others)

    final_actions = []

    for a, b in swaps:
        final_actions.append({"kind": "swap", "a": a, "b": b})

    final_count = dict(occupied)
    random.shuffle(winners)

    for p in winners:
        src = p["from"]
        dst = p["to"]
        student = p["student"]

        if p["kind"] == "exit_now":
            final_actions.append({"kind": "exit_now", "proposal": p})
            continue

        if dst in student.final_goal_set:
            final_actions.append({"kind": "move", "proposal": p})
            final_count[src] = final_count.get(src, 0) - 1
            final_count[dst] = final_count.get(dst, 0) + 1
            continue

        if final_count.get(dst, 0) < 3:
            final_actions.append({"kind": "move", "proposal": p})
            final_count[src] = final_count.get(src, 0) - 1
            final_count[dst] = final_count.get(dst, 0) + 1

    return final_actions


def 生徒を新しいマスへ置く(student, new_pos, sim_state):
    student.x, student.y = new_pos
    student.cell_entry_step = sim_state["current_step"]
    student.cell_entry_seq = sim_state["entry_seq_counter"]
    sim_state["entry_seq_counter"] += 1


def 提案を適用する(grid, actions, sim_state):
    for action in actions:
        if action["kind"] == "exit_now":
            student = action["proposal"]["student"]
            最終出口到達処理(student, sim_state)
            continue

        if action["kind"] == "move":
            p = action["proposal"]
            student = p["student"]
            old_pos = p["from"]
            new_pos = p["to"]

            if old_pos != new_pos:
                生徒を新しいマスへ置く(student, new_pos, sim_state)
                現在地を離れたら座席を壁にする(grid, student, old_pos)

            current = (student.x, student.y)
            if (not student.passed_door) and (current in student.target_door_set):
                扉通過処理(student)

            if student.passed_door and ((student.x, student.y) in student.final_goal_set):
                最終出口到達処理(student, sim_state)

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

            sa.swap_grace_steps = 1
            sb.swap_grace_steps = 1

            sa.swap_block_return_steps = 1
            sb.swap_block_return_steps = 1
            sa.swap_block_return_pos = old_a
            sb.swap_block_return_pos = old_b

            現在地を離れたら座席を壁にする(grid, sa, old_a)
            現在地を離れたら座席を壁にする(grid, sb, old_b)

            current_a = (sa.x, sa.y)
            current_b = (sb.x, sb.y)

            if (not sa.passed_door) and (current_a in sa.target_door_set):
                扉通過処理(sa)
            if (not sb.passed_door) and (current_b in sb.target_door_set):
                扉通過処理(sb)

            if sa.passed_door and ((sa.x, sa.y) in sa.final_goal_set):
                最終出口到達処理(sa, sim_state)
            if sb.passed_door and ((sb.x, sb.y) in sb.final_goal_set):
                最終出口到達処理(sb, sim_state)


def 補助カウンタを減らす(students):
    for s in students:
        if s.swap_grace_steps > 0:
            s.swap_grace_steps -= 1

        if s.swap_block_return_steps > 0:
            s.swap_block_return_steps -= 1
            if s.swap_block_return_steps <= 0:
                s.swap_block_return_pos = None


def 検証エラーを投げる(step, message):
    raise RuntimeError(f"[simulation validation error] step={step} {message}")


def ルール破綻を検証する(grid, students, sim_state):
    step = sim_state["current_step"]

    actual_remaining = sum(1 for s in students if not s.exited)
    if sim_state["remaining_count"] != actual_remaining:
        検証エラーを投げる(
            step,
            f"remaining_count mismatch sim_state={sim_state['remaining_count']} actual={actual_remaining}"
        )

    active_students = sim_state["active_students"]
    for s in active_students:
        if s.exited:
            検証エラーを投げる(step, f"active_students contains exited student id={s.id}")
        if s.x is None or s.y is None:
            検証エラーを投げる(step, f"active_students contains invalid-position student id={s.id}")

    occupied = {}
    for s in students:
        if set(s.path_history_before_door) != s.path_history_before_door_set:
            検証エラーを投げる(step, f"path history list/set mismatch id={s.id}")

        if s.exited:
            if not (s.x is None and s.y is None):
                検証エラーを投げる(step, f"exited student still has position id={s.id} pos=({s.x},{s.y})")
            continue

        if s.x is None or s.y is None:
            検証エラーを投げる(step, f"non-exited student has None position id={s.id}")

        x = s.x
        y = s.y

        if y < 0 or y >= len(grid) or x < X_MIN or x > X_MAX:
            検証エラーを投げる(step, f"student out of bounds id={s.id} pos=({x},{y})")

        cell = grid[y][x - X_MIN]

        if cell == WALL:
            検証エラーを投げる(step, f"student in WALL id={s.id} pos=({x},{y})")

        if cell == DOOR and (not s.passed_door) and ((x, y) not in s.target_door_set):
            検証エラーを投げる(
                step,
                f"student entered non-target door before passing target id={s.id} pos=({x},{y})"
            )

        pos = (x, y)
        occupied[pos] = occupied.get(pos, 0) + 1

    for pos, count in occupied.items():
        if count > 3:
            検証エラーを投げる(step, f"cell capacity exceeded pos={pos} count={count}")


def 一ステップ進める(grid, students, sim_state):
    sim_state["current_step"] += 1

    生徒の補助状態を初期化する(students, sim_state)

    if sim_state["active_dirty"]:
        active_students = [
            s for s in sim_state["active_students"]
            if (not s.exited) and s.x is not None and s.y is not None
        ]
        sim_state["active_students"] = active_students
        sim_state["active_dirty"] = False
    else:
        active_students = sim_state["active_students"]

    random.shuffle(active_students)

    position_index, occupied = 位置索引と占有表を作る(active_students)

    old_positions = {}
    proposals = []

    current_step = sim_state["current_step"]
    for s in active_students:
        old_positions[s.id] = (s.x, s.y)

        if current_step < s.start_step:
            continue

        proposal = 提案を作る(grid, s, occupied, sim_state, position_index)
        if proposal is not None:
            proposals.append(proposal)

    actions = 提案を解決する(proposals, occupied)
    提案を適用する(grid, actions, sim_state)

    if sim_state["active_dirty"]:
        sim_state["active_students"] = [
            s for s in sim_state["active_students"]
            if (not s.exited) and s.x is not None and s.y is not None
        ]
        sim_state["active_dirty"] = False

    for s in students:
        if s.exited:
            停滞カウンタを更新する(s, old_positions.get(s.id))
            continue

        if s.x is None or s.y is None:
            停滞カウンタを更新する(s, old_positions.get(s.id))
            continue

        old_pos = old_positions.get(s.id, (s.x, s.y))
        停滞カウンタを更新する(s, old_pos)

    補助カウンタを減らす(students)

    if DEBUG_VALIDATE_SIMULATION:
        ルール破綻を検証する(grid, students, sim_state)


def シミュレーションを実行する(grid, students, max_steps=200):
    sim_state = シミュレーション状態を初期化する(grid, students)

    if DEBUG_VALIDATE_SIMULATION:
        ルール破綻を検証する(grid, students, sim_state)

    history = [現在残人数を得る(students, sim_state)]

    for _ in range(max_steps):
        if 現在残人数を得る(students, sim_state) == 0:
            break
        一ステップ進める(grid, students, sim_state)
        history.append(現在残人数を得る(students, sim_state))

    return history