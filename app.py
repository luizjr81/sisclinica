from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime
import hashlib
import secrets
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configurações de segurança
DATA_DIR = 'data'
PACIENTES_FILE = os.path.join(DATA_DIR, 'pacientes.json')
ATENDIMENTOS_FILE = os.path.join(DATA_DIR, 'atendimentos.json')
PROCEDIMENTOS_FILE = os.path.join(DATA_DIR, 'procedimentos.json')
VENDAS_FILE = os.path.join(DATA_DIR, 'vendas.json')
USUARIOS_FILE = os.path.join(DATA_DIR, 'usuarios.json')

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
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "created_at": datetime.now().isoformat()
    }]
    
    if not os.path.exists(PROCEDIMENTOS_FILE):
        save_json_file(PROCEDIMENTOS_FILE, procedimentos_padrao)
    
    if not os.path.exists(USUARIOS_FILE):
        save_json_file(USUARIOS_FILE, usuarios_padrao)
    
    # Inicializar outros arquivos vazios
    for filename in [PACIENTES_FILE, ATENDIMENTOS_FILE, VENDAS_FILE]:
        if not os.path.exists(filename):
            save_json_file(filename, [])

# Autenticação simples
def check_auth(email, password):
    """Verifica credenciais do usuário"""
    usuarios = load_json_file(USUARIOS_FILE)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    for usuario in usuarios:
        if usuario['email'] == email and usuario['password_hash'] == password_hash:
            return True
    return False

def requires_auth(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in request.cookies:
            return redirect(url_for('login'))
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
    
    if check_auth(email, password):
        response = redirect(url_for('dashboard'))
        response.set_cookie('logged_in', 'true', max_age=86400)  # 24 horas
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
    
    return render_template('dashboard.html', stats=stats)

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

        if not nome or len(nome) < 2:
            flash('Nome deve ter pelo menos 2 caracteres')
            return redirect(url_for('editar_paciente', id=id))

        pacientes = load_json_file(PACIENTES_FILE)
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
            flash('Paciente atualizado com sucesso!')
        else:
            flash('Erro ao atualizar paciente')

        return redirect(url_for('pacientes'))

    except Exception as e:
        flash('Erro interno do servidor')
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
        paciente_id = int(sanitize_input(request.form.get('paciente_id', 0)))
        data_atendimento = sanitize_input(request.form.get('data_atendimento', ''))
        procedimentos_selecionados_str = request.form.get('procedimentos_selecionados', '[]')
        atendimento_relato = sanitize_input(request.form.get('atendimento', ''))
        valor_total_str = sanitize_input(request.form.get('valor_total', 'R$ 0,00'))

        procedimentos_selecionados = json.loads(procedimentos_selecionados_str)
        valor_total = float(valor_total_str.replace('R$', '').replace('.', '').replace(',', '.').strip())

        if paciente_id <= 0:
            flash('Selecione um paciente válido')
            return redirect(url_for('novo_atendimento'))
        
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

@app.route('/venda/nova')
@requires_auth
def nova_venda():
    """Formulário de nova venda"""
    return render_template('nova_venda.html')

@app.route('/venda/salvar', methods=['POST'])
@requires_auth
def salvar_venda():
    """Salva nova venda"""
    try:
        data_atendimento = sanitize_input(request.form.get('data_atendimento', ''))
        valor_bruto = sanitize_input(request.form.get('valor_bruto', ''))
        forma_pagamento = sanitize_input(request.form.get('forma_pagamento', ''))
        observacoes = sanitize_input(request.form.get('observacoes', ''))
        
        # Validations
        if not validate_date(data_atendimento):
            flash('Data inválida (use DD/MM/AAAA)')
            return redirect(url_for('nova_venda'))
        
        try:
            valor = float(valor_bruto.replace('R$', '').replace('.', '').replace(',', '.').strip())
            if valor <= 0:
                raise ValueError()
        except ValueError:
            flash('Valor inválido')
            return redirect(url_for('nova_venda'))
        
        if forma_pagamento not in ['pix', 'debito', 'credito', 'especie', 'transferencia']:
            flash('Forma de pagamento inválida')
            return redirect(url_for('nova_venda'))
        
        # Carregar vendas
        vendas = load_json_file(VENDAS_FILE)
        
        # Gerar novo ID
        novo_id = max([v.get('id', 0) for v in vendas], default=0) + 1
        
        # Criar nova venda
        nova_venda = {
            'id': novo_id,
            'data': data_atendimento,
            'valor': valor,
            'forma_pagamento': forma_pagamento,
            'observacoes': observacoes,
            'created_at': datetime.now().isoformat()
        }
        
        vendas.append(nova_venda)
        
        if save_json_file(VENDAS_FILE, vendas):
            flash('Venda registrada com sucesso!')
        else:
            flash('Erro ao salvar venda')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash('Erro interno do servidor')
        return redirect(url_for('nova_venda'))

# Rota para a página de manutenção de usuários
@app.route('/manutencao/usuarios')
@requires_auth
def manutencao_usuarios():
    usuarios = load_json_file(USUARIOS_FILE)
    return render_template('manutencao_usuarios.html', usuarios=usuarios)

# Rota para salvar (adicionar/editar) um usuário
@app.route('/manutencao/usuarios/salvar', methods=['POST'])
@requires_auth
def salvar_usuario():
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
                    usuario['password_hash'] = hashlib.sha256(password.encode()).hexdigest()
                usuario['perfil'] = perfil
                break
    else:  # Adição
        new_id = max([u.get('id', 0) for u in usuarios], default=0) + 1
        new_user = {
            'id': new_id,
            'email': email,
            'password_hash': hashlib.sha256(password.encode()).hexdigest(),
            'perfil': perfil,
            'ativo': True,
            'created_at': datetime.now().isoformat()
        }
        usuarios.append(new_user)

    save_json_file(USUARIOS_FILE, usuarios)
    flash('Usuário salvo com sucesso!', 'success')
    return redirect(url_for('manutencao_usuarios'))

# Rota para editar um usuário
@app.route('/manutencao/usuarios/editar/<int:id>')
@requires_auth
def editar_usuario(id):
    usuarios = load_json_file(USUARIOS_FILE)
    usuario_para_editar = None
    for usuario in usuarios:
        if usuario.get('id') == id:
            usuario_para_editar = usuario
            break

    return render_template('manutencao_usuarios.html', usuarios=usuarios, usuario_para_editar=usuario_para_editar)

# Rota para desativar um usuário
@app.route('/manutencao/usuarios/desativar/<int:id>')
@requires_auth
def desativar_usuario(id):
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
def ativar_usuario(id):
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
def excluir_usuario(id):
    usuarios = load_json_file(USUARIOS_FILE)
    usuarios = [u for u in usuarios if u.get('id') != id]
    save_json_file(USUARIOS_FILE, usuarios)
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('manutencao_usuarios'))

if __name__ == '__main__':
    init_data_files()
    app.run(debug=True, host='0.0.0.0', port=5000)
