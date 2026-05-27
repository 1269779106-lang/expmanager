import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, STATUS_MAP
from db import (get_experiments, get_experiment, add_experiment, update_experiment,
                delete_experiment, get_phases, add_phase, get_metrics, add_metrics,
                clear_metrics)
from ui_dialog import ExperimentDialog, MetricsImportDialog

# 科研进度排序：Phase 内的实验按优先级排
ROUTER_ORDER = {
    "fixed": 0, "progressive": 1, "R1": 2, "R2": 3, "R3": 4, "R4": 5,
}
STATUS_ORDER = {"running": 0, "planned": 1, "completed": 2, "failed": 3}

GUIDE_TEXT = """【操作指南】

1. 新建实验
   点击顶部 [+ 新建实验]，填写配置后保存

2. 编辑实验
   选中实验 → 右侧详情 → 点 [编辑]

3. 导入训练指标
   选中实验 → [导入指标] → 粘贴 CSV 数据
   格式: epoch,train_loss,val_loss,train_acc,val_acc

4. 查看训练曲线
   选中实验 → [查看曲线]（需先导入指标）

5. 对比实验
   按住 Ctrl 多选 → 点 [对比选中]

6. 导出论文表格
   点 [导出表格] → Markdown 自动复制到剪贴板

7. 排序
   左侧 [排序] 下拉框选择排序方式

【科研顺序】
   Phase 1 → Phase 2 → Phase 3 → Phase 4
   先跑基线(FIX)，再跑路由器(R1)，最后对比汇总
"""


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("实验记录管理器")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1100x700")
        self._selected_exp = None
        self._build()

    def _build(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg=COLORS["bg2"], height=48)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="实验记录管理器", font=("Microsoft YaHei", 14, "bold"),
                 bg=COLORS["bg2"], fg=COLORS["fg"]).pack(side=tk.LEFT, padx=16)

        tk.Button(toolbar, text="? 操作指南", command=self._show_guide,
                  font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=12).pack(side=tk.RIGHT, padx=8, pady=8)
        tk.Button(toolbar, text="+ 新建实验", command=self._new_exp,
                  font=("Microsoft YaHei", 10), bg=COLORS["accent"], fg="white",
                  relief=tk.FLAT, padx=12).pack(side=tk.RIGHT, padx=4, pady=8)
        tk.Button(toolbar, text="对比选中", command=self._compare,
                  font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=12).pack(side=tk.RIGHT, padx=4, pady=8)
        tk.Button(toolbar, text="导出表格", command=self._export_md,
                  font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=12).pack(side=tk.RIGHT, padx=4, pady=8)

        tk.Frame(self.root, height=1, bg=COLORS["border"]).pack(fill=tk.X)

        # 主体
        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True)

        # 左侧面板
        left = tk.Frame(body, bg=COLORS["bg2"], width=320)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # 筛选 + 排序
        filter_frame = tk.Frame(left, bg=COLORS["bg2"], padx=8, pady=8)
        filter_frame.pack(fill=tk.X)

        tk.Label(filter_frame, text="筛选与排序", font=("Microsoft YaHei", 9, "bold"),
                 bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(anchor="w")

        self.filter_phase = tk.StringVar(value="全部")
        self.filter_status = tk.StringVar(value="全部")
        self.filter_router = tk.StringVar(value="全部")
        self.sort_var = tk.StringVar(value="科研顺序")

        row = tk.Frame(filter_frame, bg=COLORS["bg2"])
        row.pack(fill=tk.X, pady=4)
        self._mini_combo(row, "Phase", self.filter_phase, self._get_phase_names())
        self._mini_combo(row, "状态", self.filter_status, ["全部"] + list(STATUS_MAP.keys()))

        row2 = tk.Frame(filter_frame, bg=COLORS["bg2"])
        row2.pack(fill=tk.X, pady=4)
        self._mini_combo(row2, "路由器", self.filter_router, ["全部", "fixed", "progressive", "R1", "R2", "R3", "R4"])
        self._mini_combo(row2, "排序", self.sort_var,
                         ["科研顺序", "Phase顺序", "状态", "名称", "精度高→低", "精度低→高"])

        for var in [self.filter_phase, self.filter_status, self.filter_router, self.sort_var]:
            var.trace_add("write", lambda *_: self._refresh_list())

        # 进度概览
        self.progress_frame = tk.Frame(left, bg=COLORS["bg2"], padx=8, pady=4)
        self.progress_frame.pack(fill=tk.X)
        self._build_progress()

        # 实验列表
        list_frame = tk.Frame(left, bg=COLORS["bg2"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.exp_list = tk.Listbox(list_frame, font=("Microsoft YaHei", 11),
                                   bg=COLORS["bg2"], fg=COLORS["fg"],
                                   selectbackground=COLORS["accent_light"],
                                   selectforeground=COLORS["fg"],
                                   relief=tk.FLAT, bd=0, highlightthickness=0,
                                   activestyle="none")
        self.exp_list.pack(fill=tk.BOTH, expand=True)
        self.exp_list.bind("<<ListboxSelect>>", self._on_select)

        # 右侧详情
        self.detail_frame = tk.Frame(body, bg=COLORS["bg"])
        self.detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self._build_detail_empty()
        self._refresh_list()

    def _build_progress(self):
        for w in self.progress_frame.winfo_children():
            w.destroy()
        exps = get_experiments()
        total = len(exps)
        done = sum(1 for e in exps if e["status"] == "completed")
        running = sum(1 for e in exps if e["status"] == "running")
        planned = sum(1 for e in exps if e["status"] == "planned")

        tk.Label(self.progress_frame,
                 text=f"进度: {done}/{total} 完成 | {running} 进行中 | {planned} 待做",
                 font=("Microsoft YaHei", 9), bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(anchor="w")

        # 进度条
        bar_frame = tk.Frame(self.progress_frame, bg=COLORS["border"], height=6)
        bar_frame.pack(fill=tk.X, pady=4)
        bar_frame.pack_propagate(False)
        if total > 0:
            done_width = int(300 * done / total)
            if done_width > 0:
                tk.Frame(bar_frame, bg=COLORS["success"], width=done_width).pack(side=tk.LEFT, fill=tk.Y)

    def _get_phase_names(self):
        phases = get_phases()
        return ["全部"] + [p["name"] for p in phases]

    def _mini_combo(self, parent, label, var, values):
        col = tk.Frame(parent, bg=COLORS["bg2"])
        col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Label(col, text=label, font=("Microsoft YaHei", 8),
                 bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(anchor="w")
        ttk.Combobox(col, textvariable=var, values=values, state="readonly",
                     font=("Microsoft YaHei", 9), width=10).pack(fill=tk.X)

    def _refresh_list(self):
        self.exp_list.delete(0, tk.END)
        self._exps = get_experiments()
        self._filtered = []

        phase_filter = self.filter_phase.get()
        status_filter = self.filter_status.get()
        router_filter = self.filter_router.get()

        for exp in self._exps:
            if phase_filter != "全部" and exp.get("phase_name") != phase_filter:
                continue
            if status_filter != "全部" and exp["status"] != status_filter:
                continue
            if router_filter != "全部" and exp["router_type"] != router_filter:
                continue
            self._filtered.append(exp)

        # 排序
        sort_mode = self.sort_var.get()
        if sort_mode == "科研顺序":
            self._filtered.sort(key=lambda e: (
                e.get("phase_id") or 99,
                ROUTER_ORDER.get(e["router_type"], 99),
                e["name"]
            ))
        elif sort_mode == "Phase顺序":
            self._filtered.sort(key=lambda e: (e.get("phase_id") or 99, e["name"]))
        elif sort_mode == "状态":
            self._filtered.sort(key=lambda e: (STATUS_ORDER.get(e["status"], 99), e["name"]))
        elif sort_mode == "名称":
            self._filtered.sort(key=lambda e: e["name"])
        elif sort_mode == "精度高→低":
            self._filtered.sort(key=lambda e: -(e.get("best_acc") or 0))
        elif sort_mode == "精度低→高":
            self._filtered.sort(key=lambda e: (e.get("best_acc") or 999))

        for i, exp in enumerate(self._filtered):
            status_icon = STATUS_MAP.get(exp["status"], ("", ""))[0]
            phase = exp.get("phase_name", "")
            phase_short = phase.split(":")[0] if ":" in phase else phase
            prefix = f"[{phase_short}] " if phase_short else ""
            self.exp_list.insert(tk.END, f"{status_icon} {prefix}{exp['name']}")

        self._build_progress()

    def _on_select(self, event):
        sel = self.exp_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._filtered):
            self._selected_exp = self._filtered[idx]
            self._show_detail(self._selected_exp)

    def _build_detail_empty(self):
        for w in self.detail_frame.winfo_children():
            w.destroy()
        tk.Label(self.detail_frame, text="选择左侧实验查看详情\n\n按科研顺序排列：先 Phase 1 基线，再 Phase 2 路由器",
                 font=("Microsoft YaHei", 11), bg=COLORS["bg"], fg=COLORS["fg2"],
                 justify=tk.CENTER).pack(expand=True)

    def _show_detail(self, exp):
        for w in self.detail_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.detail_frame, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.detail_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLORS["bg"])
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        f = inner

        # 标题行
        header = tk.Frame(f, bg=COLORS["bg"])
        header.pack(fill=tk.X, padx=16, pady=(12, 4))
        tk.Label(header, text=exp["name"], font=("Microsoft YaHei", 16, "bold"),
                 bg=COLORS["bg"], fg=COLORS["fg"]).pack(side=tk.LEFT)
        status_text, status_color = STATUS_MAP.get(exp["status"], ("未知", COLORS["fg2"]))
        tk.Label(header, text=status_text, font=("Microsoft YaHei", 11),
                 bg=COLORS["bg"], fg=status_color).pack(side=tk.LEFT, padx=12)

        # 操作按钮
        btn_row = tk.Frame(f, bg=COLORS["bg"])
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Button(btn_row, text="编辑", command=lambda: self._edit_exp(exp),
                  font=("Microsoft YaHei", 9), relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="导入指标", command=lambda: self._import_metrics(exp),
                  font=("Microsoft YaHei", 9), relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="查看曲线", command=lambda: self._show_chart(exp),
                  font=("Microsoft YaHei", 9), relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="删除", command=lambda: self._delete_exp(exp),
                  font=("Microsoft YaHei", 9), fg=COLORS["danger"], relief=tk.FLAT, padx=8).pack(side=tk.RIGHT, padx=2)

        self._info_card(f, "基本信息", [
            ("Phase", exp.get("phase_name", "-")),
            ("路由器", exp["router_type"]),
            ("数据集", exp["dataset"]),
            ("备注", exp.get("notes", "") or "-"),
        ])
        self._info_card(f, "模型配置", [
            ("dim", str(exp["dim"])),
            ("depth", str(exp["depth"])),
            ("max_latents", str(exp["max_latents"])),
            ("patch_size", str(exp["patch_size"])),
        ])
        self._info_card(f, "训练配置", [
            ("epochs", str(exp["epochs"])),
            ("batch_size", str(exp["batch_size"])),
            ("lr", str(exp["lr"])),
            ("optimizer", exp["optimizer"]),
        ])
        if exp.get("best_acc") or exp.get("flops"):
            self._info_card(f, "实验结果", [
                ("Best Acc", f"{exp['best_acc']}%" if exp.get("best_acc") else "-"),
                ("Best Epoch", str(exp["best_epoch"]) if exp.get("best_epoch") else "-"),
                ("Avg Latents", str(exp["avg_latents"]) if exp.get("avg_latents") else "-"),
                ("FLOPs", exp.get("flops") or "-"),
                ("训练时间", exp.get("train_time") or "-"),
            ])
        metrics = get_metrics(exp["id"])
        if metrics:
            last = metrics[-1]
            self._info_card(f, f"训练指标（共 {len(metrics)} 个 epoch）", [
                ("train_loss", f"{last['train_loss']:.4f}" if last.get("train_loss") else "-"),
                ("val_loss", f"{last['val_loss']:.4f}" if last.get("val_loss") else "-"),
                ("train_acc", f"{last['train_acc']:.2f}%" if last.get("train_acc") else "-"),
                ("val_acc", f"{last['val_acc']:.2f}%" if last.get("val_acc") else "-"),
            ])

    def _info_card(self, parent, title, items):
        card = tk.Frame(parent, bg=COLORS["bg2"], padx=12, pady=8)
        card.pack(fill=tk.X, padx=16, pady=4)
        tk.Label(card, text=title, font=("Microsoft YaHei", 10, "bold"),
                 bg=COLORS["bg2"], fg=COLORS["fg"]).pack(anchor="w", pady=(0, 4))
        for key, val in items:
            row = tk.Frame(card, bg=COLORS["bg2"])
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{key}:", width=12, anchor="w", font=("Microsoft YaHei", 10),
                     bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(side=tk.LEFT)
            tk.Label(row, text=str(val), font=("Microsoft YaHei", 10),
                     bg=COLORS["bg2"], fg=COLORS["fg"], anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _show_guide(self):
        win = tk.Toplevel(self.root)
        win.title("操作指南")
        win.configure(bg=COLORS["bg2"])
        win.geometry("500x520")
        win.transient(self.root)
        text = tk.Text(win, font=("Microsoft YaHei", 11), bg=COLORS["bg2"], fg=COLORS["fg"],
                       relief=tk.FLAT, padx=20, pady=16, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", GUIDE_TEXT)
        text.configure(state=tk.DISABLED)

    def _new_exp(self):
        phases = get_phases()
        if not phases:
            add_phase("Phase 1", "")
            phases = get_phases()
        dlg = ExperimentDialog(self.root, phases)
        if dlg.result:
            add_experiment(dlg.result)
            self._refresh_list()

    def _edit_exp(self, exp):
        phases = get_phases()
        dlg = ExperimentDialog(self.root, phases, exp)
        if dlg.result:
            update_experiment(exp["id"], **dlg.result)
            self._refresh_list()
            updated = get_experiment(exp["id"])
            if updated:
                self._show_detail(updated)

    def _delete_exp(self, exp):
        if messagebox.askyesno("确认", f"删除实验 {exp['name']}？"):
            delete_experiment(exp["id"])
            self._refresh_list()
            self._build_detail_empty()

    def _import_metrics(self, exp):
        dlg = MetricsImportDialog(self.root, exp["name"])
        if dlg.result:
            clear_metrics(exp["id"])
            add_metrics(exp["id"], dlg.result)
            messagebox.showinfo("成功", f"导入 {len(dlg.result)} 条记录")
            updated = get_experiment(exp["id"])
            if updated:
                self._show_detail(updated)

    def _show_chart(self, exp):
        from ui_chart import show_chart
        show_chart(self.root, exp)

    def _compare(self):
        selected = self.exp_list.curselection()
        if len(selected) < 2:
            messagebox.showinfo("提示", "请按住 Ctrl 选择至少 2 个实验")
            return
        exps = [self._filtered[i] for i in selected]
        from ui_compare import show_compare
        show_compare(self.root, exps)

    def _export_md(self):
        if not self._filtered:
            messagebox.showinfo("提示", "没有实验数据")
            return
        lines = ["| 方法 | 路由器 | Acc@1 | FLOPs | avg_k | 训练时间 | 状态 |",
                 "|------|--------|-------|-------|-------|---------|------|"]
        for exp in self._filtered:
            acc = f"{exp['best_acc']}%" if exp.get("best_acc") else "?"
            flops = exp.get("flops") or "?"
            avg_k = str(exp["avg_latents"]) if exp.get("avg_latents") else "?"
            t = exp.get("train_time") or "?"
            status = STATUS_MAP.get(exp["status"], ("?",))[0]
            lines.append(f"| {exp['name']} | {exp['router_type']} | {acc} | {flops} | {avg_k} | {t} | {status} |")
        md = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(md)
        messagebox.showinfo("已复制", "Markdown 表格已复制到剪贴板\n可直接粘贴到论文中")
