from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from datetime import date
from models import Usuario, Paciente
from decorators import login_required
from utils import testar_conexao_banco
from extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(username=username, ativo=True).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['user_type'] = usuario.tipo
            flash(f'Bem-vindo, {usuario.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuário ou senha inválidos!', 'error')

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso!', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    hoje = date.today()

    # Estatísticas para o dashboard
    total_pacientes = Paciente.query.count()

    return render_template('dashboard.html',
        total_pacientes=total_pacientes,
        atendimentos_hoje=0,
        valores_recebidos_hoje=0.0,
        agendamentos_hoje=0,
        ultimos_atendimentos=[]
    )

@main_bp.route('/test')
def test():
    """Rota de teste para verificar se tudo está funcionando"""
    return jsonify({
        'status': 'OK',
        'message': 'Sistema funcionando!',
        'database': 'Conectado' if testar_conexao_banco() else 'Erro',
        'tables': [table.name for table in db.metadata.tables.values()]
    })
