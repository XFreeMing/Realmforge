# Realmforge（铸造世界）— 机器学习自升级系统设计文档

> 将铸造算法和妖兽系统从静态规则升级为可学习的 ML 管道，支持玩家个性化与全服全局优化双层级进化。

---

## 目录

1. [整体架构](#1-整体架构)
2. [特征仓库](#2-特征仓库)
3. [模型注册与版本管理](#3-模型注册与版本管理)
4. [铸造算法自升级](#4-铸造算法自升级)
5. [妖兽系统自升级](#5-妖兽系统自升级)
6. [数据收集与反馈闭环](#6-数据收集与反馈闭环)
7. [模型训练管线](#7-模型训练管线)
8. [冷启动策略](#8-冷启动策略)
9. [隐私与儿童安全](#9-隐私与儿童安全)
10. [技术实现与部署](#10-技术实现与部署)
11. [与现有文档的交叉引用](#11-与现有文档的交叉引用)

---

## 1. 整体架构

### 1.1 双层学习管道

系统采用**双层学习架构**：玩家级（Player-Level）个性化适配 + 服务器级（Server-Level）全局聚合优化。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        客户端 (Godot / 移动端)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ 玩家级个性化  │  │ 特征采集器    │  │ 本地推理引擎             │   │
│  │ 权重向量      │  │ FeatureLog   │  │ (ONNX Runtime Mobile)   │   │
│  │ (~100 浮点数) │  │ (事件队列)    │  │                         │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬─────────────┘   │
│         │                 │                       │                  │
│         ▼                 ▼                       ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ 个性化属性    │  │ 行为事件流    │  │ Delta Model 下载器      │   │
│  │ 计算引擎      │  │ (每日同步)    │  │ (差分更新, <2MB)        │   │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ HTTPS 差分同步
┌─────────────────────────────────────┼───────────────────────────────┐
│                         后端服务层 (FastAPI)                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ 特征接收服务  │  │ 全局训练管线  │  │ 模型注册中心             │   │
│  │ Feature      │  │ Training     │  │ Model Registry           │   │
│  │ Ingestion    │  │ Pipeline     │  │ (MLflow)                 │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬─────────────┘   │
│         │                 │                       │                  │
│         ▼                 ▼                       ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ 全局特征仓库  │  │ 训练调度器    │  │ 模型分发服务             │   │
│  │ Feature Store │  │ (Prefect)    │  │ Model Delivery (CDN)    │   │
│  │ (PostgreSQL + │  │              │  │                         │   │
│  │  Redis)       │  └──────┬───────┘  └─────────────────────────┘   │
│  └──────────────┘         │                                          │
│                           ▼                                          │
│                  ┌────────────────┐                                  │
│                  │ 评估 & A/B 测试 │                                  │
│                  └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 双层同步机制

**玩家级**：每个玩家拥有独立的轻量个性化权重向量（约 100 个浮点数，<1KB），存储在客户端本地 + 云端加密备份。

**服务器级**：聚合所有玩家的行为数据，训练全局模型。每日增量训练，每周全量重训练。产出的全局模型以**先验权重**形式下发给所有客户端。

**同步公式（FedAvg 变体）：**

```
玩家 i 的个性化权重更新:
  w_i(t+1) = α · w_i(t) + (1-α) · w_global(t) + δ_i(t)

  其中:
    α = 0.7（个性化保持率，70% 保留个人偏好）
    w_global = 全局先验权重
    δ_i = 本地梯度更新（SGD step）

全局权重聚合 (加权 FedAvg):
  w_global(t+1) = Σ(n_i · w_i(t)) / Σ(n_i)

  其中 n_i = 玩家 i 的活跃锻造次数（活跃度加权）
```

### 1.3 学习频率层级

| 层级 | 模式 | 频率 | 数据量 | 模型大小 |
|------|------|------|--------|----------|
| 玩家级-即时 | 在线微调 (SGD on latest event) | 每次锻造后 | 单条事件 | ~100 参数 |
| 玩家级-日度 | 本地批量更新 (Mini-batch GD) | 每日离线时 | 当天全部事件 (5-30 条) | ~100 参数 |
| 服务器-日度 | 增量训练 (Online SGD on stream) | 每日凌晨 | 当日全量事件 (数万条) | 主模型 |
| 服务器-周度 | 全量重训练 (Full batch training) | 每周 | 全部历史数据 | 主模型 + 新特征 |
| 服务器-月度 | 架构搜索 + 特征工程 | 每月 | 全部数据 + 新特征 | 可能新增子模型 |

---

## 2. 特征仓库

### 2.1 铸造相关特征 (Forge Features)

基于 [DESIGN.md](../DESIGN.md) 第 3 节的形状分析和 [unified_economy](../docs/unified_economy_attributes_design.md) 的材料模型：

```
形状特征 (Shape Features, 7 维):
  sharpness: float (0-1)        # 尖锐点数 / 总笔画数
  area_ratio: float (0-1)       # 封闭像素面积 / 包围盒面积
  symmetry: float (0-1)         # 1 - 左右像素差异 / 总像素
  complexity: float (0-1)       # 唯一颜色数 / 最大颜色数
  center_offset: float (0-1)    # 质心偏移 / 最大距离
  stroke_count: int             # 总笔画数
  aspect_ratio: float           # 高宽比

材料特征 (Material Features, 12 维):
  avg_hardness: float (1-10)        # 平均硬度
  avg_flexibility: float (1-10)     # 平均柔韧性
  avg_density: float (1-10)         # 平均密度
  avg_conductivity: float (1-10)    # 平均导性
  element_distribution: float[8]    # 八灵分布 [金,木,水,火,土,生,丝,玉]
  material_count: int               # 使用材料数量
  element_diversity: float (1-5)    # 不同五行元素数量

锻造过程特征 (Process Features, 3 维):
  forge_quality: float (0-1)        # 小游戏得分
  perfect_hit_rate: float (0-1)     # 完美击中段
  combo_max: int                    # 最大连击数

上下文特征 (Context Features, 4 维):
  craft_mastery_level: int          # 工艺等级
  total_forge_count: int            # 累计锻造数
  days_since_first_play: int        # 首次游玩天数
  faction: enum [焱族, 渊族]
```

### 2.2 妖兽相关特征 (Beast Features)

基于 [beast_and_combat_design](../docs/beast_and_combat_design.md) 的妖兽数据结构和战斗系统：

```
基础属性 (Base Stats, 4 维):
  base_health: int
  base_attack: int
  base_defense: int
  base_speed: int

基因特征 (Gene Features, 8 维):
  mutation_count: int (1-4)                     # 变异数量
  mutation_rarity_dist: float[5]                # [N%, R%, SR%, SSR%, UR%]
  gene_families: bool[6]                        # [外观,能力,元素,性格,体型,稀有]
  elemental_affinity: enum

战斗表现 (Combat History, 5 维):
  total_battles: int
  win_rate: float (0-1)
  avg_damage_dealt: float
  avg_damage_received: float
  pacify_rate: float (0-1)                      # 安抚成功率

培育特征 (Breeding Features, 3 维):
  bond_level: int (1-10)                        # 好感度等级
  feeding_count: int                            # 喂食次数
  breeding_generation: int                      # 繁育代数
```

### 2.3 特征存储架构

```
Feature Store
├── Online Store (Redis)
│   Key: feat:{player_id}:{event_type}
│   TTL: 7 天 (热特征)
│   用途: 实时推理
│
├── Offline Store (PostgreSQL)
│   ├── player_events 表
│   │   - player_id (UUID)
│   │   - event_type (forge / combat / breed / capture / abandon)
│   │   - timestamp (TIMESTAMPTZ)
│   │   - features (JSONB)
│   │   - outcome (JSONB)
│   │   - session_id (UUID)
│   │
│   ├── player_profile 表
│   │   - player_id (UUID)
│   │   - personalization_weights (JSONB)
│   │   - last_model_version (TEXT)
│   │   - updated_at (TIMESTAMPTZ)
│   │
│   └── global_model_history 表
│       - model_id (UUID)
│       - model_type (TEXT)
│       - version (TEXT)
│       - weights (BYTEA, 压缩)
│       - metrics (JSONB)
│       - created_at (TIMESTAMPTZ)
│
└── Training Data Lake (Parquet on OSS/S3)
    s3://realmforge-ml-data/
      forge_events/year=2026/month=04/day=11/part-00000.parquet
      combat_events/
      beast_events/
      photo_events/
```

---

## 3. 模型注册与版本管理

### 3.1 模型注册表

使用 MLflow 管理所有子模型的版本、元数据和生命周期：

```
Model Registry
├── forge_attribute_model/          # 铸造属性预主模型 (LightGBM)
│   ├── v1.0.0/ (static baseline, 规则引擎)
│   ├── v1.1.0/ (first learned model)
│   └── v2.0.0/ (architecture change)
├── forge_personalization/          # 玩家个性化偏移模型
│   └── per-player sharded
├── beast_mutation_model/           # 妖兽变异概率模型
├── beast_combat_balance/           # 妖兽战斗平衡模型 (Bradley-Terry + ELO)
├── beast_appearance_evolution/     # 妖兽外观演化模型 (SD LoRA)
├── beast_breeding_optimizer/       # 繁育优化模型 (协同过滤)
├── beautification_diffusion/       # 绘画美化扩散模型
│   ├── base_lora/                  # 基础山海经风格 LoRA
│   └── updated_lora/               # 持续微调的 LoRA
├── photo_classifier/               # 照片分类模型 (MobileNetV4)
├── synergy_encoder/                # 五行协同编码器 (可学习矩阵)
└── drop_rate_calibrator/           # 掉率校准模型
```

### 3.2 版本语义

```
MAJOR.MINOR.PATCH

MAJOR: 模型架构变更 (不兼容旧客户端, 强制更新)
  例: 线性模型 → 树模型

MINOR: 权重更新 (兼容旧客户端, 性能提升, 可选下载)
  例: 每周全局重训练产出

PATCH: 安全修复 / 紧急回滚 (强制热修复)
  例: 发现数值溢出 bug
```

### 3.3 A/B 测试框架

```
分流配置:
  control: 70%     → 当前稳定模型
  treatment_a: 15% → 新候选模型 A
  treatment_b: 15% → 新候选模型 B

成功指标:
  - forge_completion_rate (铸造完成率)
  - player_satisfaction_score (玩家满意度)
  - attribute_balance_variance (属性平衡方差)
  - retention_7d (7 日留存)

护栏指标:
  - attribute_outlier_rate < 0.1%   (异常属性值比例)
  - no_weapon_above_power_95        (不能超过安全上限)
  - minigame_win_rate_change < 10%  (难度不能突变)

最小样本: 每桶 1000 玩家，最少运行 7 天
```

---

## 4. 铸造算法自升级

### 4.1 从静态公式到可学习模型

**当前静态公式**（来自 [unified_economy](../docs/unified_economy_attributes_design.md) 第 2.4 节）：

```
power     = (sharpness × 50 + avg_hardness × 4 + avg_density × 1) × (1 + synergy)
guard     = (area_ratio × 60 + avg_hardness × 2 + avg_density × 2) × (1 + synergy)
swiftness = (symmetry × 40 + avg_flexibility × 4 + (10 - avg_density) × 2) × (1 + synergy)
spirit    = (complexity × 30 + avg_conductivity × 5) × (1 + synergy)
steady    = (symmetry × 60 + (1 - center_offset) × 40)
```

**问题**：权重手工调参，无法从玩家行为中学习，无法个性化，无法自动平衡。

### 4.2 双层混合模型架构

**Tier 1 — 全局基础模型 (LightGBM 多输出回归)**

```
输入: 22 维特征向量 (形状 7 + 材料 12 + 过程 3 + 上下文 4 - 冗余)
输出: 5 个属性基准预测 [power, guard, swiftness, spirit, steady]
模型配置:
  - num_leaves: 31
  - learning_rate: 0.05
  - n_estimators: 200
  - max_depth: 6
训练: 服务器端每周全量训练
优点: 可解释性强、非线性、自动捕获特征交互、推理速度快 (<5ms)
```

**Tier 2 — 玩家个性化偏移 (轻量线性层)**

```
输入: 22 维特征向量 + 全局模型预测
输出: 5 个属性的偏移量 delta
参数: ~100 浮点数 (<1KB)
训练: 客户端每日在线微调 (SGD)
约束: 偏移幅度不超过 30%，最终属性偏移不超过 ±15 点

最终预测:
  attr_final = clamp(attr_global + attr_personalization_delta)
```

### 4.3 玩家个性化示例

```
玩家 A (偏好剑):
  - 历史行为: 80% 铸造剑类武器
  - 学习到的偏移: sharpness → Power 的权重 +15%
  - 结果: 同样的形状+材料，玩家 A 的剑得到更高的 Power

玩家 B (偏好盾):
  - 历史行为: 70% 铸造盾类武器
  - 学习到的偏移: area_ratio → Guard 的权重 +12%
  - 结果: 同样的形状+材料，玩家 B 的盾得到更高的 Guard
```

### 4.4 五行协同编码器

**当前**：离散规则表（相生 +15%, 相克 -10%）。

**升级后**：可学习的 5×5 协同矩阵，支持连续优化：

```
协同矩阵 G (可学习, 初始值来自五行先验):

      金     木     水     火     土
金  [ 0.0, -0.10, +0.20, -0.15, +0.10]  # 金生水, 金克木
木  [-0.10,  0.0,  +0.10, +0.20, -0.15]  # 木生火, 木克土
水  [+0.20, +0.10,  0.0,  -0.15, +0.10]  # 水生木, 水克火
火  [-0.15, +0.20, -0.15,  0.0,  +0.10]  # 火生土, 火克金
土  [+0.10, -0.15, +0.10, -0.15,  0.0 ]  # 土生金, 土克水

通过学习，这些值可以偏离初始设定:
  - 如果"水火"组合被玩家发现意外好用，相克惩罚自动降低
  - 如果某些组合被广泛认为不平衡，协同值自动调整

协同分数计算:
  synergy = Σ G[i][j] / (n × (n-1))  对所有 i≠j 的元素对求和
```

### 4.5 儿童安全约束（硬规则，不可学习）

```
安全约束 (永远不变):
  - 属性范围: [1, 100]
  - 单一属性上限: 95
  - 5 属性总和上限: 350
  - 属性方差下限: 50 (确保有弱点)
  - 个性化偏移上限: ±15 点
  - 每周同一配方属性变化上限: ±10 点
  - 新手保护期 (前 10 次铸造): Power 限制在 [20, 70]
```

---

## 5. 妖兽系统自升级

### 5.1 基因变异概率自适应

**当前**：固定概率分布 (60/25/10/4/1)。

**升级后**：根据玩家状态动态调整的自适应分布：

```
基础分布 (先验):
  N(普通): 60%, R(稀有): 25%, SR(精英): 10%, SSR(传说): 4%, UR(神话): 1%

动态调整信号:
  1. 战斗胜率: 胜率 >75% → 降低稀有变异 (+挑战); 胜率 <35% → 提高稀有变异 (+动力)
  2. 收集进度: 收集率 <20% → 增加惊喜感; 收集率 >80% → 保持稀有追求
  3. 全局经济: 某类材料溢出 → 调整相关变异概率
  4. 游戏时长/活跃度: 新玩家友好

安全约束:
  N: [45%, 75%], R: [15%, 40%], SR: [5%, 18%], SSR: [2%, 8%], UR: [0.5%, 2%]
  调整后必须重新归一化
```

### 5.2 妖兽外观演化 (Experience Marks)

妖兽的外观随战斗/喂养经历积累"经验印记"，让每只妖兽有独特的成长视觉故事：

```
印记系统:
  战痕 (Battle):   胜利 10+ 场     → 微妙的光纹
  元素 (Elemental): 同元素胜利 5+ 场 → 元素光环
  守护 (Guardian):  安抚 5+ 只妖兽   → 柔和光晕
  智慧 (Wisdom):   解谜胜利 3+ 场   → 符文浮现
  友情 (Bond):     喂食 20+ 次      → 温暖色调
  传奇 (Legend):   击败 Boss       → 金色边框

视觉生成: SD + ControlNet + 印记条件
  - 基础妖兽图像 (来自基因编码)
  - + 印记叠加层 (根据印记类型和强度)
  - + 全局风格 (山海经 LoRA)

印记强度随新战斗/喂养持续累积，旧印记缓慢褪色（半衰期 30 天），
保证长期活跃的妖兽有独特的视觉辨识度。
```

### 5.3 繁育优化学习

```
繁育优化模型: 学习哪些父母组合产生最受欢迎的后代

方法: 协同过滤 + EMA (指数移动平均) 权重更新
  - 记录所有繁育事件的 (父母1, 父母2) → 后代品质 映射
  - 学习"哪些基因家族组合产生高品质后代"
  - 为玩家推荐最优繁育配对

继承权重矩阵 (6 基因家族 × 多性状):
  - 外观 (20 种特征), 能力 (15 种), 元素 (5 种)
  - 性格 (6 种), 体型 (10 种), 稀有度 (5 级)

每次繁育后更新:
  W_new = α × W_actual + (1-α) × W_old  (α = 0.1)

推荐逻辑:
  预测后代品质 = 基因互补性 × 0.2 + 稀有度协同 × 0.3
               + 元素相生 × 0.2 + 历史成功率 × 0.3
```

### 5.4 战斗平衡自动调优

```
Bradley-Terry + ELO 混合模型:

每个妖兽实例有一个隐藏 ELO 评分 (初始 1500):
  - 战斗后根据胜负和幅度更新 ELO
  - K 因子 = 32

每个物种有全局平衡系数 (可学习):
  species_balance_coeffs[species_id] = {attack: 1.0, defense: 1.0, speed: 1.0}

不平衡检测:
  - 计算每个物种的平均 ELO
  - 偏差超过全局均值 15% → 标记为不平衡
  - 推荐渐进式调整 (每次最多 5%)

安全约束:
  - 平衡系数变化范围: [0.8, 1.2]
  - 每周调整次数上限: 2 次
  - 需要人工审核后才发布
```

---

## 6. 数据收集与反馈闭环

### 6.1 隐式信号采集

```
铸造相关:
  - weapon_used_count: 武器被使用次数
  - weapon_equipped_duration: 武器装备时长
  - repeat_design: 是否重复相似设计
  - abandon_rate: 放弃铸造率
  - time_spent: 铸造耗时

战斗相关:
  - win_rate: 胜率
  - avg_rounds: 平均回合数
  - pacify_rate: 安抚成功率
  - element_success_rate: 五行相克选择正确率
  - flee_rate: 逃跑率

收集相关:
  - photo_capture_count: 拍照次数
  - material_variety_score: 材料多样性
  - beast_collection_rate: 妖兽收集率
  - codex_completion_rate: 图鉴完成率

社交/反馈:
  - bond_increase_count: 羁绊提升次数
  - breeding_success_rate: 繁育成功率
  - sharing_count: 分享次数
```

### 6.2 显式反馈采集

```
儿童端 (游戏内, 非文字):
  - weapon_happiness: 😊😐😢 三表情评分
  - forge_fun_rating: 点击星星 (1-5)
  - beast_friendship: 拥抱动画 = 喜欢

家长端 (家长面板):
  - parent_difficulty_feedback: 太难/合适/太简单
  - parent_content_rating: 内容适宜度
  - parent_time_concern: 是否担心游戏时间
```

### 6.3 反馈流回模型

```
即时 (Online, <1 秒):
  └── 玩家铸造 → 本地个性化权重更新 (SGD step)
  └── 战斗结果 → 本地妖兽 ELO 更新

日度 (Daily Batch, 凌晨):
  └── 客户端上传当日事件 → 特征接收服务
  └── 增量训练: 全局模型 SGD on new data
  └── 产出: 新权重差分包 (<2MB)
  └── 下发: CDN 推送到客户端

周度 (Weekly Retraining, 周日凌晨):
  └── 全量数据训练 (Parquet on S3)
  └── 评估指标计算 + A/B 测试分析
  └── 产出: 完整模型 + 个性化先验
  └── 人工审核 → 灰度发布 (10% → 50% → 100%)

月度 (Monthly Review):
  └── 特征重要性分析 → 新特征发现
  └── 模型架构评估 → 是否需要升级
  └── 平衡报告 → 设计团队审核
```

---

## 7. 模型训练管线

### 7.1 各子系统模型选型

| 子系统 | 模型类型 | 理由 | 部署位置 |
|--------|---------|------|----------|
| **铸造属性预测** | LightGBM (多输出回归) | 可解释、非线性、小模型、推理快 | 服务器 (训练) + 客户端 (推理) |
| **玩家个性化偏移** | 轻量线性层 (~100 参数) | 极小、可在线学习 | 客户端 |
| **妖兽变异概率** | 动态规则 + 逻辑回归 | 需要安全约束 + 可解释 | 服务器 + 客户端 |
| **妖兽战斗平衡** | Bradley-Terry + ELO | 成熟的竞技平衡模型 | 服务器 |
| **繁育优化** | 协同过滤 + EMA 权重更新 | 推荐系统经典方法 | 服务器 |
| **妖兽外观演化** | Stable Diffusion + 可学习 LoRA | 高质量图像生成 | 服务器 (生成) |
| **照片分类** | MobileNetV4 (int8 量化) | 端侧实时推理 | 客户端 |
| **绘画美化** | ControlNet (Scribble) + 山海经 LoRA | 保留笔触意图 | 服务器 |
| **五行协同编码器** | 可学习矩阵 + 约束优化 | 五行关系的连续表示 | 客户端 |

### 7.2 训练数据需求

```
最小有效数据量:

铸造属性模型 (LightGBM):
  冷启动: 0 (使用手工规则)
  有意义: ~5,000 条铸造事件 (~500 玩家 × 10 次)
  高质量: ~100,000 条铸造事件

玩家个性化模型:
  冷启动: 0 (α=1.0, 完全依赖全局)
  有意义: ~20 条个人铸造事件
  成熟: ~100 条个人铸造事件

妖兽战斗平衡 (Bradley-Terry):
  冷启动: 0 (使用设计值)
  有意义: ~2,000 场战斗
  高质量: ~50,000 场战斗

繁育优化:
  冷启动: 0 (使用均等继承)
  有意义: ~1,000 次繁育事件
  高质量: ~10,000 次繁育事件

外观演化 LoRA:
  冷启动: 基础山海经 LoRA (预训练)
  有意义: ~500 张玩家接受的美化图片
  高质量: ~5,000 张图片 + 人类评估反馈
```

### 7.3 评估指标

```
铸造属性模型:
  - MAE < 5 (1-100 尺度)
  - RMSE < 8
  - 玩家满意度相关性 > 0.6
  - 属性平衡指数 0.7-0.9

妖兽战斗平衡:
  - 物种间 ELO 标准差 < 200
  - 各物种胜率方差 < 0.05
  - 五行克制有效性 > 0.85

外观演化:
  - 玩家接受率 > 70%
  - 原始意图保留度 > 0.8
  - 风格一致性 > 0.9

系统级:
  - 7 日留存 > 40%
  - 30 日留存 > 25%
  - 平均会话时长 15-30 分钟
  - 铸造完成率 > 85%
  - 战斗参与度 > 60%
```

### 7.4 评估流程

```
每次模型更新后:

1. 离线评估 (Offline Evaluation)
   ├── 在保留测试集上计算指标
   ├── 与当前生产模型对比
   └── 必须满足所有护栏指标

2. 影子模式 (Shadow Mode)
   ├── 新模型在后台运行, 不直接影响玩家
   ├── 对比新旧模型的预测差异
   └── 验证无异常行为

3. A/B 测试 (10% 流量)
   ├── 运行至少 7 天
   ├── 监控核心指标和护栏指标
   └── 统计学显著性检验 (p < 0.05)

4. 渐进发布
   ├── 10% → 50% → 100%
   ├── 每阶段至少 24 小时
   └── 任何阶段可随时回滚
```

---

## 8. 冷启动策略

### 8.1 零数据阶段

在没有玩家数据时，系统完全依赖设计团队定义的**先验规则**：

```
冷启动阶段过渡:

RULE_ENGINE (事件数 < 100):
  纯规则引擎 (当前 DESIGN.md 的公式)

HYBRID_RULE (事件数 100-1,000):
  70% 规则 + 30% ML 预测混合
  ML 模型使用合成数据预训练

HYBRID_ML (事件数 1,000-5,000):
  30% 规则 + 70% ML 预测混合
  规则仅作为安全网

FULL_ML (事件数 > 5,000):
  100% ML 预测
  规则仅做安全约束 (属性边界等)
```

### 8.2 合成数据预热

使用设计规则 + 随机扰动生成合成训练数据，用于：
1. 测试训练管线
2. 预训练模型的初始权重
3. 验证安全约束

```
合成数据生成:
  - 随机采样形状特征 (0-1 均匀分布)
  - 随机采样材料属性 (1-10 均匀分布)
  - 用规则引擎计算标签 (属性值)
  - 添加高斯噪声模拟真实方差
  - 生成 50,000 条样本用于预训练
```

---

## 9. 隐私与儿童安全

### 9.1 数据处理分层

```
Layer 0 (完全本地, 不离开设备):
  - 原始照片
  - 原始绘画
  - 照片分类结果 (仅上传分类标签, 不上传图片)
  - 本地个性化权重 (加密存储在设备上)

Layer 1 (匿名化后上传):
  - 事件特征 (已去除个人标识)
  - 聚合统计 (每日汇总)
  - 玩家 UUID (不可逆哈希)

Layer 2 (家长授权后):
  - 家长面板数据
  - 分享功能
  - 跨设备同步

Layer 3 (可选, 明确同意):
  - 云端美化 (需要上传图片到服务器)
  - 高级分类 (Cloud CLIP fallback)
  - 社区功能
```

### 9.2 差分隐私

在上传到服务器的特征中添加差分隐私噪声 (Laplace 机制, ε=1.0)，确保单个玩家数据无法被反推。

### 9.3 合规措施

- COPPA (美国儿童在线隐私保护法)
- GDPR-K (欧盟儿童数据保护)
- 中国《儿童个人信息网络保护规定》
- 家长控制面板 (PIN 保护)
- 非活跃玩家数据 90 天后自动删除

---

## 10. 技术实现与部署

### 10.1 客户端部署

```
客户端 (Godot + 移动端) 组件:
  ├── ONNX Runtime Mobile (~5MB)
  │   └── forge_model_v2.1.onnx (~2MB)
  ├── 本地特征提取器
  ├── 个性化权重管理器 (~1KB 浮点数组, 加密)
  └── 事件队列 (SQLite, 离线缓存)

本地存储:
  ├── player_personalization.json (AES-256 加密)
  ├── onnx_models/ (LightGBM 转 ONNX)
  └── event_queue.db (SQLite, 离线事件缓存)
```

### 10.2 后端部署

```
模型训练服务 (GPU 实例, 按需启动):
  ├── LightGBM 训练 (CPU, 快速)
  ├── SD LoRA 微调 (GPU, A10G)
  ├── Bradley-Terry 求解 (CPU)
  └── 评估 & A/B 分析 (CPU)

模型推理服务 (CPU, 高并发):
  ├── 属性预测 API (LightGBM 推理, <5ms)
  ├── 变异概率 API (动态计算, <2ms)
  ├── 繁育推荐 API (<10ms)
  └── 战斗平衡检查 (<5ms)

模型分发服务:
  ├── CDN (模型文件缓存)
  ├── 差分更新生成 (bsdiff, 增量 <2MB)
  └── 推送通知 (模型可用时通知客户端)
```

### 10.3 模型更新分发

```
模型更新流程:
  1. 训练完成 (周日凌晨 3:00)
     ├── 新模型写入 Model Registry
     ├── 自动评估通过
     └── 生成差分补丁

  2. 灰度发布 (周一 09:00)
     ├── 选择 10% 活跃玩家 (随机抽样)
     ├── 推送模型更新通知
     └── 客户端在下次启动时下载

  3. 监控期 (周一-周三)
     ├── 实时监控指标
     ├── 异常自动回滚
     └── A/B 测试对比

  4. 全量发布 (周四 09:00)
     ├── 推送到 100% 玩家
     └── 旧模型标记为可废弃

  5. 回滚机制 (随时)
     ├── 一键回滚到上一个稳定版本
     ├── 客户端自动检测模型异常
     └── 5 分钟内完成回滚
```

### 10.4 存储选型

| 数据类型 | 存储方案 | 保留期 | 大小预估 |
|---------|---------|--------|----------|
| 玩家事件 | PostgreSQL (JSONB) | 2 年 (活跃) | 10GB/百万玩家/年 |
| 个性化权重 | PostgreSQL (JSONB) | 永久 | ~1KB/玩家 |
| ONNX 模型 | OSS/S3 + CDN | 永久 | ~2MB/模型版本 |
| 训练数据 (Parquet) | OSS/S3 | 2 年 | 50GB/百万玩家/年 |
| 特征缓存 | Redis | 7 天 | 5GB/10万在线 |
| 图片 (美化结果) | OSS/S3 | 30 天 | 500KB/张 |
| 日志 | ELK Stack | 90 天 | 20GB/天 |

### 10.5 监控与告警

```
模型性能:
  - 推理延迟 P99 < 50ms
  - 属性预测误差 MAE < 8
  - 模型版本覆盖率 > 90% (7 天内)
  - 个性化权重更新成功率 > 99%

业务指标:
  - 铸造完成率 > 85%
  - 战斗参与度 > 60%
  - 玩家满意度 > 70%
  - 7 日留存 > 40%

告警规则:
  CRITICAL: 属性异常值 > 0.1% → 立即回滚
  CRITICAL: 模型推理失败率 > 1% → 自动回滚
  WARNING: 属性变化速率 > 10%/周 → 通知设计团队
  WARNING: 玩家满意度下降 > 5% → 通知设计团队
  INFO: 新特征发现 → 通知数据科学团队
```

### 10.6 实施阶段

```
Phase 0 (MVP, 1-2 个月):
  ├── 实现静态规则引擎 (当前 DESIGN.md 的公式)
  ├── 搭建数据采集管线 (事件日志 → PostgreSQL)
  ├── 搭建 Model Registry (MLflow)
  ├── 实现基本的个人化权重框架 (线性偏移)
  └── 部署 A/B 测试框架

Phase 1 (基础 ML, 3-4 个月):
  ├── 部署 LightGBM 铸造属性模型 (服务器训练, 客户端推理)
  ├── 实现 FedAvg 个性化同步
  ├── 部署妖兽战斗平衡 ELO 系统
  ├── 实现动态变异概率分配
  ├── 搭建训练调度管线 (Prefect)
  └── 实现模型差分更新分发

Phase 2 (高级 ML, 5-6 个月):
  ├── 部署 SD LoRA 持续微调管线
  ├── 实现繁育优化推荐系统
  ├── 实现妖兽外观演化系统
  ├── 部署五行协同编码器
  ├── 实现差分隐私特征上传
  └── 完善监控告警系统

Phase 3 (优化迭代, 7+ 个月):
  ├── 基于数据驱动的特征工程
  ├── 自动化模型架构搜索
  ├── 多目标优化 (平衡 vs 趣味性 vs 教育性)
  ├── 跨玩家协同推荐
  └── 持续性能优化
```

---

## 11. 与现有文档的交叉引用

| 本文档章节 | 引用文档 | 关联内容 |
|-----------|---------|---------|
| 铸造算法自升级 (4.1) | [DESIGN.md](../DESIGN.md) Section 3 | 当前静态公式，ML 替代目标 |
| 铸造算法自升级 (4.2) | [unified_economy](../docs/unified_economy_attributes_design.md) Section 2 | 统一属性数据模型 |
| 妖兽变异概率 (5.1) | [beast_and_combat](../docs/beast_and_combat_design.md) Section 2 | 基因变异系统 |
| 妖兽外观演化 (5.2) | [beast_and_combat](../docs/beast_and_combat_design.md) Section 2.2 | 基因家族定义 |
| 战斗平衡 (5.4) | [beast_and_combat](../docs/beast_and_combat_design.md) Section 4 | 战斗系统与小游戏 |
| 特征仓库 (2.1) | [unified_economy](../docs/unified_economy_attributes_design.md) Section 1 | 材料属性定义 |
| 照片分类 (7.1) | [DESIGN.md](../DESIGN.md) Section 3 | 照片→材料管线 |
| 绘画美化 (7.1) | [technical-architecture](../docs/technical-architecture.md) Section 5 | AI 服务架构 |
| 隐私保护 (9) | [technical-architecture](../docs/technical-architecture.md) Section 7 | 儿童安全设计 |
| 部署架构 (10) | [technical-architecture](../docs/technical-architecture.md) Section 8 | 部署拓扑 |

---

*Document version: 1.0 | Realmforge Design Team | 2026-04-11*
