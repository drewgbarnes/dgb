"""
TODO:
    get this running on pi even when I logout of SSH
    get this to email me when it fails to run
    get sophisticated with the replies to ensure we follow contest rules
    make sure I do not comment on expired giveaways
    print oldest and newest post dates
"""

import logging
import os
import praw
import random
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("reddit.log")
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize PRAW with your Reddit credentials
reddit = praw.Reddit(
    client_id="",
    client_secret="",
    password=os.environ["REDDIT_PASSWORD"],
    user_agent="macOS:dnd-app:v1.0 (by /u/mehabahaha)",
    username="mehabahaha",
)
logger.info("Initializing reddit API client")

logger.info("Initializing SQLAlchemy")
engine = create_engine("sqlite:///reddit_posts.db")
Base = declarative_base()


class Post(Base):
    __tablename__ = "post"
    id: str = Column(String, primary_key=True)
    reddit_id: str = Column(String)
    title: str = Column(String)
    url: str = Column(String)
    date_posted: str = Column(String)
    my_reply_id: str = Column(String)


# Create all tables in the database
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# eventually look for flair posts with `giveaway`
# look for posts with `giveaway` in the title

# Choose the subreddit you're interested in
subreddit_name = "DnD"  # Replace with the name of the subreddit you're interested in

# Get the subreddit object
subreddit = reddit.subreddit(subreddit_name)

# monitor the subreddit for new posts

# a list of 10 potential replies that can be chosen at random which express gratitude for running the giveaway
potential_replies = [
    "Thank you for doing this",
    "Good luck to everyone!",
    "May the odds be ever in your favor",
    "Thanks for the giveaway!",
    "Thank you for your generosity!",
    "I hope I win",
    "I would love this for my campaign!",
    "thanks",
    "Good luck everyone!",
    "comment",
]

API_WRITES_ENABLED = True


def reply(submission):
    if API_WRITES_ENABLED:
        choice = random.choice(potential_replies)
        return submission.reply(choice)


def mark_post_as_replied(submission, reply_id):
    post = session.query(Post).filter_by(id=submission.id).first()
    if not post:
        post = Post(
            id=submission.id,
            reddit_id=submission.id,
            title=submission.title,
            url=submission.permalink,
            date_posted=submission.created_utc,
            my_reply_id=reply_id or "",
        )
        session.add(post)
        session.commit()


def get_already_replied_id(submission):
    post = session.query(Post).filter_by(id=submission.id).first()
    if post:
        logger.info("Already replied via database")
        return post.my_reply_id

    # also check if my account has already replied to the post
    submission.comments.replace_more(limit=None)
    for comment in submission.comments:
        # logger.info(comment.author.name)
        if comment.author.name == "mehabahaha":
            logger.info("Already replied via comment")
            return comment.id
    return None


def run():
    num_posts = 0
    for submission in subreddit.stream.submissions():
        num_posts += 1
        logger.info(f"Processing post {num_posts}")
        logger.info(f"Title: {submission.title}")
        if "giveaway" in submission.title.lower():
            logger.info("title contains giveaway")
            logger.info(f"permalink: https://www.reddit.com{submission.permalink}")
            already_replied_id = get_already_replied_id(submission)
            if not already_replied_id:
                already_replied_id = reply(submission).id
            mark_post_as_replied(submission, already_replied_id)
        elif (
            submission.link_flair_text
            and "giveaway" in submission.link_flair_text.lower()
        ):
            logger.info("tagged with giveaway")
            logger.info(f"permalink: https://www.reddit.com{submission.permalink}")
            already_replied_id = get_already_replied_id(submission)
            if not already_replied_id:
                already_replied_id = reply(submission).id
            mark_post_as_replied(submission, already_replied_id)
        logger.info("-" * 80)


run()
