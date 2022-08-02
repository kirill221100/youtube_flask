from flask import render_template, flash, request, session, redirect, url_for
from app import app, service
from app.models import db, User, Video, Comment, Banned_ips
from upload import upload_video, pictures

@app.route('/', methods=['POST', 'GET'])
def index():
    videos = db.session.query(Video).order_by(Video.id.desc()).all()
    if request.method == 'POST':
        videos = db.session.query(Video).filter((Video.title.contains(request.form['search_input'])) | (Video.key_words.contains(request.form['search_input']))).order_by(Video.views).all()
    if session.get('nick'):
        user = db.session.query(User).filter(User.nick == session['nick']).first()
        return render_template('index.html', videos=videos, user=user)
    return render_template('index.html', videos=videos)

@app.route('/video/<int:id>', methods=['POST', 'GET'])
def video(id):
    session['url'] = url_for('video', id=id)
    videos = db.session.query(Video).order_by(Video.id.desc()).all()
    video = db.session.query(Video).filter(Video.id == id).first()
    if not session.get('nick'):
        return render_template('video.html', video=video)
    if video.user.nick != session.get('nick'):
        video.views += 1
        db.session.commit()
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    if request.method == 'POST':
        comment = Comment(text=request.form['text'], user=user, video=video)
        if not video.user.notific:
            video.user.notific = True
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('video', id=id))
    return render_template('play-video.html', video=video, user=user, videos=videos)

@app.route('/account', methods=['POST', 'GET'])
def account():
    if not session.get('nick'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    if request.method == 'POST':
        if request.files.get('img'):
            if request.files['img'].content_length > 1:
                flash('Choose image which is not more than 1 megabyte')
                return redirect(url_for('account'))
            user.avatar = pictures(request.files['img'])[1]
        if request.form.get('nick'):
            if db.session.query(User).filter(User.nick == request.form['nick']).first():
                flash('This username is registered')
                return redirect(url_for('account'))
            user.nick = request.form['nick']
            session['nick'] = request.form['nick']
        if request.form.get('desc'):
            user.desc = request.form['desc']
        if request.form.get('password'):
            user.password = request.form['password']
        db.session.commit()
        return redirect(url_for('account'))
    return render_template('account.html', user=user)

@app.route('/notific')
def notific():
    if not session.get('nick'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    if user.notific:
        user.notific = False
    db.session.commit()
    notifics_v = db.session.query(Video).join(User).filter(User.followed_by.contains(user)).limit(25).all()
    notifics_c = db.session.query(Comment).join(Video).filter(Video.user == user).limit(25).all()
    return render_template('notific.html', notifics_v=notifics_v, notifics_c=notifics_c)

@app.route('/channel/<string:nick>', methods=['POST', 'GET'])
def channel(nick):
    session['url'] = url_for('channel', nick=nick)
    channel = db.session.query(User).filter(User.nick == nick).first()
    if not session.get('nick'):
        return render_template('channel.html', channel=channel)
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    return render_template('channel.html', channel=channel, user=user)

# @app.route('/search', methods=['POST', 'GET'])
# def search():
#     if request.method == 'POST':
#         res = db.session.query(Video).filter((Video.title.contains(request.form['text'])) | (Video.key_words.contains(request.form['text']))).order_by(Video.views).all()
#         return render_template('search.html', res=res)
#     return render_template('search.html')

@app.route('/subs')
def subs():
    if not session.get('nick'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    subs = db.session.query(Video).join(User).filter(User.followed_by.contains(user)).all()

    return render_template('subs.html', subs=subs, user=user)

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if not session.get('nick'):
        return redirect(url_for('login'))
    bans = Banned_ips.query.get(1)
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    if bans:
        if request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr) in bans.ips['ips'] or user.is_banned:
            return "Your ip is banned and you can't upload videos"
    if request.method == 'POST':
        if request.files['file'].content_type != 'video/mp4':
            flash('Choose mp4 video')
            return redirect(url_for('upload'))
        if request.files['file'].content_length > 50:
            flash('Choose video which is not more than 50 megabytes')
            return redirect(url_for('upload'))
        desc, preview, key_words = None, None, None
        file_id = upload_video(service=service, file=request.files['file'])
        if request.files.get('img'):
            preview = pictures(request.files['img'])[1]
        if request.form.get('desc'):
            desc = request.form['desc']
        if request.form.get('key_words'):
            key_words = request.form['key_words']
        for i in user.followed_by:
            if not i.notific:
                i.notific = True
        video = Video(link=f"https://drive.google.com/file/d/{file_id}/preview", user=user, title=request.form['title'], preview=preview, desc=desc, key_words=key_words)
        db.session.add(video)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/sub/<string:nick>')
def sub(nick):
    if not session.get('nick'):
        return redirect(url_for('login'))
    user1 = db.session.query(User).filter(User.nick == session['nick']).first()
    user2 = db.session.query(User).filter(User.nick == nick).first()
    user1.following.append(user2)
    db.session.commit()
    if session.get('url'):
        return redirect(session['url'])
    return redirect(url_for('channel', nick=nick))

@app.route('/unsub/<string:nick>')
def unsub(nick):
    if not session.get('nick'):
        return redirect(url_for('login'))
    user1 = db.session.query(User).filter(User.nick == session['nick']).first()
    user2 = db.session.query(User).filter(User.nick == nick).first()
    user1.following.remove(user2)
    db.session.commit()
    if session.get('url'):
        return redirect(session['url'])
    return redirect(url_for('channel', nick=nick))

@app.route('/like/<int:id>/<action>')
def like(id, action):
    if not session.get('nick'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    video = db.session.query(Video).filter(Video.id == id).first()
    if action == 'create':
        if user in video.dislikes:
            video.dislikes.remove(user)
        video.likes.append(user)
    else:
        video.likes.remove(user)
    db.session.commit()
    return redirect(url_for('video', id=id))

@app.route('/dislike/<int:id>/<action>')
def dislike(id, action):
    if not session.get('nick'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.nick == session['nick']).first()
    video = db.session.query(Video).filter(Video.id == id).first()
    if action == 'create':
        if user in video.likes:
            video.likes.remove(user)
        video.dislikes.append(user)
    else:
        video.dislikes.remove(user)
    db.session.commit()
    return redirect(url_for('video', id=id))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = db.session.query(User).filter(User.nick == request.form['username']).first()
        if not user:
            flash("Incorrect nickname")
            return redirect(url_for('login'))
        elif not user.validate_password(request.form['password']):
            flash("Incorrect password")
            return redirect(url_for('login'))
        session['nick'] = user.nick
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if db.session.query(User).filter(User.nick == request.form['username']).first():
            flash("This nick is registered")
            return redirect(url_for('register'))
        user = User(nick=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        session['nick'] = user.nick
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    if not session.get('nick'):
        return redirect(url_for('index'))
    session.pop('nick')
    return redirect(url_for('login'))

@app.route('/ip')
def chk_ip():
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

# @app.route('/ban/<nick>')
# def ban(nick):
#     user = db.session.query(User).filter(User.nick == nick).first()
#     user.is_banned = True
#     ban = Banned_ips.query.get(1)
#     l = ban.ips
#     l['ips'].extend(user.ip['ip'])
#     ban.ips = {'ips': list(set(l['ips']))}
#     flag_modified(ban, 'ips')
#     db.session.commit()
#     return redirect(url_for('index'))
#
# @app.route('/unban/<nick>')
# def unban(nick):
#     user = db.session.query(User).filter(User.nick == nick).first()
#     user.is_banned = False
#     ban = Banned_ips.query.get(1)
#     for i in user.ip['ip']:
#         ban.ips['ips'].remove(i)
#     flag_modified(ban, 'ips')
#     db.session.commit()
#     return redirect(url_for('index'))
#
# @app.route('/bban')
# def bban():
#     ban = Banned_ips.query.get(1)
#     ban.ips = {'ips': []}
#     db.session.commit()
#     return redirect(url_for('index'))