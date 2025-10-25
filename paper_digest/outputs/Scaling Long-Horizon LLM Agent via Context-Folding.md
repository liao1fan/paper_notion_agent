# Scaling Long-Horizon LLM Agent via Context-Folding

## 📋 基本信息
- **标题**: Scaling Long-Horizon LLM Agent via Context-Folding  
- **作者**: Weiwei Sun, Miao Lu, Zhan Ling, Kang Liu, Xuesong Yao, Yiming Yang, Jiecao Chen  
- **机构**: ByteDance Seed; Carnegie Mellon University; Stanford University  
- **发表时间**: 2025-10-15  
- **来源**: arXiv (preprint)  
- **论文链接**: https://huggingface.co/papers/2510.11967  
- **关键词**: Context-Folding, LLM agent, long-horizon, context management, FoldGRPO, reinforcement learning, summarization  
- **项目页**: https://context-folding.github.io/  
- **其他资源**: https://huggingface.co/papers/2510.11967

---

## 📝 摘要 (Abstract)
本文提出 Context-Folding：一种使 LLM agent 主动管理其工作上下文的机制。Agent 可对某子任务“分支（branch）”到临时子轨迹执行细粒度操作，完成后通过“返回（return）”将子轨迹折叠（fold），只保留扼要的结果摘要，从而压缩活动上下文。为使该行为可学习，作者设计了端到端强化学习算法 FoldGRPO，引入动态折叠上下文与基于 token 级别的过程奖励（如 Unfolded Token Penalty、Out-of-Scope Penalty），鼓励合适的任务分解与压缩策略。在复杂长周期任务（Deep Research 与 SWE）上，折叠 agent 在使用约 10× 更小的活跃上下文下，匹配或超越 ReAct 基线，并显著优于基于后置摘要的方法。

---

## 🎯 研究背景与动机 (Background & Motivation)

### 问题背景
- LLM agent 在长时程任务（如深度研究、 agentic 编程）中需要大量交互与工具调用，交互历史被线性累积到模型上下文中。  
- 这导致两类核心问题：1) 超长上下文会削弱 LLM 检索与推理相关信息的能力；2) 计算效率与内存开销随上下文长度二次/更高阶增长（attention、KV-cache）。

### 研究动机
- 现有方案（基于摘要压缩或多 agent 分工）存在分别的缺点：摘要会中断推理流并丢失关键信息；多 agent 方法依赖手工设计流程、难以端到端优化。  
- 因此希望让单一 agent 能主动决策何时把“重”操作移出主线上下文并在完成后压缩保留关键信息，以保持短期推理环境的干净性并可扩展到更长的交互历史。

### 核心观点
- 引入“分支-折叠（branch-fold）”语义：agent 可创建临时子轨迹做局部探索/工具调用，然后以紧凑摘要回归主线并删除子轨迹细节，从而主动管理上下文规模与信息密度。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure1.png" alt="Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).">
  <figcaption>Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).</figcaption>
</figure>

---

## 🔍 现有方法及其局限 (Related Work & Limitations)

### 现有解决方案
1. **Summary-based methods**：当上下文满时触发后置摘要，把历史压缩为摘要片段（引用：多篇 work）。优点：直接压缩。缺点：可能破坏正在进行的推理流、丢失细节且为后处理步骤。  
2. **Multi-agent systems**：把任务拆给多个专用 agent（例如专门检索、专门推理）。优点：模块化处理。缺点：通常依赖手工流程、难以联合训练、迁移性差。  
3. **纯增加上下文窗口**：通过模型/硬件扩展缓解，但成本高且仍受模型在超长上下文中检索效率下降的限制。

### 存在的问题
- 问题1：被动压缩（后置摘要）会中断思路并可能丢关键信息，影响最终任务表现。  
- 问题2：多 agent/流程化方案不利于端到端学习与泛化。  
- 问题3：直接扩展上下文规模在计算上不可持续，难以形成高效长期交互系统。

---

## 💡 本文方法 (Proposed Method)

### 核心思想
Context-Folding 让 agent 用两种显式动作管理上下文：branch（创建子轨迹）与 return（折叠并返回主线）。子轨迹的中间步骤在 return 后被删除，仅保留简洁的 outcome summary，从而主动控制活动上下文规模。

### 技术路线
- 在 agent 行为空间加入 branch/return 操作，允许局部化、临时的 token 密集探索（如网页搜索、多步代码分析）。  
- 设计 FoldGRPO：基于 GRPO 的端到端强化学习框架，联合优化折叠策略与常规动作，通过密集过程级奖励引导合理分支与摘要生成。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure2.png" alt="Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.">
  <figcaption>Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.</figcaption>
</figure>

### 关键创新点
1. **Context-Folding 操作集**：显式 branch/return，用以创建并折叠子轨迹，保持主线上下文简洁。  
2. **FoldGRPO**：将动态折叠的上下文纳入 RL 训练回路，允许策略端到端学习何时分支与如何摘要。  
3. **过程级奖励设计**：引入 Unfolded Token Penalty（惩罚在主线做的 token 密集操作）、Out-of-Scope Penalty（惩罚分支越界/跑题）、以及鼓励保留关键信息的奖励，直接引导上下文管理行为。

---

## ⚙️ 方法实现细节 (Implementation Details)

### 算法/模型设计
- 基础 agent：基于 LLM 的行动决策架构（类似 ReAct 方式结合工具调用）。  
- 新动作集：branch — 触发后创建新子轨迹，后续操作写入子轨迹；return — 结束子轨迹、由模型生成该子轨迹的 outcome summary，将子轨迹内细节从主上下文中移除，仅把 summary 写回主线程。  
- FoldGRPO 扩展：在原 GRPO（gradient-based RL policy optimization）基础上，folding 的状态表示包含“已折叠摘要”的历史表示；训练时对 token 级操作施加稠密奖励/惩罚。

### 技术细节
- 输入：主线程上下文 + 当前子轨迹（若在分支中） + 工具观察（如搜索结果、代码文件片段）。  
- 处理流程：策略决定是否 branch/return/常规动作 → 若 branch，则转入子轨迹并隔离 token-heavy 操作 → 若 return，则生成 summary，并执行折叠（删除子轨迹中间 token，仅保留 summary）。  
- 输出：任务级动作（包括工具调用）或 fold/return 指令及对应的 summary 文本。

### 实现要点
- **折叠实现**：折叠不仅是文本删除，还需在模型的上下文管理层（KV-cache）中实际移除或替换，确保计算/内存效率。  
- **奖励设计**：Unfolded Token Penalty 促使 agent 把 token-heavy 操作放入 branch；Out-of-Scope Penalty 保证分支内行为聚焦于子任务；任务最终成功给予正向终局奖励。  
- **训练稳定性**：FoldGRPO 使用稠密过程奖励缓解稀疏终局奖励，提升学习分支策略的样本效率。

---

## 📊 实验与结果 (Experiments & Results)

### 实验设置
- **任务集**：长时程任务代表性数据集，包括 Deep Research（BrowseComp-Plus）与 SWE（SWE-Bench Verified）。（论文在 N=150 / N=500 等规模上评估）  
- **基线方法**：ReAct 基线、基于摘要的上下文管理方法、以及未做 folding 的 agent 变体。  
- **评价指标**：Pass@1 / 完成率 / scope accuracy / 活动上下文平均 token 数 / 工具调用次数 等。

### 主要结果（概述）
- 折叠 agent（FoldGRPO）在 BrowseComp-Plus 与 SWE-Bench 上表现匹配或优于 ReAct 基线（在同等模型规模下），并在使用约 10× 更小的活动上下文时保持性能。  
- 与基于摘要的被动压缩方法相比，FoldGRPO 在最终任务成功率上有显著提升（说明主动分支并在合适时折叠能更好保留关键信息与思路连贯性）。  
- 行为上，RL 优化使得 agent 更频繁合理地分支与调用工具，但主线上下文保持紧凑，scope accuracy 与 finish rate 提升。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Table1.png" alt="Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.">
  <figcaption>Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.</figcaption>
</figure>

- 附加对比（context 长度敏感性实验）：作者展示了 Pass@1 随 agent 最大上下文长度的变化和随合并问题数（即需要更多动作的复杂度）上升的曲线，表明折叠能在较小活动上下文下支持更复杂的多步骤问题（见下图）。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure5.png" alt="Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.">
  <figcaption>Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.</figcaption>
</figure>

### 分析与讨论
- 主动 folding 与过程奖励使 agent 学会在合适场景下把 token-heavy 操作迁移到分支，从而减少主线冗余信息、改善推理效率。  
- 相较被动摘要，Context-Folding 保持了子任务的局部连贯性与信息完整性（在生成 summary 时主动保留 outcome），因此对终局任务更有利。  
- FoldGRPO 引导的策略在各种难度组（easy/medium/hard）上普遍带来性能提升（论文中有细分实验与统计）。（[详细数值见 Table1 / 论文原文]）

---

## ⚠️ 局限性 (Limitations)
1. **训练成本与复杂性**：FoldGRPO 需要 RL 训练与精细的过程级奖励设计，训练时间与样本效率是现实制约（论文给出训练时间成本图，训练开销不可忽视）。  
2. **summary 质量与信息丢失风险**：折叠后仅保留 summary，若 summary 生成质量不足可能丢失对后续决策关键的信息。  
3. **泛化与工具接口负担**：不同任务/工具组合可能需要不同的分支粒度与奖励调优，跨域泛化还需进一步验证。  
4. **可解释性与安全性问题**：自动折叠会删除中间证据链，审计与可追溯性需求下需设计额外的可恢复机制或日志保存策略（trade-off）。

---

## 🔮 未来方向 (Future Work)
1. 自动化与自适应的奖励设计：使 Unfolded Token Penalty 等参数可自适应于任务类型与模型规模。  
2. 折叠可逆/可追溯机制：在不损失效率的前提下保留检索中间证据的可视化或压缩索引，便于审计与调试。  
3. 多尺度 folding 策略：探索层级化分支（sub-branch）与不同粒度的 summary，以适应更复杂的多任务场景。  
4. 更广泛的基准验证：在更多领域（如长文档写作、复杂规划、多模态代理）上测试 folding 的普适性。

---

## 💭 个人思考 (Personal Notes)
- Context-Folding 把主动的上下文管理从「被动压缩」提升到「策略化分支与折叠」，是一个很自然且有效的设计方向，尤其适合需要大量工具调用与长证据链的任务。  
- 实际工程化时需要关注 summary 的反馈回路（例如当摘要不足以支持后续决策时，如何自动回滚或展开历史）。  
- 值得探索把 folding 与检索式长期记忆（memory/index）结合：折叠后把子轨迹索引化而非彻底删除，可在需要时按需恢复。

---

## 📚 参考资料 (References)
- 论文原文 (arXiv / PDF): https://huggingface.co/papers/2510.11967  
- 项目页: https://context-folding.github.io/  
- 相关资源/预印本: https://huggingface.co/papers/2510.11967

---

整理时间: 2025-10-25  
置信度: 0.87

(注：本文整理严格基于论文 PDF 内容与作者摘要；部分数值性细节与表格数据请参见论文原文 Table1 与对应章节以获取精确数值。)