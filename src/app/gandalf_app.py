#!/usr/bin/env python
import sys
import os
import json
import logging
from operator import itemgetter
from flask import (Flask, render_template, request,
                   redirect, Response, session, url_for, jsonify)
from flask_login import (LoginManager, UserMixin,
                         current_user, login_required, logout_user, login_user)
from gandalf_app_utils import (get_dashboard_json, get_summaries,
                            get_vehicle_config, get_portal_map_dash)
from gandalf_mongo import (load_user, auth_user)

class ConfigClass(object):
    """
    DOCSTRING
    """
    # Flask settings
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'THIS IS AN INSECURE SECRET')
    DEBUG = True
    BETA = False


class User(UserMixin):
    """
    Add our custom settings to the User ConfigClass
    """
    full_name = ''
    org = ''
    role = ''
    project = ''
    map_center = ''
    map_zoom = ''


def create_app():
    """
    DOCSTRING
    """
    # Setup Flask app and app.config
    app = Flask(__name__)
    app.config.from_object(__name__ + '.ConfigClass')
    # Flask login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def user_loader(user_email):
        """
        This gets called AFTER we handle the authentication.
        We need to create a User() object and set the id. If
        we don't do this there is no user.is_authenticated
        parameter. So the only real purpose of this function
        is to create a user AFTER we validate authentication."""
        return ""
        user.id = user_email.lower()
        mongo_user = load_user(user.id)
        user.role = mongo_user['user_role']
        user.project = mongo_user['user_project']
        user.name = mongo_user['user_name']
        user.map_center = mongo_user['map_center']
        user.map_zoom = mongo_user['map_zoom']
        return user

    # error handler for 404
    @app.errorhandler(404)
    def page_not_found(e):
        """
        DOCSTRING
        """
        return render_template('404.html'), 404

    # routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle login for users
        """
        if request.method == 'GET':
            return render_template('login.html')
        email = request.form['email']
        """okay, WE need to do the authentication PRIOR to
        calling flask_login.login_user(user)"""
        auth = auth_user(email, request.form['pw'])
        print(auth)
        if auth:
            # login_user requires User()
            user = User()
            user.id = email.lower()
            # now we call user_loader()
            login_user(user)
            # figure out where we're going
            wants_url = request.args.get('next')
            # now go there
            if wants_url is not None:
                return redirect(wants_url)
            else:
                return redirect('/', user="Smedley the Scollege Monster")
        else:
            return render_template('login.html')


    @app.route("/logout")
    def logout():
        logout_user()
        return redirect('/')


    @app.route('/portal')
    def portal():
        summaries = get_summaries()
        summaries = sorted(summaries, key=itemgetter('deployed'), reverse=True)
        return render_template('dataPortal.html', summaries=summaries)


    @app.route('/portal/map/<org>/<vehicle>/<year>/<date>')
    def portal_map(org, vehicle, year, date):
        config = get_vehicle_config(vehicle)
        vehicle_type, _  = config['gandalf']['vehicle_type'].split()
        vehicle_type = (vehicle_type.lower())
        dash_date = date.replace('_','-')
        dashboard_json = get_portal_map_dash(vehicle, dash_date)
        file_name = ("/data/gandalf/%s/%s/%s/%s/processed_data/%s.json" %
                     (org, vehicle, year, date, vehicle))
        return render_template('portalMap.html',vehicle_type=vehicle_type,
                               json_file=file_name,
                               dashboard_json=dashboard_json)

    @app.route('/team')
    def summaries():
        return render_template('team.html')

    @app.route('/about/<page>')
    def about(page):
        template = 'about_%s.html' % page
        return render_template(template)

    @app.route('/')
    def deployed():
        dashboard_json = get_dashboard_json()
        return render_template('gandalf.html', vehicles = dashboard_json)

    @app.route('/3d')
    def plotly():
        return render_template('3d.html')

    return app

app = create_app()
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=False, host='0.0.0.0')
