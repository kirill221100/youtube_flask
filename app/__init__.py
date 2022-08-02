from flask import Flask
from flask_migrate import Migrate
from app.config import Config
from app.models import db, User, Video, Banned_ips, Comment
from app.admin import DashboardView
from upload import get_gdrive_service
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
service = get_gdrive_service()
admin = Admin(app, index_view=DashboardView())
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Video, db.session))
admin.add_view(ModelView(Comment, db.session))
admin.add_view(ModelView(Banned_ips, db.session))

@app.before_first_request
def create_tables():
    db.create_all()

@app.before_request
def log_ip():
    if session.get('nick'):
        user = db.session.query(User).filter(User.nick == session['nick']).first()
        ip = request.headers['X-Forwarded-For']

        if not user.ip:
            user.ip = {'ip': []}
        if ip not in user.ip['ip']:
            user.ip['ip'].append(ip)
        else:
            return
        db.session.commit()


from app.views import *