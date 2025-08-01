import pytest
from app import app as flask_app, init_data_files, save_json_file, USUARIOS_FILE
import os
import json
import hashlib
from datetime import datetime

from werkzeug.security import generate_password_hash

# Fixture to provide the Flask app instance
@pytest.fixture
def app():
    # Setup: ensure data files are initialized for a clean test environment
    # Use a temporary file for test users to avoid modifying the real data
    TEST_USUARIOS_FILE = 'data/test_usuarios.json'

    # Store the original path and set it to the test path
    original_usuarios_file = flask_app.config.get('USUARIOS_FILE', USUARIOS_FILE)
    flask_app.config['USUARIOS_FILE'] = TEST_USUARIOS_FILE

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

    # Teardown: clean up the test user file and restore the original path
    if os.path.exists(TEST_USUARIOS_FILE):
        os.remove(TEST_USUARIOS_FILE)
    flask_app.config['USUARIOS_FILE'] = original_usuarios_file

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
    assert b'Dashboard' in response.data
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
def test_update_patient_with_invalid_cpf(client):
    """
    GIVEN a logged-in user
    WHEN updating a patient with an invalid CPF
    THEN check for an error message
    """
    with client:
        client.post('/auth', data={'email': 'admin@admin.com', 'password': 'admin123'}, follow_redirects=True)

        # Setup a dummy patient file for this test
        TEST_PACIENTES_FILE = 'data/test_pacientes.json'
        original_pacientes_file = flask_app.config.get('PACIENTES_FILE')
        flask_app.config['PACIENTES_FILE'] = TEST_PACIENTES_FILE

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
        if original_pacientes_file:
            flask_app.config['PACIENTES_FILE'] = original_pacientes_file
