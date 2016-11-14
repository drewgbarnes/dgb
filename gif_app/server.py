'''
FRONTEND TODO
handle imgur images that no longer exist
handle imgur galleries
make it prettier
'''

from datetime import datetime
import random, math

from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient, errors

app = Flask(__name__)

client = MongoClient()
db = client['test']
collection = db['giffit']


@app.route('/')
def show_all():
    total = collection.count()
    r = int(math.floor(random.random() * total))
    posts = collection.find().limit(9).skip(r)

    p = build_posts(posts)

    return render_template('list.html', posts=p)

@app.route('/search')
def show_search():
    query = request.args.get('query', '').split()
    query = {'kw': {'$in': query}}
    posts = collection.find(query).limit(12)
    p = build_posts(posts)

    return render_template('list.html', posts=p)


def build_posts(posts):
    p = []
    for post in posts:
        try:
            if str(post['url']).index('.gifv') > 0:
                post['url'] = str(post['url'])[:-1]
                post['webm'] = str(post['url'])[:-3] + 'webm'
        except:
            pass
        try:
            if str(post['url']).index('gallery') > 0 or str(post['url']).index('/a/') > 0:
                pass
        except:
            p.append(post)
    return p

if __name__ == '__main__':
    app.debug = True
    app.run()
