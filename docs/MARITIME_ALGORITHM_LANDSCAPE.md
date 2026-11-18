# RIVER-Agent：航运专业算法与开源实现调研

> **研究分工更新（2026-11-18）**：本文件作为**团队专业算法研究的参考资料与待办清单**，当前总体架构对话不再逐项深化算法选型和代码。团队负责论文阅读、代码/许可/依赖核查、复现、评价和数据适配；系统研究只处理算法类别、数据产品和模块边界。该标记不代表任何算法已实现或验证。
>
> 版本：v0.1（专题研究草案）  
> 调研日期：2026-11-15  
> 状态：**公开论文与仓库信息梳理，非已集成/复现/通过适航安全验证的算法清单**  
> 目标：从 RIVER-Agent 的业务任务 K01–K13 出发，汇集传统、机器学习与深度学习/优化算法；明确数据依赖与开源实现，而不是反向绑定 DSF-Net 或其他单一模型。  
> 项目开发底座仍以 dsh 为主。此处 Algorithm 指航运专业计算算法，区别于中央 Agent 使用的 LLM。

## 1. 检索与判定原则

- **任务先行**：用户问题决定业务工具，算法是工具背后的可替换实现；同一工具可对接多算法，也可用确定性计算而非训练模型。
- **证据分级**：明确区分【经典通用算法】、【航运领域论文】、【已找到开源仓库 README/源码】、【仅推荐借鉴的跨领域实现】；开源代码存在并不保证已运行、数据可用、可直接适配长江内河或许可证满足项目条件。
- **输出目标不同不得直接比较**：航段通行流量（单位时间通过量）、窗口内船舶数、空间密度、速度、拥堵指数、未来位置、碰撞风险不是同一个预测目标。
- **先基础、后复杂**：每类任务至少保留有解释力的简单基线，再选择有明确增益验证目标的复杂算法；跨领域道路交通代码需重新构造航运航段图与时空特征。
- **公平验证**：固定数据来源、历史可用截止时间、时间切分、特征、预测时域及指标；多模型选择不得默默切换固定科研实验的算法版本。

## 2. 任务与算法全景

| 业务任务 / 组件 | 传统或确定性基线 | 进阶候选 | 数据与约束 |
| --- | --- | --- | --- |
| K01 区域态势与 C12 多源融合 | 船舶计数、空间覆盖、轨迹插值、最近邻关联、Kalman / EKF | IMM、JPDA/MHT、多传感器融合 | AIS 点、雷达航迹、时间戳、测量不确定性、坐标系 |
| K02 单船历史轨迹 | 清洗、插值、航段匹配、SOG/COG 统计 | HMM 地图匹配、轨迹聚类 | AIS 点按 MMSI/时间组织；不可混入未观测真实位置 |
| K03 船舶轨迹预测 | 恒速度 CV、恒加速度 CA、Kalman/EKF、历史航迹模式 | KNN/SVR、LSTM/GRU/Seq2Seq、TrAISformer、交互 GNN/生成模型 | 船舶时间序列、船型、航道环境、必要时邻船关系图 |
| K04 多船冲突与风险 | DCPA/TCPA、船舶领域 Ship Domain、相对运动阈值 | 模糊/Bayesian 风险、VO、概率场景/Monte Carlo | 船舶同时态状态、速度、船长宽、预测不确定性、适用规则 |
| K05 异常行为识别 | 超速/急转/停航规则、DBSCAN、KDE、LOF | Isolation Forest、Autoencoder、GeoTrackNet | AIS 历史轨迹、区域/船型正常模式、异常定义 |
| K06 航段拥堵分析 | 窗口计数、速度/密度/占用率指标、瓶颈排序 | KDE、聚类、时空状态估计、交通状态分类 | AIS/航段统计、局部通行能力；拥堵阈值须有业务定义 |
| K07 交通流预测 | 历史同期均值、季节性朴素预测、ARIMA/SARIMA、VAR | SVR/XGBoost、LSTM/GRU、DCRNN、STGCN、Graph WaveNet、AGCRN、STMGCN | 航段小时/日级序列；图模型额外需要航段拓扑/邻接矩阵 |
| K08 规则及通告查询 | 规则库、关键词匹配、BM25、空间与时间过滤 | Dense Retrieval、Hybrid Retrieval、RAG 加确定性约束校验 | 官方原文、发布/生效时间、航段空间映射；LLM 不能自行发明规定 |
| K09 通航事件影响 | 空间交集、网络可达性、受影响船舶筛选、情景比较 | 交通流情景预测、仿真、优化 | 限航事件时空范围、航段图、当前与预测交通状态 |
| K10 航路规划 | Dijkstra、A*、时间依赖最短路径 | 多目标规划、RRT*、MPC、VO/APF 辅助 | 航道图、吃水/水深、限航时段、船舶参数；不是直接控制指令 |
| K11 交通组织/船闸调度 | FCFS、优先级规则、MILP、约束规划 | CP-SAT、启发式/ALNS、滚动优化 | 航段容量、过闸窗口、船舶 ETA、船型与通行约束 |
| K12 综合报告 | 规则化统计、证据聚合、可复核模板 | Agent 驱动多工具汇总与证据校验 | 取决于被引用分析工具；不需要强行新增独立专业预测模型 |
| K13 定时任务管理 | dsh Host Schedule、运行状态管理 | 业务恢复策略（未定） | 不属于航运专业算法；事件触发第一版暂缓 |

**风险和避碰是不同层次**：K04 首先进行识别与评价；VO/APF/MPC 更常见于避碰操纵与候选策略，不能把其输出直接作为岸基可执行指令。内河水域还须核实实际适用的中国及地方航行规则，不能直接假设海上 COLREGs 规则可照搬。

## 3. 优先阅读的论文（已经定位）

| 主题 | 论文及链接 | 主要价值 | 代码状态 |
| --- | --- | --- | --- |
| 航运交通流综述 | [Predictive modelling for vessel traffic flow: A comprehensive survey from statistics to AI](https://doi.org/10.1093/tse/tdaf022)（Transportation Safety and Environment, 2025） | 梳理 ARIMA/SARIMA、LSTM、时空图等及不同预测目标，检索106篇相关文献 | 综述；非统一开源实现 |
| 船舶轨迹方法对比 | [Ship trajectory prediction based on machine learning and deep learning: A systematic review and methods analysis](https://doi.org/10.1016/j.engappai.2023.107062)（Engineering Applications of AI） | KF/GPR/SVR/RF、RNN/LSTM/GRU/Seq2Seq/STGCN/Transformer 选型 | 方法综述，需独立核实各代码 |
| 船舶轨迹实证比较 | [AIS data-driven ship trajectory prediction modelling and analysis based on machine learning and deep learning methods](https://www.sciencedirect.com/science/article/pii/S1366554523001400) | 12类轨迹预测方法与不同航行区域比较，提醒跨环境迁移 | 文中说明 AIS 数据不可共享 |
| 内河/海事交通图预测 | [Fine-grained vessel traffic flow prediction with a spatio-temporal multigraph convolutional network](https://doi.org/10.1109/TITS.2022.3199160)（IEEE T-ITS, 2022） | 船舶交通网络、多图相关性、STMGCN，紧贴 RIVER-Agent K07 | 本次未核实官方开源实现 |
| 港区交通流图预测 | [TG-PGAT: An AIS Data-Driven Dynamic Spatiotemporal Prediction Model for Ship Traffic Flow in the Port](https://doi.org/10.3390/jmse12101875)（JMSE, 2024） | GAT + TCN + BiGRU 的港区流量分析 | 本次未核实官方开源实现 |
| 航运 AIS 异常综述 | [Anomaly Detection in Maritime AIS Tracks: A Review of Recent Approaches](https://doi.org/10.3390/jmse10010112)（JMSE, 2022） | DBSCAN、概率模型、深度模型和异常定义的系统梳理 | 综述 |
| 航运碰撞风险 | [A quantitative method for the analysis of ship collision risk using AIS data](https://doi.org/10.1016/j.oceaneng.2023.113906)（Ocean Engineering） | DCPA/TCPA、VCRO、VO、Ship Domain 等风险算法及局限 | 本次未核实官方开源实现 |
| 自主避碰综述 | [Autonomous Collision Avoidance at Sea: A Survey](https://doi.org/10.3389/frobt.2021.739013)（Frontiers, 2021） | CPA、APF、MPC、VO、ORCA、A*、RRT 的边界 | 综述 |
| 内河船闸优化 | [Optimal scheduling of ships in inland waterway with serial locks](https://doi.org/10.1016/j.trc.2025.105241)（TR Part C, 2025） | 串联船闸、船舶速度与通行优先级 MILP 优化 | 本次未核实官方开源实现 |
| 船闸与港口协同 | [A lock and port resource collaborative scheduling method based on mathematical programming model and heuristic](https://doi.org/10.1016/j.ejor.2025.08.021)（EJOR, 2026） | 船闸—港口资源联动、MILP、ALNS | 本次未核实官方开源实现 |

## 4. 确认可访问的 GitHub 仓库（代码可见 ≠ 已复现）

| 类别 | 仓库 | 实际定位与可复用点 | 对内河适配工作 |
| --- | --- | --- | --- |
| AIS 数据加工 | [KaysenWB/AIS-Process](https://github.com/KaysenWB/AIS-Process) | 清洗、插值、多船场景、交互图，代码与 README 已核查 | 核对 AIS 字段、采样间隔、航道地理约束 |
| 目标跟踪与融合 | [dstl/Stone-Soup](https://github.com/dstl/Stone-Soup) | KF/数据关联/多目标跟踪研究框架；文档和示例 | 定义航运坐标、传感器误差、融合策略 |
| 基础估计器 | [rlabbe/filterpy](https://github.com/rlabbe/filterpy) | KF/EKF/UKF/粒子滤波实现 | 设计船舶运动模型和轨迹初始化 |
| 海事轨迹 Benchmark | [MAPGroup/WUT-TrajData](https://github.com/MAPGroup/WUT-TrajData) | CV/CA/KF/EKF、KNN/SVR、LSTM/GRU/BiLSTM/Transformer，以及改编 TrAISformer、Social-LSTM/GAN 等 | 不同水域、数据时域及轨迹采样标准需统一 |
| AIS 轨迹预测 | [CIA-Oceanix/TrAISformer](https://github.com/CIA-Oceanix/TrAISformer) | Transformer 船舶轨迹生成式预测，提供训练/评估代码及示例数据格式 | 路径局部化、预测时域、依赖与误差单位 |
| 航运轨迹研究复现 | [isaacOnline/ships](https://github.com/isaacOnline/ships) | AIS+气象预处理和 RNN 模型评估，使用 MLflow | 抽取独立推理接口，避免把实验脚本当生产 API |
| 时序预测实验框架 | [GestaltCogTeam/BasicTS](https://github.com/GestaltCogTeam/BasicTS) | 多种时间序列和时空预测模型、数据/训练/评价接口 | 交通对象从道路传感器映射到航段、航运特征 |
| 时空图预测 | [liyaguang/DCRNN](https://github.com/liyaguang/DCRNN) | ICLR 2018 官方实现；扩散图卷积与循环预测 | 构造航道图；原仓库主要用于道路速度预测 |
| 时空图预测 | [VeritasYin/STGCN_IJCAI-18](https://github.com/VeritasYin/STGCN_IJCAI-18) | IJCAI 2018 官方时空图卷积基线 | 航段关联、时间分辨率、交通流预测目标 |
| 时空图预测 | [nnzhan/Graph-WaveNet](https://github.com/nnzhan/Graph-WaveNet) | IJCAI 2019 原始 PyTorch 实现；自适应图关系 | 航运拓扑与相关图之间的关系需要实验区分 |
| 时空图预测 | [LeiBAI/AGCRN](https://github.com/LeiBAI/AGCRN) | NeurIPS 2020 交通预测实现 | 训练数据、航段图、模型迁移 |
| AIS 异常检测 | [CIA-Oceanix/GeoTrackNet](https://github.com/CIA-Oceanix/GeoTrackNet) | VRNN 概率轨迹建模 + A Contrario 异常检测 | 必须区分异常行为与安全事故，核对分布迁移 |
| 异常算法库 | [yzhao062/pyod](https://github.com/yzhao062/pyod) | IF/LOF/OCSVM/KDE 等标准检测算法 | 将时间轨迹转换为适用的特征，不直接当作碰撞风险 |
| 船舶避碰研究 | [ZHIBO-HE/MPAPF-ship-collision-avoidance-method](https://github.com/ZHIBO-HE/MPAPF-ship-collision-avoidance-method) | MATLAB MPAPF、COLREGs 相关演示、CPA/TCPA 函数 | 属于仿真和算法参考，不能直接用于指挥实船 |
| 图搜索 | [networkx/networkx](https://github.com/networkx/networkx) | Dijkstra、最短路径等通用算法 | 航道网络构建、水深与通行约束、时变边权 |
| 整数规划与调度 | [google/or-tools](https://github.com/google/or-tools) | CP-SAT、MILP/线性规划接口、路径/网络优化 | 船闸容量、船舶排序、通行窗口建模 |
| 规则与通告检索 | [castorini/pyserini](https://github.com/castorini/pyserini) | BM25、稀疏/密集/混合检索 | 中文规则、航行通告、生效时空和原文证据 |

**说明**：以上大部分 GitHub 仓库的 README 已核对；未运行安装、训练或测试命令，也未核对所有仓库的许可证及维护适配成本。“官方实现”仅用于 README 或论文明确表述为作者实现的项目。道路交通模型需数据迁移；通用算法库不声称已支持内河业务。

## 5. 推荐的候选算法梯队（待实际数据决定）

| 问题 | 第一批可验证基线 | 后续研究型候选 | 不应提前锁定的点 |
| --- | --- | --- | --- |
| 航段交通流/拥堵预测 | 季节性朴素、SARIMA、XGBoost、LSTM | STGCN、DCRNN、Graph WaveNet、STMGCN | 预测目标、流量口径、航段图是否可用 |
| 船舶轨迹预测 | CV/CA、KF/EKF、LSTM | TrAISformer、交互 GNN/生成式模型 | 预测时域、采样频率、邻船轨迹覆盖 |
| 多船风险评估 | CPA/TCPA、Ship Domain | 含不确定性的概率风险/VO/仿真 | 风险阈值、内河适用规则、证据强度 |
| 异常行为 | 业务阈值、DBSCAN、Isolation Forest | GeoTrackNet/Autoencoder | 异常真值定义、基线正常行为、船型差异 |
| 多源跟踪融合 | 单源 KF/EKF、最近邻匹配 | JPDA/MHT/IMM | 雷达与 AIS 数据同源识别、时延、测量噪声 |
| 通告与规则检索 | 关键词、BM25 + 生效时间/空间筛选 | 混合检索、RAG + 可验证规则引擎 | 官方原文准确性、法规适用范围 |
| 航路与交通组织 | Dijkstra/A*、FCFS、MILP | 时变路径、多目标优化、ALNS/滚动求解 | 是否拥有可用于规划的权威航道图及约束数据 |

**注意**：初期 K07/K08 场景仍可优先用于验证 dsh 工具体系，但算法调研覆盖所有 K01–K13，不把技术路线固定在该两场景或任何一种模型上。

## 6. 对 Data Access Service 的反向要求

专业算法的共同输入更适合按**业务数据产品**组织，而不是按“某模型需要的五流特征”组织：

| 数据产品（建议） | 核心信息 | 代表消费者 |
| --- | --- | --- |
| Raw AIS Observations | MMSI、观测时间、位置、SOG/COG、静态信息、来源/质量 | 数据清洗、状态估计、异常识别 |
| Vessel Tracks | 船舶、连续时间位置序列、插值/缺失标记、船型 | KF、LSTM、TrAISformer、GeoTrackNet |
| Vessel State Snapshot | 同一分析时刻的区域多船状态及误差/陈旧信息 | CPA/TCPA、Ship Domain、多船风险 |
| Segment Time Series | 航段方案、时间窗口、指标和单位、质量/版本 | SARIMA、XGBoost、LSTM、STGCN |
| Waterway Graph | 航段/节点、上下游/支流连接、空间边界、通航能力 | DCRNN、STGCN、Dijkstra、优化求解 |
| Environmental / Infrastructure | 水文气象、桥/闸/航道状态、有效时间 | 特征增强、通行约束、风险计算 |
| Navigation Rules / Notices | 原文、发布时间、有效时间、适用水域、状态和来源 | BM25、RAG、规则过滤、事件影响分析 |

推荐通过 Dataset/Spatial/Feature/Asset Catalog 描述它们。**Data Access Service 的统一性体现在查询语义、版本、权限、时效和可追溯性，而不是强制所有数据或所有算法使用同一种张量格式。**

工具间数据传输继续保持【待定】：A. 通过已有 Agent 工具获取并传值/引用；B. 算法内部调用 Data Access Service；C. 专用数据准备或共享机制。不得提前确定 `series_ref` 为唯一方式。

## 7. 接下来需核实的事项

1. 按每个业务问题确定**输入/输出口径**：航段流量 ≠ 区域船舶数 ≠ 拥堵指数；轨迹误差与风险评估指标也不同。
2. 核实算法仓库的依赖、许可证、数据获取权限与是否存在独立 inference API，避免将训练脚本误作可插拔在线工具。
3. 对 K07 选取朴素、SARIMA、XGBoost、STGCN 等不同复杂度方法，用统一数据时间切分与指标进行验证，而不是只实现一个复杂模型。
4. 对 K03 选取 CV/KF、LSTM、TrAISformer 等分层基线，数据允许时再加入显式多船交互模型。
5. 分离 Algorithm Registry 的**算法定义**、**适用数据契约**、**已部署实例**和**实际运行记录**；简单确定性算法无需全套训练/部署管理。
6. 与第 04 阶段 Data Access Service 专题衔接：先根据跨任务数据产品定义查询，再决定模型输入如何在工具间传递。

## 8. 后续引用原则

- 通用开源模型只是**可借鉴的代码基线**，不等于经内河数据验证的算法或已有安全适用性。
- 官方海事法规与内河当地通航规则的适用性必须由对应权威来源确定；COLREGs 不能直接作为所有中国内河场景的完整业务规则。
- 所有预测、风险、优化的精度或性能必须在统一数据、公开评价协议和相同输入信息约束下才能比较。
