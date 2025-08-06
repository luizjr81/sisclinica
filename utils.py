import re
from datetime import date
from sqlalchemy import text
from extensions import db

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
