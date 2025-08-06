from functools import wraps
from flask import session, redirect, url_for, flash
from models import Usuario

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login')) # Note: url_for needs to be updated to blueprint syntax
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login')) # Note: url_for needs to be updated to blueprint syntax
        usuario = Usuario.query.get(session['user_id'])
        if not usuario or usuario.tipo != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
            return redirect(url_for('main.dashboard')) # Note: url_for needs to be updated to blueprint syntax
        return f(*args, **kwargs)
    return decorated_function
