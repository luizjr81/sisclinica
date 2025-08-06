from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from extensions import db
from models import Atendimento, Paciente, Profissional, Procedimento, AtendimentoProcedimento
from decorators import login_required

atendimentos_bp = Blueprint('atendimentos', __name__, url_prefix='/atendimentos')

# Criar objeto de paginação manual
class PaginationMock:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.total = total
        self.pages = max(1, (total + per_page - 1) // per_page)
        self.page = page
        self.per_page = per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

    def iter_pages(self):
        for num in range(1, self.pages + 1):
            yield num

@atendimentos_bp.route('/')
@login_required
def lista():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')

    try:
        query = db.session.query(
            Atendimento,
            Paciente.nome.label('paciente_nome'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Atendimento.paciente_id == Paciente.id)\
         .join(Profissional, Atendimento.profissional_id == Profissional.id)

        if search:
            query = query.filter(Paciente.nome.ilike(f'%{search}%'))

        if status:
            query = query.filter(Atendimento.status == status)

        query = query.order_by(Atendimento.data_atendimento.desc())

        total = query.count()
        per_page = 20
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

    except Exception:
        items = []
        total = 0

    atendimentos_paginados = PaginationMock(items, page, 20, total)

    return render_template('atendimentos/lista.html',
                         atendimentos=atendimentos_paginados,
                         search=search,
                         status=status)

@atendimentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            paciente_id = request.form['paciente_id']
            profissional_id = request.form['profissional_id']
            data_atendimento = datetime.strptime(request.form['data_atendimento'], '%Y-%m-%d').date()
            descricao = request.form.get('descricao', '')

            procedimento_ids = request.form.getlist('procedimentos[]')
            quantidades = request.form.getlist('quantidades[]')

            if not procedimento_ids:
                flash('É necessário adicionar pelo menos um procedimento!', 'error')
                # Re-render form
                pacientes = Paciente.query.order_by(Paciente.nome).all()
                profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()
                procedimentos = Procedimento.query.filter_by(ativo=True).order_by(Procedimento.nome).all()
                return render_template('atendimentos/form.html',
                                     pacientes=pacientes,
                                     profissionais=profissionais,
                                     procedimentos=procedimentos,
                                     dados=request.form)

            valor_total_calculado = 0
            procedimentos_do_atendimento = []

            for i, proc_id in enumerate(procedimento_ids):
                procedimento = Procedimento.query.get(proc_id)
                if not procedimento:
                    raise Exception(f"Procedimento com ID {proc_id} não encontrado.")

                quantidade = int(quantidades[i]) if i < len(quantidades) else 1
                valor_item = procedimento.valor * quantidade
                valor_total_calculado += valor_item

                procedimentos_do_atendimento.append({
                    "procedimento_id": proc_id,
                    "quantidade": quantidade,
                    "valor_unitario": procedimento.valor,
                    "valor_total": valor_item
                })

            atendimento = Atendimento(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                data_atendimento=data_atendimento,
                descricao=descricao,
                valor_total=valor_total_calculado,
                status='pendente'
            )

            db.session.add(atendimento)
            db.session.flush()

            for item in procedimentos_do_atendimento:
                ap = AtendimentoProcedimento(
                    atendimento_id=atendimento.id,
                    procedimento_id=item['procedimento_id'],
                    quantidade=item['quantidade'],
                    valor_unitario=item['valor_unitario'],
                    valor_total=item['valor_total']
                )
                db.session.add(ap)

            db.session.commit()

            flash('Atendimento registrado com sucesso!', 'success')
            return redirect(url_for('atendimentos.lista'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar atendimento: {str(e)}', 'error')
            # Re-render form
            pacientes = Paciente.query.order_by(Paciente.nome).all()
            profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()
            procedimentos = Procedimento.query.filter_by(ativo=True).order_by(Procedimento.nome).all()
            return render_template('atendimentos/form.html',
                                 pacientes=pacientes,
                                 profissionais=profissionais,
                                 procedimentos=procedimentos,
                                 dados=request.form)

    # GET
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()
    procedimentos = Procedimento.query.filter_by(ativo=True).order_by(Procedimento.nome).all()

    return render_template('atendimentos/form.html',
                         pacientes=pacientes,
                         profissionais=profissionais,
                         procedimentos=procedimentos)

@atendimentos_bp.route('/<int:id>')
@login_required
def ver(id):
    try:
        atendimento_data = db.session.query(
            Atendimento,
            Paciente.nome.label('paciente_nome'),
            Paciente.cpf.label('paciente_cpf'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Atendimento.paciente_id == Paciente.id)\
         .join(Profissional, Atendimento.profissional_id == Profissional.id)\
         .filter(Atendimento.id == id).first()

        if not atendimento_data:
            flash('Atendimento não encontrado!', 'error')
            return redirect(url_for('atendimentos.lista'))

        return render_template('atendimentos/detalhes.html', atendimento=atendimento_data)

    except Exception as e:
        flash(f'Erro ao buscar atendimento: {str(e)}', 'error')
        return redirect(url_for('atendimentos.lista'))
