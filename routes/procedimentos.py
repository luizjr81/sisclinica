from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Procedimento
from decorators import login_required

procedimentos_bp = Blueprint('procedimentos', __name__, url_prefix='/procedimentos')

@procedimentos_bp.route('/')
@login_required
def lista():
    search = request.args.get('search', '')

    query = Procedimento.query.filter_by(ativo=True)

    if search:
        query = query.filter(Procedimento.nome.ilike(f'%{search}%'))

    procedimentos = query.order_by(Procedimento.nome).all()

    return render_template('procedimentos/lista.html', procedimentos=procedimentos, search=search)

@procedimentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form['nome']
        try:
            valor = float(request.form['valor'])
        except ValueError:
            flash('Valor inválido!', 'error')
            return render_template('procedimentos/form.html', dados=request.form)

        # Verificar se procedimento já existe
        if Procedimento.query.filter_by(nome=nome, ativo=True).first():
            flash('Procedimento já cadastrado!', 'error')
            return render_template('procedimentos/form.html', dados=request.form)

        procedimento = Procedimento(nome=nome, valor=valor)

        db.session.add(procedimento)
        db.session.commit()

        flash(f'Procedimento "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('procedimentos.lista'))

    return render_template('procedimentos/form.html')

@procedimentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    procedimento = Procedimento.query.get_or_404(id)

    if request.method == 'POST':
        nome = request.form['nome']
        try:
            valor = float(request.form['valor'])
        except ValueError:
            flash('Valor inválido!', 'error')
            return render_template('procedimentos/form.html', procedimento=procedimento, dados=request.form)

        # Verificar se nome já existe (exceto o atual)
        existente = Procedimento.query.filter(
            Procedimento.nome == nome,
            Procedimento.id != id,
            Procedimento.ativo == True
        ).first()

        if existente:
            flash('Já existe um procedimento com este nome!', 'error')
            return render_template('procedimentos/form.html', procedimento=procedimento, dados=request.form)

        procedimento.nome = nome
        procedimento.valor = valor

        db.session.commit()

        flash(f'Procedimento "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('procedimentos.lista'))

    return render_template('procedimentos/form.html', procedimento=procedimento)
