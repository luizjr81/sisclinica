import pytest
from app import (
    app as flask_app,
    init_data_files,
    save_json_file,
    USUARIOS_FILE,
    validate_cpf,
    validate_date,
    validate_phone
)
import os
import json
import hashlib
from datetime import datetime

from werkzeug.security import generate_password_hash

# Fixture to provide the Flask app instance
@pytest.fixture
def app(monkeypatch):
    # Setup: ensure data files are initialized for a clean test environment
    TEST_USUARIOS_FILE = 'data/test_usuarios.json'

    # Use monkeypatch to temporarily change the global variable in the app module
    monkeypatch.setattr('app.USUARIOS_FILE', TEST_USUARIOS_FILE)

    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)

    # Create a default admin user for testing with the new hash
    admin_user = {
        "id": 1,
        "email": "admin@admin.com",
        "password_hash": generate_password_hash("admin123"),
        "perfil": "admin",
        "ativo": True,
        "created_at": datetime.now().isoformat()
    }

    # Create a non-admin user for testing permissions
    regular_user = {
        "id": 2,
        "email": "user@test.com",
        "password_hash": generate_password_hash("password123"),
        "perfil": "usuario",
        "ativo": True,
        "created_at": datetime.now().isoformat()
    }

    save_json_file(TEST_USUARIOS_FILE, [admin_user, regular_user])

    yield flask_app

    # Teardown: clean up the test user file
    if os.path.exists(TEST_USUARIOS_FILE):
        os.remove(TEST_USUARIOS_FILE)

# Fixture to provide a test client for making requests
@pytest.fixture
def client(app):
    return app.test_client()

# Test 1: Check if the login page loads correctly and does not contain the default credentials
def test_login_page_loads_without_credentials(client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and does not contain the default credentials text
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b'<h1>Login</h1>' in response.data
    # Check that the hardcoded credentials are no longer present
    assert b'Credenciais padr' not in response.data
    assert b'admin@admin.com' not in response.data
    assert b'admin123' not in response.data

# Test 2: Check if a user can log in with correct credentials
def test_successful_login(client):
    """
    GIVEN a Flask application with a default user
    WHEN the '/auth' page is posted to with correct credentials
    THEN check that the user is redirected to the dashboard
    """
    response = client.post('/auth', data=dict(
        email='admin@admin.com',
        password='admin123'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Painel Principal' in response.data
    assert b'Login' not in response.data

# Test 3: Check if an unsuccessful login attempt is handled correctly
def test_unsuccessful_login(client):
    """
    GIVEN a Flask application
    WHEN the '/auth' page is posted to with incorrect credentials
    THEN check that the user is redirected back to the login page with an error message
    """
    response = client.post('/auth', data=dict(
        email='wrong@user.com',
        password='wrongpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Credenciais inv' in response.data  # Checks for "Credenciais inválidas"

# Test 4: Check if an admin user can access the user maintenance page
def test_admin_can_access_user_maintenance(client):
    """
    GIVEN a logged-in admin user
    WHEN the '/manutencao/usuarios' page is requested (GET)
    THEN check that the page loads correctly
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)
        response = client.get('/manutencao/usuarios')
        assert response.status_code == 200
        assert b'Manuten' in response.data

# Test 5: Check that a non-admin user is denied access to user maintenance
def test_non_admin_denied_user_maintenance(client):
    """
    GIVEN a logged-in non-admin user
    WHEN the '/manutencao/usuarios' page is requested (GET)
    THEN check that the user is redirected to the dashboard with an error
    """
    with client:
        client.post('/auth', data={'email': 'user@test.com', 'password': 'password123'}, follow_redirects=True)
        response = client.get('/manutencao/usuarios', follow_redirects=True)
        assert response.status_code == 200
        assert b'Acesso n' in response.data  # "Acesso não autorizado"
        assert b'Manuten' not in response.data

# Test 6: Check if a new user can be added by an admin
def test_admin_can_add_new_user(client):
    """
    GIVEN a logged-in admin
    WHEN a new user is added
    THEN check that the new user appears in the list
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)
        response = client.post('/manutencao/usuarios/salvar', data={
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'perfil': 'usuario'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Usu' in response.data
        assert b'newuser@example.com' in response.data

# Test 7: Check patient update with invalid data
def test_update_patient_with_invalid_cpf(client, monkeypatch):
    """
    GIVEN a logged-in user
    WHEN updating a patient with an invalid CPF
    THEN check for an error message
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)

        # Setup a dummy patient file for this test
        TEST_PACIENTES_FILE = 'data/test_pacientes.json'
        monkeypatch.setattr('app.PACIENTES_FILE', TEST_PACIENTES_FILE)

        pacientes = [{'id': 1, 'nome': 'Teste', 'cpf': '11122233344', 'data_nascimento': '01/01/2000', 'telefone': '11999998888'}]
        save_json_file(TEST_PACIENTES_FILE, pacientes)

        response = client.post('/paciente/atualizar/1', data={
            'nome': 'Teste Nome',
            'cpf': '123',  # Invalid CPF
            'data_nascimento': '01/01/2000',
            'telefone': '11999998888'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'CPF inv' in response.data  # "CPF inválido"

        # Teardown for this specific test
        if os.path.exists(TEST_PACIENTES_FILE):
            os.remove(TEST_PACIENTES_FILE)

# --- Testes de Validação ---

@pytest.mark.parametrize("cpf, expected", [
    ("123.456.789-00", True),
    ("12345678900", True),
    ("123.456.789-0", False),
    ("1234567890", False),
    ("abcdefghijk", False),
])
def test_validate_cpf(cpf, expected):
    """Testa a função de validação de CPF."""
    assert validate_cpf(cpf) == expected

@pytest.mark.parametrize("date_str, expected", [
    ("31/12/2025", True),
    ("29/02/2024", True), # Ano bissexto
    ("31/13/2025", False), # Mês inválido
    ("32/12/2025", False), # Dia inválido
    ("2025/12/31", False), # Formato errado
])
def test_validate_date(date_str, expected):
    """Testa a função de validação de data."""
    assert validate_date(date_str) == expected

@pytest.mark.parametrize("phone, expected", [
    ("(11) 98765-4321", True),
    ("11987654321", True),
    ("(11) 8765-4321", True),
    ("1187654321", True),
    ("123456789", False), # Curto demais
    ("123456789012", False), # Longo demais
])
def test_validate_phone(phone, expected):
    """Testa a função de validação de telefone."""
    assert validate_phone(phone) == expected

# --- Testes de Funcionalidade ---

def test_create_new_patient_successfully(client, monkeypatch):
    """
    GIVEN um usuário logado
    WHEN um novo paciente é criado com dados válidos
    THEN o paciente deve ser salvo e o usuário redirecionado
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)

        TEST_PACIENTES_FILE = 'data/test_pacientes.json'
        monkeypatch.setattr('app.PACIENTES_FILE', TEST_PACIENTES_FILE)
        # Garante que o arquivo de pacientes de teste está vazio
        save_json_file(TEST_PACIENTES_FILE, [])

        response = client.post('/paciente/salvar', data={
            'nome': 'Paciente Teste',
            'cpf': '11122233344',
            'data_nascimento': '01/01/1990',
            'telefone': '11999998888',
            'gosto_musical': 'Teste',
            'observacoes': ''
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Paciente cadastrado com sucesso!' in response.data

        # Verifica se o paciente foi realmente salvo
        pacientes = json.load(open(TEST_PACIENTES_FILE))
        assert len(pacientes) == 1
        assert pacientes[0]['nome'] == 'Paciente Teste'
        assert pacientes[0]['cpf'] == '11122233344'

        if os.path.exists(TEST_PACIENTES_FILE):
            os.remove(TEST_PACIENTES_FILE)

def test_relatorio_page_shows_details_correctly(client, monkeypatch):
    """
    GIVEN a patient with an appointment
    WHEN the report page for that patient is requested
    THEN the procedure name and consultation details should be visible
    """
    with client:
        # Log in
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)

        # --- Setup test data ---
        TEST_PACIENTES_FILE = 'data/test_pacientes.json'
        TEST_PROCEDIMENTOS_FILE = 'data/test_procedimentos.json'
        TEST_ATENDIMENTOS_FILE = 'data/test_atendimentos.json'

        monkeypatch.setattr('app.PACIENTES_FILE', TEST_PACIENTES_FILE)
        monkeypatch.setattr('app.PROCEDIMENTOS_FILE', TEST_PROCEDIMENTOS_FILE)
        monkeypatch.setattr('app.ATENDIMENTOS_FILE', TEST_ATENDIMENTOS_FILE)

        # Create dummy data
        paciente = {'id': 1, 'nome': 'Paciente Relatorio', 'cpf': '99988877766'}
        procedimento = {'id': 101, 'nome': 'Teste de Procedimento', 'valor': '123.45'}
        atendimento = {
            'id': 1,
            'paciente_id': 1,
            'data': '01/08/2025',
            'procedimentos': ['101'], # Note: ID is a string in the data
            'atendimento': 'Este é o detalhe do atendimento.',
            'valor_total': 123.45
        }

        save_json_file(TEST_PACIENTES_FILE, [paciente])
        save_json_file(TEST_PROCEDIMENTOS_FILE, [procedimento])
        save_json_file(TEST_ATENDIMENTOS_FILE, [atendimento])

        # --- Make request to the report page ---
        response = client.get('/relatorio?paciente_id=1')

        # --- Assertions ---
        assert response.status_code == 200
        # Check if procedure name is present
        assert b'Teste de Procedimento' in response.data
        # Check if consultation detail is present
        assert b'Este \xc3\xa9 o detalhe do atendimento.' in response.data
        # Check that the "not found" message is NOT present
        assert b'Procedimento com ID' not in response.data
        assert b'n_o encontrado' not in response.data


        # --- Teardown ---
        for f in [TEST_PACIENTES_FILE, TEST_PROCEDIMENTOS_FILE, TEST_ATENDIMENTOS_FILE]:
            if os.path.exists(f):
                os.remove(f)

def test_create_patient_with_duplicate_cpf(client, monkeypatch):
    """
    GIVEN um paciente já existente
    WHEN tenta-se criar um novo paciente com o mesmo CPF
    THEN a criação deve falhar com uma mensagem de erro
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)

        TEST_PACIENTES_FILE = 'data/test_pacientes.json'
        monkeypatch.setattr('app.PACIENTES_FILE', TEST_PACIENTES_FILE)

        # Paciente pré-existente
        existing_patient = {'id': 1, 'nome': 'Já Existe', 'cpf': '11122233344', 'data_nascimento': '01/01/2000', 'telefone': '11999998888'}
        save_json_file(TEST_PACIENTES_FILE, [existing_patient])

        response = client.post('/paciente/salvar', data={
            'nome': 'Novo Paciente',
            'cpf': '11122233344', # CPF duplicado
            'data_nascimento': '02/02/1992',
            'telefone': '11988887777',
            'gosto_musical': '',
            'observacoes': ''
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'CPF j' in response.data # "CPF já cadastrado"

        # Verifica que o novo paciente não foi salvo
        pacientes = json.load(open(TEST_PACIENTES_FILE))
        assert len(pacientes) == 1

        if os.path.exists(TEST_PACIENTES_FILE):
            os.remove(TEST_PACIENTES_FILE)
