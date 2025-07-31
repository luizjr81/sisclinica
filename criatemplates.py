#!/usr/bin/env python3
"""
Gerador de templates HTML para o sistema de atendimentos
Executa este arquivo para criar todos os templates necessários
"""

import os

# Criar diretório de templates
TEMPLATES_DIR = 'templates'
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Template base
BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Atendimentos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
        }
        
        /* Mobile-first: fonte mínima 16px */
        body { font-size: 16px; }
        
        .container {
            max-width: 480px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: white;
            padding: 16px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header h1 {
            font-size: 18px;
            font-weight: 600;
            color: #111418;
            flex: 1;
            text-align: center;
        }
        
        .back-btn, .menu-btn {
            width: 48px;
            height: 48px;
            border: none;
            background: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #111418;
        }
        
        .content {
            flex: 1;
            padding: 16px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #111418;
            font-size: 16px;
        }
        
        .form-control {
            width: 100%;
            padding: 16px;
            border: 1px solid #dbe0e6;
            border-radius: 8px;
            font-size: 16px;
            background: white;
            color: #111418;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #0c7ff2;
        }
        
        .form-control.bg-gray {
            background: #f0f2f5;
            border: none;
        }
        
        textarea.form-control {
            resize: vertical;
            min-height: 120px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            min-width: 84px;
        }
        
        .btn-primary {
            background: #0c7ff2;
            color: white;
        }
        
        .btn-secondary {
            background: #f0f2f5;
            color: #111418;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .btn-group {
            display: flex;
            gap: 12px;
            justify-content: space-between;
            margin-top: auto;
            padding: 16px;
        }
        
        .alert {
            padding: 12px 16px;
            margin-bottom: 16px;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .stats-card {
            background: white;
            padding: 20px;
            margin-bottom: 16px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .stats-card h3 {
            font-size: 16px;
            font-weight: 600;
            color: #111418;
            margin-bottom: 8px;
        }
        
        .stats-card .value {
            font-size: 24px;
            font-weight: 700;
            color: #0c7ff2;
        }
        
        .nav-bottom {
            background: white;
            border-top: 1px solid #f0f2f5;
            padding: 12px 16px;
            display: flex;
            justify-content: space-around;
        }
        
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #60758a;
            font-size: 12px;
            padding: 8px;
        }
        
        .nav-item.active {
            color: #111418;
        }
        
        .nav-icon {
            width: 24px;
            height: 24px;
            margin-bottom: 4px;
        }
        
        .radio-group {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 8px;
        }
        
        .radio-item {
            position: relative;
        }
        
        .radio-item input[type="radio"] {
            position: absolute;
            opacity: 0;
        }
        
        .radio-item label {
            display: block;
            padding: 12px 16px;
            border: 1px solid #dbe0e6;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .radio-item input[type="radio"]:checked + label {
            border: 3px solid #0c7ff2;
            padding: 10px 14px;
        }
        
        .list-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            border-bottom: 1px solid #f0f2f5;
        }
        
        .list-item:last-child {
            border-bottom: none;
        }
        
        .list-item-content {
            flex: 1;
        }
        
        .list-item-title {
            font-weight: 500;
            color: #111418;
            margin-bottom: 4px;
        }
        
        .list-item-subtitle {
            font-size: 14px;
            color: #60758a;
        }
        
        .select-arrow {
            width: 24px;
            height: 24px;
            color: #111418;
        }
        
        @media (min-width: 480px) {
            body { font-size: 16px; }
            .container { max-width: 600px; }
        }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>'''

# Template de login
LOGIN_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <h1>Login</h1>
</div>

<div class="content">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-danger">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="POST" action="{{ url_for('auth') }}">
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" class="form-control" 
                   placeholder="Digite seu email" required>
        </div>
        
        <div class="form-group">
            <label for="password">Senha</label>
            <input type="password" id="password" name="password" class="form-control" 
                   placeholder="Digite sua senha" required>
        </div>
        
        <button type="submit" class="btn btn-primary" style="width: 100%;">
            Entrar
        </button>
    </form>
    
    <div style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px; font-size: 14px;">
        <strong>Credenciais padrão:</strong><br>
        Email: admin@admin.com<br>
        Senha: admin123
    </div>
</div>
{% endblock %}'''

# Template do dashboard
DASHBOARD_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <h1>Painel Principal</h1>
    <button class="menu-btn" onclick="window.location.href='{{ url_for('logout') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 17v-3H9v-4h7V7l5 5-5 5M14 2a2 2 0 012 2v2h-2V4H4v16h10v-2h2v2a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2h10z"/>
        </svg>
    </button>
</div>

<div class="content">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-success">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <div class="stats-card">
        <h3>Pacientes Cadastrados</h3>
        <div class="value">{{ stats.total_pacientes }}</div>
    </div>
    
    <div class="stats-card">
        <h3>Atendimentos de Hoje</h3>
        <div class="value">{{ stats.atendimentos_hoje }}</div>
    </div>
    
    <div class="stats-card">
        <h3>Vendas do Dia</h3>
        <div class="value">{{ stats.vendas_hoje }}</div>
    </div>
    
    <div class="stats-card">
        <h3>Próximos Atendimentos</h3>
        <div class="value">{{ stats.proximos_atendimentos }}</div>
    </div>
</div>

<div class="nav-bottom">
    <a href="{{ url_for('dashboard') }}" class="nav-item active">
        <div class="nav-icon">🏠</div>
        Início
    </a>
    <a href="{{ url_for('pacientes') }}" class="nav-item">
        <div class="nav-icon">👥</div>
        Pacientes
    </a>
    <a href="{{ url_for('novo_atendimento') }}" class="nav-item">
        <div class="nav-icon">📅</div>
        Atendimentos
    </a>
    <a href="{{ url_for('nova_venda') }}" class="nav-item">
        <div class="nav-icon">💰</div>
        Vendas
    </a>
    <a href="{{ url_for('procedimentos') }}" class="nav-item">
        <div class="nav-icon">📊</div>
        Procedimentos
    </a>
</div>
{% endblock %}'''

# Template de lista de pacientes
PACIENTES_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <button class="back-btn" onclick="window.location.href='{{ url_for('dashboard') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
    </button>
    <h1>Pacientes</h1>
    <button class="menu-btn" onclick="window.location.href='{{ url_for('novo_paciente') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
    </button>
</div>

<div class="content">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-success">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    {% if pacientes %}
        {% for paciente in pacientes %}
            <div class="list-item">
                <div class="list-item-content">
                    <div class="list-item-title">{{ paciente.nome }}</div>
                    <div class="list-item-subtitle">{{ paciente.telefone }} • {{ paciente.data_nascimento }}</div>
                </div>
                <div class="select-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                    </svg>
                </div>
            </div>
        {% endfor %}
    {% else %}
        <div style="text-align: center; padding: 40px; color: #60758a;">
            <p>Nenhum paciente cadastrado ainda.</p>
            <a href="{{ url_for('novo_paciente') }}" class="btn btn-primary" style="margin-top: 16px;">
                Cadastrar Primeiro Paciente
            </a>
        </div>
    {% endif %}
</div>
{% endblock %}'''

# Template de novo paciente
NOVO_PACIENTE_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <button class="back-btn" onclick="window.location.href='{{ url_for('pacientes') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
    </button>
    <h1>Novo Paciente</h1>
</div>

<form method="POST" action="{{ url_for('salvar_paciente') }}" style="flex: 1; display: flex; flex-direction: column;">
    <div class="content">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-group">
            <label for="nome">Nome</label>
            <input type="text" id="nome" name="nome" class="form-control bg-gray" 
                   placeholder="Nome do paciente" required>
        </div>
        
        <div class="form-group">
            <label for="cpf">CPF</label>
            <input type="text" id="cpf" name="cpf" class="form-control bg-gray" 
                   placeholder="000.000.000-00" maxlength="14" required>
        </div>
        
        <div class="form-group">
            <label for="data_nascimento">Data de Nascimento</label>
            <input type="text" id="data_nascimento" name="data_nascimento" class="form-control bg-gray" 
                   placeholder="DD/MM/AAAA" maxlength="10" required>
        </div>
        
        <div class="form-group">
            <label for="telefone">Telefone</label>
            <input type="text" id="telefone" name="telefone" class="form-control bg-gray" 
                   placeholder="(00) 00000-0000" maxlength="15" required>
        </div>
        
        <div class="form-group">
            <label for="gosto_musical">Gosto Musical</label>
            <input type="text" id="gosto_musical" name="gosto_musical" class="form-control bg-gray" 
                   placeholder="Gosto musical do paciente">
        </div>
    </div>
    
    <div class="btn-group">
        <button type="button" class="btn btn-secondary" onclick="window.location.href='{{ url_for('pacientes') }}'">
            Cancelar
        </button>
        <button type="submit" class="btn btn-primary">
            Salvar
        </button>
    </div>
</form>

<script>
// Máscara para CPF
document.getElementById('cpf').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    e.target.value = value;
});

// Máscara para data
document.getElementById('data_nascimento').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{2})(\d)/, '$1/$2');
    value = value.replace(/(\d{2})(\d)/, '$1/$2');
    e.target.value = value;
});

// Máscara para telefone
document.getElementById('telefone').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length <= 10) {
        value = value.replace(/(\d{2})(\d)/, '($1) $2');
        value = value.replace(/(\d{4})(\d)/, '$1-$2');
    } else {
        value = value.replace(/(\d{2})(\d)/, '($1) $2');
        value = value.replace(/(\d{5})(\d)/, '$1-$2');
    }
    e.target.value = value;
});
</script>
{% endblock %}'''

# Template de novo atendimento
NOVO_ATENDIMENTO_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <button class="back-btn" onclick="window.location.href='{{ url_for('dashboard') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
    </button>
    <h1>Novo Atendimento</h1>
</div>

<form method="POST" action="{{ url_for('salvar_atendimento') }}" style="flex: 1; display: flex; flex-direction: column;">
    <div class="content">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-group">
            <label for="paciente_id">Paciente</label>
            <select id="paciente_id" name="paciente_id" class="form-control" required>
                <option value="">Selecione o paciente</option>
                {% for paciente in pacientes %}
                    <option value="{{ paciente.id }}">{{ paciente.nome }} - {{ paciente.telefone }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label for="observacoes">Observações</label>
            <textarea id="observacoes" name="observacoes" class="form-control" 
                      placeholder="Adicione observações"></textarea>
        </div>
        
        <div class="form-group">
            <label for="anamnese">Anamnese</label>
            <textarea id="anamnese" name="anamnese" class="form-control" 
                      placeholder="Preencha a anamnese"></textarea>
        </div>
    </div>
    
    <div class="btn-group">
        <button type="button" class="btn btn-secondary" onclick="window.location.href='{{ url_for('dashboard') }}'">
            Cancelar
        </button>
        <button type="submit" class="btn btn-primary">
            Salvar
        </button>
    </div>
</form>
{% endblock %}'''

# Template de procedimentos
PROCEDIMENTOS_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <button class="back-btn" onclick="window.location.href='{{ url_for('dashboard') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
    </button>
    <h1>Procedimentos</h1>
    <button class="menu-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
    </button>
</div>

<div class="content">
    {% for procedimento in procedimentos %}
        <div class="list-item">
            <div class="list-item-content">
                <div class="list-item-title">{{ procedimento.nome }}</div>
            </div>
            <div class="select-arrow">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                </svg>
            </div>
        </div>
    {% endfor %}
</div>
{% endblock %}'''

# Template de nova venda
NOVA_VENDA_TEMPLATE = '''{% extends "base.html" %}
{% block content %}
<div class="header">
    <button class="back-btn" onclick="window.location.href='{{ url_for('dashboard') }}'">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
    </button>
    <h1>Registro de Vendas</h1>
</div>

<form method="POST" action="{{ url_for('salvar_venda') }}" style="flex: 1; display: flex; flex-direction: column;">
    <div class="content">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-group">
            <label for="data_atendimento">Data do Atendimento</label>
            <input type="text" id="data_atendimento" name="data_atendimento" class="form-control bg-gray" 
                   placeholder="DD/MM/AAAA" maxlength="10" required>
        </div>
        
        <div class="form-group">
            <label for="valor_bruto">Valor Bruto</label>
            <input type="text" id="valor_bruto" name="valor_bruto" class="form-control bg-gray" 
                   placeholder="R$ 0,00" required>
        </div>
        
        <div class="form-group">
            <label>Forma de Pagamento</label>
            <div class="radio-group">
                <div class="radio-item">
                    <input type="radio" id="pix" name="forma_pagamento" value="pix" required>
                    <label for="pix">Pix</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="debito" name="forma_pagamento" value="debito">
                    <label for="debito">Débito</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="credito" name="forma_pagamento" value="credito">
                    <label for="credito">Crédito</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="especie" name="forma_pagamento" value="especie">
                    <label for="especie">Espécie</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="transferencia" name="forma_pagamento" value="transferencia">
                    <label for="transferencia">Transferência</label>
                </div>
            </div>
        </div>
        
        <div class="form-group">
            <label for="observacoes">Observações</label>
            <textarea id="observacoes" name="observacoes" class="form-control bg-gray" 
                      placeholder="Adicione informações relevantes"></textarea>
        </div>
    </div>
    
    <div class="btn-group">
        <button type="button" class="btn btn-secondary" onclick="window.location.href='{{ url_for('dashboard') }}'">
            Cancelar
        </button>
        <button type="submit" class="btn btn-primary">
            Salvar
        </button>
    </div>
</form>

<script>
// Máscara para data
document.getElementById('data_atendimento').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{2})(\d)/, '$1/$2');
    value = value.replace(/(\d{2})(\d)/, '$1/$2');
    e.target.value = value;
});

// Máscara para valor
document.getElementById('valor_bruto').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = (parseFloat(value) / 100).toFixed(2);
    value = 'R$ ' + value.replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    e.target.value = value;
});

// Definir data atual
document.getElementById('data_atendimento').value = new Date().toLocaleDateString('pt-BR');
</script>
{% endblock %}'''

# Função para criar todos os templates
def create_templates():
    """Cria todos os arquivos de template"""
    
    templates = {
        'base.html': BASE_TEMPLATE,
        'login.html': LOGIN_TEMPLATE,
        'dashboard.html': DASHBOARD_TEMPLATE,
        'pacientes.html': PACIENTES_TEMPLATE,
        'novo_paciente.html': NOVO_PACIENTE_TEMPLATE,
        'novo_atendimento.html': NOVO_ATENDIMENTO_TEMPLATE,
        'procedimentos.html': PROCEDIMENTOS_TEMPLATE,
        'nova_venda.html': NOVA_VENDA_TEMPLATE
    }
    
    print("Criando templates...")
    
    for filename, content in templates.items():
        filepath = os.path.join(TEMPLATES_DIR, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {filename} criado com sucesso")
        except Exception as e:
            print(f"✗ Erro ao criar {filename}: {e}")
    
    print(f"\nTodos os templates foram criados no diretório '{TEMPLATES_DIR}'")
    print("\nPara executar o sistema:")
    print("1. Instale as dependências: pip install flask")
    print("2. Execute o aplicativo: python app.py")
    print("3. Acesse: http://localhost:5000")
    print("\nCredenciais padrão:")
    print("Email: admin@admin.com")
    print("Senha: admin123")

if __name__ == '__main__':
    create_templates()
