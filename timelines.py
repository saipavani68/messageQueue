import flask
from flask import Flask,url_for,jsonify,g,request
from flask_json_multidict import get_json_multidict
from datetime import datetime
from redis import Redis
from rq import Queue
import sqlite3
import logging

app=Flask('timelines')
app.config.from_envvar('APP_CONFIG')

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

@app.cli.command('init')
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = make_dicts
    return db


#Retrieve the 25 most recent tweets of the user

@app.route('/getUserTimeline',methods=['GET'])
def getUserTimeline():
    query_parameters=request.args
    username=query_parameters.get('username')
    
    #Returns 400 error when username is not provided.
    if username == '' or username == None:
        return jsonify({"statusCode": 400, "error": "Bad Request", "message": "Invalid parameter" })
    else:
        getUserTimeline=query_db('SELECT * FROM Tweets WHERE username=? ORDER BY timestamp DESC LIMIT 25',[username])
        return jsonify(getUserTimeline)


#Retrieve the 25 most recent tweets from all users
 
@app.route('/getPublicTimeline',methods=['GET'])
def getPublicTimeline():
    
    getPublicTimeline=query_db('SELECT * FROM Tweets ORDER BY timestamp DESC LIMIT 25')

    return jsonify(getPublicTimeline)


#Returns recent(limited to 25) tweets from all users that this user follows.

@app.route('/getHomeTimeline',methods=['GET'])
def getHomeTimeline():
    db=get_db()
    query_parameters=request.args
    username=query_parameters.get('username')
    
    #Returns 400 error when username is not provided.
    if username == '' or username == None:
        return jsonify({"statusCode": 400, "error": "Bad Request", "message": "Invalid parameter" })
    else:
        getHomeTimeline=query_db('SELECT * from Tweets WHERE username IN (SELECT usernameToFollow FROM user_following WHERE username=?) ORDER BY timestamp DESC LIMIT 25',[username])
        return jsonify(getHomeTimeline)
  
@app.route('/trending',methods=['GET'])
def hashtagAnalysis():
    with app.app_context():
        hashtag_list = []
        tweets= query_db('SELECT * FROM Tweets ORDER BY timestamp DESC')
        for tweet in tweets:
            for tweet in tweet["text"].split():
                if tweet[0] == '#':
                    hashtag_list.append(tweet)
        
        return jsonify(hashtag_list)

@app.route('/status/<job_id>')
def postTweet(username, text):
    with app.app_context():
        timestamp = datetime.utcnow()
        db= get_db()
        result = query_db('SELECT COUNT(*) as count FROM users WHERE username = ?', [username])
        
        #Returns 400 error when username or text is not provided.
        if username == '' or username == None or text == '' or text== None:
            return jsonify({"statusCode": 400, "error": "Bad Request", "message": "Invalid parameter" })
        
        #Only an existing user can post a tweet
        elif result[0].get('count') > 0:
            db.execute('INSERT INTO Tweets (username, text, timestamp) VALUES(?,?, ?)',(username, text, timestamp))
            db.commit()
            return jsonify({"statusCode": 200})
        else:
            return jsonify({"message": "Username doesn't exist. If you are a new user please register, or if you are an existing user please sign in."})
    
@app.route('/postTweet', methods=['POST'])
def callPostTweet():
    redis_conn = Redis()
    q = Queue(connection=redis_conn)
    request.body = request.form
    if request.headers['content-type'] == 'application/json':
        request.body = get_json_multidict(request)
    username =  request.body.get('username')
    text = request.body.get('text')
    postTweets_job = q.enqueue(postTweet, args=(username, text,))
    q_hashtags = Queue('hashtags', connection=redis_conn)
    q_hashtags.enqueue(hashtagAnalysis)
    return jsonify({}), 202, {'Location': url_for('postTweet', job_id=postTweets_job.get_id())}

