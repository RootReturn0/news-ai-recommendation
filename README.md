# news-ai-recommendation

FastAPI + Telegram Bot + OpenAI/Tavily powered personalized news agent.

## 项目概览

这是一个以 Telegram Bot 为交互入口的个性化新闻推荐项目。

核心能力：
- 用户可以通过 `/topics` 和 `/keywords` 保存长期偏好
- `/news` 会基于用户偏好调用 Tavily 搜索个性化新闻
- `/hotnews` 会读取热点 RSS 新闻并逐条返回
- 用户可以通过回复 `/like`、`/dislike`，或直接使用 `👍`、`👎` 反馈新闻
- 系统会用 LLM 从用户反馈过的新闻中提取关键词，并自动更新用户的 `keywords`
- 支持根据用户 `topics` 和 `keywords` 从 RSS mock data 中筛选新增新闻并触发推送

## 运行方式

1. 创建并激活虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置 `.env`

至少需要：
- `TG_BOT_TOKEN`
- `TG_BASE_URL` 或你自己的 webhook 对外地址

按功能可选：
- `TAVILY_API_KEY`
- `OPENAI_API_KEY` 或兼容 OpenAI 的网关配置
- `RSS_FEED_URL`

4. 启动服务

```bash
uvicorn app.main:app --reload
```

## 接口

- `GET /health`
  - 健康检查
- `POST /telegram/webhook`
  - Telegram webhook 入口
- `POST /telegram/debug`
  - 本地调试 Telegram payload
- `POST /push/check`
  - 手动触发一次 RSS 匹配推送检查

## Telegram 使用说明

基础命令：
- `/start`
- `/help`
- `/topics AI, startups`
- `/keywords OpenAI, YC`
- `/settings`
- `/news today`
- `/hotnews`

反馈方式：
- 回复一条已发送的新闻消息后发送 `/like`
- 回复一条已发送的新闻消息后发送 `/dislike`
- 也可以直接对 bot 发出的新闻消息使用 `👍` 或 `👎` reaction

## 当前实现说明

- `/news`
  - 使用 Tavily 搜索，并按用户 `topics`、`keywords`、当前请求做个性化排序
  - 新闻按条逐条返回

- `/hotnews`
  - 使用 RSS 数据源读取热点新闻
  - 结果按条逐条返回

- 关键词更新
  - 用户点赞一条新闻时，系统会调用 LLM 从新闻文本中提取高信号关键词，追加到用户 `keywords`
  - 用户点踩一条新闻时，系统会使用同样的方式提取关键词，并从用户 `keywords` 中删除

- RSS 推送
  - 当前提供手动触发的 RSS 推送检查
  - 使用 `data/rss/*.xml` 作为 mock data
  - 只有新闻文本中命中用户 `topics` 或 `keywords`，并且该新闻是“未推送过的新新闻”时，才会推送

## 数据存储

- `data/users/`
  - 保存用户 JSON 数据，包括 `topics`、`keywords`、已推送新闻 ID 等
- `data/sent_messages/`
  - 保存 bot 发出的新闻文本，供后续 reaction 和回复反馈使用
- `data/rss/`
  - RSS mock data，用于本地演示和手动推送检查

## 有用的命令

curl -X POST http://127.0.0.1:8000/push/check


## 简短的说明

### 对"个性化"的定义  

用户应该能在自己偏好的领域里获取新闻，包括但不限于主题和主题下的关键词。对用户来说，确定主题很容易，但是确定关键词可能非常困难。一款好产品应该能够自动学习用户喜好，因此该产品主要特色在于根据用户反馈自动更新关键词，在使用/news搜索和rss推送时获得更精确的推送。


### 做了哪些取舍及原因

1. 没有做前端ui，而是使用了telegram的bot。
原因：没有把握在两小时内做出一个好用美观的前端界面；bot更符合用户日常需求，开箱即用，且回复中带上了新闻源url，用户如果有兴趣可以自己打开浏览器看（笑

2. 没有仔细做prompt engineering
原因：所需消耗的时间不确定，以及该功能与模型本身能力相关性较高

3. 没有实际上做出推荐过滤算法，是否推荐以及推荐顺序都由gpt5.4 mini完成。
原因：做不完。作为demo比较快和稳定

4. 没有让用户自定义新闻源
原因：做不完。不同新闻的RSS源的返回结构不一样，很难在两小时内完成自动适配的功能

5. 没有严格过滤RSS的推送，也没有做轮询
原因：不太严格的条件确保功能在演示的时候能正常推送，同时严格过滤很难使用大模型完成，短时间内做不完，使用关键词文本匹配的话，demo的时候需要对数据源有了解，并多次测试流程，但我没研究过数据源的内容；轮询的功能在demo中不好演示，用curl手动触发更方便

6. 没有做真实的实时热点判断，例如根据ycombinator的排名变化来判断某话题是否正在变得更加热门
原因：做不完

7. 在代码中没有严格限制用户反馈使用的关键词和方式
原因：确保稳定性，有时间限制在，能跑就不要动

8. 没有做出更多的用户反馈，只更新了关键词。实际上还应该记忆和判断新闻源、话题等。
原因：可能写不完，关键词的交互效果最明显。

9. topics和keywords的区别只有是否自动更新，在分析用户偏好上没有做分层判断
原因：写不完，而且作为demo，是否分层判断其实演示过程中看不出来。

10. 没有做边界和意外事件测试，非预先定义的指令输入时，bot可能出现意料之外的反馈
原因：演示过程正常就可以

11. git commit很随便
原因：快

12. 没有用claude code
原因：不能保证两小时内不出意外，比如被封号

13. 代码开发几乎全部交给codex，边开发边修改
原因：快

14. 没有一开始就使用多个codex agents协作
原因：需要确保开发过程的稳定性，当项目基本稳定后，再多开来加功能；开发时需要思考，例如在时间不够的情况下如何突出特色，实际上最后做出来的东西和计划不一样

15. 没有仔细review代码，不确定代码逻辑是否和预想的完全一致
原因：codex写的一般不太差，以及有时间限制在，能跑就不要动

16. 没有一开始就配完.env
原因：有录屏大概率会暴露key，以及很有可能需要中途更换技术方案

17. 还有一些时间但是没有接着完善
原因：剩下的功能和问题都很难保证在十几分钟内解决，如果只是赌codex能不能一次写成，我觉得不是很有必要。而且事先做过一些准备，比如下载了飞书文档，连了一次telegram的bot（没写过，担心需要配很久，还有网络问题需要测一下），要模拟从收到文档就计时开始的话，这个时长刚好。

### 如果还有两天会做什么

要看接下来两天的目标是什么，首先清理GitHub的多余文件，并整理项目结构。其次：

1. 如果是发布给别人试用：修复所有安全性问题，包括但不限于隔离大模型，确保隐藏API keys，增加webhook的secret；还有有时间的话接入数据库，完善tavily search的参数传输，缩小搜索范围
2. 如果是demo给别人看：修改telegram的返回格式，让信息更加用户友好；增加更严格的新闻过滤，比如embeddings做similarity的score，避免与用户偏好不匹配和重复推荐；完善tavily search的参数传输，缩小搜索范围
3. 如果是自己用：增加自定义新闻源的功能，增加关键词黑名单机制，增加定时推送，增加热点推送的时段和频率限制，完善新闻筛选功能
4. 如果需要宣传项目：做一个好看的官网界面。

当以上目标全部完成后，如果还有时间可以做新闻的topic聚类，再分层匹配关键词。
