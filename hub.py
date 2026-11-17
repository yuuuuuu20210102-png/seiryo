from copy import deepcopy
from functools import lru_cache

from config.sim_settings import (
    CLASS_NAMES,
    VALID_DOOR_NAMES,
    DEFAULT_MAX_STEPS,
    DEFAULT_PROCESS_STEPS_PER_FRAME,
    DEFAULT_DISPLAY_INTERVAL_MS,
    DEFAULT_DOOR_ASSIGNMENT,
    DEFAULT_START_STEPS,
)

from data.make_seiryo_data import create_hall_model
from data.make_students_data import create_students
from sim.simulation import シミュレーション状態を初期化する, 一ステップ進める, 残人数を数える
from sim.visualization_sub2 import シミュレーションを表示する


@lru_cache(maxsize=1)
def 固定ホール情報を取得する():
    grid, doors, final_goals = create_hall_model()

    immutable_grid = tuple(tuple(row) for row in grid)
    immutable_doors = {
        door_name: tuple(tuple(pos) for pos in door_cells)
        for door_name, door_cells in doors.items()
    }
    immutable_final_goals = tuple(tuple(pos) for pos in final_goals)

    return immutable_grid, immutable_doors, immutable_final_goals


def 固定ホールから可変グリッドを作る():
    immutable_grid, _, _ = 固定ホール情報を取得する()
    return [list(row) for row in immutable_grid]


def 扉辞書を取得する():
    _, immutable_doors, _ = 固定ホール情報を取得する()
    return {
        door_name: [tuple(pos) for pos in door_cells]
        for door_name, door_cells in immutable_doors.items()
    }


def 最終出口一覧を取得する():
    _, _, immutable_final_goals = 固定ホール情報を取得する()
    return [tuple(pos) for pos in immutable_final_goals]


def 扉割り当てを座標辞書に変換する(doors, door_assignment_by_name):
    assignment = {}
    for class_name in CLASS_NAMES:
        door_name = str(door_assignment_by_name[class_name])
        if door_name not in doors:
            raise ValueError(f"{class_name} の扉指定が不正です: {door_name}")
        assignment[class_name] = list(doors[door_name])
    return assignment


def 条件を正規化する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
    process_steps_per_frame=None,
    display_interval_ms=None,
):
    if door_assignment_by_name is None:
        door_assignment_by_name = deepcopy(DEFAULT_DOOR_ASSIGNMENT)
    else:
        merged = deepcopy(DEFAULT_DOOR_ASSIGNMENT)
        merged.update(door_assignment_by_name)
        door_assignment_by_name = {k: str(v) for k, v in merged.items()}

    if start_steps is None:
        start_steps = deepcopy(DEFAULT_START_STEPS)
    else:
        merged = deepcopy(DEFAULT_START_STEPS)
        merged.update(start_steps)
        start_steps = {k: int(v) for k, v in merged.items()}

    for class_name in CLASS_NAMES:
        if door_assignment_by_name[class_name] not in VALID_DOOR_NAMES:
            raise ValueError(f"{class_name} の扉は {VALID_DOOR_NAMES} のどれかにしてください。")
        if start_steps[class_name] < 0:
            raise ValueError(f"{class_name} の開始ステップは0以上にしてください。")

    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS
    if process_steps_per_frame is None:
        process_steps_per_frame = DEFAULT_PROCESS_STEPS_PER_FRAME
    if display_interval_ms is None:
        display_interval_ms = DEFAULT_DISPLAY_INTERVAL_MS

    max_steps = int(max_steps)
    process_steps_per_frame = int(process_steps_per_frame)
    display_interval_ms = int(display_interval_ms)

    if max_steps <= 0:
        raise ValueError("最大ステップ数は1以上にしてください。")
    if process_steps_per_frame <= 0:
        raise ValueError("1表示あたり内部ステップ数は1以上にしてください。")
    if display_interval_ms <= 0:
        raise ValueError("表示間隔(ms)は1以上にしてください。")

    return {
        "door_assignment_by_name": door_assignment_by_name,
        "start_steps": start_steps,
        "max_steps": max_steps,
        "process_steps_per_frame": process_steps_per_frame,
        "display_interval_ms": display_interval_ms,
    }


def 実行条件を準備する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
    process_steps_per_frame=None,
    display_interval_ms=None,
):
    normalized = 条件を正規化する(
        door_assignment_by_name=door_assignment_by_name,
        start_steps=start_steps,
        max_steps=max_steps,
        process_steps_per_frame=process_steps_per_frame,
        display_interval_ms=display_interval_ms,
    )

    doors = 扉辞書を取得する()
    assignment = 扉割り当てを座標辞書に変換する(
        doors,
        normalized["door_assignment_by_name"]
    )

    prepared = {
        "door_assignment_by_name": dict(normalized["door_assignment_by_name"]),
        "start_steps": dict(normalized["start_steps"]),
        "max_steps": normalized["max_steps"],
        "process_steps_per_frame": normalized["process_steps_per_frame"],
        "display_interval_ms": normalized["display_interval_ms"],
        "assignment": {
            class_name: [tuple(pos) for pos in assignment[class_name]]
            for class_name in CLASS_NAMES
        },
    }
    return prepared


def 準備済み条件からデータを構築する(prepared_condition):
    grid = 固定ホールから可変グリッドを作る()
    doors = 扉辞書を取得する()
    final_goals = 最終出口一覧を取得する()

    students = create_students(
        grid=grid,
        doors=doors,
        final_goals=final_goals,
        assignment=prepared_condition["assignment"],
        start_steps=prepared_condition["start_steps"]
    )

    return grid, doors, final_goals, students


def データを構築する(door_assignment_by_name=None, start_steps=None):
    prepared = 実行条件を準備する(
        door_assignment_by_name=door_assignment_by_name,
        start_steps=start_steps,
    )
    return 準備済み条件からデータを構築する(prepared)


def 描画なしでシミュレーションを実行する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
    prepared_condition=None,
):
    if prepared_condition is None:
        prepared_condition = 実行条件を準備する(
            door_assignment_by_name=door_assignment_by_name,
            start_steps=start_steps,
            max_steps=max_steps,
        )
    else:
        prepared_condition = dict(prepared_condition)
        if max_steps is not None:
            prepared_condition["max_steps"] = int(max_steps)

    grid, _, final_goals, students = 準備済み条件からデータを構築する(prepared_condition)

    sim_state = シミュレーション状態を初期化する(grid, students)
    history = [残人数を数える(students)]

    step_count = 0
    class_finish_steps = {class_name: None for class_name in CLASS_NAMES}

    while step_count < prepared_condition["max_steps"] and 残人数を数える(students) > 0:
        一ステップ進める(grid, students, sim_state)
        step_count += 1
        history.append(残人数を数える(students))

        for class_name in CLASS_NAMES:
            if class_finish_steps[class_name] is not None:
                continue
            class_students = [s for s in students if s["class_name"] == class_name]
            if class_students and all(s["exited"] for s in class_students):
                class_finish_steps[class_name] = step_count

    completed = 残人数を数える(students) == 0

    for class_name in CLASS_NAMES:
        if class_finish_steps[class_name] is None:
            class_finish_steps[class_name] = -1

    result = {
        "completed": completed,
        "total_steps": step_count,
        "remaining_students": 残人数を数える(students),
        "initial_students": len(students),
        "final_goals": str(final_goals),
        "history": history,
        "class_finish_steps": class_finish_steps,
        "door_assignment_by_name": prepared_condition["door_assignment_by_name"],
        "start_steps": prepared_condition["start_steps"],
    }

    return result


def 描画ありでシミュレーションを実行する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
    process_steps_per_frame=None,
    display_interval_ms=None,
    prepared_condition=None,
):
    if prepared_condition is None:
        prepared_condition = 実行条件を準備する(
            door_assignment_by_name=door_assignment_by_name,
            start_steps=start_steps,
            max_steps=max_steps,
            process_steps_per_frame=process_steps_per_frame,
            display_interval_ms=display_interval_ms,
        )
    else:
        prepared_condition = dict(prepared_condition)
        if max_steps is not None:
            prepared_condition["max_steps"] = int(max_steps)
        if process_steps_per_frame is not None:
            prepared_condition["process_steps_per_frame"] = int(process_steps_per_frame)
        if display_interval_ms is not None:
            prepared_condition["display_interval_ms"] = int(display_interval_ms)

    grid, _, _, students = 準備済み条件からデータを構築する(prepared_condition)

    visual_result = シミュレーションを表示する(
        grid=grid,
        students=students,
        max_steps=prepared_condition["max_steps"],
        interval=prepared_condition["display_interval_ms"],
        process_steps_per_frame=prepared_condition["process_steps_per_frame"],
    )

    result = {
        "completed": visual_result["completed"],
        "total_steps": visual_result["total_steps"],
        "remaining_students": visual_result["remaining_students"],
        "door_assignment_by_name": prepared_condition["door_assignment_by_name"],
        "start_steps": prepared_condition["start_steps"],
    }

    return result


if __name__ == "__main__":
    描画ありでシミュレーションを実行する()