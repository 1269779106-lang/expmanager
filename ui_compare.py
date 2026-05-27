import tkinter as tk
from tkinter import ttk
from config import COLORS, STATUS_MAP
from db import get_metrics


def show_compare(parent, experiments: list[dict]):
    win = tk.Toplevel(parent)
    win.title("实验对比")
    win.configure(bg=COLORS["bg"])
    win.geometry("900x500")

    # 表格
    cols = ("name", "router", "status", "acc", "flops", "avg_k", "time")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=len(experiments))
    tree.heading("name", text="实验名称")
    tree.heading("router", text="路由器")
    tree.heading("status", text="状态")
    tree.heading("acc", text="Acc(%)")
    tree.heading("flops", text="FLOPs")
    tree.heading("avg_k", text="avg_latents")
    tree.heading("time", text="训练时间")

    tree.column("name", width=120)
    tree.column("router", width=80)
    tree.column("status", width=80)
    tree.column("acc", width=80)
    tree.column("flops", width=100)
    tree.column("avg_k", width=100)
    tree.column("time", width=100)

    for exp in experiments:
        acc = f"{exp['best_acc']}" if exp.get("best_acc") else "?"
        flops = exp.get("flops") or "?"
        avg_k = str(exp["avg_latents"]) if exp.get("avg_latents") else "?"
        t = exp.get("train_time") or "?"
        status = STATUS_MAP.get(exp["status"], ("?",))[0]
        tree.insert("", tk.END, values=(exp["name"], exp["router_type"], status, acc, flops, avg_k, t))

    tree.pack(fill=tk.X, padx=16, pady=16)

    # 导出按钮
    btn_frame = tk.Frame(win, bg=COLORS["bg"])
    btn_frame.pack(fill=tk.X, padx=16, pady=(0, 16))

    def export_md():
        lines = ["| 方法 | 路由器 | Acc@1 | FLOPs | avg_k | 训练时间 |",
                 "|------|--------|-------|-------|-------|---------|"]
        for exp in experiments:
            acc = f"{exp['best_acc']}%" if exp.get("best_acc") else "?"
            flops = exp.get("flops") or "?"
            avg_k = str(exp["avg_latents"]) if exp.get("avg_latents") else "?"
            t = exp.get("train_time") or "?"
            lines.append(f"| {exp['name']} | {exp['router_type']} | {acc} | {flops} | {avg_k} | {t} |")
        md = "\n".join(lines)
        parent.clipboard_clear()
        parent.clipboard_append(md)
        from tkinter import messagebox
        messagebox.showinfo("已复制", "Markdown 表格已复制到剪贴板")

    def show_curves():
        from ui_chart import show_multi_chart
        show_multi_chart(parent, experiments)

    tk.Button(btn_frame, text="导出 Markdown", command=export_md,
              font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
    tk.Button(btn_frame, text="查看曲线对比", command=show_curves,
              font=("Microsoft YaHei", 10), bg=COLORS["accent"], fg="white",
              relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
