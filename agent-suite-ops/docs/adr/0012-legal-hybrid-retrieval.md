# ADR-0012：法律 Agent 混合检索（修订 ADR-0008）

- 状态：已确认（修订 ADR-0008 检索策略章节）
- 日期：2026-07-04
- 阶段：DESIGN-002 修订 / LEGAL-120 实施前
- 关联：取代 ADR-0008 §"决策 — 检索方式 / 向量库"；ADR-0008 其余章节（来源、引用格式、高风险升级、免责声明、知识更新）继续生效。

## 背景

ADR-0008 原选 Chroma + 单路 dense 向量召回，但在法律咨询场景存在系统性短板：

| 现象 | 根因 | 业务影响 |
|---|---|---|
| 法条编号漂移（"第三十五条"召回第三十四/三十六条） | 数字 token 在 dense 向量里几乎没有语义信号 | 引用错误，违反"不伪造法条"铁律 |
| 同义但法律后果不同（"调岗"vs"调薪"vs"调职"） | dense 向量把语义近邻聚到一起 | 答非所问，误导用户 |
| 专有名词长尾（"竞业限制补偿金""劳务派遣许可证"） | 训练语料覆盖不足 | 直接 0 召回 |
| 跨分类串扰 | 纯 dense 不感知分类边界 | 劳动法问题召回出合同法条文 |
| top-K 同义重复 | dense 召回的 top-5 互相高度相似 | 覆盖面窄，证据不足 |

LEGAL-110 验收样本 S1（"公司单方面调岗，我可以拒绝吗"）要求**至少 1 条精确引用**，单 dense 召回达不到该标准。

## 决策

采用**三路混合检索 + 元数据过滤 + cross-encoder 重排 + 引用字符级校验**架构。

### 检索栈

```
用户问题
   │
   1. classification 节点
   │   输出: category_code (civil_labor / family / ...) + 法律实体
   │   实体抽取: 法条编号（正则）/ 法规名称（词典）/ 案由关键词
   │
   2. 混合召回（并行，Qdrant 服务端融合）
   ├─ Dense   top-20   (BGE-M3 dense,  cosine sim)
   ├─ Sparse  top-20   (BGE-M3 sparse, 学习版 BM25)
   └─ 元数据过滤: category_code + material_status='ready'
   │
   3. Qdrant Query API 原生融合（加权 RRF, k=60）
   │   → top-20 候选
   │
   4. Reranker (bge-reranker-v2-m3, cross-encoder)
   │   → top-5 最终片段
   │
   5. citation_check 节点（已有）
   │   答案中的引用必须能在 top-5 snippet 中字符匹配
   │   不匹配 → CITATION_INVALID，丢弃重生成或返回"未找到依据"
```

### 关键技术选型

| 组件 | 选型 | 理由 |
|---|---|---|
| 嵌入模型 | BGE-M3（BAAI/bge-m3） | 一次推理同时输出 dense + sparse + ColBERT，无需额外 BM25；中文效果好；CPU 可推理 |
| 向量库 | **Qdrant 1.12+** | 单容器部署；原生支持 dense + sparse 同时查询与服务端融合；payload 元数据过滤；Python SDK 成熟 |
| 重排模型 | BGE-Reranker-v2-m3（BAAI/bge-reranker-v2-m3） | cross-encoder，多语言，与 BGE-M3 同源；通过 HuggingFace TEI 服务化 |
| 嵌入/重排服务化 | HuggingFace text-embeddings-inference（TEI） | 官方镜像，同时支持 embed 与 rerank；非 root；支持 healthcheck |
| 融合策略 | Qdrant Query API（fusion_mode=rrf, 加权） | 服务端融合，无需客户端代码；权重可配置 |
| 元数据过滤 | Qdrant payload filter（category_code + status） | 强约束，避免跨分类串扰 |

### 配置化参数（Settings 注入，禁硬编码）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `rag_vector_db_url` | `http://qdrant:6333` | Qdrant 服务地址 |
| `rag_vector_collection` | `legal_kb` | 集合名 |
| `rag_dense_weight` | `0.7` | dense 融合权重 |
| `rag_sparse_weight` | `0.3` | sparse 融合权重 |
| `rag_recall_top_n` | `20` | 召回候选数 |
| `rag_rerank_top_n` | `5` | 重排后保留数 |
| `rag_category_filter_enabled` | `true` | 是否启用分类过滤 |
| `rag_reranker_enabled` | `true` | 是否启用重排（false 则直接用融合 top-5） |
| `rag_reranker_base_url` | `http://bge-reranker:8081` | reranker 服务地址 |
| `rag_reranker_model` | `BAAI/bge-reranker-v2-m3` | 模型名 |
| `rag_similarity_threshold` | `0.65` | 最终阈值，低于此丢弃 |
| `embedding_base_url` | `http://bge-embedding:8080` | TEI 嵌入服务地址（输出 dense + sparse） |
| `embedding_model` | `BAAI/bge-m3` | 嵌入模型名 |

## 后果

### 新增依赖
- **Qdrant 容器**：单实例 ~512MB 内存，1 个 docker 服务
- **bge-reranker 容器**：CPU 推理 ~1G 内存（与 bge-embedding 同档）
- **Python 依赖**：移除 `chromadb`，添加 `qdrant-client>=1.12.0`

### 工程影响
- `infrastructure/integrations/retrieval/` adapter 需实现 Qdrant 客户端（port 接口由 domain 定义）
- knowledge_materials 索引构建时需调用 TEI 同时拿 dense + sparse，写入 Qdrant payload
- 启动时若 Qdrant 集合不存在，自动创建（带 dense + sparse + payload schema）
- LEGAL-120 首次发布前需重建知识库索引

### 评测影响
- LEGAL-110 验收集 S1-S8 必须在混合检索下全部通过
- 新增 LEGAL-120 评测：法条编号召回准确率 ≥ 95%、专有名词召回率 ≥ 85%、跨分类串扰率 ≤ 2%

## 关键实现约束

- 检索调用必须经 `domain/ports/retrieval_port.py` 抽象，application 层不直接调 Qdrant 客户端
- 配置项全部走 Settings，禁硬编码；权重和 top-N 可在线评测后调整
- Qdrant payload schema 固定：`{category_code, material_id, source_name, source_section, status, version, chunk_index}`
- citation_check 节点的字符级匹配必须用 snippet 原文，不接受 LLM 自由改写
- bge-embedding 与 bge-reranker 是运行依赖；健康检查纳入 `/health/ready`
- 检索调用不得持有数据库事务（database-standards.md §5）

## 回滚

按降级严重程度递增：

1. **reranker 故障**：`rag_reranker_enabled=false`，直接用 Qdrant 融合 top-5
2. **sparse 服务异常**：`rag_sparse_weight=0`，降级为纯 dense + 元数据过滤
3. **Qdrant 不可用**：返回 `RETRIEVAL_FAILED` (503)，前端降级为"无知识库"模式（仅输出免责声明）
4. **整体方案不达验收**：切回 ADR-0008 原方案（Chroma + dense），但需在 LEGAL-120 评测报告中明确记录差距

## 待用户确认

- 是否接受新增 Qdrant + bge-reranker 两个容器（总 ~1.5G 内存）的资源开销
- 是否需要预置的初始法律分类词典（用于 classification 节点）

## 关联文档

- `agents/legal-consulting-agent/docs/detailed-design.md` §5 retrieval 节点 I/O（同步更新）
- `agent-suite-ops/docs/runbooks/deployment-design.md`（服务清单 + 卷 + 资源）
- `agent-suite-ops/docker-compose.yml`（新增服务）
