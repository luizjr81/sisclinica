from flask import Blueprint, redirect, url_for, flash
from decorators import login_required

pagamentos_bp = Blueprint('pagamentos', __name__, url_prefix='/pagamentos')

@pagamentos_bp.route('/')
@login_required
def lista():
    flash('Módulo de pagamentos em desenvolvimento. Use a área de atendimentos para gerenciar pagamentos.', 'info')
    return redirect(url_for('atendimentos.lista'))

@pagamentos_bp.route('/novo/<int:atendimento_id>')
@login_required
def novo(atendimento_id):
    flash('A funcionalidade de registrar novos pagamentos ainda está em desenvolvimento.', 'info')
    return redirect(url_for('atendimentos.ver', id=atendimento_id))
