import os
import time
import math
import multiprocessing
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ProcessPoolExecutor, as_completed

from openpyxl import Workbook, load_workbook

from config.sim_settings import CLASS_NAMES, VALID_DOOR_NAMES
from hub import 描画なしでシミュレーションを実行する, 実行条件を準備する


MAX_STEPS_FIXED = 1000
PROCESS_RATE_FIXED = 1000
DEFAULT_WORKER_COUNT = max(1, (os.cpu_count() or 2) - 1)


def サンプルファイルを作る(save_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "条件"

    ws["A1"] = "パターン数"
    ws["B1"] = "1パターン当たり何回読み込むか"

    ws["A2"] = 2
    ws["B2"] = 3

    headers = [
        "11R出る扉", "12R出る扉", "13R出る扉", "14R出る扉",
        "15R出る扉", "16R出る扉", "17R出る扉", "18R出る扉",
        "11R待つ回数", "12R待つ回数", "13R待つ回数", "14R待つ回数",
        "15R待つ回数", "16R待つ回数", "17R待つ回数", "18R待つ回数",
        "平均step数", "止まった回数"
    ]

    for col, value in enumerate(headers, start=1):
        ws.cell(row=4, column=col, value=value)

    sample_rows = [
        ["5", "5", "5", "5", "5", "5", "5", "5", 0, 0, 0, 0, 0, 0, 0, 0, "", ""],
        ["5", "5", "5", "5", "5", "5", "5", "5", 0, 20, 40, 60, 80, 100, 120, 140, "", ""],
    ]

    for r, row_values in enumerate(sample_rows, start=5):
        for c, value in enumerate(row_values, start=1):
            ws.cell(row=r, column=c, value=value)

    wb.save(save_path)


def ファイルを選ぶ(entry_widget):
    path = filedialog.askopenfilename(
        title="入力ファイルを選択",
        filetypes=[("Excelファイル", "*.xlsx")]
    )
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)


def サンプルを保存する():
    save_path = filedialog.asksaveasfilename(
        title="サンプルファイルを保存",
        defaultextension=".xlsx",
        filetypes=[("Excelファイル", "*.xlsx")]
    )
    if not save_path:
        return

    サンプルファイルを作る(save_path)
    messagebox.showinfo("保存完了", f"サンプルファイルを保存しました。\n{save_path}")


def セル値を読む(ws, row, col, default=None):
    value = ws.cell(row=row, column=col).value
    if value is None or value == "":
        return default
    return value


def 非負整数に変換する(value, name):
    try:
        ivalue = int(value)
    except Exception:
        raise ValueError(f"{name} は整数で入力してください。")
    if ivalue < 0:
        raise ValueError(f"{name} は0以上にしてください。")
    return ivalue


def 正整数に変換する(value, name):
    ivalue = 非負整数に変換する(value, name)
    if ivalue <= 0:
        raise ValueError(f"{name} は1以上にしてください。")
    return ivalue


def 条件ファイルを読む(path):
    wb = load_workbook(path)
    ws = wb.active

    pattern_count = 非負整数に変換する(セル値を読む(ws, 2, 1, 0), "A2 パターン数")
    trial_count = 非負整数に変換する(セル値を読む(ws, 2, 2, 1), "B2 1パターン当たり回数")

    if pattern_count <= 0:
        raise ValueError("パターン数は1以上にしてください。")
    if trial_count <= 0:
        raise ValueError("1パターン当たり何回読み込むかは1以上にしてください。")

    conditions = []

    for i in range(pattern_count):
        row = 5 + i

        door_assignment = {}
        start_steps = {}

        for idx, class_name in enumerate(CLASS_NAMES):
            door_value = str(セル値を読む(ws, row, 1 + idx, "5")).strip()
            if door_value not in VALID_DOOR_NAMES:
                raise ValueError(f"{row}行目 {class_name}出る扉 は {VALID_DOOR_NAMES} のどれかにしてください。")
            door_assignment[class_name] = door_value

        for idx, class_name in enumerate(CLASS_NAMES):
            start_value = 非負整数に変換する(
                セル値を読む(ws, row, 9 + idx, 0),
                f"{row}行目 {class_name}待つ回数"
            )
            start_steps[class_name] = start_value

        conditions.append({
            "row": row,
            "condition_index": i + 1,
            "door_assignment_by_name": door_assignment,
            "start_steps": start_steps,
        })

    return wb, ws, pattern_count, trial_count, conditions


def 実行用条件一覧を準備する(conditions):
    prepared_conditions = []

    for condition in conditions:
        prepared_condition = 実行条件を準備する(
            door_assignment_by_name=condition["door_assignment_by_name"],
            start_steps=condition["start_steps"],
            max_steps=MAX_STEPS_FIXED,
        )

        prepared_conditions.append({
            "row": condition["row"],
            "condition_index": condition["condition_index"],
            "prepared_condition": prepared_condition,
        })

    return prepared_conditions


def 平均を計算する(values):
    if not values:
        return 0
    return sum(values) / len(values)


def 秒を時分秒にする(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def 進捗表示を更新する(
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label,
    total_done,
    total_count,
    start_time,
    latest_message=""
):
    progress_percent = 0
    if total_count > 0:
        progress_percent = (total_done / total_count) * 100

    elapsed = time.time() - start_time
    if total_done > 0:
        avg_time = elapsed / total_done
        remain = avg_time * (total_count - total_done)
    else:
        remain = 0

    progress_var.set(progress_percent)

    status_label.config(
        text=f"進捗: {total_done} / {total_count}  ({progress_percent:.1f}%)"
    )
    detail_label.config(text=latest_message)
    elapsed_label.config(
        text=f"経過時間: {秒を時分秒にする(elapsed)}   残り予想: {秒を時分秒にする(remain)}"
    )
    root.update_idletasks()


def 推奨チャンクサイズを決める(trial_count, worker_count):
    if worker_count <= 1:
        return 1
    return max(1, min(16, math.ceil(trial_count / (worker_count * 4))))


def 試行チャンクを作る(prepared_conditions, trial_count, chunk_size):
    tasks = []

    for prepared in prepared_conditions:
        remaining = trial_count
        chunk_index = 0

        while remaining > 0:
            repeat_count = min(chunk_size, remaining)
            tasks.append({
                "condition_index": prepared["condition_index"],
                "row": prepared["row"],
                "prepared_condition": prepared["prepared_condition"],
                "repeat_count": repeat_count,
                "chunk_index": chunk_index,
            })
            remaining -= repeat_count
            chunk_index += 1

    return tasks


def 試行チャンクを実行する(task):
    completed_steps = []
    failed_count = 0

    for _ in range(task["repeat_count"]):
        result = 描画なしでシミュレーションを実行する(
            prepared_condition=task["prepared_condition"]
        )

        if result["completed"]:
            completed_steps.append(result["total_steps"])
        else:
            failed_count += 1

    return {
        "condition_index": task["condition_index"],
        "row": task["row"],
        "repeat_count": task["repeat_count"],
        "completed_steps": completed_steps,
        "failed_count": failed_count,
        "chunk_index": task["chunk_index"],
    }


def 並列で条件を実行して集計する(
    prepared_conditions,
    trial_count,
    worker_count,
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label
):
    total_count = len(prepared_conditions) * trial_count
    start_time = time.time()
    total_done = 0

    stats_by_condition = {}
    for prepared in prepared_conditions:
        stats_by_condition[prepared["condition_index"]] = {
            "row": prepared["row"],
            "completed_steps": [],
            "failed_count": 0,
        }

    chunk_size = 推奨チャンクサイズを決める(trial_count, worker_count)
    tasks = 試行チャンクを作る(prepared_conditions, trial_count, chunk_size)

    last_ui_update = 0.0

    if worker_count <= 1:
        for task in tasks:
            result = 試行チャンクを実行する(task)

            stat = stats_by_condition[result["condition_index"]]
            stat["completed_steps"].extend(result["completed_steps"])
            stat["failed_count"] += result["failed_count"]

            total_done += result["repeat_count"]

            now = time.time()
            if now - last_ui_update >= 0.2 or total_done >= total_count:
                進捗表示を更新する(
                    root=root,
                    progress_var=progress_var,
                    status_label=status_label,
                    detail_label=detail_label,
                    elapsed_label=elapsed_label,
                    total_done=total_done,
                    total_count=total_count,
                    start_time=start_time,
                    latest_message=(
                        f"実行中: 条件 {result['condition_index']} "
                        f"(チャンク {result['chunk_index'] + 1}) / "
                        f"並列数 {worker_count} / チャンクサイズ {chunk_size}"
                    )
                )
                last_ui_update = now
    else:
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(試行チャンクを実行する, task) for task in tasks]

            for future in as_completed(futures):
                result = future.result()

                stat = stats_by_condition[result["condition_index"]]
                stat["completed_steps"].extend(result["completed_steps"])
                stat["failed_count"] += result["failed_count"]

                total_done += result["repeat_count"]

                now = time.time()
                if now - last_ui_update >= 0.2 or total_done >= total_count:
                    進捗表示を更新する(
                        root=root,
                        progress_var=progress_var,
                        status_label=status_label,
                        detail_label=detail_label,
                        elapsed_label=elapsed_label,
                        total_done=total_done,
                        total_count=total_count,
                        start_time=start_time,
                        latest_message=(
                            f"並列実行中: 条件 {result['condition_index']} "
                            f"(チャンク {result['chunk_index'] + 1}) 完了 / "
                            f"並列数 {worker_count} / チャンクサイズ {chunk_size}"
                        )
                    )
                    last_ui_update = now

    total_elapsed = time.time() - start_time
    return stats_by_condition, total_elapsed, chunk_size


def 結果を書き込む(ws, prepared_conditions, stats_by_condition):
    for prepared in prepared_conditions:
        stat = stats_by_condition[prepared["condition_index"]]
        row = prepared["row"]

        avg_steps = 平均を計算する(stat["completed_steps"])
        failed_count = stat["failed_count"]

        ws.cell(row=row, column=17, value=avg_steps)
        ws.cell(row=row, column=18, value=failed_count)


def 保存先を選ぶ():
    return filedialog.asksaveasfilename(
        title="結果ファイルを保存",
        defaultextension=".xlsx",
        filetypes=[("Excelファイル", "*.xlsx")]
    )


def 結果保存画面を表示する(root, wb, total_elapsed):
    win = tk.Toplevel(root)
    win.title("sub1 実行完了")
    win.geometry("450x220")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="シミュレーションが完了しました",
        font=("Yu Gothic", 13, "bold")
    ).pack(pady=8)

    ttk.Label(
        frame,
        text=f"総実行時間: {秒を時分秒にする(total_elapsed)}"
    ).pack(pady=4)

    ttk.Label(
        frame,
        text="結果ファイルを保存してください"
    ).pack(pady=8)

    def 保存する():
        save_path = 保存先を選ぶ()
        if not save_path:
            return
        wb.save(save_path)
        messagebox.showinfo("保存完了", f"結果ファイルを保存しました。\n{save_path}")

    ttk.Button(frame, text="結果ファイルを保存", command=保存する).pack(pady=12)


def シミュレーション開始(
    entry_widget,
    worker_entry,
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label,
    run_button,
    sample_button
):
    path = entry_widget.get().strip()

    if not path:
        messagebox.showerror("エラー", "まず入力ファイルを選択してください。")
        return

    if not os.path.exists(path):
        messagebox.showerror("エラー", "選択されたファイルが存在しません。")
        return

    try:
        worker_count = 正整数に変換する(worker_entry.get().strip(), "並列プロセス数")
    except Exception as e:
        messagebox.showerror("入力エラー", str(e))
        return

    run_button.config(state="disabled")
    sample_button.config(state="disabled")

    try:
        progress_var.set(0)
        status_label.config(text="ファイルを読み込み中...")
        detail_label.config(text="")
        elapsed_label.config(text="")
        root.update()

        wb, ws, pattern_count, trial_count, conditions = 条件ファイルを読む(path)

        status_label.config(
            text=f"条件準備中: 条件数={pattern_count} / 各条件試行回数={trial_count}"
        )
        detail_label.config(text="実行条件を前処理しています...")
        elapsed_label.config(text="")
        root.update()

        prepared_conditions = 実行用条件一覧を準備する(conditions)

        status_label.config(
            text=f"実行準備完了: 条件数={pattern_count} / 各条件試行回数={trial_count}"
        )
        detail_label.config(
            text=f"最大step={MAX_STEPS_FIXED} / 並列数={worker_count}"
        )
        elapsed_label.config(text="これから並列実行します...")
        root.update()

        stats_by_condition, total_elapsed, chunk_size = 並列で条件を実行して集計する(
            prepared_conditions=prepared_conditions,
            trial_count=trial_count,
            worker_count=worker_count,
            root=root,
            progress_var=progress_var,
            status_label=status_label,
            detail_label=detail_label,
            elapsed_label=elapsed_label
        )

        結果を書き込む(ws, prepared_conditions, stats_by_condition)

        status_label.config(text="完了しました。保存先を選んでください。")
        detail_label.config(
            text=f"すべての試行が終了しました。並列数={worker_count} / チャンクサイズ={chunk_size}"
        )
        elapsed_label.config(text=f"総実行時間: {秒を時分秒にする(total_elapsed)}")
        root.update()

        結果保存画面を表示する(root, wb, total_elapsed)

    except Exception as e:
        messagebox.showerror("実行エラー", f"処理中にエラーが起きました。\n{e}")
    finally:
        run_button.config(state="normal")
        sample_button.config(state="normal")


def 画面を作る():
    root = tk.Tk()
    root.title("sub1 一括シミュレーション")
    root.geometry("760x400")
    root.minsize(760, 400)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="sub1 一括シミュレーション実行（並列高速版）",
        font=("Yu Gothic", 14, "bold")
    ).pack(pady=6)

    desc = (
        "1. 入力ファイル（.xlsx）を選択\n"
        "2. 並列プロセス数を設定\n"
        "3. シミュレーション開始を押す\n"
        "4. 完了後に結果ファイルを保存"
    )
    ttk.Label(frame, text=desc, justify="left").pack(anchor="w", pady=6)

    file_frame = ttk.Frame(frame)
    file_frame.pack(fill="x", pady=6)

    ttk.Label(file_frame, text="入力ファイル").pack(side="left", padx=4)

    path_entry = ttk.Entry(file_frame, width=64)
    path_entry.pack(side="left", padx=4, fill="x", expand=True)

    ttk.Button(
        file_frame,
        text="選択",
        command=lambda: ファイルを選ぶ(path_entry)
    ).pack(side="left", padx=4)

    setting_frame = ttk.Frame(frame)
    setting_frame.pack(fill="x", pady=6)

    ttk.Label(setting_frame, text="並列プロセス数").pack(side="left", padx=4)

    worker_entry = ttk.Entry(setting_frame, width=8)
    worker_entry.pack(side="left", padx=4)
    worker_entry.insert(0, str(DEFAULT_WORKER_COUNT))

    ttk.Label(
        setting_frame,
        text=f"推奨: {DEFAULT_WORKER_COUNT}（CPUコア数 - 1 の目安）",
        foreground="gray"
    ).pack(side="left", padx=8)

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill="x", pady=10)

    sample_button = ttk.Button(
        button_frame,
        text="サンプルファイルを保存",
        command=サンプルを保存する
    )
    sample_button.pack(side="left", padx=4)

    progress_var = tk.DoubleVar(value=0)

    status_label = ttk.Label(frame, text="待機中")
    detail_label = ttk.Label(frame, text="")
    elapsed_label = ttk.Label(frame, text="")

    run_button = ttk.Button(
        button_frame,
        text="シミュレーション開始",
        command=lambda: シミュレーション開始(
            path_entry,
            worker_entry,
            root,
            progress_var,
            status_label,
            detail_label,
            elapsed_label,
            run_button,
            sample_button
        )
    )
    run_button.pack(side="left", padx=4)

    progress_bar = ttk.Progressbar(
        frame,
        orient="horizontal",
        mode="determinate",
        maximum=100,
        variable=progress_var
    )
    progress_bar.pack(fill="x", pady=10)

    status_label.pack(anchor="w", pady=4)
    detail_label.pack(anchor="w", pady=4)
    elapsed_label.pack(anchor="w", pady=4)

    ttk.Label(
        frame,
        text=(
            f"固定設定: 最大step={MAX_STEPS_FIXED} / 処理間隔=毎秒{PROCESS_RATE_FIXED}回相当\n"
            "高速化内容: 固定ホールの再利用 + 条件前処理 + 並列実行 + チャンク実行"
        ),
        foreground="gray"
    ).pack(anchor="w", pady=8)

    root.mainloop()


def 実行する():
    画面を作る()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    実行する()