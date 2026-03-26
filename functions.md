# Personalized News Agent 功能架构

本文档基于 [codex/plan.md](/Users/return0/Study/Learning/Programming/news-ai-recommendation/codex/plan.md) 设计项目架构，并将 MVP 拆解为可独立实现的功能模块。

## 1. 项目目标

项目目标是构建一个基于 FastAPI、OpenAI 和 Telegram Bot 的个性化新闻 Agent。

它不是传统新闻聚合器，而是一个会基于用户目标、关注点和当前情境，替用户判断“今天哪些新闻值得看、为什么值得看”的系统。

## 2. 推荐项目结构

```text
news-ai-recommendation/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   ├── health.py
│   │   └── telegram.py
│   ├── bot/
│   │   ├── handlers.py
│   │   ├── commands.py
│   │   └── formatter.py
│   ├── services/
│   │   ├── personalization_service.py
│   │   ├── llm_service.py
│   │   └── user_settings_service.py
│   ├── providers/
│   │   ├── tavily_provider.py
│   │   ├── rss_provider.py
│   │   ├── mock_news_provider.py
│   │   └── telegram_provider.py
│   ├── models/
│   │   ├── news.py
│   │   ├── user.py
│   │   ├── feedback.py
│   │   └── telegram.py
│   └── prompts/
│       ├── rank_news.txt
│       └── summarize_news.txt
├── data/
│   └── rss/
│       └── yc-example.xml
├── tests/
│   ├── test_rss_provider.py
│   ├── test_personalization_service.py
│   └── test_formatter.py
├── functions.md
├── README.md
└── .env
```

## 3. 系统分层

### 3.1 接入层

职责：
- 提供 FastAPI HTTP 服务入口
- 接收 Telegram webhook 或调试模式下的消息输入
- 暴露健康检查接口，便于本地联调

对应模块：
- `app/main.py`
- `app/routes/health.py`
- `app/routes/telegram.py`

### 3.2 Bot 交互层

职责：
- 解析 Telegram 用户消息
- 识别 `/start`、`/help`、`/news`、`/hotnews`、`/topics`、`/keywords`、`/settings` 等命令
- 组织对话状态，处理用户显式设置的主题和关键词偏好
- 接收用户对已推送新闻的反馈动作
- 将推荐结果格式化为适合手机阅读的消息文本

对应模块：
- `app/bot/commands.py`
- `app/bot/handlers.py`
- `app/bot/formatter.py`

### 3.3 业务编排层

职责：
- 协调整个“用户输入/用户设置 -> 新闻读取 -> 个性化筛选 -> 推荐输出”的主流程
- 将底层数据读取、LLM 调用和业务规则组合成一个完整闭环

对应模块：
- `app/services/personalization_service.py`

### 3.4 领域服务层

职责：
- 处理用户设置、新闻反馈、个性化判断、推荐解释生成等领域逻辑
- 保持每个服务单一职责，减少耦合

对应模块：
- `app/services/personalization_service.py`
- `app/services/llm_service.py`
- `app/services/user_settings_service.py`

### 3.5 数据提供层

职责：
- 使用 Tavily 根据用户设置的 `topics` 和 `keywords` 搜索新闻
- 从 `data/rss` 中读取热点 RSS 文件
- 将搜索结果或原始 XML 数据转换为统一新闻结构
- `data/rss` 用于 `/hotnews` 热点推送和本地样例演示

对应模块：
- `app/providers/tavily_provider.py`
- `app/providers/mock_news_provider.py`
- `app/providers/rss_provider.py`

### 3.6 模型层

职责：
- 定义统一的数据结构，确保模块之间输入输出清晰稳定

对应模块：
- `app/models/news.py`
- `app/models/user.py`
- `app/models/feedback.py`
- `app/models/telegram.py`

## 4. 功能模块拆解

### 模块 A：应用启动与配置

目标：
- 启动 FastAPI 服务
- 加载 `.env` 中的 OpenAI 和 Telegram 配置
- 初始化核心依赖

建议职责：
- 管理环境变量
- 初始化 OpenAI client
- 初始化 Bot 配置
- 注册路由

输入：
- `.env` 配置

输出：
- 可运行的应用实例

建议文件：
- `app/main.py`
- `app/config.py`

### 模块 B：Telegram 消息接入

目标：
- 接收 Telegram 消息并转成内部请求对象

建议职责：
- 校验 webhook 请求
- 解析 message、chat id、user id、command、text
- 将消息传给 Bot handler

输入：
- Telegram update payload

输出：
- 结构化的 Bot 请求对象

建议文件：
- `app/routes/telegram.py`
- `app/models/telegram.py`

### 模块 C：Bot 命令与对话处理

目标：
- 管理最小可行交互流程

建议职责：
- `/start`：介绍产品和使用方式
- `/help`：返回命令说明
- `/news` 或自然语言输入：基于用户设置的 `topics` 和 `keywords` 调用 Tavily 搜索并触发个性化推荐
- `/hotnews`：读取 `data/rss` 中的热点内容并触发热点推送
- `/topics`：设置用户长期关注主题，例如 `AI, startups, devtools`
- `/keywords`：设置用户长期关注关键词，例如 `OpenAI, YC, GPT-5`
- `/settings`：查看当前保存的 `topics` 和 `keywords`
- 支持查看、更新和清空当前用户设置

输入：
- 用户文本消息

输出：
- 内部推荐请求

建议文件：
- `app/bot/commands.py`
- `app/bot/handlers.py`

### 模块 D：RSS Mock Data 读取

目标：
- 使用 `data/rss` 下的 XML 文件作为热点推送模块的数据源

建议职责：
- 读取本地 XML 文件
- 解析 RSS item
- 提取标题、摘要、链接、发布时间、来源
- 输出统一 `NewsItem` 列表
- 为 `/hotnews` 提供稳定的热点新闻输入

输入：
- `data/rss/*.xml`

输出：
- 标准化新闻对象列表

建议文件：
- `app/providers/rss_provider.py`
- `app/providers/mock_news_provider.py`

### 模块 E：Tavily 新闻搜索

目标：
- 使用 Tavily 根据用户偏好的 `topics` 和 `keywords` 搜索新闻结果，作为 `/news` 的主数据来源

建议职责：
- 将 `topics`、`keywords` 和用户当前请求拼装为搜索 query
- 调用 Tavily 搜索相关新闻
- 提取标题、摘要、链接、来源、发布时间等字段
- 将 Tavily 返回结果转换为统一 `NewsItem` 列表

输入：
- `User`
- 当前请求文本

输出：
- 标准化新闻对象列表

建议文件：
- `app/providers/tavily_provider.py`

### 模块 F：用户设置管理

目标：
- 支持用户显式设置 `topics` 和 `keywords`

建议职责：
- 解析并保存用户设置的主题列表和关键词列表
- 提供读取、查看、更新、重置当前设置的接口
- 按 `chat_id` 或 `user_id` 管理内存中的用户设置
- 将用户设置转换为个性化排序可直接使用的结构化输入

输入：
- Telegram 命令或文本中的设置内容

输出：
- `User`

建议文件：
- `app/services/user_settings_service.py`
- `app/models/user.py`

### 模块 G：LLM 调用层

目标：
- 封装 OpenAI 调用，避免业务层直接依赖 SDK 细节

建议职责：
- 统一管理模型名、温度、超时、重试
- 支持结构化输出
- 提供画像提取、新闻排序、推荐理由生成等能力

输入：
- prompt + 结构化上下文

输出：
- 模型返回结果

建议文件：
- `app/services/llm_service.py`

### 模块 H：个性化排序与推荐生成

目标：
- 将“个性化”落地为可解释的推荐结果

建议职责：
- 根据用户设置的 `topics`、`keywords` 和当前请求评估每条新闻的相关性
- 优先匹配用户显式设置的主题和关键词，再结合即时请求做排序
- 输出推荐分数、推荐理由、阅读价值
- 控制推荐数量，优先返回 3 到 5 条
- 支持“为什么推荐给你”解释

输入：
- `User`
- `NewsItem[]`
- 当前请求文本

输出：
- 格式化前的新闻结果列表

建议文件：
- `app/services/personalization_service.py`
- `app/prompts/rank_news.txt`
- `app/prompts/summarize_news.txt`

### 模块 I：Telegram 消息格式化

目标：
- 把推荐结果转换成简洁、好读、适合手机端的消息

建议职责：
- 控制消息长度
- 组织标题、推荐理由、摘要、链接
- 支持 Markdown 或 Telegram 支持的格式
- 为反馈按钮或后续命令预留格式

输入：
- 新闻结果列表

输出：
- Telegram 文本消息

建议文件：
- `app/bot/formatter.py`

### 模块 J：用户反馈记录

目标：
- 记录用户对已推送新闻的反馈，用于后续偏好优化和推荐调优

建议职责：
- 记录用户针对某条新闻的反馈动作，例如喜欢、不感兴趣、想看更多
- 保存反馈对应的用户、新闻、命令来源和时间戳
- 为后续个性化优化提供结构化输入
- MVP 阶段允许只定义模型并进行内存记录，不要求完整学习闭环

建议字段：
- `user_id`
- `chat_id`
- `news_id` 或 `news_url`
- `feedback_type`
- `source_command`
- `created_at`

反馈类型建议：
- `liked`
- `disliked`
- `more_like_this`

建议文件：
- `app/models/feedback.py`

### 模块 K：Demo 与稳定性支持

目标：
- 确保演示链路稳定、可重复

建议职责：
- 固定一组 RSS 样本
- 固定一个演示 persona
- 提供本地快速验证方式
- 在 LLM 不稳定时保留兜底逻辑

建议文件：
- `README.md`
- `tests/`

### 模块 L：热点推送

目标：
- 使用 `data/rss` 中的热点新闻样本，为 `/hotnews` 提供固定、稳定的热点推送能力

建议职责：
- 读取并组织本地热点 RSS 数据
- 输出通用热点列表，必要时可再结合用户偏好做轻量排序
- 为 Demo 和本地调试提供稳定可复现的数据

输入：
- `data/rss/*.xml`
- 可选的 `User`

输出：
- 新闻结果列表

建议文件：
- `app/providers/rss_provider.py`
- `app/providers/mock_news_provider.py`

## 5.1 Telegram 命令协议

### `/topics`

用途：
- 设置用户长期关注主题

建议格式：
- `/topics AI, startups, devtools`

行为规则：
- 使用逗号分隔多个 topic
- 自动去掉首尾空格
- 自动去重
- 若用户未提供内容，返回示例用法

成功返回示例：
```text
Topics updated.
Current topics:
- AI
- startups
- devtools
```

### `/keywords`

用途：
- 设置用户长期关注关键词

建议格式：
- `/keywords OpenAI, YC, GPT-5`

行为规则：
- 使用逗号分隔多个 keyword
- 自动去掉首尾空格
- 自动去重
- 若用户未提供内容，返回示例用法

成功返回示例：
```text
Keywords updated.
Current keywords:
- OpenAI
- YC
- GPT-5
```

### `/news`

用途：
- 使用 Tavily 根据用户当前保存的 `topics`、`keywords` 和本次请求搜索新闻，并返回个性化推荐

建议格式：
- `/news`
- `/news today`
- `/news AI agent startup funding`

行为规则：
- 若用户未附加额外文本，则使用当前保存的 `topics` 和 `keywords` 作为默认搜索条件
- 若用户附加额外文本，则将其与保存的偏好一起拼装为 Tavily 查询
- 优先返回与用户偏好最相关的 3 到 5 条结果
- 若用户尚未设置偏好，也允许直接用命令文本发起搜索

搜索查询示意：
```text
topics: AI, startups
keywords: OpenAI, YC
request: today

final query:
AI startups OpenAI YC today latest news
```

成功返回示例：
```text
Top picks for you today

1. OpenAI launches new developer feature
Why it matters: matches your AI and OpenAI focus, and may affect builder workflows.

2. YC-backed startup raises new round
Why it matters: relevant to your startup and YC interests.
```

### `/hotnews`

用途：
- 使用 `data/rss` 中的热点样本触发热点推送

建议格式：
- `/hotnews`

行为规则：
- 从 `data/rss` 读取热点 RSS 数据
- 返回当前热点新闻列表
- 可选地结合用户设置的 `topics` 和 `keywords` 做轻量排序或解释增强
- 优先保证结果稳定，适合本地调试和 Demo

成功返回示例：
```text
Hot news today

1. YC startup launches new AI tool
Why it matters: this is one of the most notable items in the current hot feed.

2. Major model release draws developer attention
Why it matters: broadly relevant and highly discussed in the tech news cycle.
```

### `/settings`

用途：
- 查看用户当前保存的设置

建议格式：
- `/settings`

返回内容：
- 当前保存的 `topics`
- 当前保存的 `keywords`
- 若为空，明确提示用户尚未设置

成功返回示例：
```text
Your current settings

Topics:
- AI
- startups

Keywords:
- OpenAI
- YC
```

空设置返回示例：
```text
You have no saved settings yet.
Use /topics and /keywords to add your preferences.
```

## 5.2 统一返回格式

`/news` 和 `/hotnews` 建议使用同一套消息结构，减少 Telegram 端格式分支。

建议结构：
```text
{header}

{summary}

1. {title}
Why it matters: {reason}
Source: {source}
Link: {url}

2. {title}
Why it matters: {reason}
Source: {source}
Link: {url}
```

字段说明：
- `header`：命令类型对应的标题，例如 `Top picks for you today` 或 `Hot news today`
- `summary`：1 到 2 句整体总结，说明这批新闻为什么值得看
- `title`：新闻标题
- `reason`：个性化推荐理由或热点价值说明
- `source`：新闻来源
- `url`：原始链接

格式规则：
- 默认返回 3 到 5 条
- 单条推荐保持 4 行以内，避免 Telegram 消息过长
- `Why it matters` 必须保留，作为 Agent 判断的核心展示位
- 若链接过长，允许只保留标题超链接或截断显示
- 若结果为空，返回明确提示和下一步建议

`/news` 标题建议：
- `Top picks for you today`
- `News matched to your interests`

`/hotnews` 标题建议：
- `Hot news today`
- `Trending now`

空结果返回示例：
```text
No strong matches found right now.
Try broadening your topics or keywords, or use /hotnews to see the current hot feed.
```

## 6. 核心流程设计

### 主流程

1. 用户可先通过 `/topics` 设置关注主题，通过 `/keywords` 设置关键词
2. 用户在 Telegram 中发送一句请求，例如“给我今天最值得看的 AI 创业新闻”
3. Telegram webhook 将消息发送给 FastAPI
4. Bot handler 识别请求类型并提取原始文本或设置命令
5. `user_settings_service` 读取当前用户的 `topics` 和 `keywords`
6. 若命令为 `/news`，`tavily_provider` 根据用户设置和当前请求搜索相关新闻
7. 若命令为 `/hotnews`，`rss_provider` / `mock_news_provider` 从 `data/rss` 读取热点新闻
8. `personalization_service` 基于用户设置和当前请求筛选、排序新闻，或对热点结果做轻量解释增强
9. `llm_service` 生成简洁结论和推荐理由
10. `formatter` 将推荐结果格式化为 Telegram 消息
11. 用户可对推送结果进行反馈，系统将反馈记录到 `Feedback`
12. Bot 将消息返回给用户

## 7. MVP 必做功能

- FastAPI 服务可启动
- Telegram Bot 可收到消息并返回内容
- 支持用户设置和更新 `topics`
- 支持用户设置和更新 `keywords`
- 支持用户查看当前设置的 `topics` 和 `keywords`
- `/news` 能使用 Tavily 根据用户偏好搜索新闻
- `/hotnews` 能使用 `data/rss` 提供热点推送
- 能返回 3 到 5 条个性化新闻推荐
- 每条推荐都附带“推荐原因”
- 有模型可记录用户对推送新闻的反馈
- README 中说明个性化定义、取舍和运行方式

## 8. 可以延后的功能

- 多用户状态管理
- 持久化用户设置
- 多新闻源聚合
- 高级反馈学习
- 多轮对话记忆
- 后台任务定时抓取
- Web 管理面板

## 9. 模块实现优先级

### P0

- `app/main.py`
- `app/config.py`
- `app/routes/telegram.py`
- `app/providers/tavily_provider.py`
- `app/providers/rss_provider.py`
- `app/providers/mock_news_provider.py`
- `app/services/user_settings_service.py`
- `app/services/llm_service.py`
- `app/services/personalization_service.py`
- `app/bot/formatter.py`

### P1

- `app/bot/commands.py`
- `app/bot/handlers.py`
- `tests/test_rss_provider.py`
- `tests/test_formatter.py`

### P2

- 更丰富的 prompt 拆分
- 反馈信号处理
- 真实 RSS/API 扩展

## 10. 建议先实现的最小闭环

建议按照下面顺序落地：

1. FastAPI 服务启动 + 健康检查
2. 实现 `/topics`、`/keywords` 和 `/settings`
3. 接入 Tavily，并根据用户设置拼装搜索 query
4. 实现 `/hotnews`，读取 `data/rss/yc-example.xml` 输出热点新闻
5. 编写一个结合用户设置的个性化推荐函数
6. 用 OpenAI 生成推荐理由
7. 将推荐结果格式化成 Telegram 文本
8. 接入 Telegram webhook 或轮询调试

这样可以最快完成一个能演示的主链路，同时保留后续扩展空间。
