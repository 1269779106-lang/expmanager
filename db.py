import sqlite3
from datetime import datetime
from config import DB_PATH, APP_DIR

def _conn():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'planned',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase_id INTEGER,
            name TEXT NOT NULL,
            router_type TEXT DEFAULT 'fixed',
            status TEXT DEFAULT 'planned',
            dataset TEXT DEFAULT 'CIFAR-100',
            dim INTEGER DEFAULT 256,
            depth INTEGER DEFAULT 6,
            max_latents INTEGER DEFAULT 256,
            patch_size INTEGER DEFAULT 4,
            epochs INTEGER DEFAULT 100,
            batch_size INTEGER DEFAULT 128,
            lr REAL DEFAULT 3e-4,
            optimizer TEXT DEFAULT 'AdamW',
            best_acc REAL,
            best_epoch INTEGER,
            avg_latents REAL,
            flops TEXT,
            params TEXT,
            train_time TEXT,
            notes TEXT DEFAULT '',
            log_path TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            epoch INTEGER,
            train_loss REAL,
            val_loss REAL,
            train_acc REAL,
            val_acc REAL,
            lr REAL,
            n_latents REAL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS hyperparams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            key TEXT,
            value TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_exp_phase ON experiments(phase_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_exp ON metrics(experiment_id);
    """)
    conn.commit()
    conn.close()

# ========== Phase CRUD ==========

def get_phases() -> list[dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM phases ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_phase(name: str, description: str = "") -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO phases (name, description, created_at) VALUES (?,?,?)",
        (name, description, datetime.now().isoformat())
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def update_phase(pid: int, **kw):
    conn = _conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    vals = list(kw.values()) + [pid]
    conn.execute(f"UPDATE phases SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_phase(pid: int):
    conn = _conn()
    conn.execute("DELETE FROM phases WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# ========== Experiment CRUD ==========

def get_experiments(phase_id: int = None, status: str = None,
                    router_type: str = None) -> list[dict]:
    conn = _conn()
    q = "SELECT e.*, p.name as phase_name FROM experiments e LEFT JOIN phases p ON e.phase_id=p.id WHERE 1=1"
    params = []
    if phase_id:
        q += " AND e.phase_id=?"
        params.append(phase_id)
    if status:
        q += " AND e.status=?"
        params.append(status)
    if router_type:
        q += " AND e.router_type=?"
        params.append(router_type)
    q += " ORDER BY e.phase_id, e.id"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_experiment(eid: int) -> dict | None:
    conn = _conn()
    row = conn.execute(
        "SELECT e.*, p.name as phase_name FROM experiments e LEFT JOIN phases p ON e.phase_id=p.id WHERE e.id=?",
        (eid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def add_experiment(data: dict) -> int:
    conn = _conn()
    now = datetime.now().isoformat()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    cols = ", ".join(data.keys())
    phs = ", ".join(["?"] * len(data))
    cur = conn.execute(f"INSERT INTO experiments ({cols}) VALUES ({phs})", list(data.values()))
    eid = cur.lastrowid
    conn.commit()
    conn.close()
    return eid

def update_experiment(eid: int, **kw):
    kw["updated_at"] = datetime.now().isoformat()
    conn = _conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    vals = list(kw.values()) + [eid]
    conn.execute(f"UPDATE experiments SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_experiment(eid: int):
    conn = _conn()
    conn.execute("DELETE FROM experiments WHERE id=?", (eid,))
    conn.commit()
    conn.close()

# ========== Metrics ==========

def add_metrics(eid: int, rows: list[dict]):
    conn = _conn()
    for r in rows:
        r["experiment_id"] = eid
    cols = ", ".join(rows[0].keys())
    phs = ", ".join(["?"] * len(rows[0]))
    conn.executemany(
        f"INSERT INTO metrics ({cols}) VALUES ({phs})",
        [list(r.values()) for r in rows]
    )
    conn.commit()
    conn.close()

def get_metrics(eid: int) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM metrics WHERE experiment_id=? ORDER BY epoch", (eid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_metrics(eid: int):
    conn = _conn()
    conn.execute("DELETE FROM metrics WHERE experiment_id=?", (eid,))
    conn.commit()
    conn.close()

# ========== Hyperparams ==========

def set_hyperparams(eid: int, params: dict):
    conn = _conn()
    conn.execute("DELETE FROM hyperparams WHERE experiment_id=?", (eid,))
    for k, v in params.items():
        conn.execute(
            "INSERT INTO hyperparams (experiment_id, key, value) VALUES (?,?,?)",
            (eid, k, str(v))
        )
    conn.commit()
    conn.close()

def get_hyperparams(eid: int) -> dict:
    conn = _conn()
    rows = conn.execute(
        "SELECT key, value FROM hyperparams WHERE experiment_id=?", (eid,)
    ).fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

# ========== Preset Data ==========

def seed_preset_data():
    """预置动态 Latent 研究的实验模板"""
    conn = _conn()
    if conn.execute("SELECT COUNT(*) FROM phases").fetchone()[0] > 0:
        conn.close()
        return

    # Phases
    phases = [
        ("Phase 1: 渐进式激活 + 固定基线", "5组固定Latent + 1组渐进式，CIFAR-100验证前提"),
        ("Phase 2: 全局特征路由器 (R1)", "R1主实验 + λ消融 + warmup消融"),
        ("Phase 3: 综合对比 + 论文图表", "汇总分析，生成论文实验章全部图表"),
        ("Phase 4: ImageNet 主实验", "完整规模验证（可选）"),
    ]
    for name, desc in phases:
        conn.execute(
            "INSERT INTO phases (name, description, status, created_at) VALUES (?,?,?,?)",
            (name, desc, "planned", datetime.now().isoformat())
        )

    # Phase 1 experiments
    p1_exps = [
        ("FIX-16", "fixed", 16, "~55-60%", "基线：16个Latent"),
        ("FIX-32", "fixed", 32, "~60-65%", "基线：32个Latent"),
        ("FIX-64", "fixed", 64, "~65-70%", "基线：64个Latent"),
        ("FIX-128", "fixed", 128, "~68-73%", "基线：128个Latent"),
        ("FIX-256", "fixed", 256, "~70-75%", "基线：256个Latent"),
        ("PROG", "progressive", 256, None, "渐进式激活: [0.10,0.15,0.25,0.40,0.65,1.00]"),
    ]
    for name, rtype, max_lat, acc, notes in p1_exps:
        conn.execute(
            "INSERT INTO experiments (phase_id, name, router_type, max_latents, dataset, status, notes, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (1, name, rtype, max_lat, "CIFAR-100", "planned", notes,
             datetime.now().isoformat(), datetime.now().isoformat())
        )

    # Phase 2 experiments
    p2_exps = [
        ("R1-BASE", "R1", "λ_eff=0.01, warmup=20, temp=1.0→0.1"),
        ("R1-L00", "R1", "消融: λ_eff=0, 无效率正则化"),
        ("R1-L001", "R1", "消融: λ_eff=0.001, 弱正则化"),
        ("R1-L01", "R1", "消融: λ_eff=0.1, 强正则化"),
        ("R1-NW", "R1", "消融: warmup=0, 无课程学习"),
        ("R1-2L", "R1", "消融: router_layers=2, 2层MLP"),
    ]
    for name, rtype, notes in p2_exps:
        conn.execute(
            "INSERT INTO experiments (phase_id, name, router_type, dataset, status, notes, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (2, name, rtype, "CIFAR-100", "planned", notes,
             datetime.now().isoformat(), datetime.now().isoformat())
        )

    conn.commit()
    conn.close()
