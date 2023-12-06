import asyncio
from twscrape import API, gather
from twscrape.logger import set_log_level

async def main():
    api = API()
    
    q = "anies baswedan since:2023-01-01 until:2023-11-30"
    async for tweet in api.search(q, limit=5000):
        print(tweet.id, tweet.user.username, tweet.rawContent)


if __name__ == "__main__":
    asyncio.run(main())