import csv 
import tweepy
import pandas as pd


class TwitterScrapper:
    def __init__(self, token, secret, api_key, api_secret):
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(token, secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
    def search(self, keyword):
        c, i, u, t = [], [], [], []
        output_filename = open(
            keyword + ".csv", mode="a+", 
            newline="", encoding="utf-8"
        )
        csv_file = csv.writer(output_filename)
        
        for tweet in tweepy.Cursos(
            self.api.search_tweets, 
            q=keyword, count=15, lang="id", 
            start_time="2023-01-01T00:00:00Z", end_time="2023-11-30T23:59:59Z"
            ).items():
            c.append(tweet.created_at)
            i.append(tweet.id)
            u.append(tweet.user.name)
            t.append(tweet.text.encode("utf-8"))
            tweets = [tweet.created_at, tweet.id, tweet.user.name, tweet.text.encode("utf-8")]
            csv_file.writerow(tweets)

        dictTweets = {"waktu": c, "id": i, "username": u, "teks": t}
        df = pd.DataFrame(dictTweets, columns=["waktu", "id", "username", "teks"])


if __name__ == "__main__":
    scrapping = TwitterScrapper(..., ..., ..., ...)
    scrapping.search('...')