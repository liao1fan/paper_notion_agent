# Scaling Long-Horizon LLM Agent via Context-Folding

## 📋 基本信息
- **标题**: Scaling Long-Horizon LLM Agent via Context-Folding  
- **作者**: Weiwei Sun, Miao Lu, Zhan Ling, Kang Liu, Xuesong Yao, Yiming Yang, Jiecao Chen  
- **机构**: ByteDance Seed; Carnegie Mellon University; Stanford University  
- **发表时间**: 2025-10-15  
- **来源**: arXiv (arXiv:2510.11967)  
- **论文链接**: https://huggingface.co/papers/2510.11967 (PDF)  
- **关键词**: Context-Folding, LLM agent, long-horizon, FoldGRPO, reinforcement learning, context management  
- **项目页**: https://context-folding.github.io/  
- **其他资源**: https://huggingface.co/papers/2510.11967

---

## 📝 摘要 (Abstract)
本文提出 Context‑Folding：一种允许 LLM agent 主动管理工作上下文的机制。Agent 可以通过 branch 动作进入局部子轨迹处理子任务，完成后通过 return 动作折叠（fold）该分支，将中间步骤移出主上下文，仅保留简洁的总结以支持后续高层推理。为让该行为可学习，作者提出端到端强化学习算法 FoldGRPO，设计若干 token 级别的过程奖励（如 Unfolded Token Penalty、Out‑of‑Scope Penalty）来引导有效分解与折叠行为。在长周期任务（Deep Research、SWE）上，折叠 agent 在使用约 10× 更小的活跃上下文下，匹配或超越 ReAct 基线，并明显优于基于摘要的方法。

---

## 🎯 研究背景与动机 (Background & Motivation)

### 问题背景
随着 LLM agent 在复杂长任务（如深度研究、agentic 编程）中的广泛应用，任务交互历史长度持续增长。传统 agentic 框架将整个交互历史线性累积到单一上下文中，导致两类主要问题：1) LLM 难以在超长上下文中有效检索与利用关键信息；2) 注意力/缓存开销随上下文长度呈二次或更差缩放，效率下降显著。

### 研究动机
现有两类主流思路（基于摘要的后处理与多 agent 分工）各有不足：摘要会在关键时刻打断工作流并可能丢失细节；多 agent 系统依赖手工设计的流程，不利于端到端优化与普适性。作者提出让 agent 自主决定何时“分支—折叠”以主动管理上下文，从而保持短期工作上下文的连贯性并自动积累紧凑的长期历史。

以下图示直观说明了问题与 Context‑Folding 的高层动机（分支用于密集 token 操作，折叠后仅保留要点）：

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure1.png" alt="Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).">
  <figcaption>Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).</figcaption>
</figure>

### 核心观点
将“分支—折叠”作为 agent 的可操作动作，配合专门的强化学习奖励设计，使 agent 学会：
- 在主线保持简洁、把高 token 代价的探索放到临时子轨迹；
- 在子轨迹完成时生成高质量摘要并折叠中间细节，从而扩展 agent 的有效任务视野（effective horizon）与系统效率。

---

## 🔍 现有方法及其局限 (Related Work & Limitations)

### 现有解决方案
1. **摘要/压缩后处理**：当上下文接近限制时进行自动或半自动摘要，替换历史内容以腾出空间（例如基于 LLM 的总结模块）。  
2. **多 agent/分布式策略**：通过多个专业 agent 分担子任务，将不同流的上下文分开管理。  
3. **检索增强与长期记忆**：将重要信息写入外部记忆/知识库，通过检索恢复历史要点而非直接保留长上下文。

### 存在的问题
- 摘要方法会在关键推理阶段造成突兀的上下文变化，可能损害连续性或遗漏细节。  
- 多 agent 方案常依赖人工设计的任务分配与流程，难以端到端训练与通用化。  
- 检索/长期记忆方法需要高质量索引与检索策略，且在操作密集的短期决策中仍需保持工作上下文连贯性。

---

## 💡 本文方法 (Proposed Method)

### 核心思想
设计一个可训练的 agent 能主动通过“branch（分支）”和“return（返回并折叠）”两类操作来管理工作上下文：把代价高或局部封闭的子任务移到分支处理，完成后折叠分支历史，仅保留紧凑的总结回到主线程。

### 技术路线
整体在 LLM agent 的行动空间中引入两种特殊动作（branch、return），并用强化学习（FoldGRPO）端到端训练 agent，奖励信号包括过程级（token 级）奖励以鼓励良好的分解与折叠行为，同时惩罚在主上下文执行耗 token 操作。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure2.png" alt="Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.">
  <figcaption>Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.</figcaption>
</figure>

### 关键创新点
1. **Context‑Folding 机制**：在 agent 行为集成入 branch/return，实现临时子轨迹与折叠操作，使主上下文保持紧凑。  
2. **FoldGRPO（强化学习方案）**：在 GRPO 基础上扩展，支持动态折叠的上下文和密集的 token 级过程奖励。  
3. **过程奖励设计**：包括 Unfolded Token Penalty（惩罚在主上下文执行高 token 操作）、Out‑of‑Scope Penalty（鼓励分支聚焦）和 summary‑quality incentives（奖励保留有用信息的折叠总结）。

---

## ⚙️ 方法实现细节 (Implementation Details)

### 算法/模型设计
- Agent 基于 LLM（指定可替换的 backbone），在生成时可选择常规生成、触发 branch（开启子轨迹）或 return（结束子轨迹并折叠）。  
- 分支（branch）创建独立的临时上下文（子轨迹），支持工具调用（如 web 浏览、代码查询）。子轨迹中的所有交互默认不计入主上下文的 token 使用，直到 return。  
- 返回（return）要求 agent 生成一个简洁的 summary（折叠摘要），该摘要被加入主上下文，子轨迹的原始中间消息被删除（folded）。

### 技术细节
- **输入**: 主上下文（包括问题、历史 summary）、当前观测、工具接口结果。  
- **处理流程**:
  1. Agent 决策：继续主线 / branch / return。  
  2. 如果 branch：新子轨迹上下文初始化，agent在子轨迹中继续交互（可多次工具调用）。  
  3. 当子任务完成且 agent 选择 return：生成 fold summary；将 summary 写回主上下文并删除子轨迹细节。  
- **输出**: 主上下文更新（含新 summary），agent 后续决策以更新后的主上下文为基础。

### 实现要点
- 强化学习细粒度奖励：设计了过程级（token 级）奖励而非仅终局奖励，能直接引导分支时机与总结质量。  
- Unfolded Token Penalty：对在主上下文中产生大量 token 的操作给予即时负奖励，促使 agent 把这类操作移入分支。  
- Out‑of‑Scope Penalty：在分支中若 agent 偏离目标（长时间搜索无关信息）则惩罚，以保证分支聚焦。  
- 将 GRPO（Generalized Retrace Policy Optimization）扩展为 FoldGRPO，支持动态改变的环境状态（折叠操作改变上下文长度/内容），并在训练时模拟分支/折叠的开销与效果。

---

## 📊 实验与结果 (Experiments & Results)

### 实验设置
- **任务/数据集**: Deep Research（BrowseComp-Plus，N=150）与 SWE（SWE‑Bench Verified，N=500）等复杂长跨度任务集合（详见论文）。  
- **基线方法**: ReAct（无主动折叠）、基于摘要的上下文管理方法、多 agent 策略等。  
- **评价指标**: Pass@1（或任务特定的正确率）、scope accuracy（分支聚焦度）、finish rate（任务完成率）、活跃上下文大小、效率（时间/token 开销）。

### 主要结果
- 折叠 agent（FoldGRPO 训练）在 BrowseComp‑Plus 与 SWE‑Bench 上匹配或超越 327K ReAct‑36B 基线的表现，同时活跃上下文规模减少约 10×（主文摘要与结论）。下表为论文的核心性能对比（见原表）：

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Table1.png" alt="Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.">
  <figcaption>Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.</figcaption>
</figure>

- 在难度分组实验中，RL（FoldGRPO）训练带来的改进在 easy/medium/hard 三组均显著（论文 Figure 3）。  
- 关于上下文长度敏感性，作者展示了 Pass@1 随 agent 最大上下文长度与问题合并数（combined questions）变化的关系，FoldGRPO 在短活跃上下文下仍能保持高性能（见下图）：

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure5.png" alt="Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.">
  <figcaption>Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.</figcaption>
</figure>

### 分析与讨论
- FoldGRPO 的过程奖励显著改变 agent 行为：更多有针对性的分支、更多工具调用但集中于子轨迹，从而减少主上下文的 token 压力并提升整体完成率。  
- 相比纯摘要方法，Context‑Folding 在保留关键细节与维持工作流连贯性上更有优势；相比多 agent，Context‑Folding 更易端到端训练与泛化。  
- 训练与部署成本：引入 RL（FoldGRPO）会提高训练复杂度与时间开销（论文报告了训练时间曲线与步骤成本），但在长期运行中能节约推理成本与 KV‑cache 负担。

---

## ⚠️ 局限性 (Limitations)
1. **训练复杂度与成本**：FoldGRPO 依赖 RL 的端到端训练与精细奖励设计，训练时间与资源开销高，难以在资源受限场景直接复现。  
2. **折叠摘要质量依赖**：若 return 生成的 summary 质量不高，折叠会导致信息丢失，影响后续高层推理。当前方法对 summary 质量仍敏感。  
3. **环境与工具支持要求**：Context‑Folding 假设运行时环境支持子轨迹隔离与回收（folding）的操作；在一些现有 agent 平台中实现需要额外系统/工具适配。  
4. **泛化性问题**：尽管在 Deep Research 与 SWE 上表现良好，但对其它任务域（如对话式连续交互、实时决策）需要进一步验证。

---

## 🔮 未来方向 (Future Work)
1. 自动化或自适应的折叠策略：让 agent 学会更鲁棒的折叠触发条件与 summary 长度控制。  
2. 更强的 summary 验证机制：在 return 时加入可检验的 summary‑quality 信号（例如基于检索可验证性或下游任务反馈）。  
3. 与长期记忆 / 强检索结合：把折叠 summary 系统化写入外部长期记忆并支持高效检索恢复。  
4. 减少训练成本的策略：采用离线 RL、模仿学习预训练或更高效的过程奖励替代方案以缩短训练周期。  
5. 将 Context‑Folding 扩展到多 agent 协同，研究分布式折叠/合并策略。

---

## 💭 个人思考 (Personal Notes)
- Context‑Folding 在概念上很契合“局部密集操作 + 全局精简记忆”的直觉，特别适合需要大量工具调用或网页浏览的长任务（如文献综述、代码库理解）。  
- 过程奖励（token 级）是促使 agent 学会良好上下文管控的关键，但如何设计通用且稳定的奖励仍具挑战。  
- 工业落地需关注系统支持（如何高效折叠/回滚上下文、KV‑cache 管理）以及 summary 质量保证机制（可考虑结合可检索性或断言/验证步骤）。

---

## 📚 参考资料 (References)
- 论文原文 (arXiv): https://huggingface.co/papers/2510.11967 (arXiv:2510.11967)  
- 项目页: https://context-folding.github.io/  
- 其他资源: https://huggingface.co/papers/2510.11967

---

**整理时间**: 2025-10-25  
**置信度**: 0.90 (基于提供 PDF 内容片段与 figure/table 信息的提取质量)