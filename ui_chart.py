import tkinter as tk
from config import COLORS
from db import get_metrics

CHART_COLORS = ["#4a90d9", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                "#1abc9c", "#e67e22", "#3498db"]


def show_chart(parent, exp: dict):
    """显示单个实验的训练曲线"""
    metrics = get_metrics(exp["id"])
    if not metrics:
        from tkinter import messagebox
        messagebox.showinfo("提示", "没有训练指标数据，请先导入")
        return
    _show_plot(parent, f"训练曲线 - {exp['name']}", [(exp["name"], metrics)])


def show_multi_chart(parent, experiments: list[dict]):
    """显示多个实验的对比曲线"""
    data = []
    for exp in experiments:
        metrics = get_metrics(exp["id"])
        if metrics:
            data.append((exp["name"], metrics))
    if not data:
        from tkinter import messagebox
        messagebox.showinfo("提示", "选中的实验没有训练指标数据")
        return
    _show_plot(parent, "训练曲线对比", data)


def _show_plot(parent, title: str, datasets: list[tuple]):
    """用 matplotlib 画训练曲线"""
    try:
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except ImportError:
        from tkinter import messagebox
        messagebox.showerror("错误", "需要安装 matplotlib: pip install matplotlib")
        return

    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=COLORS["bg"])
    win.geometry("800x500")

    fig = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS["bg"])

    # Loss 图
    ax1 = fig.add_subplot(121)
    ax1.set_title("Loss", fontsize=11)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")

    # Acc 图
    ax2 = fig.add_subplot(122)
    ax2.set_title("Accuracy", fontsize=11)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Acc (%)")

    for i, (name, metrics) in enumerate(datasets):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        epochs = [m["epoch"] for m in metrics]

        train_loss = [m.get("train_loss") for m in metrics]
        val_loss = [m.get("val_loss") for m in metrics]
        train_acc = [m.get("train_acc") for m in metrics]
        val_acc = [m.get("val_acc") for m in metrics]

        if any(v is not None for v in train_loss):
            ax1.plot(epochs, train_loss, color=color, linestyle="-", label=f"{name} train", alpha=0.7)
        if any(v is not None for v in val_loss):
            ax1.plot(epochs, val_loss, color=color, linestyle="--", label=f"{name} val")

        if any(v is not None for v in train_acc):
            ax2.plot(epochs, train_acc, color=color, linestyle="-", label=f"{name} train", alpha=0.7)
        if any(v is not None for v in val_acc):
            ax2.plot(epochs, val_acc, color=color, linestyle="--", label=f"{name} val")

    ax1.legend(fontsize=8)
    ax2.legend(fontsize=8)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
