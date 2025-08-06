from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import text
from datetime import datetime
from extensions import db
from models import Anamnese, Paciente
from decorators import login_required

anamnese_bp = Blueprint('anamnese', __name__, url_prefix='/anamnese')

@anamnese_bp.route('/<int:paciente_id>/nova', methods=['GET', 'POST'])
@login_required
def nova(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)

    if request.method == 'POST':
        conteudo = request.form['conteudo']

        # Gerar número identificador único
        ultimo_numero = db.session.execute(text("SELECT COALESCE(MAX(id), 0) FROM anamnese")).scalar() or 0
        numero_identificador = f"ANM{(ultimo_numero + 1):05d}"

        anamnese = Anamnese(
            paciente_id=paciente_id,
            numero_identificador=numero_identificador,
            conteudo=conteudo
        )

        db.session.add(anamnese)
        db.session.commit()

        flash(f'Anamnese {numero_identificador} criada com sucesso!', 'success')

        # Se clicou em "Salvar como", permite criar nova anamnese
        if 'salvar_como' in request.form:
            return redirect(url_for('anamnese.nova', paciente_id=paciente_id))

        return redirect(url_for('pacientes.ver', id=paciente_id))

    return render_template('anamnese/form.html', paciente=paciente)

@anamnese_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    anamnese = Anamnese.query.get_or_404(id)
    paciente = Paciente.query.get(anamnese.paciente_id)

    if request.method == 'POST':
        anamnese.conteudo = request.form['conteudo']
        anamnese.atualizado_em = datetime.utcnow()

        db.session.commit()

        flash(f'Anamnese {anamnese.numero_identificador} atualizada com sucesso!', 'success')

        # Se clicou em "Salvar como", cria nova anamnese
        if 'salvar_como' in request.form:
            novo_numero = db.session.execute(text("SELECT COALESCE(MAX(id), 0) FROM anamnese")).scalar() or 0
            numero_identificador = f"ANM{(novo_numero + 1):05d}"

            nova_anamnese_obj = Anamnese(
                paciente_id=anamnese.paciente_id,
                numero_identificador=numero_identificador,
                conteudo=request.form['conteudo']
            )

            db.session.add(nova_anamnese_obj)
            db.session.commit()

            flash(f'Nova anamnese {numero_identificador} criada com sucesso!', 'success')

        return redirect(url_for('pacientes.ver', id=anamnese.paciente_id))

    return render_template('anamnese/form.html', paciente=paciente, anamnese=anamnese)

@anamnese_bp.route('/<int:id>')
@login_required
def ver(id):
    anamnese = Anamnese.query.get_or_404(id)
    paciente = Paciente.query.get(anamnese.paciente_id)

    return render_template('anamnese/detalhes.html', anamnese=anamnese, paciente=paciente)
