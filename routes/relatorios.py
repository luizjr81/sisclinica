from flask import Blueprint, render_template, redirect, url_for, flash
from decorators import login_required

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@relatorios_bp.route('/')
@login_required
def index():
    return render_template('relatorios/index.html')

@relatorios_bp.route('/financeiro')
@login_required
def financeiro():
    flash('Relatório financeiro em desenvolvimento', 'info')
    return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/pendencias')
@login_required
def pendencias():
    flash('Relatório de pendências em desenvolvimento', 'info')
    return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/procedimentos')
@login_required
def procedimentos():
    flash('Relatório de procedimentos em desenvolvimento', 'info')
    return redirect(url_for('relatorios.index'))
