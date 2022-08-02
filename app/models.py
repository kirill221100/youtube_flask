

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

db = SQLAlchemy()

videos_dislikes_assotiation = db.Table('videos_dislikes',
                                      db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                                      db.Column("video_id", db.Integer, db.ForeignKey("video.id")))

videos_likes_assotiation = db.Table('videos_likes',
                                      db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                                      db.Column("video_id", db.Integer, db.ForeignKey("video.id")))

user_to_user = db.Table('user_to_user',
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    avatar = db.Column(db.String)
    desc = db.Column(db.Text)
    password_hash = db.Column(db.String)
    disliked = db.relationship("Video", secondary=videos_dislikes_assotiation, back_populates="dislikes")
    liked = db.relationship("Video", secondary=videos_likes_assotiation, back_populates="likes")
    videos = db.relationship('Video', back_populates='user')
    following = db.relationship("User",
                                secondary=user_to_user,
                                primaryjoin=id == user_to_user.c.follower_id,
                                secondaryjoin=id == user_to_user.c.followed_id,
                                backref="followed_by"
                                )
    comments = db.relationship("Comment", back_populates='user')
    ip = db.Column(db.JSON)
    is_banned = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    notific = db.Column(db.Boolean, default=False)


    @property
    def password(self):
        raise Exception('no')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    desc = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    preview = db.Column(db.String)
    views = db.Column(db.Integer, default=0)
    link = db.Column(db.String)
    dislikes = db.relationship("User", secondary=videos_dislikes_assotiation, back_populates="disliked")
    likes = db.relationship("User", secondary=videos_likes_assotiation, back_populates="liked")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='videos')
    comments = db.relationship("Comment", back_populates='video')
    key_words = db.Column(db.String)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='comments')
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    video = db.relationship('Video', back_populates='comments')

class Banned_ips(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ips = db.Column(db.JSON, nullable=False)
