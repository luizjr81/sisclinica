from flask import Blueprint, render_template, redirect, url_for, flash
from models import Usuario, Paciente, Procedimento
from decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    total_usuarios = Usuario.query.count()
    usuarios_ativos = Usuario.query.filter_by(ativo=True).count()
    total_pacientes = Paciente.query.count()
    total_procedimentos = Procedimento.query.filter_by(ativo=True).count()

    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         usuarios_ativos=usuarios_ativos,
                         total_pacientes=total_pacientes,
                         total_procedimentos=total_procedimentos)

@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    usuarios = Usuario.query.order_by(Usuario.username).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/backup')
@admin_required
def backup():
    flash('Funcionalidade de backup em desenvolvimento', 'info')
    return redirect(url_for('admin.dashboard'))
