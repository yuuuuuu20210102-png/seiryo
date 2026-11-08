import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config.sim_settings import (
    CLASS_NAMES,
    DEFAULT_MAX_STEPS,
    DEFAULT_PROCESS_STEPS_PER_FRAME,
    DEFAULT_DISPLAY_INTERVAL_MS,
    DEFAULT_DOOR_ASSIGNMENT,
    DEFAULT_START_STEPS,
)
from hub import 描画ありでシミュレーションを実行する


def 入力値を辞書化する(entries):
    door_assignment = {}
    start_steps = {}

    for class_name in CLASS_NAMES:
        door_assignment[class_name] = entries[f"door_{class_name}"].get().strip()
        start_steps[class_name] = int(entries[f"start_{class_name}"].get().strip())

    max_steps = int(entries["max_steps"].get().strip())
    process_steps_per_frame = int(entries["process_steps_per_frame"].get().strip())
    display_interval_ms = int(entries["display_interval_ms"].get().strip())

    return {
        "door_assignment_by_name": door_assignment,
        "start_steps": start_steps,
        "max_steps": max_steps,
        "process_steps_per_frame": process_steps_per_frame,
        "display_interval_ms": display_interval_ms,
    }


def 賞状テキストを作る(result):
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("========================================")
    lines.append("         退場シミュレーション結果賞状")
    lines.append("========================================")
    lines.append("")
    lines.append(f"全員退場: {'達成' if result['completed'] else '未達成'}")
    lines.append(f"総ステップ数: {result['total_steps']}")
    lines.append(f"残人数: {result['remaining_students']}")
    lines.append("")
    lines.append("【クラス別設定】")
    lines.append("----------------------------------------")
    lines.append("クラス | 向かう扉 | 退場開始ステップ")
    lines.append("----------------------------------------")

    for class_name in CLASS_NAMES:
        door_name = result["door_assignment_by_name"][class_name]
        start_step = result["start_steps"][class_name]
        lines.append(f"{class_name:>4} | {str(door_name):>8} | {str(start_step):>16}")

    lines.append("")
    lines.append(f"表示日時: {now_text}")
    lines.append("========================================")

    return "\n".join(lines)


def 賞状画面を表示する(root, result):
    win = tk.Toplevel(root)
    win.title("賞状")
    win.geometry("680x520")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    title_label = ttk.Label(
        frame,
        text="退場シミュレーション結果賞状",
        font=("Yu Gothic", 16, "bold")
    )
    title_label.pack(pady=8)

    text_widget = tk.Text(
        frame,
        wrap="none",
        font=("Consolas", 11)
    )
    text_widget.pack(fill="both", expand=True)

    text_widget.insert("1.0", 賞状テキストを作る(result))
    text_widget.config(state="disabled")

    close_button = ttk.Button(frame, text="閉じる", command=win.destroy)
    close_button.pack(pady=10)


def 完了画面を表示する(root, result):
    win = tk.Toplevel(root)
    win.title("シミュレーション完了")
    win.geometry("420x220")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="シミュレーションが終了しました",
        font=("Yu Gothic", 14, "bold")
    ).pack(pady=12)

    ttk.Label(
        frame,
        text=f"総ステップ数: {result['total_steps']}\n残人数: {result['remaining_students']}",
        justify="center"
    ).pack(pady=10)

    def 次へ():
        win.destroy()
        賞状画面を表示する(root, result)

    ttk.Button(frame, text="次の画面へ", command=次へ).pack(pady=12)


def 実行ボタン処理(entries, root):
    try:
        params = 入力値を辞書化する(entries)
    except Exception as e:
        messagebox.showerror("入力エラー", f"入力値を確認してください。\n{e}")
        return

    result = 描画ありでシミュレーションを実行する(
        door_assignment_by_name=params["door_assignment_by_name"],
        start_steps=params["start_steps"],
        max_steps=params["max_steps"],
        process_steps_per_frame=params["process_steps_per_frame"],
        display_interval_ms=params["display_interval_ms"],
    )

    完了画面を表示する(root, result)


def ラベル付き入力(frame, row, label_text, default_value):
    ttk.Label(frame, text=label_text).grid(row=row, column=0, sticky="w", padx=4, pady=2)

    entry = ttk.Entry(frame, width=12)
    entry.grid(row=row, column=1, sticky="w", padx=4, pady=2)
    entry.insert(0, str(default_value))

    return entry


def 画面を作る():
    root = tk.Tk()
    root.title("シミュレーション設定画面")
    root.geometry("420x520")
    root.minsize(420, 520)

    main = ttk.Frame(root, padding=10)
    main.pack(fill="both", expand=True)

    entries = {}

    base_frame = ttk.LabelFrame(main, text="基本設定", padding=8)
    base_frame.pack(fill="x", expand=False, pady=6)

    entries["max_steps"] = ラベル付き入力(
        base_frame, 0, "最大ステップ数", DEFAULT_MAX_STEPS
    )
    entries["process_steps_per_frame"] = ラベル付き入力(
        base_frame, 1, "処理間隔（1表示あたり内部ステップ数）", DEFAULT_PROCESS_STEPS_PER_FRAME
    )
    entries["display_interval_ms"] = ラベル付き入力(
        base_frame, 2, "表示間隔(ms)", DEFAULT_DISPLAY_INTERVAL_MS
    )

    class_frame = ttk.LabelFrame(main, text="クラス設定", padding=8)
    class_frame.pack(fill="both", expand=True, pady=6)

    ttk.Label(class_frame, text="クラス").grid(row=0, column=0, padx=4, pady=2)
    ttk.Label(class_frame, text="向かう扉").grid(row=0, column=1, padx=4, pady=2)
    ttk.Label(class_frame, text="出発ステップ").grid(row=0, column=2, padx=4, pady=2)

    for i, class_name in enumerate(CLASS_NAMES, start=1):
        ttk.Label(class_frame, text=class_name).grid(row=i, column=0, padx=4, pady=2, sticky="w")

        door_entry = ttk.Entry(class_frame, width=10)
        door_entry.grid(row=i, column=1, padx=4, pady=2)
        door_entry.insert(0, str(DEFAULT_DOOR_ASSIGNMENT[class_name]))
        entries[f"door_{class_name}"] = door_entry

        start_entry = ttk.Entry(class_frame, width=10)
        start_entry.grid(row=i, column=2, padx=4, pady=2)
        start_entry.insert(0, str(DEFAULT_START_STEPS[class_name]))
        entries[f"start_{class_name}"] = start_entry

    button_frame = ttk.Frame(main)
    button_frame.pack(fill="x", expand=False, pady=10)

    run_button = ttk.Button(
        button_frame,
        text="シミュレーション開始",
        command=lambda: 実行ボタン処理(entries, root)
    )
    run_button.pack(side="left", padx=4)

    root.mainloop()


def 実行する():
    画面を作る()


if __name__ == "__main__":
    画面を作る()