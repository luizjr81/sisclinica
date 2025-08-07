"""
Sistema de Gestão para Clínica de Estética - Versão Básica
Desenvolvido com Flask + PostgreSQL
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
from functools import wraps
import re
from dotenv import load_dotenv
from sqlalchemy import text

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações usando variáveis de ambiente
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-padrao-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://clinica_user:senha123@localhost:5432/clinica_estetica')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração para SQLAlchemy 2.0+
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

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

# ==================== DECORADORES ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        usuario = Usuario.query.get(session['user_id'])
        if not usuario or usuario.tipo != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== FUNÇÕES UTILITÁRIAS ====================

def validar_cpf(cpf):
    """Valida CPF removendo caracteres especiais"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cpf_base):
        soma = sum(int(cpf_base[i]) * (len(cpf_base) + 1 - i) for i in range(len(cpf_base)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    primeiro_digito = calcular_digito(cpf[:9])
    segundo_digito = calcular_digito(cpf[:10])
    
    return cpf[-2:] == f"{primeiro_digito}{segundo_digito}"

def formatar_cpf(cpf):
    """Formata CPF para exibição"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def calcular_idade(data_nascimento):
    """Calcula idade baseada na data de nascimento"""
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(username=username, ativo=True).first()
        
        if usuario and check_password_hash(usuario.senha_hash, senha):
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['user_type'] = usuario.tipo
            flash(f'Bem-vindo, {usuario.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    hoje = date.today()
    
    # Estatísticas básicas
    total_pacientes = Paciente.query.count()
    total_profissionais = Profissional.query.filter_by(ativo=True).count()
    total_procedimentos = Procedimento.query.filter_by(ativo=True).count()
    
    # Estatísticas de atendimentos (com tratamento de erro)
    try:
        total_atendimentos = Atendimento.query.count()
        atendimentos_hoje = Atendimento.query.filter_by(data_atendimento=hoje).count()
        
        # Valores financeiros
        valores_hoje = db.session.query(db.func.sum(Atendimento.valor_total))\
                                .filter_by(data_atendimento=hoje).scalar() or 0
        
        # Atendimentos pendentes
        atendimentos_pendentes = Atendimento.query.filter_by(status='pendente').count()
        
        # Últimos atendimentos
        ultimos_atendimentos = db.session.query(
            Atendimento,
            Paciente.nome.label('paciente_nome'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Atendimento.paciente_id == Paciente.id)\
         .join(Profissional, Atendimento.profissional_id == Profissional.id)\
         .order_by(Atendimento.criado_em.desc()).limit(5).all()
        
    except Exception:
        # Se tabelas não existem ainda
        total_atendimentos = 0
        atendimentos_hoje = 0
        valores_hoje = 0
        atendimentos_pendentes = 0
        ultimos_atendimentos = []
    
    # Estatísticas de agendamentos (com tratamento de erro)
    try:
        agendamentos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_hora) == hoje
        ).count()
        
        proximos_agendamentos = db.session.query(
            Agendamento,
            Paciente.nome.label('paciente_nome'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Agendamento.paciente_id == Paciente.id)\
         .join(Profissional, Agendamento.profissional_id == Profissional.id)\
         .filter(Agendamento.data_hora >= datetime.now())\
         .filter_by(status='agendado')\
         .order_by(Agendamento.data_hora).limit(5).all()
        
    except Exception:
        agendamentos_hoje = 0
        proximos_agendamentos = []
    
    return render_template('dashboard.html',
        # Estatísticas básicas
        total_pacientes=total_pacientes,
        total_profissionais=total_profissionais,
        total_procedimentos=total_procedimentos,
        
        # Estatísticas de atendimentos
        total_atendimentos=total_atendimentos,
        atendimentos_hoje=atendimentos_hoje,
        valores_recebidos_hoje=float(valores_hoje),
        atendimentos_pendentes=atendimentos_pendentes,
        
        # Estatísticas de agendamentos
        agendamentos_hoje=agendamentos_hoje,
        
        # Listas
        ultimos_atendimentos=ultimos_atendimentos,
        proximos_agendamentos=proximos_agendamentos
    )

# ==================== MÓDULO DE PACIENTES ====================

@app.route('/pacientes')
@login_required
def pacientes():
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

@app.route('/pacientes/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_paciente():
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
            return redirect(url_for('nova_anamnese', paciente_id=paciente.id))
        
        return redirect(url_for('pacientes'))
    
    return render_template('pacientes/form.html')

@app.route('/pacientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
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
        return redirect(url_for('pacientes'))
    
    return render_template('pacientes/form.html', paciente=paciente)

@app.route('/pacientes/<int:id>')
@login_required
def ver_paciente(id):
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

# ==================== MÓDULO DE PROCEDIMENTOS ====================

@app.route('/procedimentos')
@login_required
def procedimentos():
    search = request.args.get('search', '')
    
    query = Procedimento.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(Procedimento.nome.ilike(f'%{search}%'))
    
    procedimentos = query.order_by(Procedimento.nome).all()
    
    return render_template('procedimentos/lista.html', procedimentos=procedimentos, search=search)

@app.route('/procedimentos/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_procedimento():
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
        return redirect(url_for('procedimentos'))
    
    return render_template('procedimentos/form.html')

@app.route('/procedimentos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_procedimento(id):
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
        return redirect(url_for('procedimentos'))
    
    return render_template('procedimentos/form.html', procedimento=procedimento)

# ==================== ANAMNESE ====================

@app.route('/anamnese/<int:paciente_id>/nova', methods=['GET', 'POST'])
@login_required
def nova_anamnese(paciente_id):
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
            return redirect(url_for('nova_anamnese', paciente_id=paciente_id))
        
        return redirect(url_for('ver_paciente', id=paciente_id))
    
    return render_template('anamnese/form.html', paciente=paciente)

@app.route('/anamnese/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_anamnese(id):
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
            
            nova_anamnese = Anamnese(
                paciente_id=anamnese.paciente_id,
                numero_identificador=numero_identificador,
                conteudo=request.form['conteudo']
            )
            
            db.session.add(nova_anamnese)
            db.session.commit()
            
            flash(f'Nova anamnese {numero_identificador} criada com sucesso!', 'success')
        
        return redirect(url_for('ver_paciente', id=anamnese.paciente_id))
    
    return render_template('anamnese/form.html', paciente=paciente, anamnese=anamnese)

@app.route('/anamnese/<int:id>')
@login_required
def ver_anamnese(id):
    anamnese = Anamnese.query.get_or_404(id)
    paciente = Paciente.query.get(anamnese.paciente_id)
    
    return render_template('anamnese/detalhes.html', anamnese=anamnese, paciente=paciente)

# ==================== INICIALIZAÇÃO ====================

def testar_conexao_banco():
    """Testa a conexão com o banco de dados"""
    try:
        # Teste simples usando SQLAlchemy 2.0
        result = db.session.execute(text('SELECT 1 as test'))
        test_value = result.scalar()
        if test_value == 1:
            print("✅ Conexão com banco de dados OK")
            return True
        else:
            print("❌ Erro: Resposta inesperada do banco")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão com banco: {str(e)}")
        return False

def verificar_permissoes_banco():
    """Verifica se o usuário tem permissões para criar tabelas"""
    try:
        # Testar criação e remoção de tabela temporária
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS teste_permissoes_temp (
                id SERIAL PRIMARY KEY,
                teste VARCHAR(10)
            )
        '''))
        db.session.commit()
        
        db.session.execute(text('DROP TABLE IF EXISTS teste_permissoes_temp'))
        db.session.commit()
        
        print("✅ Permissões de criação de tabelas: OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro de permissões: {str(e)}")
        return False

def criar_usuario_admin():
    """Cria usuário administrador padrão se não existir"""
    try:
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                email='admin@clinica.com',
                senha_hash=generate_password_hash('admin123'),
                tipo='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário administrador criado: admin/admin123")
        else:
            print("✅ Usuário administrador já existe")
    except Exception as e:
        print(f"❌ Erro ao criar usuário admin: {str(e)}")

def criar_tabelas():
    """Cria todas as tabelas do banco de dados"""
    with app.app_context():
        try:
            print("🔄 Testando conexão com banco de dados...")
            
            # Testar conexão primeiro
            if not testar_conexao_banco():
                print("❌ Falha na conexão. Verifique as configurações do banco.")
                return False
            
            print("🔄 Verificando permissões...")
            
            # Verificar permissões
            if not verificar_permissoes_banco():
                print("❌ Usuário sem permissões suficientes.")
                return False
            
            print("🔄 Criando tabelas...")
            db.create_all()
            
            print("🔄 Configurando usuário administrador...")
            criar_usuario_admin()
            
            print("✅ Banco de dados inicializado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {str(e)}")
            return False

# Adicionar funções ao contexto do template
@app.context_processor
def utility_processor():
    return dict(
        formatar_cpf=formatar_cpf,
        calcular_idade=calcular_idade,
        date=date,
        timedelta=timedelta
    )

# ==================== MÓDULO DE ANAMNESES (MENU SEPARADO) ====================

@app.route('/anamneses')
@login_required
def listar_anamneses():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Query base com join para pegar dados do paciente
    query = db.session.query(
        Anamnese,
        Paciente.nome.label('paciente_nome'),
        Paciente.cpf.label('paciente_cpf')
    ).join(Paciente, Anamnese.paciente_id == Paciente.id)
    
    # Aplicar filtro de busca se houver
    if search:
        query = query.filter(
            db.or_(
                Paciente.nome.ilike(f'%{search}%'),
                Paciente.cpf.ilike(f'%{search}%'),
                Anamnese.numero_identificador.ilike(f'%{search}%')
            )
        )
    
    # Ordenar por data mais recente
    query = query.order_by(Anamnese.criado_em.desc())
    
    # Paginar
    total = query.count()
    per_page = 20
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
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
    
    anamneses_paginadas = PaginationMock(items, page, per_page, total)
    
    return render_template('anamneses/lista.html', 
                         anamneses=anamneses_paginadas,
                         search=search)

@app.route('/anamneses/paciente/<int:paciente_id>')
@login_required
def anamneses_por_paciente(paciente_id):
    """Lista todas as anamneses de um paciente específico"""
    paciente = Paciente.query.get_or_404(paciente_id)
    
    anamneses = Anamnese.query.filter_by(paciente_id=paciente_id)\
                             .order_by(Anamnese.criado_em.desc()).all()
    
    return render_template('anamneses/por_paciente.html',
                         paciente=paciente,
                         anamneses=anamneses)

@app.route('/anamneses/buscar-pacientes')
@login_required
def buscar_pacientes_anamnese():
    """Busca pacientes para criar nova anamnese"""
    termo = request.args.get('termo', '')
    
    if len(termo) < 2:
        return jsonify([])
    
    pacientes = Paciente.query.filter(
        db.or_(
            Paciente.nome.ilike(f'%{termo}%'),
            Paciente.cpf.ilike(f'%{termo}%')
        )
    ).limit(10).all()
    
    resultado = []
    for paciente in pacientes:
        # Contar anamneses do paciente
        total_anamneses = Anamnese.query.filter_by(paciente_id=paciente.id).count()
        
        resultado.append({
            'id': paciente.id,
            'nome': paciente.nome,
            'cpf': formatar_cpf(paciente.cpf),
            'idade': calcular_idade(paciente.data_nascimento),
            'telefone': paciente.telefone or '',
            'total_anamneses': total_anamneses
        })
    
    return jsonify(resultado)




# ==================== ROTAS DE TESTE ====================

@app.route('/test')
def test():
    """Rota de teste para verificar se tudo está funcionando"""
    return jsonify({
        'status': 'OK',
        'message': 'Sistema funcionando!',
        'database': 'Conectado' if testar_conexao_banco() else 'Erro',
        'tables': [table.name for table in db.metadata.tables.values()]
    })

# ==================== MÓDULO DE ATENDIMENTOS ====================

@app.route('/atendimentos')
@login_required
def atendimentos():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    try:
        # Criar query básica com join para buscar dados relacionados
        query = db.session.query(
            Atendimento,
            Paciente.nome.label('paciente_nome'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Atendimento.paciente_id == Paciente.id)\
         .join(Profissional, Atendimento.profissional_id == Profissional.id)
        
        # Aplicar filtros se houver
        if search:
            query = query.filter(Paciente.nome.ilike(f'%{search}%'))
        
        if status:
            query = query.filter(Atendimento.status == status)
        
        # Ordenar por data mais recente
        query = query.order_by(Atendimento.data_atendimento.desc())
        
        # Executar query e paginar manualmente
        total = query.count()
        per_page = 20
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
    except Exception:
        # Se tabelas não existem, retorna dados vazios
        items = []
        total = 0
    
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
    
    atendimentos_paginados = PaginationMock(items, page, per_page, total)
    
    return render_template('atendimentos/lista.html', 
                         atendimentos=atendimentos_paginados,
                         search=search, 
                         status=status)

@app.route('/atendimentos/novo', methods=['GET', 'POST'])
@login_required
def novo_atendimento():
    if request.method == 'POST':
        try:
            paciente_id = request.form['paciente_id']
            profissional_id = request.form['profissional_id']
            data_atendimento = datetime.strptime(request.form['data_atendimento'], '%Y-%m-%d').date()
            descricao = request.form.get('descricao', '')
            valor_total = float(request.form.get('valor_total', 0))
            
            # Validações
            if not paciente_id or not profissional_id:
                flash('Paciente e Profissional são obrigatórios!', 'error')
                raise ValueError('Campos obrigatórios não preenchidos')
                
            if valor_total <= 0:
                flash('Valor total deve ser maior que zero!', 'error')
                raise ValueError('Valor inválido')
            
            # Verificar se paciente e profissional existem
            paciente = Paciente.query.get(paciente_id)
            profissional = Profissional.query.get(profissional_id)
            
            if not paciente:
                flash('Paciente não encontrado!', 'error')
                raise ValueError('Paciente inválido')
                
            if not profissional or not profissional.ativo:
                flash('Profissional não encontrado ou inativo!', 'error')
                raise ValueError('Profissional inválido')
            
            # Criar novo atendimento
            atendimento = Atendimento(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                data_atendimento=data_atendimento,
                descricao=descricao,
                valor_total=valor_total,
                status='pendente'
            )
            
            db.session.add(atendimento)
            db.session.commit()
            
            flash(f'✅ Atendimento para {paciente.nome} registrado com sucesso!', 'success')
            
            # Se clicou em "Registrar e Ir para Pagamento"
            if 'criar_e_pagar' in request.form:
                return redirect(url_for('novo_pagamento', atendimento_id=atendimento.id))
            
            return redirect(url_for('atendimentos'))
            
        except ValueError as ve:
            # Erro de validação - não faz rollback
            pass
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao registrar atendimento: {str(e)}', 'error')
    
    # GET - Exibir formulário
    # Buscar pacientes com suas observações
    pacientes = db.session.query(Paciente.id, Paciente.nome, Paciente.cpf, Paciente.observacoes)\
                          .order_by(Paciente.nome).all()
    
    profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()
    procedimentos = Procedimento.query.filter_by(ativo=True).order_by(Procedimento.nome).all()
    
    return render_template('atendimentos/form.html', 
                         pacientes=pacientes, 
                         profissionais=profissionais, 
                         procedimentos=procedimentos)

@app.route('/atendimentos/<int:id>')
@login_required
def ver_atendimento(id):
    try:
        # Buscar atendimento com dados relacionados
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
            return redirect(url_for('atendimentos'))
            
        return render_template('atendimentos/detalhes.html', atendimento=atendimento_data)
        
    except Exception as e:
        flash(f'Erro ao buscar atendimento: {str(e)}', 'error')
        return redirect(url_for('atendimentos'))

# ==================== MÓDULO DE AGENDAMENTOS ====================

@app.route('/agendamentos')
@login_required
def agendamentos():
    data_param = request.args.get('data')
    if data_param:
        try:
            data_selecionada = datetime.strptime(data_param, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = date.today()
    else:
        data_selecionada = date.today()
    
    hoje = date.today()
    
    # Buscar agendamentos do dia selecionado
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
        # Se não conseguir fazer a query (tabelas não existem), retorna lista vazia
        agendamentos_data = []
    
    return render_template('agendamentos/lista.html',
                         agendamentos=agendamentos_data,
                         data_selecionada=data_selecionada,
                         hoje=hoje,
                         timedelta=timedelta)

@app.route('/agendamentos/novo', methods=['GET', 'POST'])
@login_required
def novo_agendamento():
    if request.method == 'POST':
        try:
            paciente_id = request.form['paciente_id']
            profissional_id = request.form['profissional_id']
            data = request.form['data']
            horario = request.form['horario']
            observacoes = request.form.get('observacoes', '')
            status = request.form.get('status', 'agendado')
            
            # Combinar data e horário
            data_hora = datetime.strptime(f"{data} {horario}", '%Y-%m-%d %H:%M')
            
            # Criar novo agendamento
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
            return redirect(url_for('agendamentos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar agendamento: {str(e)}', 'error')
    
    # GET - Exibir formulário
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    profissionais = Profissional.query.filter_by(ativo=True).order_by(Profissional.nome).all()
    
    return render_template('agendamentos/form.html', 
                         pacientes=pacientes, 
                         profissionais=profissionais)

@app.route('/agendamentos/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status_agendamento(id):
    try:
        status = request.form['status']
        agendamento = Agendamento.query.get_or_404(id)
        agendamento.status = status
        db.session.commit()
        
        flash(f'Status do agendamento atualizado para {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
    
    return redirect(url_for('agendamentos'))

# ==================== MÓDULO DE PROFISSIONAIS ====================

@app.route('/profissionais')
@login_required
def profissionais():
    search = request.args.get('search', '')
    
    query = Profissional.query
    if search:
        query = query.filter(Profissional.nome.ilike(f'%{search}%'))
    
    profissionais = query.order_by(Profissional.nome).all()
    
    return render_template('profissionais/lista.html', 
                         profissionais=profissionais, 
                         search=search)

@app.route('/profissionais/novo', methods=['GET', 'POST'])
@login_required
def cadastrar_profissional():
    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form.get('especialidade', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        
        # Verificar se já existe
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
        return redirect(url_for('profissionais'))
    
    return render_template('profissionais/form.html')

@app.route('/profissionais/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_profissional(id):
    profissional = Profissional.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form.get('especialidade', '')
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        
        # Verificar se nome já existe (exceto o atual)
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
        return redirect(url_for('profissionais'))
    
    return render_template('profissionais/form.html', profissional=profissional)

# ==================== MÓDULO DE PAGAMENTOS ====================

@app.route('/pagamentos')
@login_required
def pagamentos():
    # Por enquanto redireciona para atendimentos
    flash('Módulo de pagamentos em desenvolvimento. Use a área de atendimentos para gerenciar pagamentos.', 'info')
    return redirect(url_for('atendimentos'))

@app.route('/pagamentos/novo/<int:atendimento_id>', methods=['GET', 'POST'])
@login_required
def novo_pagamento(atendimento_id):
    if request.method == 'POST':
        try:
            valor = float(request.form['valor'])
            forma_pagamento = request.form['forma_pagamento']
            data_pagamento = datetime.strptime(request.form['data_pagamento'], '%Y-%m-%d').date()
            observacoes = request.form.get('observacoes', '')
            
            # Buscar atendimento
            atendimento = Atendimento.query.get_or_404(atendimento_id)
            
            # Calcular valores já pagos
            try:
                pagamentos_existentes = Pagamento.query.filter_by(atendimento_id=atendimento_id).all()
                valor_ja_pago = sum(float(p.valor) for p in pagamentos_existentes)
            except:
                valor_ja_pago = 0
                
            valor_pendente = float(atendimento.valor_total) - valor_ja_pago
            
            # Validações
            if valor <= 0:
                flash('O valor deve ser maior que zero!', 'error')
                raise ValueError('Valor inválido')
                
            if valor > valor_pendente:
                flash(f'O valor não pode ser maior que o pendente (R$ {valor_pendente:.2f})', 'error')
                raise ValueError('Valor maior que pendente')
                
            if not forma_pagamento:
                flash('Selecione a forma de pagamento!', 'error')
                raise ValueError('Forma de pagamento não selecionada')
            
            # Criar novo pagamento
            pagamento = Pagamento(
                atendimento_id=atendimento_id,
                valor=valor,
                forma_pagamento=forma_pagamento,
                data_pagamento=data_pagamento,
                observacoes=observacoes
            )
            
            db.session.add(pagamento)
            
            # Atualizar status do atendimento
            novo_valor_pago = valor_ja_pago + valor
            if abs(novo_valor_pago - float(atendimento.valor_total)) < 0.01:  # Considera diferenças de centavos
                atendimento.status = 'pago'
                status_msg = 'totalmente pago'
            else:
                atendimento.status = 'parcial'
                status_msg = 'parcialmente pago'
            
            db.session.commit()
            
            # Buscar dados do paciente para a mensagem
            paciente = Paciente.query.get(atendimento.paciente_id)
            
            flash(f'💰 Pagamento de R$ {valor:.2f} registrado com sucesso!', 'success')
            flash(f'📊 Atendimento de {paciente.nome} agora está {status_msg}.', 'info')
            
            # Se ainda há valor pendente significativo, oferecer continuar pagando
            valor_restante = float(atendimento.valor_total) - novo_valor_pago
            if valor_restante > 0.01:
                flash(f'💡 Valor restante: R$ {valor_restante:.2f}', 'warning')
                return redirect(url_for('novo_pagamento', atendimento_id=atendimento_id))
            else:
                return redirect(url_for('ver_atendimento', id=atendimento_id))
            
        except ValueError:
            # Erro de validação - não faz rollback
            pass
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao registrar pagamento: {str(e)}', 'error')
    
    # GET - Exibir formulário
    try:
        # Buscar atendimento com dados relacionados
        atendimento_data = db.session.query(
            Atendimento,
            Paciente.nome.label('paciente_nome'),
            Paciente.cpf.label('paciente_cpf'),
            Profissional.nome.label('profissional_nome')
        ).join(Paciente, Atendimento.paciente_id == Paciente.id)\
         .join(Profissional, Atendimento.profissional_id == Profissional.id)\
         .filter(Atendimento.id == atendimento_id).first()
        
        if not atendimento_data:
            flash('❌ Atendimento não encontrado!', 'error')
            return redirect(url_for('atendimentos'))
        
        # Calcular valores e buscar histórico de pagamentos
        try:
            pagamentos_existentes = Pagamento.query.filter_by(atendimento_id=atendimento_id)\
                                                   .order_by(Pagamento.criado_em.desc()).all()
            valor_pago = sum(float(p.valor) for p in pagamentos_existentes)
        except:
            pagamentos_existentes = []
            valor_pago = 0
            
        valor_pendente = max(0, float(atendimento_data.Atendimento.valor_total) - valor_pago)
        
        return render_template('pagamentos/form.html', 
                             atendimento=atendimento_data,
                             valor_pago=valor_pago,
                             valor_pendente=valor_pendente,
                             historico_pagamentos=pagamentos_existentes)
        
    except Exception as e:
        flash(f'❌ Erro ao buscar dados do pagamento: {str(e)}', 'error')
        return redirect(url_for('atendimentos'))

# ==================== MÓDULO DE RELATÓRIOS ====================

@app.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios/index.html')

@app.route('/relatorios/financeiro')
@login_required
def relatorio_financeiro():
    flash('Relatório financeiro em desenvolvimento', 'info')
    return redirect(url_for('relatorios'))

@app.route('/relatorios/pendencias')
@login_required
def relatorio_pendencias():
    flash('Relatório de pendências em desenvolvimento', 'info')
    return redirect(url_for('relatorios'))

@app.route('/relatorios/procedimentos')
@login_required
def relatorio_procedimentos():
    flash('Relatório de procedimentos em desenvolvimento', 'info')
    return redirect(url_for('relatorios'))

# ==================== MÓDULO DE ADMINISTRAÇÃO ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_usuarios = Usuario.query.count()
    usuarios_ativos = Usuario.query.filter_by(ativo=True).count()
    total_pacientes = Paciente.query.count()
    total_procedimentos = Procedimento.query.filter_by(ativo=True).count()
    
    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         usuarios_ativos=usuarios_ativos,
                         total_pacientes=total_pacientes,
                         total_procedimentos=total_procedimentos)

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.order_by(Usuario.username).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/backup')
@admin_required
def admin_backup():
    flash('Funcionalidade de backup em desenvolvimento', 'info')
    return redirect(url_for('admin_dashboard'))

# ==================== TRATAMENTO DE ERROS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
    
    
# ==================== ROTAS EXTRAS ====================

@app.route('/api/estatisticas')
@login_required
def api_estatisticas():
    """API para dados do dashboard em tempo real"""
    try:
        hoje = date.today()
        
        stats = {
            'pacientes_total': Paciente.query.count(),
            'atendimentos_hoje': Atendimento.query.filter_by(data_atendimento=hoje).count() if 'Atendimento' in globals() else 0,
            'agendamentos_hoje': Agendamento.query.filter(db.func.date(Agendamento.data_hora) == hoje).count() if 'Agendamento' in globals() else 0,
            'profissionais_ativos': Profissional.query.filter_by(ativo=True).count(),
            'procedimentos_ativos': Procedimento.query.filter_by(ativo=True).count(),
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/buscar-pacientes')
@login_required
def buscar_pacientes():
    """Busca rápida de pacientes para autocomplete"""
    termo = request.args.get('termo', '')
    
    if len(termo) < 2:
        return jsonify([])
    
    pacientes = Paciente.query.filter(
        db.or_(
            Paciente.nome.ilike(f'%{termo}%'),
            Paciente.cpf.ilike(f'%{termo}%')
        )
    ).limit(10).all()
    
    resultado = []
    for paciente in pacientes:
        resultado.append({
            'id': paciente.id,
            'nome': paciente.nome,
            'cpf': formatar_cpf(paciente.cpf),
            'telefone': paciente.telefone or '',
            'idade': calcular_idade(paciente.data_nascimento)
        })
    
    return jsonify(resultado)

@app.route('/verificar-disponibilidade')
@login_required
def verificar_disponibilidade():
    """Verifica disponibilidade de horário para agendamento"""
    try:
        profissional_id = request.args.get('profissional_id')
        data = request.args.get('data')
        horario = request.args.get('horario')
        
        if not all([profissional_id, data, horario]):
            return jsonify({'disponivel': True, 'mensagem': 'Dados incompletos'})
        
        data_hora = datetime.strptime(f"{data} {horario}", '%Y-%m-%d %H:%M')
        
        # Verificar se já existe agendamento neste horário
        conflito = Agendamento.query.filter_by(
            profissional_id=profissional_id,
            data_hora=data_hora,
            status='agendado'
        ).first()
        
        if conflito:
            paciente = Paciente.query.get(conflito.paciente_id)
            return jsonify({
                'disponivel': False,
                'mensagem': f'Horário ocupado por {paciente.nome}'
            })
        else:
            return jsonify({
                'disponivel': True,
                'mensagem': 'Horário disponível'
            })
            
    except Exception as e:
        return jsonify({'disponivel': True, 'mensagem': f'Erro: {str(e)}'})

@app.route('/dashboard/refresh')
@login_required
def dashboard_refresh():
    """Endpoint para atualizar dados do dashboard via AJAX"""
    try:
        hoje = date.today()
        
        # Calcular estatísticas
        stats = {
            'atendimentos_hoje': Atendimento.query.filter_by(data_atendimento=hoje).count() if 'Atendimento' in globals() else 0,
            'agendamentos_hoje': Agendamento.query.filter(db.func.date(Agendamento.data_hora) == hoje).count() if 'Agendamento' in globals() else 0,
            'valores_hoje': 0,
            'pendentes': 0
        }
        
        try:
            valores_hoje = db.session.query(db.func.sum(Atendimento.valor_total)).filter_by(data_atendimento=hoje).scalar()
            stats['valores_hoje'] = float(valores_hoje) if valores_hoje else 0
            
            pendentes = Atendimento.query.filter_by(status='pendente').count()
            stats['pendentes'] = pendentes
        except:
            pass
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_user():
    """Injeta informações do usuário em todos os templates"""
    usuario_atual = None
    if 'user_id' in session:
        try:
            usuario_atual = Usuario.query.get(session['user_id'])
        except:
            pass
    
    return dict(usuario_atual=usuario_atual)

@app.context_processor
def inject_stats():
    """Injeta estatísticas básicas em todos os templates"""
    try:
        stats = {
            'total_pacientes_global': Paciente.query.count(),
            'total_profissionais_global': Profissional.query.filter_by(ativo=True).count(),
            'sistema_versao': '1.0.0'
        }
    except:
        stats = {
            'total_pacientes_global': 0,
            'total_profissionais_global': 0,
            'sistema_versao': '1.0.0'
        }
    
    return dict(**stats)

# ==================== FILTROS JINJA PERSONALIZADOS ====================

@app.template_filter('currency')
def currency_filter(value):
    """Filtro para formatar valores monetários"""
    try:
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

@app.template_filter('phone')
def phone_filter(value):
    """Filtro para formatar telefones"""
    if not value:
        return ''
    
    # Remove caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', value)
    
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    else:
        return value

@app.template_filter('titlecase')
def titlecase_filter(value):
    """Filtro para formatar nomes próprios"""
    if not value:
        return ''
    
    # Palavras que não devem ser capitalizadas
    prepositions = ['de', 'da', 'do', 'dos', 'das', 'e', 'em', 'na', 'no', 'para', 'por']
    
    words = value.lower().split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0 or word not in prepositions:
            result.append(word.capitalize())
        else:
            result.append(word)
    
    return ' '.join(result)  
    
    
  
    

if __name__ == '__main__':
    print("🏥 Iniciando Sistema Clínica Estética")
    print("=" * 50)
    
    # Mostrar configurações (mascarando senha)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
    print(f"Database URL: {masked_url}")
    
    # Tentar inicializar o banco
    print("🔄 Inicializando banco de dados...")
    if criar_tabelas():
        print("🚀 Servidor iniciado em: http://localhost:5000")
        print("👤 Login: admin | Senha: admin123")
        print("🧪 Teste: http://localhost:5000/test")
        print("")
        app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', host='0.0.0.0', port=5000)
    else:
        print("❌ Não foi possível iniciar o servidor")
        print("🔧 Execute os comandos de configuração do PostgreSQL novamente")