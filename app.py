from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configurações de segurança
DATA_DIR = os.path.abspath('data')
PACIENTES_FILE = os.path.join(DATA_DIR, 'pacientes.json')
ATENDIMENTOS_FILE = os.path.join(DATA_DIR, 'atendimentos.json')
PROCEDIMENTOS_FILE = os.path.join(DATA_DIR, 'procedimentos.json')
VENDAS_FILE = os.path.join(DATA_DIR, 'vendas.json')
USUARIOS_FILE = os.path.join(DATA_DIR, 'usuarios.json')
ANAMNESE_FILE = os.path.join(DATA_DIR, 'anamnese.json')

# Criar diretório de dados se não existir
os.makedirs(DATA_DIR, exist_ok=True)

# Validações e sanitização
def sanitize_input(data):
    """Remove caracteres perigosos e limita tamanho"""
    if isinstance(data, str):
        # Remove caracteres de controle e limita tamanho
        data = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', data)
        return data[:1000]  # Limita a 1000 caracteres
    return data

def validate_cpf(cpf):
    """Valida formato do CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return len(cpf) == 11 and cpf.isdigit()

def validate_date(date_str):
    """Valida formato de data DD/MM/AAAA"""
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def validate_phone(phone):
    """Valida formato do telefone"""
    phone = re.sub(r'[^0-9]', '', phone)
    return len(phone) >= 10 and len(phone) <= 11

# Funções de arquivo seguras
def load_json_file(filename):
    """Carrega arquivo JSON de forma segura"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        return []
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return []

def save_json_file(filename, data):
    """Salva arquivo JSON de forma segura"""
    try:
        # Backup do arquivo atual
        if os.path.exists(filename):
            backup_name = f"{filename}.backup"
            with open(filename, 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
        
        # Salva novo arquivo
        temp_filename = f"{filename}.tmp"
        with open(temp_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Move arquivo temporário para destino final
        os.replace(temp_filename, filename)
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo {filename}: {e}")
        return False

# Inicializar arquivos de dados
def init_data_files():
    """Inicializa arquivos de dados com estruturas padrão"""
    
    # Procedimentos padrão
    procedimentos_padrao = [
        {"id": 1, "nome": "Limpeza de Pele"},
        {"id": 2, "nome": "Peeling Químico"},
        {"id": 3, "nome": "Microagulhamento"},
        {"id": 4, "nome": "Toxina Botulínica"},
        {"id": 5, "nome": "Preenchimento Facial"},
        {"id": 6, "nome": "Laser"},
        {"id": 7, "nome": "Radiofrequência"},
        {"id": 8, "nome": "Ultrassom Microfocado"},
        {"id": 9, "nome": "Carboxiterapia"},
        {"id": 10, "nome": "Drenagem Linfática"},
        {"id": 11, "nome": "Massagem Modeladora"},
        {"id": 12, "nome": "Criolipólise"},
        {"id": 13, "nome": "Depilação a Laser"}
    ]
    
    # Usuário padrão (senha: admin123)
    usuarios_padrao = [{
        "id": 1,
        "email": "admin@admin.com",
        "password_hash": generate_password_hash("admin123"),
        "perfil": "admin",
        "created_at": datetime.now().isoformat()
    }]
    
    if not os.path.exists(PROCEDIMENTOS_FILE):
        save_json_file(PROCEDIMENTOS_FILE, procedimentos_padrao)
    
    if not os.path.exists(USUARIOS_FILE):
        save_json_file(USUARIOS_FILE, usuarios_padrao)
    else:
        # Migração de senhas antigas (se necessário)
        migrate_passwords()

    # Inicializar outros arquivos vazios
    for filename in [PACIENTES_FILE, ATENDIMENTOS_FILE, VENDAS_FILE, ANAMNESE_FILE]:
        if not os.path.exists(filename):
            save_json_file(filename, [])

def migrate_passwords():
    """Migra senhas de hashlib para werkzeug.security"""
    usuarios = load_json_file(USUARIOS_FILE)
    updated = False
    for usuario in usuarios:
        # Hashes Werkzeug começam com 'pbkdf2:sha256' ou similar.
        # Hashes SHA256 puros são hex de 64 caracteres.
        if 'password_hash' in usuario and not usuario['password_hash'].startswith('pbkdf2'):
            # Esta é uma suposição perigosa. Não sabemos a senha original.
            # Esta migração só funcionará se a senha for conhecida ou
            # se for resetada. Para o caso do 'admin123', podemos fazer.
            if usuario['email'] == 'admin@admin.com':
                usuario['password_hash'] = generate_password_hash("admin123")
                updated = True

    if updated:
        save_json_file(USUARIOS_FILE, usuarios)
        print("Migração de senhas concluída.")

# Autenticação simples
def check_auth(email, password):
    """Verifica credenciais do usuário e retorna o perfil"""
    usuarios = load_json_file(USUARIOS_FILE)
    
    for usuario in usuarios:
        if usuario.get('email') == email and check_password_hash(usuario.get('password_hash', ''), password):
            # Adicionado .get('ativo', True) para garantir que usuários desativados não possam logar
            if usuario.get('ativo', True):
                return usuario.get('perfil', 'usuario')
    return None

def requires_auth(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in request.cookies:
            flash('Você precisa estar logado para acessar esta página.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def requires_admin(f):
    """Decorator para rotas que requerem perfil de admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        perfil = request.cookies.get('perfil')
        if perfil != 'admin':
            flash('Acesso não autorizado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# Rotas
@app.route('/')
def login():
    """Página de login"""
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    """Processa login"""
    email = sanitize_input(request.form.get('email', ''))
    password = sanitize_input(request.form.get('password', ''))
    
    perfil = check_auth(email, password)
    if perfil:
        response = redirect(url_for('dashboard'))
        response.set_cookie('logged_in', 'true', max_age=86400)  # 24 horas
        response.set_cookie('perfil', perfil, max_age=86400)
        return response
    else:
        flash('Credenciais inválidas')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout do usuário"""
    response = redirect(url_for('login'))
    response.delete_cookie('logged_in')
    return response

@app.route('/dashboard')
@requires_auth
def dashboard():
    """Dashboard principal"""
    pacientes = load_json_file(PACIENTES_FILE)
    atendimentos = load_json_file(ATENDIMENTOS_FILE)
    vendas = load_json_file(VENDAS_FILE)
    perfil = request.cookies.get('perfil')
    
    # Estatísticas do dia
    hoje = datetime.now().strftime('%d/%m/%Y')
    atendimentos_hoje = [a for a in atendimentos if a.get('data') == hoje]
    vendas_hoje = [v for v in vendas if v.get('data') == hoje]
    valor_vendas_hoje = sum(float(v.get('valor', 0)) for v in vendas_hoje)
    
    stats = {
        'total_pacientes': len(pacientes),
        'atendimentos_hoje': len(atendimentos_hoje),
        'vendas_hoje': f"R$ {valor_vendas_hoje:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'proximos_atendimentos': 3  # Placeholder
    }
    
    return render_template('dashboard.html', stats=stats, perfil=perfil)

@app.route('/pacientes')
@requires_auth
def pacientes():
    """Lista de pacientes com busca"""
    query = request.args.get('q', '').lower()
    pacientes_data = load_json_file(PACIENTES_FILE)

    if query:
        pacientes_filtrados = [
            p for p in pacientes_data if
            query in p.get('nome', '').lower() or
            query in p.get('cpf', '') or
            query in p.get('codigo', '').lower()
        ]
    else:
        pacientes_filtrados = pacientes_data

    return render_template('pacientes.html', pacientes=pacientes_filtrados)

@app.route('/paciente/novo')
@requires_auth
def novo_paciente():
    """Formulário de novo paciente"""
    return render_template('novo_paciente.html')

@app.route('/paciente/salvar', methods=['POST'])
@requires_auth
def salvar_paciente():
    """Salva novo paciente"""
    try:
        # Validação e sanitização
        nome = sanitize_input(request.form.get('nome', ''))
        cpf = sanitize_input(request.form.get('cpf', ''))
        data_nascimento = sanitize_input(request.form.get('data_nascimento', ''))
        telefone = sanitize_input(request.form.get('telefone', ''))
        gosto_musical = sanitize_input(request.form.get('gosto_musical', ''))
        observacoes = sanitize_input(request.form.get('observacoes', ''))
        
        # Validações
        if not nome or len(nome) < 2:
            flash('Nome deve ter pelo menos 2 caracteres')
            return redirect(url_for('novo_paciente'))
        
        if not validate_cpf(cpf):
            flash('CPF inválido')
            return redirect(url_for('novo_paciente'))
        
        if not validate_date(data_nascimento):
            flash('Data de nascimento inválida (use DD/MM/AAAA)')
            return redirect(url_for('novo_paciente'))
        
        if not validate_phone(telefone):
            flash('Telefone inválido')
            return redirect(url_for('novo_paciente'))
        
        # Carregar pacientes existentes
        pacientes = load_json_file(PACIENTES_FILE)
        
        # Verificar CPF duplicado
        for paciente in pacientes:
            if paciente['cpf'] == cpf:
                flash('CPF já cadastrado')
                return redirect(url_for('novo_paciente'))
        
        # Gerar novo ID e código de paciente
        novo_id = max([p.get('id', 0) for p in pacientes], default=0) + 1
        codigo_paciente = f"PAC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"

        # Criar novo paciente
        novo_paciente = {
            'id': novo_id,
            'codigo': codigo_paciente,
            'nome': nome,
            'cpf': cpf,
            'data_nascimento': data_nascimento,
            'telefone': telefone,
            'gosto_musical': gosto_musical,
            'observacoes': observacoes,
            'created_at': datetime.now().isoformat()
        }
        
        pacientes.append(novo_paciente)
        
        if save_json_file(PACIENTES_FILE, pacientes):
            flash('Paciente cadastrado com sucesso!')
        else:
            flash('Erro ao salvar paciente')
        
        return redirect(url_for('pacientes'))
        
    except Exception as e:
        flash('Erro interno do servidor')
        return redirect(url_for('novo_paciente'))

@app.route('/paciente/editar/<int:id>')
@requires_auth
def editar_paciente(id):
    """Página de edição de paciente"""
    pacientes = load_json_file(PACIENTES_FILE)
    paciente = next((p for p in pacientes if p['id'] == id), None)
    if paciente:
        return render_template('editar_paciente.html', paciente=paciente)
    else:
        flash('Paciente não encontrado')
        return redirect(url_for('pacientes'))

@app.route('/paciente/atualizar/<int:id>', methods=['POST'])
@requires_auth
def atualizar_paciente(id):
    """Atualiza dados do paciente"""
    try:
        nome = sanitize_input(request.form.get('nome', ''))
        cpf = sanitize_input(request.form.get('cpf', ''))
        data_nascimento = sanitize_input(request.form.get('data_nascimento', ''))
        telefone = sanitize_input(request.form.get('telefone', ''))
        gosto_musical = sanitize_input(request.form.get('gosto_musical', ''))
        observacoes = sanitize_input(request.form.get('observacoes', ''))

        # Validações
        if not nome or len(nome) < 2:
            flash('Nome deve ter pelo menos 2 caracteres', 'danger')
            return redirect(url_for('editar_paciente', id=id))

        if not validate_cpf(cpf):
            flash('CPF inválido', 'danger')
            return redirect(url_for('editar_paciente', id=id))

        if not validate_date(data_nascimento):
            flash('Data de nascimento inválida (use DD/MM/AAAA)', 'danger')
            return redirect(url_for('editar_paciente', id=id))

        if not validate_phone(telefone):
            flash('Telefone inválido', 'danger')
            return redirect(url_for('editar_paciente', id=id))

        pacientes = load_json_file(PACIENTES_FILE)

        # Verificar CPF duplicado (ignorando o próprio paciente)
        for p in pacientes:
            if p['cpf'] == cpf and p['id'] != id:
                flash('CPF já cadastrado para outro paciente.', 'danger')
                return redirect(url_for('editar_paciente', id=id))

        for paciente in pacientes:
            if paciente['id'] == id:
                paciente['nome'] = nome
                paciente['cpf'] = cpf
                paciente['data_nascimento'] = data_nascimento
                paciente['telefone'] = telefone
                paciente['gosto_musical'] = gosto_musical
                paciente['observacoes'] = observacoes
                break

        if save_json_file(PACIENTES_FILE, pacientes):
            flash('Paciente atualizado com sucesso!', 'success')
        else:
            flash('Erro ao atualizar paciente', 'danger')

        return redirect(url_for('pacientes'))

    except Exception as e:
        flash('Erro interno do servidor', 'danger')
        return redirect(url_for('editar_paciente', id=id))

@app.route('/atendimento/novo')
@requires_auth
def novo_atendimento():
    """Formulário de novo atendimento"""
    pacientes = load_json_file(PACIENTES_FILE)
    procedimentos = load_json_file(PROCEDIMENTOS_FILE)
    return render_template('novo_atendimento.html', pacientes=pacientes, procedimentos=procedimentos)

@app.route('/atendimento/salvar', methods=['POST'])
@requires_auth
def salvar_atendimento():
    """Salva novo atendimento"""
    try:
        # CORREÇÃO: Validar paciente_id antes de converter para int
        paciente_id_str = sanitize_input(request.form.get('paciente_id'))
        if not paciente_id_str or not paciente_id_str.isdigit():
            flash('Selecione um paciente válido.', 'danger')
            return redirect(url_for('novo_atendimento'))
        paciente_id = int(paciente_id_str)

        data_atendimento = sanitize_input(request.form.get('data_atendimento', ''))
        procedimentos_selecionados_str = request.form.get('procedimentos_selecionados', '[]')
        atendimento_relato = sanitize_input(request.form.get('atendimento', ''))
        valor_total_str = sanitize_input(request.form.get('valor_total', 'R$ 0,00'))
        desconto_str = sanitize_input(request.form.get('desconto', '0,00'))

        procedimentos_selecionados = json.loads(procedimentos_selecionados_str)
        valor_total = float(valor_total_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
        desconto = float(desconto_str.replace(',', '.'))
        
        pacientes = load_json_file(PACIENTES_FILE)
        paciente_existe = any(p['id'] == paciente_id for p in pacientes)
        
        if not paciente_existe:
            flash('Paciente não encontrado')
            return redirect(url_for('novo_atendimento'))
        
        atendimentos = load_json_file(ATENDIMENTOS_FILE)
        novo_id = max([a.get('id', 0) for a in atendimentos], default=0) + 1
        
        novo_atendimento = {
            'id': novo_id,
            'paciente_id': paciente_id,
            'data': data_atendimento,
            'procedimentos': procedimentos_selecionados,
            'atendimento': atendimento_relato,
            'valor_total': valor_total,
            'created_at': datetime.now().isoformat()
        }
        
        atendimentos.append(novo_atendimento)
        
        if save_json_file(ATENDIMENTOS_FILE, atendimentos):
            flash('Atendimento registrado com sucesso!')
        else:
            flash('Erro ao salvar atendimento')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Erro interno do servidor: {e}')
        return redirect(url_for('novo_atendimento'))

@app.route('/procedimentos')
@requires_auth
def procedimentos():
    """Lista de procedimentos"""
    procedimentos_data = load_json_file(PROCEDIMENTOS_FILE)
    return render_template('procedimentos.html', procedimentos=procedimentos_data)

@app.route('/procedimentos/salvar', methods=['POST'])
@requires_auth
def salvar_procedimento():
    """Salva novo ou edita procedimento"""
    procedimentos = load_json_file(PROCEDIMENTOS_FILE)
    procedimento_id = request.form.get('id')
    nome = request.form.get('nome')
    valor = request.form.get('valor')

    if procedimento_id:  # Edição
        for p in procedimentos:
            if str(p.get('id')) == procedimento_id:
                p['nome'] = nome
                p['valor'] = valor
                break
    else:  # Adição
        new_id = max([p.get('id', 0) for p in procedimentos], default=0) + 1
        new_proc = {
            'id': new_id,
            'nome': nome,
            'valor': valor
        }
        procedimentos.append(new_proc)

    save_json_file(PROCEDIMENTOS_FILE, procedimentos)
    flash('Procedimento salvo com sucesso!', 'success')
    return redirect(url_for('procedimentos'))

@app.route('/procedimentos/editar/<int:id>')
@requires_auth
def editar_procedimento(id):
    """Página de edição de procedimento"""
    procedimentos = load_json_file(PROCEDIMENTOS_FILE)
    procedimento_para_editar = next((p for p in procedimentos if p['id'] == id), None)
    return render_template('procedimentos.html', procedimentos=procedimentos, procedimento_para_editar=procedimento_para_editar)

@app.route('/procedimentos/excluir/<int:id>')
@requires_auth
def excluir_procedimento(id):
    """Exclui um procedimento"""
    procedimentos = load_json_file(PROCEDIMENTOS_FILE)
    procedimentos = [p for p in procedimentos if p.get('id') != id]
    save_json_file(PROCEDIMENTOS_FILE, procedimentos)
    flash('Procedimento excluído com sucesso!', 'success')
    return redirect(url_for('procedimentos'))

@app.route('/relatorio')
@requires_auth
def relatorio():
    """Página de relatório de atendimentos"""
    pacientes = load_json_file(PACIENTES_FILE)
    selected_patient_id = request.args.get('paciente_id', type=int)
    atendimentos = []
    selected_patient = None

    if selected_patient_id:
        all_atendimentos = load_json_file(ATENDIMENTOS_FILE)
        atendimentos = [a for a in all_atendimentos if a.get('paciente_id') == selected_patient_id]
        selected_patient = next((p for p in pacientes if p['id'] == selected_patient_id), None)

    return render_template('relatorio.html',
                           pacientes=pacientes,
                           atendimentos=atendimentos,
                           selected_patient_id=selected_patient_id,
                           selected_patient=selected_patient)

@app.context_processor
def utility_processors():
    """Fornece funções utilitárias para os templates."""
    def get_procedimento_by_id(proc_id):
        procedimentos = load_json_file(PROCEDIMENTOS_FILE)
        return next((p for p in procedimentos if p.get('id') == proc_id), None)

    def get_patient_by_id(patient_id):
        pacientes = load_json_file(PACIENTES_FILE)
        return next((p for p in pacientes if p.get('id') == patient_id), None)

    return dict(
        get_procedimento_by_id=get_procedimento_by_id,
        get_patient_by_id=get_patient_by_id
    )

@app.route('/anamnese', methods=['GET'])
@requires_auth
def anamnese():
    """Página de anamnese"""
    pacientes = load_json_file(PACIENTES_FILE)
    return render_template('anamnese.html', pacientes=pacientes)

@app.route('/salvar_anamnese', methods=['POST'])
@requires_auth
def salvar_anamnese():
    """Salva a anamnese"""
    try:
        paciente_id = int(request.form.get('paciente_id'))
        if not paciente_id:
            flash('Selecione um paciente.', 'danger')
            return redirect(url_for('anamnese'))

        anamnese_data = {
            'paciente_id': paciente_id,
            'queixa_principal': sanitize_input(request.form.get('queixa_principal')),
            'historia_doenca': sanitize_input(request.form.get('historia_doenca')),
            'antecedentes_pessoais': sanitize_input(request.form.get('antecedentes_pessoais')),
            'antecedentes_familiares': sanitize_input(request.form.get('antecedentes_familiares')),
            'habitos_vida': sanitize_input(request.form.get('habitos_vida')),
            'exame_fisico': sanitize_input(request.form.get('exame_fisico')),
            'created_at': datetime.now().isoformat()
        }

        anamneses = load_json_file(ANAMNESE_FILE)

        # Opcional: em vez de adicionar uma nova, poderia atualizar uma existente
        # Por simplicidade, vamos sempre adicionar uma nova.

        novo_id = max([a.get('id', 0) for a in anamneses], default=0) + 1
        anamnese_data['id'] = novo_id

        anamneses.append(anamnese_data)

        if save_json_file(ANAMNESE_FILE, anamneses):
            flash('Anamnese salva com sucesso!', 'success')
        else:
            flash('Erro ao salvar anamnese.', 'danger')

        return redirect(url_for('dashboard'))

    except (ValueError, TypeError):
        flash('ID de paciente inválido.', 'danger')
        return redirect(url_for('anamnese'))
    except Exception as e:
        flash(f'Erro interno do servidor: {e}', 'danger')
        return redirect(url_for('anamnese'))

@app.route('/venda/nova', methods=['GET', 'POST'])
@requires_auth
def nova_venda():
    """Formulário de nova venda"""
    pacientes = load_json_file(PACIENTES_FILE)
    selected_patient_id_str = request.args.get('paciente_id')
    atendimentos = []
    selected_patient_id = None

    # CORREÇÃO: Validar se o ID do paciente existe e é um dígito
    if selected_patient_id_str and selected_patient_id_str.isdigit():
        try:
            selected_patient_id = int(selected_patient_id_str)
            all_atendimentos = load_json_file(ATENDIMENTOS_FILE)
            atendimentos = [a for a in all_atendimentos if a.get('paciente_id') == selected_patient_id and a.get('status_pagamento') != 'pago']
        except (ValueError, TypeError):
            flash('ID de paciente inválido.')
            selected_patient_id = None

    return render_template('nova_venda.html',
                           pacientes=pacientes,
                           atendimentos=atendimentos,
                           selected_patient_id=selected_patient_id)

@app.route('/venda/salvar', methods=['POST'])
@requires_auth
def salvar_venda():
    """Salva nova venda"""
    try:
        # CORREÇÃO: Validar atendimento_id antes de converter para int
        atendimento_id_str = request.form.get('atendimento_id')
        if not atendimento_id_str or not atendimento_id_str.isdigit():
            flash('Nenhum atendimento foi selecionado ou o valor é inválido.', 'danger')
            return redirect(url_for('nova_venda'))
        atendimento_id = int(atendimento_id_str)

        pagamentos_json = request.form.get('pagamentos_json', '[]')
        pagamentos = json.loads(pagamentos_json)
        valor_restante = float(request.form.get('valor_restante', '0.0').replace('R$', '').replace('.', '').replace(',', '.'))

        vendas = load_json_file(VENDAS_FILE)
        atendimentos = load_json_file(ATENDIMENTOS_FILE)

        atendimento = next((a for a in atendimentos if a['id'] == atendimento_id), None)
        if not atendimento:
            flash('Atendimento não encontrado!')
            return redirect(url_for('nova_venda'))

        novo_id = max([v.get('id', 0) for v in vendas], default=0) + 1
        nova_venda = {
            'id': novo_id,
            'atendimento_id': atendimento_id,
            'paciente_id': atendimento['paciente_id'],
            'pagamentos': pagamentos,
            'valor_total': atendimento['valor_total'],
            'valor_restante': valor_restante,
            'status': 'pendente' if valor_restante > 0 else 'pago',
            'created_at': datetime.now().isoformat()
        }
        vendas.append(nova_venda)

        atendimento['status_pagamento'] = 'pago' if valor_restante == 0 else 'parcial'
        save_json_file(ATENDIMENTOS_FILE, atendimentos)
        save_json_file(VENDAS_FILE, vendas)

        flash('Pagamento registrado com sucesso!')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Erro interno do servidor: {e}')
        return redirect(url_for('nova_venda'))

@app.route('/pagamentos_pendentes')
@requires_auth
def pagamentos_pendentes():
    """Página de pagamentos pendentes"""
    query = request.args.get('q', '').lower()
    vendas = load_json_file(VENDAS_FILE)
    pacientes = load_json_file(PACIENTES_FILE)

    pendentes = [v for v in vendas if v.get('status') == 'pendente']

    if query:
        pendentes = [v for v in pendentes if query in get_patient_by_id(v.get('paciente_id')).get('nome', '').lower()]

    return render_template('pagamentos_pendentes.html', vendas=pendentes)

@app.route('/pagamento/finalizar/<int:id>', methods=['GET', 'POST'])
@requires_auth
def finalizar_pagamento(id):
    """Página para finalizar pagamento"""
    vendas = load_json_file(VENDAS_FILE)
    venda = next((v for v in vendas if v['id'] == id), None)

    if not venda:
        flash('Venda não encontrada!')
        return redirect(url_for('pagamentos_pendentes'))

    if request.method == 'POST':
        # Lógica para adicionar mais pagamentos e finalizar a venda
        pagamentos_json = request.form.get('pagamentos_json', '[]')
        novos_pagamentos = json.loads(pagamentos_json)
        venda['pagamentos'].extend(novos_pagamentos)

        total_pago = sum(p['valor'] for p in venda['pagamentos'])
        venda['valor_restante'] = venda['valor_total'] - total_pago

        if venda['valor_restante'] <= 0:
            venda['status'] = 'pago'
            atendimentos = load_json_file(ATENDIMENTOS_FILE)
            atendimento = next((a for a in atendimentos if a['id'] == venda['atendimento_id']), None)
            if atendimento:
                atendimento['status_pagamento'] = 'pago'
                save_json_file(ATENDIMENTOS_FILE, atendimentos)

        save_json_file(VENDAS_FILE, vendas)
        flash('Pagamento atualizado com sucesso!')
        return redirect(url_for('pagamentos_pendentes'))

    return render_template('finalizar_pagamento.html', venda=venda)


@app.route('/manutencao')
@requires_auth
@requires_admin
def manutencao():
    """Página de manutenção"""
    return render_template('manutencao.html')

@app.route('/registros_sistema')
@requires_auth
@requires_admin
def registros_sistema():
    """Página de registros do sistema"""
    vendas = load_json_file(VENDAS_FILE)
    atendimentos = load_json_file(ATENDIMENTOS_FILE)
    return render_template('registros.html', vendas=vendas, atendimentos=atendimentos)

@app.route('/registros/excluir/<string:tipo>/<int:id>', methods=['POST'])
@requires_auth
@requires_admin
def excluir_registro(tipo, id):
    """Exclui um registro do sistema"""
    password = request.form.get('password')
    admin_user = next((u for u in load_json_file(USUARIOS_FILE) if u.get('perfil') == 'admin'), None)

    if not admin_user or not check_auth(admin_user['email'], password):
        flash('Senha incorreta!', 'danger')
        return redirect(url_for('registros_sistema'))

    if tipo == 'venda':
        vendas = load_json_file(VENDAS_FILE)
        vendas = [v for v in vendas if v.get('id') != id]
        if save_json_file(VENDAS_FILE, vendas):
            flash('Venda excluída com sucesso!', 'success')
        else:
            flash('Erro ao excluir venda.', 'danger')
    elif tipo == 'atendimento':
        atendimentos = load_json_file(ATENDIMENTOS_FILE)
        atendimentos = [a for a in atendimentos if a.get('id') != id]
        if save_json_file(ATENDIMENTOS_FILE, atendimentos):
            flash('Atendimento excluído com sucesso!', 'success')
        else:
            flash('Erro ao excluir atendimento.', 'danger')

    return redirect(url_for('registros_sistema'))

# Rota para a página de manutenção de usuários
@app.route('/manutencao/usuarios')
@requires_auth
@requires_admin
def manutencao_usuarios():
    """Página de manutenção de usuários"""
    usuarios = load_json_file(USUARIOS_FILE)
    return render_template('manutencao_usuarios.html', usuarios=usuarios)

# Rota para salvar (adicionar/editar) um usuário
@app.route('/manutencao/usuarios/salvar', methods=['POST'])
@requires_auth
@requires_admin
def salvar_usuario():
    """Salva (adiciona/edita) um usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    user_id = request.form.get('id')
    email = request.form.get('email')
    password = request.form.get('password')
    perfil = request.form.get('perfil')

    if user_id:  # Edição
        for usuario in usuarios:
            if str(usuario.get('id')) == user_id:
                usuario['email'] = email
                if password:
                    usuario['password_hash'] = generate_password_hash(password)
                usuario['perfil'] = perfil
                break
    else:  # Adição
        if not password:
            flash('Senha é obrigatória para novos usuários.', 'danger')
            return redirect(url_for('manutencao_usuarios'))

        new_id = max([u.get('id', 0) for u in usuarios], default=0) + 1
        new_user = {
            'id': new_id,
            'email': email,
            'password_hash': generate_password_hash(password),
            'perfil': perfil,
            'ativo': True,
            'created_at': datetime.now().isoformat()
        }
        usuarios.append(new_user)

    if save_json_file(USUARIOS_FILE, usuarios):
        flash('Usuário salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar usuário.', 'danger')
    return redirect(url_for('manutencao_usuarios'))

# Rota para editar um usuário
@app.route('/manutencao/usuarios/editar/<int:id>')
@requires_auth
@requires_admin
def editar_usuario(id):
    """Página de edição de usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    usuario_para_editar = next((u for u in usuarios if u.get('id') == id), None)
    return render_template('manutencao_usuarios.html', usuarios=usuarios, usuario_para_editar=usuario_para_editar)

# Rota para desativar um usuário
@app.route('/manutencao/usuarios/desativar/<int:id>')
@requires_auth
@requires_admin
def desativar_usuario(id):
    """Desativa um usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    for usuario in usuarios:
        if usuario.get('id') == id:
            usuario['ativo'] = False
            break
    save_json_file(USUARIOS_FILE, usuarios)
    flash('Usuário desativado com sucesso!', 'success')
    return redirect(url_for('manutencao_usuarios'))

# Rota para ativar um usuário
@app.route('/manutencao/usuarios/ativar/<int:id>')
@requires_auth
@requires_admin
def ativar_usuario(id):
    """Ativa um usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    for usuario in usuarios:
        if usuario.get('id') == id:
            usuario['ativo'] = True
            break
    save_json_file(USUARIOS_FILE, usuarios)
    flash('Usuário ativado com sucesso!', 'success')
    return redirect(url_for('manutencao_usuarios'))

# Rota para excluir um usuário
@app.route('/manutencao/usuarios/excluir/<int:id>')
@requires_auth
@requires_admin
def excluir_usuario(id):
    """Exclui um usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    usuarios = [u for u in usuarios if u.get('id') != id]
    save_json_file(USUARIOS_FILE, usuarios)
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('manutencao_usuarios'))

if __name__ == '__main__':
    init_data_files()
    app.run(debug=True, host='0.0.0.0', port=5000)
