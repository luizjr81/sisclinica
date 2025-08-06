from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date, timedelta
from extensions import db
from models import Agendamento, Paciente, Profissional
from decorators import login_required

agendamentos_bp = Blueprint('agendamentos', __name__, url_prefix='/agendamentos')

@agendamentos_bp.route('/')
@login_required
def lista():
    data_param = request.args.get('data')
    if data_param:
        try:
            data_selecionada = datetime.strptime(data_param, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = date.today()
    else:
        data_selecionada = date.today()

    hoje = date.today()

    try:
        agendamentos_data = db.session.query(
            Agendamento,
            Paciente.nome.label('paciente_nome'),
            Paciente.telefone.label('paciente_telefone'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Agendamento.paciente_id == Paciente.id)\
         .join(Profissional, Agendamento.profissional_id == Profissional.id)\
         .filter(db.func.date(Agendamento.data_hora) == data_selecionada)\
         .order_by(Agendamento.data_hora).all()
    except Exception:
        agendamentos_data = []

    return render_template('agendamentos/lista.html',
                         agendamentos=agendamentos_data,
                         data_selecionada=data_selecionada,
                         hoje=hoje,
                         timedelta=timedelta)

@agendamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            paciente_id = request.form['paciente_id']
            profissional_id = request.form['profissional_id']
            data = request.form['data']
            horario = request.form['horario']
            observacoes = request.form.get('observacoes', '')
            status = request.form.get('status', 'agendado')

            data_hora = datetime.strptime(f"{data} {horario}", '%Y-%m-%d %H:%M')

            agendamento = Agendamento(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                data_hora=data_hora,
                observacoes=observacoes,
                status=status
            )

            db.session.add(agendamento)
            db.session.commit()

            flash('Agendamento criado com sucesso!', 'success')
            return redirect(url_for('agendamentos.lista'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar agendamento: {str(e)}', 'error')

    pacientes = Paciente.query.order_by(Paciente.nome).all()
    profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()

    return render_template('agendamentos/form.html',
                         pacientes=pacientes,
                         profissionais=profissionais)

@agendamentos_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status(id):
    try:
        status = request.form['status']
        agendamento = Agendamento.query.get_or_404(id)
        agendamento.status = status
        db.session.commit()

        flash(f'Status do agendamento atualizado para {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')

    return redirect(url_for('agendamentos.lista'))
