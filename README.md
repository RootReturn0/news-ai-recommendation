# news-ai-recommendation

FastAPI + Telegram Bot + OpenAI/Tavily powered personalized news agent.

## Run

1. Create and activate a virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Fill `.env` with the needed values:
- `TG_BOT_TOKEN`
- `TAVILY_API_KEY` for `/news`
- `OPENAI_API_KEY` or your OpenAI-compatible gateway credentials for summary generation

4. Start the app:

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /telegram/webhook`
- `POST /telegram/debug`

## Commands

- `/topics AI, startups`
- `/keywords OpenAI, YC`
- `/settings`
- `/news`
- `/hotnews`

## Notes

- `/news` uses Tavily search when `TAVILY_API_KEY` is configured.
- `/hotnews` reads from `https://news.ycombinator.com/rss` by default.
- You can override the hot feed source with `RSS_FEED_URL` in `.env`.
- If no OpenAI-compatible credentials are configured, the app falls back to rule-based summaries.

## 有用的命令

curl -X POST http://127.0.0.1:8000/push/check


## 简短的说明

### 对"个性化"的定义  

用户应该能在自己偏好的领域里获取新闻，包括但不限于主题和主题下的关键词。对用户来说，确定主题很容易，但是确定关键词可能非常困难。一款好产品应该能够自动学习用户喜好，因此该产品主要特色在于根据用户反馈自动更新关键词，在使用/news搜索和rss推送时获得更精确的推送。


### 做了哪些取舍及原因

没有做前端ui，而是使用了telegram的bot。
原因：没有把握在两小时内做出一个好用美观的前端界面；bot更符合用户日常需求，开箱即用，且回复中带上了新闻源url，用户如果有兴趣可以自己打开浏览器看（笑

没有仔细做prompt engineering
原因：所需消耗的时间不确定，以及该功能与模型本身能力相关性较高

没有实际上做出推荐过滤算法，是否推荐以及推荐顺序都由gpt5.4 mini完成。
原因：做不完。作为demo比较快和稳定

没有让用户自定义新闻源
原因：做不完。不同新闻的RSS源的返回结构不一样，很难在两小时内完成自动适配的功能

没有严格过滤RSS的推送，也没有做轮询
原因：不太严格的条件确保功能在演示的时候能正常推送，同时严格过滤很难使用大模型完成，短时间内做不完，使用关键词文本匹配的话，demo的时候需要对数据源有了解，并多次测试流程，但我没研究过数据源的内容；轮询的功能在demo中不好演示，用curl手动触发更方便

没有做真实的实时热点判断，例如根据ycombinator的排名变化来判断某话题是否正在变得更加热门
原因：做不完

在代码中没有严格限制用户反馈使用的关键词和方式
原因：确保稳定性，有时间限制在，能跑就不要动

没有做出更多的用户反馈，只更新了关键词。实际上还应该记忆和判断新闻源、话题等。
原因：可能写不完，关键词的交互效果最明显。

topics和keywords的区别只有是否自动更新，在分析用户偏好上没有做分层判断
原因：写不完，而且作为demo，是否分层判断其实演示过程中看不出来。

没有做边界和意外事件测试，非预先定义的指令输入时，bot可能出现意料之外的反馈
原因：演示过程正常就可以

git commit很随便
原因：快

没有用claude code
原因：不能保证两小时内不出意外，比如被封号

代码开发几乎全部交给codex，边开发边修改
原因：快

没有一开始就使用多个codex agents协作
原因：需要确保开发过程的稳定性，当项目基本稳定后，再多开来加功能；开发时需要思考，例如在时间不够的情况下如何突出特色，实际上最后做出来的东西和计划不一样

没有仔细review代码，不确定代码逻辑是否和预想的完全一致
原因：codex写的一般不太差，以及有时间限制在，能跑就不要动

没有一开始就配完.env
原因：有录屏大概率会暴露key，以及很有可能需要中途更换技术方案

还有一些时间但是没有接着完善
原因：剩下的功能和问题都很难保证在十几分钟内解决，如果只是赌codex能不能一次写成，我觉得不是很有必要。而且事先做过一些准备，比如下载了飞书文档，连了一次telegram的bot（没写过，担心需要配很久，还有网络问题需要测一下），要模拟从收到文档就计时开始的话，这个时长刚好。

### 如果还有两天会做什么

要看接下来两天的目标是什么，首先清理GitHub的多余文件，并整理项目结构。其次：

1. 如果是发布给别人试用：修复所有安全性问题，包括但不限于隔离大模型，确保隐藏API keys，增加webhook的secret；还有有时间的话接入数据库，完善tavily search的参数传输，缩小搜索范围
2. 如果是demo给别人看：修改telegram的返回格式，让信息更加用户友好；增加更严格的新闻过滤，比如embeddings做similarity的score，避免与用户偏好不匹配和重复推荐；完善tavily search的参数传输，缩小搜索范围
3. 如果是自己用：增加自定义新闻源的功能，增加关键词黑名单机制，增加定时推送，增加热点推送的时段和频率限制，完善新闻筛选功能
4. 如果需要宣传项目：做一个好看的官网界面。

当以上目标全部完成后，如果还有时间可以做新闻的topic聚类，再分层匹配关键词。
