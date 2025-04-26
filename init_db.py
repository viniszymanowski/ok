import os
import sys
import logging
from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask para contexto
app = Flask(__name__)

# Carregar configurações
try:
    from config import Config
    app.config.from_object(Config)
    logger.info("Configurações carregadas com sucesso")
except Exception as e:
    logger.error(f"Erro ao carregar configurações: {str(e)}")
    # Configuração de fallback
    app.config['SECRET_KEY'] = 'chave_secreta_temporaria'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/sistema.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Corrigir URL do PostgreSQL se necessário
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
        logger.info("URL do PostgreSQL corrigida")

# Inicializar o banco de dados
try:
    from models import db, Usuario, Colheitadeira, ManutencaoPreventiva, ManutencaoCorretiva, TrocaOleo, RegistroHorimetro, ItemEstoque, MovimentacaoEstoque
    db.init_app(app)
    logger.info("Banco de dados inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
    raise

# Função para criar dados de exemplo
def criar_dados_exemplo():
    with app.app_context():
        # Verificar se já existem dados
        if Usuario.query.count() > 0:
            logger.info("Banco de dados já contém dados. Pulando criação de dados de exemplo.")
            return
        
        # Criar usuários
        usuarios = [
            {'username': 'admin', 'nome': 'Administrador', 'email': 'admin@example.com', 'senha': 'admin123', 'cargo': 'Administrador'},
            {'username': 'tecnico', 'nome': 'Técnico de Manutenção', 'email': 'tecnico@example.com', 'senha': 'tecnico123', 'cargo': 'Técnico'},
            {'username': 'operador', 'nome': 'Operador de Campo', 'email': 'operador@example.com', 'senha': 'operador123', 'cargo': 'Operador'}
        ]
        
        for u in usuarios:
            usuario = Usuario(username=u['username'], nome=u['nome'], email=u['email'], cargo=u['cargo'])
            usuario.password = generate_password_hash(u['senha'])
            db.session.add(usuario)
        
        db.session.commit()
        logger.info("Usuários criados com sucesso")
        
        # Criar colheitadeiras
        colheitadeiras = [
            {'modelo': 'S790', 'ano': 2022, 'numero_frota': 'JD-001', 'status': 'Ativa'},
            {'modelo': 'S680', 'ano': 2021, 'numero_frota': 'JD-002', 'status': 'Ativa'},
            {'modelo': 'S770', 'ano': 2023, 'numero_frota': 'JD-003', 'status': 'Em Manutenção'},
            {'modelo': 'S760', 'ano': 2020, 'numero_frota': 'JD-004', 'status': 'Inativa'},
            {'modelo': 'S670', 'ano': 2019, 'numero_frota': 'JD-005', 'status': 'Ativa'}
        ]
        
        for c in colheitadeiras:
            colheitadeira = Colheitadeira(modelo=c['modelo'], ano=c['ano'], numero_frota=c['numero_frota'], status=c['status'])
            db.session.add(colheitadeira)
        
        db.session.commit()
        logger.info("Colheitadeiras criadas com sucesso")
        
        # Criar registros de horímetro
        hoje = datetime.now()
        for colheitadeira_id in range(1, 6):
            for i in range(10):
                data = hoje - timedelta(days=i*10)
                valor = 1000 - (i * 50)
                registro = RegistroHorimetro(colheitadeira_id=colheitadeira_id, data=data, valor=valor)
                db.session.add(registro)
        
        db.session.commit()
        logger.info("Registros de horímetro criados com sucesso")
        
        # Criar manutenções preventivas
        manutencoes_preventivas = [
            {'colheitadeira_id': 1, 'descricao': 'Troca de filtros', 'data_agendada': hoje + timedelta(days=5), 'horimetro_agendado': 1050, 'status': 'Pendente'},
            {'colheitadeira_id': 2, 'descricao': 'Revisão geral', 'data_agendada': hoje + timedelta(days=10), 'horimetro_agendado': 1100, 'status': 'Pendente'},
            {'colheitadeira_id': 3, 'descricao': 'Calibração de sensores', 'data_agendada': hoje - timedelta(days=5), 'horimetro_agendado': 950, 'status': 'Realizada', 'data_realizacao': hoje - timedelta(days=4), 'observacoes': 'Sensores calibrados com sucesso'},
            {'colheitadeira_id': 4, 'descricao': 'Lubrificação geral', 'data_agendada': hoje - timedelta(days=15), 'horimetro_agendado': 900, 'status': 'Realizada', 'data_realizacao': hoje - timedelta(days=14), 'observacoes': 'Lubrificação realizada conforme manual'},
            {'colheitadeira_id': 5, 'descricao': 'Verificação de correias', 'data_agendada': hoje + timedelta(days=3), 'horimetro_agendado': 1020, 'status': 'Pendente'}
        ]
        
        for mp in manutencoes_preventivas:
            manutencao = ManutencaoPreventiva(
                colheitadeira_id=mp['colheitadeira_id'],
                descricao=mp['descricao'],
                data_agendada=mp['data_agendada'],
                horimetro_agendado=mp['horimetro_agendado'],
                status=mp['status']
            )
            if mp['status'] == 'Realizada':
                manutencao.data_realizacao = mp['data_realizacao']
                manutencao.observacoes = mp['observacoes']
            db.session.add(manutencao)
        
        db.session.commit()
        logger.info("Manutenções preventivas criadas com sucesso")
        
        # Criar manutenções corretivas
        manutencoes_corretivas = [
            {'colheitadeira_id': 3, 'descricao_falha': 'Falha no sistema hidráulico', 'data_inicio': hoje - timedelta(days=2), 'status': 'Em Andamento'},
            {'colheitadeira_id': 1, 'descricao_falha': 'Problema no motor', 'data_inicio': hoje - timedelta(days=20), 'status': 'Concluída', 'data_conclusao': hoje - timedelta(days=18), 'solucao': 'Substituição de componentes do motor', 'pecas_substituidas': 'Pistões, anéis e juntas'},
            {'colheitadeira_id': 2, 'descricao_falha': 'Falha elétrica', 'data_inicio': hoje - timedelta(days=15), 'status': 'Concluída', 'data_conclusao': hoje - timedelta(days=14), 'solucao': 'Reparo na fiação', 'pecas_substituidas': 'Cabos e conectores'},
            {'colheitadeira_id': 5, 'descricao_falha': 'Vazamento de óleo', 'data_inicio': hoje - timedelta(days=8), 'status': 'Concluída', 'data_conclusao': hoje - timedelta(days=7), 'solucao': 'Substituição de vedações', 'pecas_substituidas': 'Retentores e juntas'}
        ]
        
        for mc in manutencoes_corretivas:
            manutencao = ManutencaoCorretiva(
                colheitadeira_id=mc['colheitadeira_id'],
                descricao_falha=mc['descricao_falha'],
                data_inicio=mc['data_inicio'],
                status=mc['status']
            )
            if mc['status'] == 'Concluída':
                manutencao.data_conclusao = mc['data_conclusao']
                manutencao.solucao = mc['solucao']
                manutencao.pecas_substituidas = mc['pecas_substituidas']
            db.session.add(manutencao)
        
        db.session.commit()
        logger.info("Manutenções corretivas criadas com sucesso")
        
        # Criar trocas de óleo
        trocas_oleo = [
            {'colheitadeira_id': 1, 'data': hoje - timedelta(days=30), 'horimetro': 800, 'tipo_oleo': 'Óleo de Motor 15W40', 'quantidade': 20, 'proxima_troca': hoje + timedelta(days=60)},
            {'colheitadeira_id': 2, 'data': hoje - timedelta(days=15), 'horimetro': 850, 'tipo_oleo': 'Óleo Hidráulico HLP 68', 'quantidade': 30, 'proxima_troca': hoje + timedelta(days=75)},
            {'colheitadeira_id': 3, 'data': hoje - timedelta(days=45), 'horimetro': 750, 'tipo_oleo': 'Óleo de Transmissão 80W90', 'quantidade': 15, 'proxima_troca': hoje + timedelta(days=45)},
            {'colheitadeira_id': 4, 'data': hoje - timedelta(days=60), 'horimetro': 700, 'tipo_oleo': 'Óleo de Motor 15W40', 'quantidade': 20, 'proxima_troca': hoje + timedelta(days=30)},
            {'colheitadeira_id': 5, 'data': hoje - timedelta(days=10), 'horimetro': 900, 'tipo_oleo': 'Óleo Hidráulico HLP 68', 'quantidade': 30, 'proxima_troca': hoje + timedelta(days=80)}
        ]
        
        for to in trocas_oleo:
            troca = TrocaOleo(
                colheitadeira_id=to['colheitadeira_id'],
                data=to['data'],
                horimetro=to['horimetro'],
                tipo_oleo=to['tipo_oleo'],
                quantidade=to['quantidade'],
                proxima_troca=to['proxima_troca']
            )
            db.session.add(troca)
        
        db.session.commit()
        logger.info("Trocas de óleo criadas com sucesso")
        
        # Criar itens de estoque
        itens_estoque = [
            {'nome': 'Óleo de Motor 15W40', 'codigo': 'OL-001', 'categoria': 'Lubrificantes', 'quantidade': 200, 'quantidade_minima': 50, 'unidade': 'Litros', 'localizacao': 'Prateleira A1'},
            {'nome': 'Óleo Hidráulico HLP 68', 'codigo': 'OL-002', 'categoria': 'Lubrificantes', 'quantidade': 150, 'quantidade_minima': 40, 'unidade': 'Litros', 'localizacao': 'Prateleira A2'},
            {'nome': 'Óleo de Transmissão 80W90', 'codigo': 'OL-003', 'categoria': 'Lubrificantes', 'quantidade': 100, 'quantidade_minima': 30, 'unidade': 'Litros', 'localizacao': 'Prateleira A3'},
            {'nome': 'Filtro de Óleo', 'codigo': 'FL-001', 'categoria': 'Filtros', 'quantidade': 25, 'quantidade_minima': 10, 'unidade': 'Unidades', 'localizacao': 'Prateleira B1'},
            {'nome': 'Filtro de Ar', 'codigo': 'FL-002', 'categoria': 'Filtros', 'quantidade': 20, 'quantidade_minima': 8, 'unidade': 'Unidades', 'localizacao': 'Prateleira B2'},
            {'nome': 'Filtro de Combustível', 'codigo': 'FL-003', 'categoria': 'Filtros', 'quantidade': 30, 'quantidade_minima': 12, 'unidade': 'Unidades', 'localizacao': 'Prateleira B3'},
            {'nome': 'Correia do Motor', 'codigo': 'CR-001', 'categoria': 'Correias', 'quantidade': 15, 'quantidade_minima': 5, 'unidade': 'Unidades', 'localizacao': 'Prateleira C1'},
            {'nome': 'Correia do Alternador', 'codigo': 'CR-002', 'categoria': 'Correias', 'quantidade': 12, 'quantidade_minima': 4, 'unidade': 'Unidades', 'localizacao': 'Prateleira C2'},
            {'nome': 'Junta do Cabeçote', 'codigo': 'JT-001', 'categoria': 'Juntas', 'quantidade': 8, 'quantidade_minima': 3, 'unidade': 'Unidades', 'localizacao': 'Prateleira D1'},
            {'nome': 'Kit de Reparo Hidráulico', 'codigo': 'KT-001', 'categoria': 'Kits de Reparo', 'quantidade': 5, 'quantidade_minima': 2, 'unidade': 'Unidades', 'localizacao': 'Prateleira E1'}
        ]
        
        for ie in itens_estoque:
            item = ItemEstoque(
                nome=ie['nome'],
                codigo=ie['codigo'],
                categoria=ie['categoria'],
                quantidade=ie['quantidade'],
                quantidade_minima=ie['quantidade_minima'],
                unidade=ie['unidade'],
                localizacao=ie['localizacao']
            )
            db.session.add(item)
        
        db.session.commit()
        logger.info("Itens de estoque criados com sucesso")
        
        # Criar movimentações de estoque
        for item_id in range(1, 11):
            # Entradas
            for i in range(3):
                data = hoje - timedelta(days=random.randint(10, 90))
                quantidade = random.randint(10, 50)
                movimentacao = MovimentacaoEstoque(
                    item_id=item_id,
                    tipo='Entrada',
                    quantidade=quantidade,
                    data=data,
                    observacao=f'Compra de material - Nota Fiscal #{random.randint(10000, 99999)}'
                )
                db.session.add(movimentacao)
            
            # Saídas
            for i in range(2):
                data = hoje - timedelta(days=random.randint(1, 30))
                quantidade = random.randint(1, 10)
                movimentacao = MovimentacaoEstoque(
                    item_id=item_id,
                    tipo='Saída',
                    quantidade=quantidade,
                    data=data,
                    observacao=f'Utilizado na manutenção da colheitadeira JD-00{random.randint(1, 5)}'
                )
                db.session.add(movimentacao)
        
        db.session.commit()
        logger.info("Movimentações de estoque criadas com sucesso")
        
        logger.info("Todos os dados de exemplo foram criados com sucesso!")

# Criar tabelas e dados de exemplo
with app.app_context():
    try:
        # Verificar se o banco de dados já existe
        import os
        db_path = 'instance/sistema.db'
        if os.path.exists(db_path):
            logger.info(f"Banco de dados já existe em {db_path}")
        else:
            # Criar diretório instance se não existir
            os.makedirs('instance', exist_ok=True)
            logger.info("Diretório 'instance' criado")
        
        # Criar todas as tabelas
        db.create_all()
        logger.info("Tabelas do banco de dados criadas com sucesso")
        
        # Criar dados de exemplo
        criar_dados_exemplo()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise

if __name__ == '__main__':
    logger.info("Inicialização do banco de dados concluída com sucesso!")
