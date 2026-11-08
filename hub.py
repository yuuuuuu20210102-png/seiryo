from copy import deepcopy

from config.sim_settings import (
    CLASS_NAMES,
    DEFAULT_MAX_STEPS,
    DEFAULT_PROCESS_STEPS_PER_FRAME,
    DEFAULT_DISPLAY_INTERVAL_MS,
    DEFAULT_DOOR_ASSIGNMENT,
    DEFAULT_START_STEPS,
)

from data.make_students_data import シミュレーション用データを作る
from sim.simulation import シミュレーション状態を初期化する, 一ステップ進める, 残人数を数える
from sim.visualization_sub2 import シミュレーションを表示する


def 扉割り当てを座標辞書に変換する(doors, door_assignment_by_name):
    assignment = {}
    for class_name in CLASS_NAMES:
        door_name = str(door_assignment_by_name[class_name])
        assignment[class_name] = doors[door_name]
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
        door_assignment_by_name = merged

    if start_steps is None:
        start_steps = deepcopy(DEFAULT_START_STEPS)
    else:
        merged = deepcopy(DEFAULT_START_STEPS)
        merged.update(start_steps)
        start_steps = merged

    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    if process_steps_per_frame is None:
        process_steps_per_frame = DEFAULT_PROCESS_STEPS_PER_FRAME

    if display_interval_ms is None:
        display_interval_ms = DEFAULT_DISPLAY_INTERVAL_MS

    return {
        "door_assignment_by_name": door_assignment_by_name,
        "start_steps": start_steps,
        "max_steps": int(max_steps),
        "process_steps_per_frame": int(process_steps_per_frame),
        "display_interval_ms": int(display_interval_ms),
    }


def データを構築する(door_assignment_by_name=None, start_steps=None):
    base_grid, doors, final_goals, _ = シミュレーション用データを作る()

    normalized = 条件を正規化する(
        door_assignment_by_name=door_assignment_by_name,
        start_steps=start_steps,
    )

    assignment = 扉割り当てを座標辞書に変換する(
        doors,
        normalized["door_assignment_by_name"]
    )

    grid, doors, final_goals, students = シミュレーション用データを作る(
        assignment=assignment,
        start_steps=normalized["start_steps"]
    )

    return grid, doors, final_goals, students


def 描画なしでシミュレーションを実行する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
):
    params = 条件を正規化する(
        door_assignment_by_name=door_assignment_by_name,
        start_steps=start_steps,
        max_steps=max_steps,
    )

    grid, doors, final_goals, students = データを構築する(
        door_assignment_by_name=params["door_assignment_by_name"],
        start_steps=params["start_steps"],
    )

    sim_state = シミュレーション状態を初期化する(grid, students)
    history = [残人数を数える(students)]

    step_count = 0
    while step_count < params["max_steps"] and 残人数を数える(students) > 0:
        一ステップ進める(grid, students, sim_state)
        step_count += 1
        history.append(残人数を数える(students))

    completed = 残人数を数える(students) == 0

    class_finish_steps = {}
    for class_name in CLASS_NAMES:
        class_students = [s for s in students if s["class_name"] == class_name]
        if all(s["exited"] for s in class_students):
            class_finish_steps[class_name] = step_count
        else:
            class_finish_steps[class_name] = -1

    result = {
        "completed": completed,
        "total_steps": step_count,
        "remaining_students": 残人数を数える(students),
        "initial_students": len(students),
        "final_goals": str(final_goals),
        "history": history,
        "class_finish_steps": class_finish_steps,
        "door_assignment_by_name": params["door_assignment_by_name"],
        "start_steps": params["start_steps"],
    }

    return result


def 描画ありでシミュレーションを実行する(
    door_assignment_by_name=None,
    start_steps=None,
    max_steps=None,
    process_steps_per_frame=None,
    display_interval_ms=None,
):
    params = 条件を正規化する(
        door_assignment_by_name=door_assignment_by_name,
        start_steps=start_steps,
        max_steps=max_steps,
        process_steps_per_frame=process_steps_per_frame,
        display_interval_ms=display_interval_ms,
    )

    grid, doors, final_goals, students = データを構築する(
        door_assignment_by_name=params["door_assignment_by_name"],
        start_steps=params["start_steps"],
    )

    visual_result = シミュレーションを表示する(
        grid=grid,
        students=students,
        max_steps=params["max_steps"],
        interval=params["display_interval_ms"],
        process_steps_per_frame=params["process_steps_per_frame"],
    )

    result = {
        "completed": visual_result["completed"],
        "total_steps": visual_result["total_steps"],
        "remaining_students": visual_result["remaining_students"],
        "door_assignment_by_name": params["door_assignment_by_name"],
        "start_steps": params["start_steps"],
    }

    return result


if __name__ == "__main__":
    描画ありでシミュレーションを実行する()