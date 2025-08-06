import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Paciente, Anamnese
from decorators import login_required
from utils import validar_cpf

pacientes_bp = Blueprint('pacientes', __name__, url_prefix='/pacientes')

@pacientes_bp.route('/')
@login_required
def lista():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Paciente.query

    if search:
        query = query.filter(
            db.or_(
                Paciente.nome.ilike(f'%{search}%'),
                Paciente.cpf.ilike(f'%{search}%')
            )
        )

    pacientes = query.order_by(Paciente.nome).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('pacientes/lista.html', pacientes=pacientes, search=search)

@pacientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        telefone = request.form.get('telefone', '')
        gosto_musical = request.form.get('gosto_musical', '')
        observacoes = request.form.get('observacoes', '')

        # Validar CPF
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        if not validar_cpf(cpf_numeros):
            flash('CPF inválido!', 'error')
            return render_template('pacientes/form.html', dados=request.form)

        # Verificar se CPF já existe
        if Paciente.query.filter_by(cpf=cpf_numeros).first():
            flash('CPF já cadastrado!', 'error')
            return render_template('pacientes/form.html', dados=request.form)

        paciente = Paciente(
            nome=nome,
            cpf=cpf_numeros,
            data_nascimento=data_nascimento,
            telefone=telefone,
            gosto_musical=gosto_musical,
            observacoes=observacoes
        )

        db.session.add(paciente)
        db.session.commit()

        flash(f'Paciente {nome} cadastrado com sucesso!', 'success')

        # Se clicou em "Ir para Anamnese", redireciona
        if 'anamnese' in request.form:
            return redirect(url_for('anamnese.nova', paciente_id=paciente.id))

        return redirect(url_for('pacientes.lista'))

    return render_template('pacientes/form.html')

@pacientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    paciente = Paciente.query.get_or_404(id)

    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        telefone = request.form.get('telefone', '')
        gosto_musical = request.form.get('gosto_musical', '')
        observacoes = request.form.get('observacoes', '')

        # Validar CPF
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        if not validar_cpf(cpf_numeros):
            flash('CPF inválido!', 'error')
            return render_template('pacientes/form.html', paciente=paciente, dados=request.form)

        # Verificar se CPF já existe (exceto o atual)
        cpf_existente = Paciente.query.filter(
            Paciente.cpf == cpf_numeros,
            Paciente.id != id
        ).first()
        if cpf_existente:
            flash('CPF já cadastrado para outro paciente!', 'error')
            return render_template('pacientes/form.html', paciente=paciente, dados=request.form)

        paciente.nome = nome
        paciente.cpf = cpf_numeros
        paciente.data_nascimento = data_nascimento
        paciente.telefone = telefone
        paciente.gosto_musical = gosto_musical
        paciente.observacoes = observacoes

        db.session.commit()

        flash(f'Dados do paciente {nome} atualizados com sucesso!', 'success')
        return redirect(url_for('pacientes.lista'))

    return render_template('pacientes/form.html', paciente=paciente)

@pacientes_bp.route('/<int:id>')
@login_required
def ver(id):
    paciente = Paciente.query.get_or_404(id)

    # Buscar anamneses do paciente
    anamneses = Anamnese.query.filter_by(paciente_id=id).order_by(
        Anamnese.criado_em.desc()
    ).all()

    return render_template('pacientes/detalhes.html',
        paciente=paciente,
        anamneses=anamneses,
        atendimentos=[],
        agendamentos=[]
    )
