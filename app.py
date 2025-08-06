"""
Sistema de Gestão para Clínica de Estética - Versão Básica
Desenvolvido com Flask + PostgreSQL
"""

import os
import re
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from datetime import date, timedelta

# Carregar variáveis de ambiente
load_dotenv()

# Importar Extensões e Modelos
from extensions import db
from models import Usuario

# Importar Blueprints
from routes.main import main_bp
from routes.pacientes import pacientes_bp
from routes.procedimentos import procedimentos_bp
from routes.anamnese import anamnese_bp
from routes.atendimentos import atendimentos_bp
from routes.agendamentos import agendamentos_bp
from routes.profissionais import profissionais_bp
from routes.pagamentos import pagamentos_bp
from routes.relatorios import relatorios_bp
from routes.admin import admin_bp

# Importar Funções Utilitárias
from utils import formatar_cpf, calcular_idade, testar_conexao_banco


def create_app():
    """Cria e configura a instância do aplicativo Flask."""
    app = Flask(__name__)

    # --- Configurações ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-padrao-123')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://clinica_user:senha123@localhost:5432/clinica_estetica')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # --- Inicializar Extensões ---
    db.init_app(app)

    # --- Registrar Blueprints ---
    app.register_blueprint(main_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(procedimentos_bp)
    app.register_blueprint(anamnese_bp)
    app.register_blueprint(atendimentos_bp)
    app.register_blueprint(agendamentos_bp)
    app.register_blueprint(profissionais_bp)
    app.register_blueprint(pagamentos_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(admin_bp)

    # --- Context Processors ---
    @app.context_processor
    def utility_processor():
        return dict(
            formatar_cpf=formatar_cpf,
            calcular_idade=calcular_idade,
            date=date,
            timedelta=timedelta
        )

    # --- Tratamento de Erros ---
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

def setup_database(app):
    """Funções para inicialização e verificação do banco de dados."""
    with app.app_context():
        try:
            print("🔄 Testando conexão com banco de dados...")
            if not testar_conexao_banco():
                print("❌ Falha na conexão. Verifique as configurações do banco.")
                return False
            
            print("🔄 Verificando permissões...")
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

def verificar_permissoes_banco():
    """Verifica se o usuário tem permissões para criar tabelas."""
    try:
        db.session.execute(text('CREATE TABLE IF NOT EXISTS teste_permissoes_temp (id SERIAL PRIMARY KEY, teste VARCHAR(10))'))
        db.session.commit()
        db.session.execute(text('DROP TABLE IF EXISTS teste_permissoes_temp'))
        db.session.commit()
        print("✅ Permissões de criação de tabelas: OK")
        return True
    except Exception as e:
        print(f"❌ Erro de permissões: {str(e)}")
        return False

def criar_usuario_admin():
    """Cria usuário administrador padrão se não existir."""
    try:
        if not Usuario.query.filter_by(username='admin').first():
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


# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    app = create_app()

    print("🏥 Iniciando Sistema Clínica Estética")
    print("=" * 50)
    
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
    print(f"Database URL: {masked_url}")
    
    print("🔄 Inicializando banco de dados...")
    if setup_database(app):
        print("🚀 Servidor iniciado em: http://localhost:5000")
        print("👤 Login: admin | Senha: admin123")
        print("🧪 Teste: http://localhost:5000/test")
        print("")
        app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', host='0.0.0.0', port=5000)
    else:
        print("❌ Não foi possível iniciar o servidor")
        print("🔧 Execute os comandos de configuração do PostgreSQL novamente")