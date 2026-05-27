# 实验记录管理器 (ExpManager)

本地实验记录管理工具，专为深度学习研究设计。管理实验配置、追踪训练进度、对比实验结果、导出论文表格。

## 功能

- 实验 CRUD：新建、编辑、删除实验记录
- Phase 管理：按阶段分组，追踪研究进度
- 筛选过滤：按 Phase / 状态 / 路由器类型筛选
- 训练曲线：导入 epoch 数据，画 loss/accuracy 曲线
- 多实验对比：表格 + 曲线叠加
- 导出 Markdown 表格：直接粘贴到论文
- 预置模板：内置动态 Latent 研究的 12 组实验配置

## 安装

```bash
git clone https://github.com/1269779106-lang/expmanager.git
cd expmanager
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 预置实验

首次启动自动创建：

**Phase 1（渐进式激活 + 固定基线）**
- FIX-16 / FIX-32 / FIX-64 / FIX-128 / FIX-256
- PROG（渐进式激活）

**Phase 2（全局特征路由器 R1）**
- R1-BASE（主实验）
- R1-L00 / R1-L001 / R1-L01（λ 消融）
- R1-NW（warmup 消融）
- R1-2L（路由器深度消融）

## 导入训练指标

支持 CSV 格式，每行一组：
```
epoch,train_loss,val_loss,train_acc,val_acc,lr,n_latents
1,2.34,2.12,45.2,48.1,3e-4,128
2,1.89,1.76,52.3,55.0,2.9e-4,128
```

## 技术栈

- Python 3.10+
- tkinter（UI）
- SQLite（存储）
- matplotlib（图表，按需加载）

## 数据目录

```
D:\mimo_soft\expmanager\
├── experiments.db      # 数据库
├── config.py
├── db.py
├── ui_main.py
├── ui_dialog.py
├── ui_compare.py
├── ui_chart.py
└── main.py
```

## License

[MIT](LICENSE)
