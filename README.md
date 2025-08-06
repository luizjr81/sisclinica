# Sistema de Gestão para Clínica de Estética

Sistema completo desenvolvido em Flask + PostgreSQL para gerenciamento de clínicas de estética.

## Instalação

1. **Instalar PostgreSQL**
2. **Configurar banco de dados:**
   ```sql
   CREATE DATABASE clinica_estetica;
   CREATE USER usuario WITH PASSWORD 'senha';
   GRANT ALL PRIVILEGES ON DATABASE clinica_estetica TO usuario;
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variáveis:**
   ```bash
   cp .env.example .env
   # Editar .env com suas configurações
   ```

5. **Executar:**
   ```bash
   python app.py
   ```

6. **Acessar:** http://localhost:5000
   - Login: admin
   - Senha: admin123

## Funcionalidades

- ✅ Sistema de Login
- ✅ Dashboard
- ✅ Gestão de Pacientes
- ✅ Sistema de Anamnese
- ✅ Catálogo de Procedimentos

## Tecnologias

- Python 3.8+ / Flask
- PostgreSQL
- Bootstrap 5
- HTML5 / CSS3 / JavaScript
