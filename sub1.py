import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import Workbook, load_workbook

from config.sim_settings import CLASS_NAMES
from hub import 描画なしでシミュレーションを実行する


MAX_STEPS_FIXED = 3000
PROCESS_RATE_FIXED = 1000


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


def 条件ファイルを読む(path):
    wb = load_workbook(path)
    ws = wb.active

    pattern_count = int(セル値を読む(ws, 2, 1, 0))
    trial_count = int(セル値を読む(ws, 2, 2, 1))

    conditions = []

    for i in range(pattern_count):
        row = 5 + i

        door_assignment = {}
        start_steps = {}

        for idx, class_name in enumerate(CLASS_NAMES):
            door_assignment[class_name] = str(セル値を読む(ws, row, 1 + idx, "5"))

        for idx, class_name in enumerate(CLASS_NAMES):
            start_steps[class_name] = int(セル値を読む(ws, row, 9 + idx, 0))

        conditions.append({
            "row": row,
            "condition_index": i + 1,
            "door_assignment_by_name": door_assignment,
            "start_steps": start_steps,
        })

    return wb, ws, pattern_count, trial_count, conditions


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
    condition_index,
    pattern_count,
    trial_index,
    trial_count,
    start_time
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
    detail_label.config(
        text=f"条件 {condition_index} / {pattern_count}   試行 {trial_index} / {trial_count}"
    )
    elapsed_label.config(
        text=f"経過時間: {秒を時分秒にする(elapsed)}   残り予想: {秒を時分秒にする(remain)}"
    )
    root.update_idletasks()


def 条件を実行する(
    condition,
    trial_count,
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label,
    total_done_ref,
    total_count,
    pattern_count,
    start_time
):
    completed_steps = []
    failed_count = 0

    for trial_idx in range(1, trial_count + 1):
        result = 描画なしでシミュレーションを実行する(
            door_assignment_by_name=condition["door_assignment_by_name"],
            start_steps=condition["start_steps"],
            max_steps=MAX_STEPS_FIXED,
        )

        if result["completed"]:
            completed_steps.append(result["total_steps"])
        else:
            failed_count += 1

        total_done_ref["value"] += 1

        進捗表示を更新する(
            root=root,
            progress_var=progress_var,
            status_label=status_label,
            detail_label=detail_label,
            elapsed_label=elapsed_label,
            total_done=total_done_ref["value"],
            total_count=total_count,
            condition_index=condition["condition_index"],
            pattern_count=pattern_count,
            trial_index=trial_idx,
            trial_count=trial_count,
            start_time=start_time
        )

    avg_steps = 平均を計算する(completed_steps)
    return avg_steps, failed_count


def 結果を書き込む(
    wb,
    ws,
    conditions,
    trial_count,
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label
):
    total_count = len(conditions) * trial_count
    total_done_ref = {"value": 0}
    start_time = time.time()

    for condition in conditions:
        avg_steps, failed_count = 条件を実行する(
            condition=condition,
            trial_count=trial_count,
            root=root,
            progress_var=progress_var,
            status_label=status_label,
            detail_label=detail_label,
            elapsed_label=elapsed_label,
            total_done_ref=total_done_ref,
            total_count=total_count,
            pattern_count=len(conditions),
            start_time=start_time
        )

        row = condition["row"]
        ws.cell(row=row, column=17, value=avg_steps)    # Q列
        ws.cell(row=row, column=18, value=failed_count) # R列

    total_elapsed = time.time() - start_time
    return wb, total_elapsed


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

    ttk.Button(frame, text="結果ファイルをダウンロード（保存）", command=保存する).pack(pady=12)


def シミュレーション開始(
    entry_widget,
    root,
    progress_var,
    status_label,
    detail_label,
    elapsed_label
):
    path = entry_widget.get().strip()

    if not path:
        messagebox.showerror("エラー", "まず入力ファイルを選択してください。")
        return

    if not os.path.exists(path):
        messagebox.showerror("エラー", "選択されたファイルが存在しません。")
        return

    try:
        progress_var.set(0)
        status_label.config(text="ファイルを読み込み中...")
        detail_label.config(text="")
        elapsed_label.config(text="")
        root.update()

        wb, ws, pattern_count, trial_count, conditions = 条件ファイルを読む(path)

        status_label.config(
            text=f"実行準備完了: 条件数={pattern_count} / 各条件試行回数={trial_count}"
        )
        detail_label.config(
            text=f"最大step={MAX_STEPS_FIXED} / 処理間隔=毎秒{PROCESS_RATE_FIXED}回相当"
        )
        elapsed_label.config(text="これから実行します...")
        root.update()

        wb, total_elapsed = 結果を書き込む(
            wb=wb,
            ws=ws,
            conditions=conditions,
            trial_count=trial_count,
            root=root,
            progress_var=progress_var,
            status_label=status_label,
            detail_label=detail_label,
            elapsed_label=elapsed_label
        )

        status_label.config(text="完了しました。保存先を選んでください。")
        detail_label.config(text="すべての試行が終了しました。")
        elapsed_label.config(text=f"総実行時間: {秒を時分秒にする(total_elapsed)}")
        root.update()

        結果保存画面を表示する(root, wb, total_elapsed)

    except Exception as e:
        messagebox.showerror("実行エラー", f"処理中にエラーが起きました。\n{e}")


def 画面を作る():
    root = tk.Tk()
    root.title("sub1 一括シミュレーション")
    root.geometry("620x340")
    root.minsize(620, 340)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="sub1 一括シミュレーション実行",
        font=("Yu Gothic", 14, "bold")
    ).pack(pady=6)

    desc = (
        "1. 入力ファイル（.xlsx）を選択\n"
        "2. シミュレーション開始を押す\n"
        "3. 完了後に結果ファイルを保存"
    )
    ttk.Label(frame, text=desc, justify="left").pack(anchor="w", pady=6)

    file_frame = ttk.Frame(frame)
    file_frame.pack(fill="x", pady=6)

    ttk.Label(file_frame, text="入力ファイル").pack(side="left", padx=4)

    path_entry = ttk.Entry(file_frame, width=56)
    path_entry.pack(side="left", padx=4, fill="x", expand=True)

    ttk.Button(
        file_frame,
        text="選択",
        command=lambda: ファイルを選ぶ(path_entry)
    ).pack(side="left", padx=4)

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill="x", pady=10)

    ttk.Button(
        button_frame,
        text="サンプルファイルをダウンロード",
        command=サンプルを保存する
    ).pack(side="left", padx=4)

    progress_var = tk.DoubleVar(value=0)

    ttk.Button(
        button_frame,
        text="シミュレーション開始",
        command=lambda: シミュレーション開始(
            path_entry,
            root,
            progress_var,
            status_label,
            detail_label,
            elapsed_label
        )
    ).pack(side="left", padx=4)

    progress_bar = ttk.Progressbar(
        frame,
        orient="horizontal",
        mode="determinate",
        maximum=100,
        variable=progress_var
    )
    progress_bar.pack(fill="x", pady=10)

    status_label = ttk.Label(frame, text="待機中")
    status_label.pack(anchor="w", pady=4)

    detail_label = ttk.Label(frame, text="")
    detail_label.pack(anchor="w", pady=4)

    elapsed_label = ttk.Label(frame, text="")
    elapsed_label.pack(anchor="w", pady=4)

    ttk.Label(
        frame,
        text=f"固定設定: 最大step={MAX_STEPS_FIXED} / 処理間隔=毎秒{PROCESS_RATE_FIXED}回相当",
        foreground="gray"
    ).pack(anchor="w", pady=8)

    root.mainloop()


def 実行する():
    画面を作る()


if __name__ == "__main__":
    実行する()