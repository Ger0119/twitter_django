from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from .forms import TweetForm
from datetime import datetime, timedelta
import tweepy
import pandas as pd
import json

# Create your views here.

TWEEPY_AUTH = tweepy.Client(settings.BEARER_TOKEN, settings.CONSUMER_KEY, settings.CONSUMER_SECRET, settings.ACCESS_KEY,
                            settings.ACCESS_KEY_SECRET, wait_on_rate_limit=True)


class IndexView(View):
    def get(self, request, *args, **kwargs):
        form = TweetForm(request.POST or None,
                         initial={
                             'items_count': 100,
                             'like_count': 1,
                             'search_start': datetime.today() - timedelta(days=7),
                             'search_end': datetime.today(),
                         }
                         )

        return render(request, 'index.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        form = TweetForm(request.POST or None)

        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            items_count = form.cleaned_data['items_count']
            like_count = form.cleaned_data['like_count']
            search_start = form.cleaned_data['search_start']
            search_end = form.cleaned_data['search_end']

            data = get_search_tweet(keyword, items_count, like_count, search_start, search_end)
            tw_data, summary = make_df(data)
            print(summary)
            return render(request, 'tweet.html', {
                'keyword': keyword,
                'tweet_data': tw_data,
                'length': len(tw_data),
                'graph_data': summary,
            })
        else:
            return redirect('index')


def make_df(data):
    df = pd.DataFrame(data).T
    df.columns = 'Name ID Like Retweet Created_At Img URL Text'.split()

    df2 = df.copy()
    df2['Count'] = 1
    df2 = df2[['Created_At', 'Like', 'Retweet', 'Count']].astype({'Like': 'int32', 'Retweet': 'int32'}).groupby(
        'Created_At').sum()

    return df, df2.to_json(orient='index')


def get_search_tweet(keyword, items_count, like_count, search_start, search_end, next_token=None):
    Name = []
    ID = []
    Like = []
    Retweet = []
    Created_At = []
    Img = []
    URL = []
    Text = []
    while True:
        res = TWEEPY_AUTH.search_recent_tweets(
            query=keyword + ' -is:retweet',
            start_time=f'{search_start}T20:00:00Z',
            end_time=f'{search_end}T00:00:00Z',
            expansions=['author_id'],
            tweet_fields=['created_at', 'lang', 'public_metrics'],
            user_fields=['profile_image_url'],
            max_results=items_count,
            next_token=next_token,
        )

        for x, y in zip(res.includes['users'], res.data):
            if y.public_metrics['like_count'] < like_count:
                continue
            ID.append(x.data['id'])
            Name.append(x.data['username'])
            Like.append(y.public_metrics['like_count'])
            Retweet.append(y.public_metrics['retweet_count'])
            Img.append(x['profile_image_url'])
            Created_At.append(y.created_at.strftime('%Y-%m-%d'))
            URL.append("https://twitter.com/" + x.username + "/status/" + str(y.id))
            Text.append(y.text)

        if len(ID) >= items_count:
            break
        if 'next_token' not in res.meta:
            break
        next_token = res.meta['next_token']

    return Name, ID, Like, Retweet, Created_At, Img, URL, Text
