import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, STATUS_MAP, ROUTER_TYPES, DATASETS


class ExperimentDialog:
    """新建/编辑实验对话框"""

    def __init__(self, parent, phases: list[dict], experiment: dict = None):
        self.result = None
        self._phases = phases

        self.win = tk.Toplevel(parent)
        self.win.title("编辑实验" if experiment else "新建实验")
        self.win.configure(bg=COLORS["bg2"])
        self.win.geometry("520x620")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self._build(experiment)
        self.win.wait_window()

    def _build(self, exp):
        frame = tk.Frame(self.win, bg=COLORS["bg2"], padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # 基本信息
        self._section(frame, "基本信息")
        self.name_var = tk.StringVar(value=exp["name"] if exp else "")
        self._field(frame, "实验名称", self.name_var)

        self.phase_var = tk.StringVar()
        phase_names = [p["name"] for p in self._phases]
        if exp and exp.get("phase_name"):
            self.phase_var.set(exp["phase_name"])
        elif phase_names:
            self.phase_var.set(phase_names[0])
        self._combo(frame, "Phase", self.phase_var, phase_names)

        self.router_var = tk.StringVar(value=exp["router_type"] if exp else "fixed")
        self._combo(frame, "路由器类型", self.router_var, ROUTER_TYPES)

        self.status_var = tk.StringVar(value=exp["status"] if exp else "planned")
        self._combo(frame, "状态", self.status_var, list(STATUS_MAP.keys()))

        self.dataset_var = tk.StringVar(value=exp.get("dataset", "CIFAR-100") if exp else "CIFAR-100")
        self._combo(frame, "数据集", self.dataset_var, DATASETS)

        # 模型配置
        self._section(frame, "模型配置")
        row = tk.Frame(frame, bg=COLORS["bg2"])
        row.pack(fill=tk.X, pady=2)
        self.dim_var = tk.StringVar(value=str(exp["dim"]) if exp and exp.get("dim") else "256")
        self.depth_var = tk.StringVar(value=str(exp["depth"]) if exp and exp.get("depth") else "6")
        self.latents_var = tk.StringVar(value=str(exp["max_latents"]) if exp and exp.get("max_latents") else "256")
        self.patch_var = tk.StringVar(value=str(exp["patch_size"]) if exp and exp.get("patch_size") else "4")
        self._small_field(row, "dim", self.dim_var)
        self._small_field(row, "depth", self.depth_var)
        self._small_field(row, "max_latents", self.latents_var)
        self._small_field(row, "patch_size", self.patch_var)

        # 训练配置
        self._section(frame, "训练配置")
        row2 = tk.Frame(frame, bg=COLORS["bg2"])
        row2.pack(fill=tk.X, pady=2)
        self.epochs_var = tk.StringVar(value=str(exp["epochs"]) if exp and exp.get("epochs") else "100")
        self.bs_var = tk.StringVar(value=str(exp["batch_size"]) if exp and exp.get("batch_size") else "128")
        self.lr_var = tk.StringVar(value=str(exp["lr"]) if exp and exp.get("lr") else "3e-4")
        self.optim_var = tk.StringVar(value=exp["optimizer"] if exp and exp.get("optimizer") else "AdamW")
        self._small_field(row2, "epochs", self.epochs_var)
        self._small_field(row2, "batch_size", self.bs_var)
        self._small_field(row2, "lr", self.lr_var)
        self._small_field(row2, "optimizer", self.optim_var)

        # 结果
        self._section(frame, "实验结果（可选）")
        row3 = tk.Frame(frame, bg=COLORS["bg2"])
        row3.pack(fill=tk.X, pady=2)
        self.acc_var = tk.StringVar(value=str(exp["best_acc"]) if exp and exp.get("best_acc") else "")
        self.flops_var = tk.StringVar(value=exp["flops"] if exp and exp.get("flops") else "")
        self.time_var = tk.StringVar(value=exp["train_time"] if exp and exp.get("train_time") else "")
        self._small_field(row3, "best_acc(%)", self.acc_var)
        self._small_field(row3, "FLOPs", self.flops_var)
        self._small_field(row3, "train_time", self.time_var)

        # 备注
        self._section(frame, "备注")
        self.notes_text = tk.Text(frame, height=4, font=("Microsoft YaHei", 10),
                                  bg=COLORS["bg"], fg=COLORS["fg"], relief=tk.FLAT, bd=6)
        self.notes_text.pack(fill=tk.X, pady=4)
        if exp and exp.get("notes"):
            self.notes_text.insert("1.0", exp["notes"])

        # 按钮
        btn_frame = tk.Frame(frame, bg=COLORS["bg2"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Button(btn_frame, text="取消", command=self.win.destroy,
                  font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=20).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="保存", command=self._save,
                  font=("Microsoft YaHei", 10), bg=COLORS["accent"], fg="white",
                  relief=tk.FLAT, padx=20).pack(side=tk.RIGHT, padx=4)

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入实验名称")
            return

        phase_id = None
        for p in self._phases:
            if p["name"] == self.phase_var.get():
                phase_id = p["id"]
                break

        try:
            dim = int(self.dim_var.get())
            depth = int(self.depth_var.get())
            max_lat = int(self.latents_var.get())
            patch = int(self.patch_var.get())
            epochs = int(self.epochs_var.get())
            bs = int(self.bs_var.get())
            lr = float(self.lr_var.get())
        except ValueError:
            messagebox.showwarning("提示", "数值格式错误")
            return

        acc_str = self.acc_var.get().strip()
        best_acc = float(acc_str) if acc_str else None

        self.result = {
            "phase_id": phase_id,
            "name": name,
            "router_type": self.router_var.get(),
            "status": self.status_var.get(),
            "dataset": self.dataset_var.get(),
            "dim": dim,
            "depth": depth,
            "max_latents": max_lat,
            "patch_size": patch,
            "epochs": epochs,
            "batch_size": bs,
            "lr": lr,
            "optimizer": self.optim_var.get(),
            "best_acc": best_acc,
            "flops": self.flops_var.get().strip() or None,
            "train_time": self.time_var.get().strip() or None,
            "notes": self.notes_text.get("1.0", tk.END).strip(),
        }
        self.win.destroy()

    def _section(self, parent, text):
        tk.Label(parent, text=text, font=("Microsoft YaHei", 10, "bold"),
                 bg=COLORS["bg2"], fg=COLORS["fg"], anchor="w").pack(fill=tk.X, pady=(10, 4))

    def _field(self, parent, label, var):
        row = tk.Frame(parent, bg=COLORS["bg2"])
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label, width=12, anchor="w", font=("Microsoft YaHei", 10),
                 bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=var, font=("Microsoft YaHei", 10),
                 bg=COLORS["bg"], fg=COLORS["fg"], relief=tk.FLAT, bd=4).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _small_field(self, parent, label, var):
        col = tk.Frame(parent, bg=COLORS["bg2"])
        col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Label(col, text=label, font=("Microsoft YaHei", 8),
                 bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(anchor="w")
        tk.Entry(col, textvariable=var, font=("Microsoft YaHei", 10), width=10,
                 bg=COLORS["bg"], fg=COLORS["fg"], relief=tk.FLAT, bd=4).pack(fill=tk.X)

    def _combo(self, parent, label, var, values):
        row = tk.Frame(parent, bg=COLORS["bg2"])
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label, width=12, anchor="w", font=("Microsoft YaHei", 10),
                 bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(side=tk.LEFT)
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly",
                          font=("Microsoft YaHei", 10), width=20)
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)


class MetricsImportDialog:
    """导入训练指标对话框"""

    def __init__(self, parent, experiment_name: str):
        self.result = None
        self.win = tk.Toplevel(parent)
        self.win.title(f"导入指标 - {experiment_name}")
        self.win.configure(bg=COLORS["bg2"])
        self.win.geometry("500x400")
        self.win.transient(parent)
        self.win.grab_set()

        frame = tk.Frame(self.win, bg=COLORS["bg2"], padx=16, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="粘贴训练日志（每行一组，逗号分隔）",
                 font=("Microsoft YaHei", 10), bg=COLORS["bg2"], fg=COLORS["fg"]).pack(anchor="w")
        tk.Label(frame, text="格式: epoch,train_loss,val_loss,train_acc,val_acc,lr,n_latents",
                 font=("Microsoft YaHei", 9), bg=COLORS["bg2"], fg=COLORS["fg2"]).pack(anchor="w", pady=(0, 8))

        self.text = tk.Text(frame, font=("Consolas", 10), bg=COLORS["bg"], fg=COLORS["fg"],
                            relief=tk.FLAT, bd=6)
        self.text.pack(fill=tk.BOTH, expand=True)

        example = "1,2.34,2.12,45.2,48.1,3e-4,128\n2,1.89,1.76,52.3,55.0,2.9e-4,128\n3,1.56,1.45,58.1,60.2,2.8e-4,128"
        self.text.insert("1.0", example)

        btn = tk.Frame(frame, bg=COLORS["bg2"])
        btn.pack(fill=tk.X, pady=(8, 0))
        tk.Button(btn, text="取消", command=self.win.destroy,
                  font=("Microsoft YaHei", 10), relief=tk.FLAT, padx=16).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn, text="导入", command=self._import,
                  font=("Microsoft YaHei", 10), bg=COLORS["accent"], fg="white",
                  relief=tk.FLAT, padx=16).pack(side=tk.RIGHT, padx=4)

        self.win.wait_window()

    def _import(self):
        raw = self.text.get("1.0", tk.END).strip()
        rows = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            try:
                r = {"epoch": int(parts[0])}
                if len(parts) > 1 and parts[1]: r["train_loss"] = float(parts[1])
                if len(parts) > 2 and parts[2]: r["val_loss"] = float(parts[2])
                if len(parts) > 3 and parts[3]: r["train_acc"] = float(parts[3])
                if len(parts) > 4 and parts[4]: r["val_acc"] = float(parts[4])
                if len(parts) > 5 and parts[5]: r["lr"] = float(parts[5])
                if len(parts) > 6 and parts[6]: r["n_latents"] = float(parts[6])
                rows.append(r)
            except (ValueError, IndexError):
                continue
        if rows:
            self.result = rows
        self.win.destroy()
