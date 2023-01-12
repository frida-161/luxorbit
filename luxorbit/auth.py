from flask import request, redirect, url_for, session
from luxorbit import app, client
from functools import wraps
import datetime as dt


def auth_required(f):
    """Decorate function to require Strava Auth."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('access_token') or \
                not session.get('refresh_token') or \
                not session.get('expires_at'):
            return redirect(url_for('auth'))
        elif session.get('expires_at') <= dt.datetime.now().timestamp():
            token = client.refresh_access_token(session.get('refresh_token'))
            session['access_token'] = token.get('access_token')
            session['refresh_token'] = token.get('refresh_token')
            session['expires_at'] = token.get('expires_at')

        return f(*args, **kwargs)
    return decorated_function


@app.route('/auth')
def auth():
    auth_url = client.authorization_url(
        redirect_uri='http://localhost:4567/authorized')
    # TODO use environment variable
    return redirect(auth_url, code=302)


@app.route('/authorized')
def authorized():
    code = request.args.get('code')
    token = client.exchange_code_for_token(code=code)
    session['access_token'] = token.get('access_token')
    session['refresh_token'] = token.get('refresh_token')
    session['expires_at'] = token.get('expires_at')

    return 'authorized'
