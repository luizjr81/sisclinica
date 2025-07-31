# Sistema de Registro de Atendimentos

Sistema simples e seguro para gestão de atendimentos em clínicas de estética, desenvolvido em Python/Flask com armazenamento em JSON.

## 🚀 Características

- **Interface Responsiva**: Otimizada para dispositivos móveis (fonte mínima 16px em telas de 6")
- **Armazenamento Seguro**: Dados salvos em JSON com validação e sanitização
- **Sistema de Backup**: Backup automático antes de cada alteração
- **Validações Robustas**: CPF, telefone, datas e valores monetários
- **Preparado para Migração**: Estrutura pronta para MySQL/PostgreSQL

## 📱 Funcionalidades

- **Dashboard**: Estatísticas diárias (pacientes, atendimentos, vendas)
- **Gestão de Pacientes**: Cadastro com CPF, telefone e gosto musical
- **Registro de Atendimentos**: Observações e anamnese detalhada
- **Controle de Vendas**: Múltiplas formas de pagamento
- **Lista de Procedimentos**: Catálogo completo de serviços

## 🔒 Segurança Implementada

### Validação de Dados
- Sanitização de entrada removendo caracteres de controle
- Limite de 1000 caracteres por campo
- Validação de CPF com dígitos verificadores
- Validação de formato de data (DD/MM/AAAA)
- Validação de telefone (10-11 dígitos)

### Proteção de Arquivos
- Backup automático antes de alterações
- Escrita atômica usando arquivos temporários
- Tratamento de erros de I/O
- Encoding UTF-8 forçado

### Autenticação
- Hash SHA-256 para senhas
- Cookie de sessão com tempo limite
- Proteção de rotas com decorator

### Prevenção de Ataques
- Sanitização contra injeção de dados
- Limite de tamanho de campos
- Validação de tipos de dados
- Proteção contra manipulação de arquivos

## 🛠️ Instalação

### 1. Clonar/Baixar os arquivos
```bash
# Baixe os arquivos: app.py e generate_templates.py
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Gerar templates
```bash
python generate_templates.py
```

### 4. Executar aplicação
```bash
python app.py
```

### 5. Acessar sistema
```
http://localhost:5000
```

## 🔑 Credenciais Padrão

- **Email**: admin@admin.com
- **Senha**: admin123

*⚠️ Altere essas credenciais em produção!*

## 📊 Estrutura de Dados

### Pacientes (`data/pacientes.json`)
```json
{
  "id": 1,
  "nome": "João Silva",
  "cpf": "12345678901",
  "data_nascimento": "15/05/1990",
  "telefone": "11987654321",
  "gosto_musical": "Rock",
  "created_at": "2025-01-01T10:00:00"
}
```

### Atendimentos (`data/atendimentos.json`)
```json
{
  "id": 1,
  "paciente_id": 1,
  "data": "31/07/2025",
  "hora": "14:30",
  "observacoes": "Primeira consulta",
  "anamnese": "Histórico detalhado...",
  "created_at": "2025-07-31T14:30:00"
}
```

### Vendas (`data/vendas.json`)
```json
{
  "id": 1,
  "data": "31/07/2025",
  "valor": 250.00,
  "forma_pagamento": "pix",
  "observacoes": "Procedimento completo",
  "created_at": "2025-07-31T15:00:00"
}
```

## 🔄 Migração para Banco de Dados

O sistema foi projetado para facilitar a migração futura:

### Para MySQL
```python
# Substitua as funções load_json_file e save_json_file
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='user',
        password='password',
        database='atendimentos'
    )
```

### Para PostgreSQL
```python
# Substitua as funções de arquivo
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='atendimentos',
        user='user',
        password='password'
    )
```

## 📱 Design Responsivo

- **Mobile First**: Fonte base 16px
- **Touch Friendly**: Botões com 48px mínimo
- **Máximo 480px**: Layout otimizado para celular
- **Máscaras de Input**: CPF, telefone, data automáticas

## ⚡ Performance

- **Arquivos Leves**: JSON estruturado
- **Cache Local**: Mínimas operações de I/O
- **Validação Client-Side**: Reduz requisições
- **Backup Inteligente**: Somente quando necessário

## 🛡️ Boas Práticas de Segurança

1. **Altere a SECRET_KEY** em produção
2. **Use HTTPS** em ambiente real
3. **Implemente rate limiting** se necessário
4. **Monitore logs** de acesso
5. **Backup regular** dos dados
6. **Validação dupla** (client + server)

## 📝 Logs e Monitoramento

O sistema gera logs automáticos para:
- Erros de validação
- Falhas de I/O
- Tentativas de login
- Operações de dados

## 🔧 Customização

### Adicionar Novos Campos
1. Atualizar templates HTML
2. Adicionar validação em `app.py`
3. Modificar estrutura JSON

### Novos Procedimentos
Edite `data/procedimentos.json` diretamente ou implemente CRUD.

### Personalizar Estilos
Modifique o CSS no template `base.html`.

## 📞 Suporte

Para questões técnicas ou melhorias, consulte a documentação do Flask e as boas práticas de segurança web.

---

**Desenvolvido com foco em segurança, usabilidade e performance** 🚀
