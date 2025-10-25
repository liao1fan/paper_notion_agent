# Scaling Long-Horizon LLM Agent via Context-Folding

## 📋 基本信息
- **标题**: Scaling Long-Horizon LLM Agent via Context-Folding  
- **作者**: Weiwei Sun, Miao Lu, Zhan Ling, Kang Liu, Xuesong Yao, Yiming Yang, Jiecao Chen  
- **机构**: ByteDance Seed; Carnegie Mellon University; Stanford University  
- **发表时间**: 2025-10-15  
- **来源**: arXiv (cs.CL)  
- **论文链接**: https://arxiv.org/abs/2510.11967 (arXiv:2510.11967)  
- **关键词**: Context-Folding, LLM agent, long-horizon, context management, FoldGRPO, reinforcement learning, task decomposition, agentic coding, deep research  
- **项目页**: https://context-folding.github.io/  
- **其他资源**: https://huggingface.co/papers/2510.11967

---

## 📝 摘要 (Abstract)
提出 Context-Folding 框架，使 LLM agent 能主动管理工作上下文：通过 branch（建立子轨迹）和 return（折叠子轨迹并保留精简总结）两类动作，把代价高的中间步骤移出主上下文。为学习此行为，设计了端到端强化学习算法 FoldGRPO，利用 token-level 的过程奖励（如 Unfolded Token Penalty、Out-of-Scope Penalty）引导任务分解与上下文压缩。在复杂长周期任务（Deep Research、SWE）上，折叠 agent 在使用约 10× 更小的活跃上下文下匹配或优于 ReAct 基线，并显著优于基于摘要的管理方法。

---

## 🎯 研究背景与动机 (Background & Motivation)

### 问题背景
- LLM agent 在处理长路径、需多轮交互的任务（如深度研究、agentic coding）时表现优秀，但会由于交互历史线性累积而受上下文长度限制（性能衰减与计算/内存开销）。
- 线性保留完整交互历史会导致：1) 模型在超长上下文中难以检索关键信息；2) 注意力和 KV-cache 管理成本快速上升。

### 研究动机
- 现有方法主要靠事后摘要或多 agent 分工来扩展 horizon，但事后摘要会打断推理流，多 agent 系统依赖手工流程且难以端到端训练。
- 目标：让单一 agent 学会“主动管理”上下文（什么时候为子任务分支、如何折叠保留有用信息），以在不牺牲高层推理连续性的前提下扩展有效任务长度并降低活跃上下文规模。

### 核心观点
- 引入 Context-Folding——通过显式的 branch/return 操作，agent 能把 token 密集型步骤移入可折叠的子轨迹，完成后以简短总结回到主线，从而保持主上下文紧凑且信息充足。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure1.png" alt="Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).">
  <figcaption>Figure 1 Examples of context folding in long-horizon tasks: deep research (left) and agentic coding (right).</figcaption>
</figure>

---

## 🔍 现有方法及其局限 (Related Work & Limitations)

### 现有解决方案
1. **Summary-based methods**：在上下文满时对历史摘要压缩（post-hoc summarization），代表工作有若干上下文压缩与检索+生成组合方法。  
2. **Multi-agent systems**：将任务拆在多个专用 agent 之间分工（例如工具代理、检索代理），通过工作流管理上下文。  
3. **检索/外存机制**：把历史存到检索库，按需检索以减小当前上下文，但仍需设计高效检索策略和保持推理连贯性。

### 存在的问题
- 摘要方法在压缩时会“中断”原有的思路链，可能丢失决策线索，导致子最优解。  
- 多 agent/手工流程方法不利于端到端训练与泛化。  
- 检索外存增加系统复杂性：需要额外索引/检索策略与一致性维护，仍然无法保证短期工作上下文的连贯与紧凑。

---

## 💡 本文方法 (Proposed Method)

### 核心思想
- 通过两种显式动作（branch 与 return）使 agent 在交互中主动建立可折叠子轨迹并在完成后以精简 summary 折回主轨迹，从而管理上下文长度并保留关键信息。

### 技术路线
- 机制层面：Context-Folding（branch/return + 折叠子轨迹，保留 summary）。  
- 学习层面：基于 GRPO 的 FoldGRPO，加入动态 folded contexts 与 token-level 过程奖励，训练 agent 学会何时分支、分解任务、如何撰写有效总结并控制主上下文的 token 消耗。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure2.png" alt="Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.">
  <figcaption>Figure 2 (a) Context Folding: a mechanism that enables the agent to actively manage its context through branching and return. (b) FoldGRPO: end-to-end optimization of context folding agent.</figcaption>
</figure>

### 关键创新点
1. **Context-Folding 操作集**：定义 branch/return 两种原语，支持在子轨迹中自由使用工具/检索，回到主线只保留 summary。  
2. **FoldGRPO（RL 算法）**：在 GRPO 基础上引入动态 folded contexts 与稠密过程奖励以直接优化分支和折叠行为。  
3. **过程奖励设计**：包括 Unfolded Token Penalty（压缩主上下文中代价高的 token 使用）、Out-of-Scope Penalty（约束子轨迹不偏离子任务目标），以及最终任务奖励，联合引导分解与信息保留。

---

## ⚙️ 方法实现细节 (Implementation Details)

### 算法/模型设计
- Agent 接口扩展：在标准 LLM agent 的动作空间上加入两类控制动作：branch(action) 与 return(summary)。branch 创建新的临时上下文轨迹供局部推理与工具调用；return 将子轨迹折叠并将 summary 写回主上下文。  
- 动态上下文管理：在执行折叠后，从主上下文中删除子轨迹的详细交互，仅保留 summary tokens；FoldGRPO 在训练时直接暴露该动态上下文给模型。

### 技术细节
- 输入：当前主上下文（包含历史 summaries）、工具观察与任务提示。  
- 处理流程（关键步骤）：
  1. Agent 在主上下文决定是否 branch；若 branch 则进入子轨迹子上下文。  
  2. 在子轨迹内自由进行工具调用、检索与推理；过程奖励会在 token 层面评估行为（如惩罚在主上下文进行 token-heavy 操作）。  
  3. 决定 return：生成简短 summary（需保留关键信息以助后续决策），折叠子轨迹并回到主上下文。  
  4. FoldGRPO 更新策略：基于最终任务回报 + 过程奖励进行策略梯度更新（延展 GRPO 的设计以适配动态上下文和稠密奖励）。
- 输出：最终决策或答案，以及一系列子任务 summaries（保存在主上下文中）。

### 实现要点
- Summary 长度/信息量权衡：设计奖励鼓励 summary 同时简洁并包含对最终任务有帮助的关键信息。  
- 子轨迹范围控制：Out-of-Scope Penalty 抑制子轨迹偏离预定子任务，防止无谓探索。  
- 训练实践：使用模拟环境与真实工具（如浏览器检索、代码运行）混合训练；训练观察到 RL 强化后具有更积极的分支行为与更高效的 token 使用。

---

## 📊 实验与结果 (Experiments & Results)

### 实验设置
- **数据集 / 任务**：
  - BrowseComp-Plus（Deep Research 类任务集，N=150）  
  - SWE-Bench Verified（软件工程类长任务，N=500）  
- **基线方法**：ReAct 风格 agent（无折叠机制）、摘要（post-hoc summarization）为上下文管理策略的 agent 等。  
- **评价指标**：任务正确率/Pass@1、scope accuracy、finish rate、主上下文活跃 token 数量、工具调用统计等。

### 主要结果（概述）
- FoldGRPO + Context-Folding 的 agent 在两类长周期任务上匹配或超越 ReAct 基线（同规模模型），同时：
  - 活跃主上下文规模缩小约 10×（即折叠后主上下文更紧凑）；  
  - 显著优于单纯依赖摘要的上下文管理方法（在保持连贯性的同时降低 token 使用）；  
  - RL 训练导致更频繁且更聚焦的分支行为（更多有用的工具调用与搜索页数），从而提升最终任务表现与完成率。  

- 实验中还展示了当任务组合复杂度（需合并多个简单问题以形成更长的交互）提高时，折叠 agent 对上下文长度的鲁棒性优于基线（见下图对比）。

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Figure5.png" alt="Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.">
  <figcaption>Figure 5 Left: Pass@1 vs. agent max context length. Right: Pass@1 vs. number of combined questions. Multiple easy questions are combined into a single harder question to increase problem complexity; a higher number of combined questions indicates more required actions and a longer context to answer them correctly. See Section 4.4.2 for details.</figcaption>
</figure>

<figure>
  <img src="../pdfs/Scaling Long-Horizon LLM Agent via Context-Folding/extracted_images/Table1.png" alt="Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.">
  <figcaption>Table 1 Performance on BrowseComp-Plus (N=150) and SWE-Bench Verified (N=500). Boldface indicates the best-performing 36B models. Numbers in parentheses indicate improvement or reduction compared to 327K ReAct agent Seed-OSS-36B baselineψ.</figcaption>
</figure>

### 分析与讨论
- FoldGRPO 的稠密过程奖励有效促使 agent 把“高 token 成本”的操作放入可折叠子轨迹，从而减少主上下文的不必要膨胀；折叠后的 summary 保证后续高层决策所需信息被保留。  
- RL 训练下 agent 的行为更具探索性，但更受约束（通过 Out-of-Scope Penalty），从而在完成率和 scope accuracy 上提升。  
- 训练成本与实现复杂度较纯生成式基线提高（需要对动态上下文、子轨迹管理及稠密奖励进行工程化支持），但换来更好的长时序扩展能力与效率。

---

## ⚠️ 局限性 (Limitations)
1. **训练成本与复杂度**：FoldGRPO 依赖强化学习训练与环境模拟，训练时间和工程实现复杂度明显高于直接微调/提示工程方法（论文有专门训练时间成本分析）。  
2. **summary 质量依赖性**：折叠后保留的信息完全依赖 return 时生成的 summary，若 summary 丢失关键细节会影响后续决策，且 summary 生成策略尚需精细设计。  
3. **通用性验证有限**：实验主要在 BrowseComp-Plus 与 SWE-Bench 等特定长周期任务集上验证，尚需更多场景（多模态交互、更多真实工具链）来全面评估泛化能力。  
4. **系统集成复杂**：在真实生产环境把动态折叠、子轨迹管理、KV-cache 等集成到已有 LLM 基础设施需额外工作。

---

## 🔮 未来方向 (Future Work)
1. 更强的 summary 学习：探索对 summary 的显式信息保留约束（例如信息量/有用性指标）或辅助记忆模块来提高折叠后信息保真度。  
2. 分层/递归折叠：研究多级折叠（子轨迹内部再分支折叠）与跨任务信息复用策略以进一步扩展 horizon。  
3. 与检索/外部记忆结合：将折叠 summary 与外部检索库联合使用，兼顾长期记忆与短期紧凑上下文。  
4. 更广泛的任务与工具链验证：在更多真实世界工具（代码运行、实验记录、多模态采集）上检验并优化 FoldGRPO。  
5. 更高效的训练：探索离线 RL、行为克隆预训练或更低成本的监督信号来降低训练门槛。

---

## 💭 个人思考 (Personal Notes)
- Context-Folding 提供了一种可解释且可训练的上下文管理范式，比单纯的事后摘要更贴合 agent 的决策流程；在需要大量工具调用或检索的长任务场景极具应用价值（如长周期科研、复杂软件开发）。  
- 工程实践挑战在于保持 summary 的信息完整性与在训练时平衡探索/约束（过程奖励的设计是关键）。若能配合强检索/记忆模块与更高效训练策略，该方法有望成为长任务 agent 的常用范式。  
- 值得关注项目页与开源资源（HuggingFace 论文页）以获取实现细节与复现代码。

---

## 📚 参考资料 (References)
- 论文原文（arXiv）: https://arxiv.org/abs/2510.11967  
- 项目页: https://context-folding.github.io/  
- 论文在 HuggingFace: https://huggingface.co/papers/2510.11967

---

整理时间: 2025-10-25  
置信度: 0.92（基于提供的 PDF 摘要、图表信息与正文片段，数字细节在表格中以图片形式保留；若需精确数值请请求表格文字化提取）