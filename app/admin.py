from flask import session, request, redirect, url_for
from flask_admin import Admin, BaseView, AdminIndexView, expose
from app.models import User, Banned_ips
from app import db
from sqlalchemy.orm.attributes import flag_modified


def ban(user):
    user.is_banned = True
    ban = Banned_ips.query.get(1)
    print(Banned_ips.query.all())
    if not ban:
        print(12)
        ban = Banned_ips(id=1, ips={'ips': []})
        db.session.add(ban)
    #l = ban.ips
    ban.ips['ips'].extend(user.ip['ip'])
    #ban.ips['nicks'].append(user.nick)
    #ban.ips = {'ips': l['ips']), 'nicks': l['nicks']}
    print(ban.ips)
    flag_modified(ban, 'ips')
    db.session.commit()
    print(ban.ips)

def unban(user):
    user.is_banned = False
    ban = Banned_ips.query.get(1)
    for i in user.ip['ip']:
        ban.ips['ips'].remove(i)
    #ban.ips['nicks'].remove(user.nick)
    flag_modified(ban, 'ips')
    db.session.commit()

class DashboardView(AdminIndexView):
    @expose('/', methods=["POST", "GET"])
    def index(self):
        if session.get('nick'):
            user = db.session.query(User).filter(User.nick == session['nick']).first()
            if user.is_admin == True or user.nick == 'admin':
                if request.method == 'POST':
                    if request.form.get('ban'):
                        ban_user = db.session.query(User).filter(User.nick == request.form['ban']).first()
                        if ban_user and not ban_user.is_admin or ban_user.nick != 'admin':
                            ban(ban_user)
                    if request.form.get('unban'):
                        unban_user = db.session.query(User).filter(User.nick == request.form['unban']).first()
                        if unban_user and unban_user.is_banned:
                            unban(unban_user)

                return self.render('admin/dashboard_index.html')
            else:
                return redirect(url_for('index'))