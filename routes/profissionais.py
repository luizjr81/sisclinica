from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Profissional
from decorators import login_required

profissionais_bp = Blueprint('profissionais', __name__, url_prefix='/profissionais')

@profissionais_bp.route('/')
@login_required
def lista():
    search = request.args.get('search', '')

    query = Profissional.query
    if search:
        query = query.filter(Profissional.nome.ilike(f'%{search}%'))

    profissionais = query.order_by(Profissional.nome).all()

    return render_template('profissionais/lista.html',
                         profissionais=profissionais,
                         search=search)

@profissionais_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form.get('especialidade', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')

        if Profissional.query.filter_by(nome=nome, ativo=True).first():
            flash('Já existe um profissional com este nome!', 'error')
            return render_template('profissionais/form.html', dados=request.form)

        profissional = Profissional(
            nome=nome,
            especialidade=especialidade,
            telefone=telefone,
            email=email
        )

        db.session.add(profissional)
        db.session.commit()

        flash(f'Profissional {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('profissionais.lista'))

    return render_template('profissionais/form.html')

@profissionais_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    profissional = Profissional.query.get_or_404(id)

    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form.get('especialidade', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')

        existente = Profissional.query.filter(
            Profissional.nome == nome,
            Profissional.id != id,
            Profissional.ativo == True
        ).first()

        if existente:
            flash('Já existe um profissional com este nome!', 'error')
            return render_template('profissionais/form.html', profissional=profissional, dados=request.form)

        profissional.nome = nome
        profissional.especialidade = especialidade
        profissional.telefone = telefone
        profissional.email = email

        db.session.commit()

        flash(f'Dados do profissional {nome} atualizados!', 'success')
        return redirect(url_for('profissionais.lista'))

    return render_template('profissionais/form.html', profissional=profissional)
