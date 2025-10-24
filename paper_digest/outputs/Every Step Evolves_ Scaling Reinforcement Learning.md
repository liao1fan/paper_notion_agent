# Every Step Evolves: Scaling Reinforcement Learning for Trillion-Scale Thinking Model

## 📋 基本信息
- **作者**: Ling Team, Anqi Shen, Baihui Li, Bin Hu, Bin Jing, Cai Chen, Chao Huang, Chao Zhang, Chaokun Yang, Cheng Lin, Chengyao Wen, Congqi Li, Deng Zhao, Dingbo Yuan, Donghai You, Fagui Mao, Fanzhuang Meng, Feng Xu, Guojie Li, Guowei Wang, Hao Dai, Haonan Zheng, Hong Liu, Jia Guo, Jiaming Liu, Jian Liu, Jianhao Fu, Jiannan Shi, Jianwen Wang, Jianxin Lai, Jin Yang, Jun Mei, Jun Zhou, Junbo Zhao, Junping Zhao, Kuan Xu, Le Su, Lei Chen, Li Tang, Liang Jiang, Liangcheng Fu, Lianhao Xu, Linfeng Shi, Lisha Liao, Longfei Zheng, Meng Li, Mingchun Chen, Qi Zuo, Qiang Cheng, Qianggang Cao, Qitao Shi, Quanrui Guo, Senlin Zhu, Shaofei Wang, Shaomian Zheng, Shuaicheng Li, Shuwei Gu, Siba Chen, Tao Wu, Tao Zhang, Tianyu Zhang, Tianyu Zhou, Tiwei Bie, Tongkai Yang, Wang Hong, Wang Ren, Weihua Chen, Wenbo Yu, Wengang Zheng, Xiangchun Wang, Xiaodong Yan, Xiaopei Wan, Xin Zhao, Xinyu Kong, Xinyu Tang, Xudong Han, Xudong Wang, Xuemin Yang, Xueyu Hu, Yalin Zhang, Yan Sun, Yicheng Shan, Yilong Wang, Yingying Xu, Yongkang Liu, Yongzhen Guo, Yuanyuan Wang, Yuchen Yan, Yuefan Wang, Yuhong Guo, Zehuan Li, Zhankai Xu, Zhe Li, Zhenduo Zhang, Zhengke Gui, Zhenxuan Pan, Zhenyu Huang, Zhenzhong Lan, Zhiqiang Ding, Zhiqiang Zhang, Zhixun Li, Zhizhen Liu, Zihao Wang, Zujie Wen (见原文 Contributions 部分以获取完整署名)
- **机构**: Ling Team; Inclusion AI
- **发表时间**: 2025-10-22
- **来源**: arXiv (cs.CL)
- **论文链接（PDF/预印本）**: https://arxiv.org/abs/2510.18855
- **标签**: reinforcement learning, trillion-scale, thinking model, Mixture-of-Experts, MoE, large language model, training stability, rollout processing, RL system, IcePop, C3PO++, ASystem, open-source, reasoning benchmarks
- **项目页**: https://github.com/inclusionAI/Ring-V2
- **代码**: https://github.com/inclusionAI/Ring-V2
- **模型（Hugging Face）**: https://huggingface.co/inclusionAI/Ring-1T
- **其他资源**: arXiv 页面（同上）

---

## 📝 摘要 (Abstract)
Ring-1T 是首个开源的 trillion-scale（万亿参数）“thinking model”，总参数量 1T，单 token 激活约 50B 参数。为了解决在万亿参数 MoE 上使用强化学习训练时出现的训练-推理不一致、长 rollouts 处理低效和 RL 系统瓶颈，作者提出三项关键互联技术：IcePop（基于 token 级差异的掩码与裁剪以稳定 RL）、C3PO++（对长 rollout 在给定 token 预算下做动态分片以提升时间与资源效率）、ASystem（面向万亿参数 RL 的高性能系统框架）。Ring-1T 在多项推理/数学/编程基准上取得突破性成绩（如 AIME-2025: 93.4，HMMT-2025: 86.72，CodeForces: 2088，ARC-AGI-v1: 55.94），并在 IMO-2025 达到银牌级别表现。全文开源模型权重与训练代码，旨在为研究社区提供万亿级推理能力基线。

---

## 🎯 研究背景与动机 (Background & Motivation)

### 问题背景
近年来大规模语言模型（LLMs）从“记忆大量知识”逐步转向“主动推理与动态解题”，强化学习（特别是 RLHF 与基于奖励的自我改进）在提升复杂推理能力方面发挥了关键作用。与此同时，Mixture-of-Experts（MoE）架构成为提高参数规模与计算经济性的主要手段，使得激活超大参数量成为可能。然而，将强化学习方法扩展到万亿参数（trillion-scale）MoE 模型带来了全新的挑战：训练-推理不一致（导致训练不稳定）、长序列 rollouts 在 token 预算下处理效率低、以及现有 RL 系统在通信/内存/调度上的瓶颈使得大规模 RL 难以实用化。

### 研究动机
作者旨在构建并开放一个真正的万亿参数“thinking model”（Ring-1T），通过解决在这个尺度下强化学习训练的关键痛点，使得社区能在开源基础上探索更强的推理与思考能力。为实现这个目标，他们需要在算法（训练稳定性、rollout 策略）与系统（高效 RL 框架）层面同时突破。

### 核心观点
要在万亿参数 MoE 上成功应用强化学习，需要同时解决三个互为制约的问题：训练-推理一致性（稳定性）、rollout 的时间与内存效率、以及高性能的 RL 训练系统。单一维度的改进不足以在该规模实现鲁棒训练；因此必须提出互补的算法与系统协同方案。

---

## 🔍 现有方法及其局限 (Related Work & Limitations)

### 现有解决方案
1. **标准 RLHF / policy gradient 在大模型上的应用**：通过人类反馈训练策略，但在大模型上易受训练-推理不一致影响，训练不稳定（OpenAI 等工作）。
2. **Mixture-of-Experts（MoE）扩展参数规模**：在保持计算开销可控的前提下扩大量级（多家研究/公司采用），但 MoE 的巨大激活/通信导致 RL 训练复杂度显著上升。
3. **长序列/rollout 优化（分段、截断等）**：已有一些分段或截断策略用于长序列训练以节省内存，但这些方法在 token 预算、训练效率与策略一致性之间没有良好折中。

### 存在的问题
- 问题1: 训练-推理不一致。训练时的 teacher forcing / 教师注入与推理时自回归采样导致分布差异，放大至 MoE 与 RL 的联合训练时，容易触发梯度爆发或策略崩溃（训练不稳定）。
- 问题2: Rollout 处理效率低。长 rollout 在 token 预算和显存限制下难以高效并行，导致设备利用率低、训练时间巨大。
- 问题3: RL 系统瓶颈。现有 RL 框架在超大模型（trillion-scale）和 MoE 通信模式下，面临显存分配、参数切片、跨设备通信、调度延迟等综合瓶颈，成为训练速度与扩展性的主要限制因素。

---

## 💡 本文方法 (Proposed Method)

### 核心思想
通过算法与系统协同设计，分别解决训练稳定性、rollout 资源利用以及系统性能三大类问题，使得在万亿参数 MoE 上进行高效、稳定的强化学习训练成为可能。

### 技术路线
整体训练流程与系统由三层要素组成（互相配合）：
1. 算法稳定层：IcePop —— token 级差异掩码与裁剪，缓解训练-推理不一致导致的不稳定性；
2. Rollout 优化层：C3PO++ —— 在固定 token 预算下动态分片长 rollouts，提高时延与并行利用率；
3. 系统实现层：ASystem —— 面向万亿参数（MoE）的高性能 RL 框架，优化通信、内存与调度以支持上述算法高效运行。

训练管线上，作者采用三阶段训练策略（SFT → 可验证奖励 RL → RLHF），以逐步提升模型的可控性与策略质量（小红书摘要与论文中均提及三阶段方案）。

### 关键创新点
1. **IcePop**：引入 token 级别的“差异掩码（discrepancy masking）”与“裁剪（clipping）”机制，精细控制训练中因教师强制与采样差异产生的梯度/奖励噪声，从而稳定 RL 训练。
2. **C3PO++**：设计一种动态分割（dynamic partitioning）策略，将长 rollouts 按 token 预算智能分段并调度执行，显著提高设备利用率与整体时间效率，同时保持 rollout 的连贯性与效果。
3. **ASystem**：开发面向万亿参数 MoE 的高性能 RL 框架，优化模型并行、数据并行、专家路由通信、内存复用与调度策略，消除系统级瓶颈，使得上层算法能在可接受的时间内完成训练。

---

## ⚙️ 方法实现细节 (Implementation Details)

### 算法/模型设计
- 模型架构：基于 Ling 2.0 架构的 Mixture-of-Experts（MoE）模型，Ring-1T 总参数量约 1 万亿（1T），激活参数量约 50B/ token（即每个 token 激活约 50B 参数）——通过 MoE 机制实现高参数量与可控计算成本的折中。
- 训练流程（高层次）：
  1. SFT（Supervised Fine-Tuning）：用监督数据对基础模型进行指令微调，建立初始行为；
  2. 可验证奖励 RL（Verifiable Reward RL）：在可验证奖励或自监督可度量的任务上进行 RL 优化以提升策略质量和推理能力；
  3. RLHF：引入人类反馈（或代理评价）进一步提升行为质量与对齐性。
- IcePop 细节：
  - 在计算 RL 损失（如基于策略梯度/价值函数的目标）时，对训练时与推理时分布差异显著的 token 位置施加掩码或降低权重，避免因这些位置的高方差梯度破坏整体训练；
  - 同时，对奖励或梯度引入裁剪（clipping）机制，防止异常样本导致策略更新过大；
  - 目标是缩小训练分布（teacher-forced）与推理分布（free-running）之间在 token 级别的差异影响。
- C3PO++ 细节：
  - 在给定 token 预算（例如单次训练批次允许的最大 token 数）下，将长 rollouts 动态划分为多个逻辑分段（segments），每段在不同设备或不同时间片上并行执行；
  - 维持段间状态连贯（保存必要的激活或摘要信息），并通过异步/流水线化调度最大化吞吐；
  - 提供策略以在不同阶段决定是否延续、合并或重采样 segments，以兼顾样本质量与计算开销。
- ASystem 细节：
  - 在系统层面实现 MoE 路由优化、稀疏专家调度、跨设备通信压缩、显存复用（activation sharding & recompute）、并行调度策略；
  - 将训练过程与 RL 特有的调度（如 rollout 收集、策略评估、经验缓存）深度集成，降低 I/O 与同步延迟；
  - 设计用于万亿级模型的容错与伸缩机制，以提升训练可靠性。

### 技术细节汇总
- **输入**: 文本指令、问题或上下文（标准自回归 token 序列）；在 RL 阶段同时输入环境/评估器产生的 reward signals。
- **处理流程**:
  1. SFT 获得初始策略；
  2. 在 Verifiable Reward RL 中以 IcePop 机制约束训练-推理不一致并通过 C3PO++ 收集与处理长 rollouts；
  3. 使用 ASystem 承载高吞吐训练，完成大规模并行更新与 checkpoint；
  4. 最终以 RLHF 精炼策略（若有人工反馈）。
- **输出**: 优化后的策略模型（Ring-1T），并提供模型权重与推理代码供社区使用。

### 实现要点（工程与实战经验）
- MoE 专家路由是性能瓶颈，需在 ASystem 中定制高效路由与通信压缩；
- IcePop 需要在 token 级别维护额外的 mask/权重信息，实现上需低开销集成到损失计算；
- C3PO++ 的分段需要维护段间状态并处理段边界的策略连续性，工程上需设计高效的激活保存/恢复与异步调度机制；
- checkpoint 与恢复在如此规模下代价巨大，ASystem 提供增量 checkpoint 与快速恢复机制以提升训练鲁棒性。

（注：论文提供了方法框架与关键设计理念，具体超大规模系统实现细节（如每项模块的精确参数/调度策略/压缩算法实现代码级细节）在文中有一定描述，但若需完整代码级解释请参见开源仓库。若某些低层实现参数未在论文正文完全列出，标注为 “[信息不足]”。）

---

## 📊 实验与结果 (Experiments & Results)

### 实验设置
- **目标基准/任务**（论文给出多项评估）：
  - AIME-2025（数学竞赛）；
  - HMMT-2025（数学竞赛）；
  - IMO-2025（国际数学奥林匹克）成绩评估（达到银牌级别）；
  - CodeForces（编程）评分/Rating；
  - ARC-AGI-v1（通用推理/AGI基准）；
  - LiveCodeBench（编程基准集合）；
  - Arena-Hard-v2.0（对弈/agent benchmark）；
  - HealthBench、Creative Writing v3 等若干任务。
- **基线方法**:
  - 多种开源与闭源“thinking”模型（Paper 图表中与 Ring-1T 比较的包括 Qwen3-235B、DeepSeek-V3.1-Terminus、Gemini-2.5-Pro、GPT-5-Thinking (High) 等）。
- **评价指标**:
  - pass@1 / 准确率/得分（数学与编程竞赛）；
  - CodeForces rating；
  - Arena win-rate 等任务特定指标。

### 主要结果（论文中关键数值）
- AIME-2025: 93.4 (pass@1)
- HMMT-2025: 86.72 (pass@1)
- CodeForces: 2088 (rating)
- ARC-AGI-v1: 55.94 (pass@1)
- Arena-Hard-v2.0: 81.59 (win-rate)（图中显示）
- LiveCodeBench (2408-2505): ~78.30–85.70（图示不同模型区间，Ring-1T 在该区间偏高）
- Creative Writing v3: ~85.59（score）
- HealthBench: ~57.93（score）
- IMO-2025: 达到银牌级别（论文中指出“Notably, it attains a silver medal-level result on the IMO-2025”）

在多个对比图中，Ring-1T 在大部分推理与竞赛基准上领先于现有多款开源与闭源模型（论文 Figure 1）。

### 表格化（关键对比）
（基线值与 Ring-1T 的部分类比见论文图示，以下列出论文明确给出的代表性指标）

| 基准 | Ring-1T |
|------|---------|
| AIME-2025 (pass@1) | 93.4 |
| HMMT-2025 (pass@1) | 86.72 |
| CodeForces (rating) | 2088 |
| ARC-AGI-v1 (pass@1) | 55.94 |
| Arena-Hard-v2.0 (win-rate) | 81.59 |
| IMO-2025 | 银牌级别 |

### 分析与讨论
- Ring-1T 在数学与编程基准上取得显著提升，表明在万亿参数尺度与特定 RL 优化策略的组合下，模型的深度推理能力显著增强；
- IcePop 在训练时降低了由于训练-推理不一致带来的不稳定性，使得模型能在 RL 训练中保持鲁棒，从而提高最终任务表现（论文通过 ablation/实验对比展示 IcePop 带来的稳定性提升，但具体 ablation 数值需参见论文主文/附录）；
- C3PO++ 的动态分段策略在保持高质量 rollout 的同时显著提高了硬件利用率与训练时间效率（论文报告了时间效率/吞吐提升，但具体比率在文中细节或补充材料中给出）；
- ASystem 在系统级别消除了若干瓶颈，使得上述算法方法在实操中可拓展到 1T 参数级别。

（注：论文中包含更多细节性对比实验、消融研究与工程性能数据，具体的实验设置（训练步数、GPU/集群规格、token 预算数值等）若未在主文完全列明，请参阅仓库与论文附录以获取完整数值；若查阅仍不到位，标注为 “[信息不足]”。）

---

## ⚠️ 局限性 (Limitations)
1. **资源与可重复性成本高**：尽管 Ring-1T 开源权重与代码，但重训或在本地复现实验仍需要极高计算资源（数千至数万 GPU 小时），这限制了普通研究者的可操作性。
2. **工程细节与可移植性**：ASystem、C3PO++ 在实现上依赖定制化集群配置与低层优化（如通信压缩、路由实现），将这些优化移植至不同硬件/云环境可能面临实现门槛。[信息不足：具体硬件/配置跨平台适配细节]
3. **安全与对齐风险**：更强的推理与生成能力同时带来更高的滥用风险与不可预测行为，论文未深度讨论模型对齐与安全策略（虽包含 RLHF 阶段，但长期对齐问题仍需进一步研究）。
4. **可解释性与验证**：尽管在多个竞赛上取得高分，但对于“为何”模型能在复杂数学问题上表现优异的可解释分析较少，理解模型推理路径与错误模式仍需深入研究。
5. **环境与能耗影响**：大规模训练对能源消耗与碳足迹影响显著，论文未给出完整的能耗/碳排放报告。[信息不足：训练能耗/效率数值细节]

---

## 🔮 未来方向 (Future Work)
1. 提高可重复性与负担降低：探索更高效的蒸馏/压缩方法，使得近似 Ring-1T 能力在更小模型上可复制，从而降低社区门槛。
2. 更深入的对齐与安全研究：在高能力模型上开展系统性的对齐评估、鲁棒性测试与安全防护机制研究。
3. 多模态扩展：将万亿级思维模型扩展到多模态（视觉、符号、程序执行环境）以进一步验证通用思考能力。
4. 系统通用化：将 ASystem 的优化抽象为可在不同硬件/云平台上更易部署的组件与标准，提升移植性。
5. 可解释推理路径挖掘：构建工具分析模型在高难度问题（如 IMO）上的推理链，帮助理解与改进模型能力。

---

## 💭 个人思考 (Personal Notes)
- Ring-1T 展示了算法与系统共同进化在推动极大规模模型实际可训练性上的重要性：单靠模型规模或单项算法改进难以解决工程化瓶颈。
- IcePop 的 token 级别稳定性思想值得在更广泛的 RL-on-LLM 场景中借鉴（例如对话系统的长期一致性训练）。
- C3PO++ 的分段 rollouts 和 ASystem 的工程实现对产业界大规模 RL 实践具有很高的参考价值；但对小规模研究团体而言，如何“降阶”利用这些思路仍是关键问题。
- 论文开源权重对学术界与开源社区意义重大，但同时也需要配套的使用与安全指南。

---

## 📚 参考资料 (References)
- 论文原文（arXiv）: https://arxiv.org/abs/2510.18855
- 代码仓库: https://github.com/inclusionAI/Ring-V2
- 模型（Hugging Face）: https://huggingface.co/inclusionAI/Ring-1T
- 项目主页: https://github.com/inclusionAI/Ring-V2
- 小红书参考摘要（来源于用户摘录）

---

整理时间: 2025-10-23  
置信度: 0.86（基于论文正文提供的内容与图表提取；某些工程实现与训练超参细节在论文主文/附录或仓库中描述有限，已在文中标注 “[信息不足]”）