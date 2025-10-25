# Scaling Long-Horizon LLM Agent via Context-Folding

## 📋 基本信息
- **标题**: Scaling Long-Horizon LLM Agent via Context-Folding  
- **作者**: Weiwei Sun, Miao Lu, Zhan Ling, Kang Liu, Xuesong Yao, Yiming Yang, Jiecao Chen  
- **机构**: ByteDance Seed; Carnegie Mellon University; Stanford University  
- **发表时间**: 2025-10-15  
- **来源**: arXiv (arXiv:2510.11967)  
- **论文链接**: https://arxiv.org/abs/2510.11967  
- **关键词**: context-folding, LLM agents, long-horizon, context management, FoldGRPO, reinforcement learning  
- **项目页**: https://context-folding.github.io/  
- **其他资源**: https://huggingface.co/papers/2510.11967

---

## 📝 摘要 (Abstract)
提出 Context-Folding——一种使 LLM agent 主动管理工作上下文的框架。Agent 可通过 branch（创建临时子轨迹）和 return（折叠子轨迹并保留简洁总结）两类操作，把令牌密集的中间步骤折叠掉，从而保持主线上下文简洁。为使该行为可学习，作者提出 FoldGRPO：基于 GRPO 的端到端强化学习训练框架，结合若干 token 级过程奖励（如 Unfolded Token Penalty、Out-of-Scope Penalty 等），鼓励合理分解任务与高质量折叠。实验（Deep Research、SWE）表明：折叠 agent 在使用约 10× 更小的活跃上下文下，达到或超越 ReAct 基线，并明显优于纯摘要管理方法。

---

## 🎯 研究背景与动机 (Background & Motivation)

### 问题背景
- LLM agent 在长周期任务（如深度研究、代理式编程）中表现优异，但常被有限上下文长度限制。传统 agent 框架将交互历史逐条累积到单一上下文，会导致注意力分配与计算开销随时间急剧上升。  
- 长上下文带来的挑战：模型在超长上下文中检索相关信息性能下降；计算效率和 KV-cache 管理成本高（注意力为二次复杂度）。

### 研究动机
- 目标是让 agent 能够“主动管理”其工作上下文：既能保留必要的长期信息，又能在短期保持紧凑上下文以维持推理质量与效率。  
- 相比被动地在上下文满时做摘要或人工分工的多 agent 系统，希望得到一个可端到端学习、通用且不会中断短期推理流的机制。

### 核心观点
- 通过可控的“分支-折叠（branch-return-fold）”机制，agent 可把令牌密集或局部的子任务移入临时分支轨迹，完成后折叠为简洁总结，从而显著压缩主上下文并维持长期记忆摘要与任务连贯性。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure1.png" alt="Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).">
  <figcaption>Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).</figcaption>
</figure>

---

## 🔍 现有方法及其局限 (Related Work & Limitations)

### 现有解决方案
1. **Summary-based methods**：当工作上下文接近上限时触发后验摘要（compress-and-continue），例如周期性摘要或基于触发器的合并策略。优点是立刻压缩上下文；缺点是可能中断正在进行的短期推理流程并丢失细节。  
2. **Multi-agent systems**：将任务分发到多个专门 agent，沿协作流程管理上下文。优点为分工明确；缺点为需要手工设计工作流，难以端到端优化与泛化。  
3. **扩展上下文模型**（架构性改进，如长序列 Transformer、外部检索/存储）：缓解注意力成本或把部分历史移到外部模块，但不解决“何时折叠/保留哪些信息”的决策问题。

### 存在的问题
- 问题1：摘要方法会在关键时刻破坏工作上下文连贯性，导致性能下降。  
- 问题2：多 agent/手工分工方法难以通用与端到端训练。  
- 问题3：仅依赖模型架构或外部存储无法替代策略性、任务感知的上下文管理决策。

---

## 💡 本文方法 (Proposed Method)

### 核心思想
让 agent 主动通过两类操作（branch, return）管理上下文：在子任务中自由扩展、在完成后折叠子轨迹并保留紧凑总结，从而保持主干上下文小且信息有效。

### 技术路线
- 语义上把交互看成“主线 + 多个可折叠分支”。分支内可进行大量工具调用与观察（如网页搜索、代码浏览），完成后通过 return 产生 outcome summary 并把分支历史折叠（从活跃上下文中移除，只保留 summary）。  
- 使用基于 RL 的 FoldGRPO 进行端到端训练，使模型学会什么时候创建分支、如何高质量总结，以及如何在主线中保持低令牌开销与正确的高层次推理。

### 关键创新点
1. **Context-Folding 操作集**（branch / return / fold）：将“折叠”作为一等操作纳入 agent 行为空间。  
2. **FoldGRPO：端到端 RL 优化**：在 GRPO 基础上引入动态折叠上下文与密集的 token 级过程奖励，直接驱动折叠行为学习。  
3. **过程奖励设计**：包括 Unfolded Token Penalty（惩罚在主上下文中进行令牌密集操作）、Out-of-Scope Penalty（惩罚分支偏离目标）和 summary-preservation reward（奖励保留关键信息帮助最终目标）。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure2.png" alt="Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.">
  <figcaption>Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.</figcaption>
</figure>

---

## ⚙️ 方法实现细节 (Implementation Details)

### 算法/模型设计（高层）
- Agent 的动作空间扩展：在原有的语言生成与工具调用动作外，新增 branch（开始子轨迹）与 return（结束并提供 summary）动作。分支内的每一步是常规交互（生成、工具调用、观测），但在 return 时会触发折叠机制。  
- 折叠效果：fold 操作将分支内的中间 tokens 从“活跃上下文”中移除，仅在主上下文插入简洁 outcome summary（长度远小于被移除的原始步骤）。

### FoldGRPO 关键要素
- 基础算法：以 GRPO（Guided/RL policy optimization）为骨架，做策略梯度式更新。  
- 动态上下文模拟：训练时提供动态构造的“折叠后上下文”给模型，模型需在该上下文下继续决策。  
- 过程奖励（dense, token-level）：  
  - Unfolded Token Penalty：对在主上下文执行的高令牌操作给予负奖励，鼓励将令牌密集工作移入分支。  
  - Out-of-Scope Penalty：对分支内偏离 subtask 目标的行为惩罚，确保分支专注。  
  - Summary Quality Reward：基于 downstream 目标（最终任务成功）和摘要覆盖度，对 summary 质量进行正向反馈。

### 输入/输出与训练细节
- 输入：当前主线上下文（可能包含多个 summaries）、当前任务提示。  
- 输出：token 流（包含 branch/return 指令以及常规生成/工具调用）。  
- 训练数据：长-horizon 任务轨迹（包含子任务结构）；结合环境反馈（任务完成、工具返回）。  
- 计算与效率：折叠显著减少了活跃上下文长度，降低注意力/kv-cache开销，训练中通过动态构建折叠上下文来避免显存爆炸。

---

## 📊 实验与结果 (Experiments & Results)

### 实验设置
- 数据集/任务：Deep Research（BrowseComp-Plus, N=150）与软件工程任务（SWE-Bench Verified, N=500）。  
- 基线方法：ReAct 风格 agent（不折叠，直接累积历史）、摘要驱动的方法、多 agent（若可用）等。  
- 评价指标：任务成功率（Pass@1 / finish rate）、scope accuracy（分支覆盖与聚焦程度）、活跃上下文长度与计算时间。

### 主要结果（总结）
- 在两个长周期任务上，Context-Folding 的 agent（经 FoldGRPO 训练）在使用约 10× 更小的活跃上下文的情况下，达到了或超越了 ReAct 基线的性能，并明显优于基于摘要的上下文管理方法（在任务成功率与上下文效率之间取得更好折中）。  
- RL 训练促使 agent 发起更多有益的分支调用、保持分支专注并生成更有助于最终决策的 summaries。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Table1.png" alt="Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.">
  <figcaption>Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.</figcaption>
</figure>

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure5.png" alt="Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.">
  <figcaption>Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.</figcaption>
</figure>

### 分析与讨论
- 折叠机制使得 agent 能在不牺牲任务成功率的情况下，大幅降低活跃上下文规模，从而缓解长上下文导致的性能下降与计算开销。  
- FoldGRPO 的过程奖励设计（尤其是惩罚在主上下文中进行令牌密集操作）促使 agent 更积极地把细粒度工作放入分支，从而保留主线用于高阶推理。  
- 在复杂性逐步增加的设置（combined-questions）中，折叠 agent 的性能退化速度低于无折叠 baseline，表明其有效扩展了可处理的有效 horizon。

---

## ⚠️ 局限性 (Limitations)
1. **训练成本与数据需求**：FoldGRPO 需要长轨迹与环境交互数据来学习何时分支与如何总结，这对数据构造与训练成本提出较高要求。  
2. **Summary 质量依赖模型能力**：折叠依赖生成高质量 outcome summaries；若 summary 丢失关键信息，可能导致长期决策失败。  
3. **通用性边界**：当前方法在 Deep Research 与 SWE 等任务中验证；对实时交互、极端低延迟或对可解释性有强要求的场景（例如医疗决策）需进一步验证与安全性评估。

---

## 🔮 未来方向 (Future Work)
1. 引入混合检索/记忆模块：把折叠的 summary 与可检索索引结合，支持按需展开已折叠分支（动态 unfold）。  
2. 更细粒度的 summary 策略与可学习压缩：研究如何在 summary 内编码可重用的中间表示（而非单纯文本压缩）。  
3. 跨任务与跨域泛化：研究如何让折叠策略在更多任务类别上零样本或少样本迁移。

---

## 💭 个人思考 (Personal Notes)
- Context-Folding 是一个“把上下文管理策略化、把折叠做成可学习动作”的直观且实用的设计，弥补了纯摘要方法与手工多-agent 的短板。  
- 成功的关键在于 summary 的信息保留和过程奖励的设计：二者决定了折叠不会成为信息丢失点。  
- 实务上，可考虑将折叠与可检索向量库结合，以便在需要时可展开历史细节，提升灵活性。

---

## 📚 参考资料 (References)
- 论文原文（arXiv）：https://arxiv.org/abs/2510.11967  
- 项目页：https://context-folding.github.io/  
- 其他资源（HuggingFace Paper）：https://huggingface.co/papers/2510.11967

---

**整理时间**: 2025-10-25  
**置信度**: 高（基于论文 PDF 的直接抽取与阅读）