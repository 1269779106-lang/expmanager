from pathlib import Path

APP_NAME = "实验记录管理器"
APP_DIR = Path("D:/mimo_soft/expmanager")
DB_PATH = APP_DIR / "experiments.db"

# UI 配色
COLORS = {
    "bg": "#f8f9fa",
    "bg2": "#ffffff",
    "fg": "#212529",
    "fg2": "#6c757d",
    "accent": "#4a90d9",
    "accent_light": "#e8f0fe",
    "border": "#dee2e6",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8",
}

STATUS_MAP = {
    "planned": ("📋 计划中", COLORS["info"]),
    "running": ("🔄 进行中", COLORS["warning"]),
    "completed": ("✅ 已完成", COLORS["success"]),
    "failed": ("❌ 失败", COLORS["danger"]),
}

ROUTER_TYPES = [
    "fixed", "progressive", "R1", "R2", "R3", "R4",
    "R5", "R6", "R7", "R8", "other"
]

DATASETS = ["CIFAR-100", "CIFAR-10", "ImageNet-1K", "Other"]
