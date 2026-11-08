import tkinter as tk
from tkinter import ttk

import sub1
import sub2


def sub1を実行する(root):
    root.destroy()
    sub1.実行する()


def sub2を実行する(root):
    root.destroy()
    sub2.実行する()


def 画面を作る():
    root = tk.Tk()
    root.title("実行モード選択")
    root.geometry("360x220")
    root.minsize(360, 220)

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    title = ttk.Label(
        frame,
        text="実行するモードを選んでください",
        font=("Yu Gothic", 14, "bold")
    )
    title.pack(pady=12)

    desc = ttk.Label(
        frame,
        text="研究用: 条件ファイルを読んで描画なしで一括実行\n観察用: 条件を入力して描画ありで実行",
        justify="center"
    )
    desc.pack(pady=8)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=20)

    sub1_button = ttk.Button(
        button_frame,
        text="研究用",
        command=lambda: sub1を実行する(root)
    )
    sub1_button.grid(row=0, column=0, padx=10)

    sub2_button = ttk.Button(
        button_frame,
        text="観察用",
        command=lambda: sub2を実行する(root)
    )
    sub2_button.grid(row=0, column=1, padx=10)

    root.mainloop()


if __name__ == "__main__":
    画面を作る()