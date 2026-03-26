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

用户应该能在自己偏好的领域里获取新闻，包括但不限于主题和主题下的关键词。对用户来说，确定主题很容易，但是确定关键词可能非常困难。因此该产品能够根据用户反馈自动更新关键词，在使用/news搜索和rss推送时获得更精确的推送。


### 做了哪些取舍及原因

没有做前端ui，而是使用了telegram的bot。
原因：没有把握在两小时内做出一个好用美观的前端洁面；bot更符合用户日常需求，开箱即用，且回复中自带新闻源url，用户如果有兴趣可以自己打开浏览器看（笑

没有实际上做出推荐排序，是否推荐以及推荐顺序都由gpt5.4 mini完成。
原因：做不完，而且作为demo比较快和稳定

没有让用户自定义新闻源
原因：做不完，而且不同新闻源的返回结构不一样，很难在两小时内完成，使用web-search又不够精确

没有严格过滤RSS的推送，也没有做轮询
原因：严格过滤很难使用大模型完成，轮询的功能在demo中不好演示，用curl手动触发更方便

### 如果还有两天会做什么

要看接下来两天的目标是什么，首先清理GitHub的多余文件，并整理项目结构。其次：

1. 如果是发布给别人试用：修复所有安全性问题，包括但不限于隔离大模型，确保隐藏API keys，增加webhook的secret；还有有时间的话接入数据库
2. 如果是demo给别人看：修改telegram的返回格式，让信息更加用户友好；增加更严格的新闻过滤，比如embeddings做similarity的score，避免与用户偏好不匹配和重复推荐
3. 如果是自己用：增加自定义新闻源的功能，增加关键词黑名单机制，增加定时推送，增加热点推送的时段和频率限制，完善新闻筛选功能
4. 如果是拉投资：做一个好看的官网界面。