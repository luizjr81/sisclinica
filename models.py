from datetime import datetime
from extensions import db

# ==================== MODELOS DO BANCO DE DADOS ====================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # admin, atendente, profissional
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    ativo = db.Column(db.Boolean, default=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String(20))
    gosto_musical = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Anamnese(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    numero_identificador = db.Column(db.String(20), nullable=False)
    conteudo = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Procedimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

class Atendimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    data_atendimento = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.Text)
    valor_total = db.Column(db.Numeric(10, 2), default=0)
    desconto_valor = db.Column(db.Numeric(10, 2), default=0)
    desconto_percentual = db.Column(db.Numeric(5, 2), default=0)
    status = db.Column(db.String(20), default='pendente')  # pendente, parcial, pago
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class AtendimentoProcedimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atendimento_id = db.Column(db.Integer, db.ForeignKey('atendimento.id'), nullable=False)
    procedimento_id = db.Column(db.Integer, db.ForeignKey('procedimento.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado')  # agendado, realizado, cancelado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atendimento_id = db.Column(db.Integer, db.ForeignKey('atendimento.id'), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)  # dinheiro, cartao, pix
    data_pagamento = db.Column(db.Date, nullable=False)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
