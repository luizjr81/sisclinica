import pytest
from app import app as flask_app, init_data_files, save_json_file, USUARIOS_FILE
import os
import json
import hashlib
from datetime import datetime

# Fixture to provide the Flask app instance
@pytest.fixture
def app():
    # Setup: ensure data files are initialized for a clean test environment
    # Create a temporary test user file to avoid modifying the original
    TEST_USUARIOS_FILE = 'data/test_usuarios.json'
    original_usuarios_file = flask_app.config.get('USUARIOS_FILE', USUARIOS_FILE)
    flask_app.config['USUARIOS_FILE'] = TEST_USUARIOS_FILE

    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)

    # Create a default user for testing
    usuarios_padrao = [{
        "id": 1,
        "email": "admin@admin.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "perfil": "admin",
        "ativo": True,
        "created_at": datetime.now().isoformat()
    }]
    save_json_file(TEST_USUARIOS_FILE, usuarios_padrao)

    yield flask_app

    # Teardown: clean up the test user file
    if os.path.exists(TEST_USUARIOS_FILE):
        os.remove(TEST_USUARIOS_FILE)
    # Restore original file path in config if needed
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

# Test 4: Check if the user maintenance page is accessible after login
def test_user_maintenance_page_access(client):
    """
    GIVEN a logged-in user
    WHEN the '/manutencao/usuarios' page is requested (GET)
    THEN check that the page loads correctly
    """
    # First, log in
    client.post('/auth', data=dict(
        email='admin@admin.com',
        password='admin123'
    ), follow_redirects=True)

    # Then, access the maintenance page
    response = client.get('/manutencao/usuarios')
    assert response.status_code == 200
    assert b'Manuten' in response.data
    assert b'Adicionar Novo Usu' in response.data

# Test 5: Check if a new user can be added
def test_add_new_user(client):
    """
    GIVEN a logged-in user on the user maintenance page
    WHEN a new user is added through the form
    THEN check that the new user appears in the list of users
    """
    # Log in first
    client.post('/auth', data=dict(
        email='admin@admin.com',
        password='admin123'
    ), follow_redirects=True)

    # Add a new user
    response = client.post('/manutencao/usuarios/salvar', data=dict(
        email='newuser@example.com',
        password='newpassword',
        perfil='usuario'
    ), follow_redirects=True)

    assert response.status_code == 200
    assert b'Usu' in response.data
    assert b'newuser@example.com' in response.data

# Test 6: Check if the link to user maintenance is on the dashboard
def test_dashboard_has_maintenance_link(client):
    """
    GIVEN a logged-in user
    WHEN the dashboard is viewed
    THEN check that the link to the user maintenance page is present
    """
    # Log in
    client.post('/auth', data=dict(
        email='admin@admin.com',
        password='admin123'
    ), follow_redirects=True)

    # Get dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'manutencao/usuarios' in response.data
    assert b'Usu' in response.data
