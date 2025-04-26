import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_sqlalchemy import SQLAlchemy

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask com tratamento de erros aprimorado
app = Flask(__name__)

# Configuração para o PythonAnywhere
app.config['SECRET_KEY'] = 'chave_secreta_sistema_manutencao_agricola'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://viniszymanowski:04fdce3c5d614f2d@viniszymanowski.mysql.pythonanywhere-services.com/viniszymanowski$default'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o banco de dados
db = SQLAlchemy(app)

# Modelo de Usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)

# Modelo de Colheitadeira
class Colheitadeira(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    numero_frota = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Ativa')  # Ativa, Em Manutenção, Inativa
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    manutencoes_preventivas = db.relationship('ManutencaoPreventiva', backref='colheitadeira', lazy=True)
    manutencoes_corretivas = db.relationship('ManutencaoCorretiva', backref='colheitadeira', lazy=True)
    trocas_oleo = db.relationship('TrocaOleo', backref='colheitadeira', lazy=True)
    registros_horimetro = db.relationship('RegistroHorimetro', backref='colheitadeira', lazy=True)

# Modelo de Manutenção Preventiva
class ManutencaoPreventiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_programada = db.Column(db.DateTime, nullable=False)
    horimetro_programado = db.Column(db.Float)
    data_realizada = db.Column(db.DateTime)
    horimetro_realizado = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Realizada, Cancelada

# Modelo de Manutenção Corretiva
class ManutencaoCorretiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    descricao_falha = db.Column(db.Text, nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    horimetro = db.Column(db.Float)
    solucao_aplicada = db.Column(db.Text)
    pecas_substituidas = db.Column(db.Text)
    status = db.Column(db.String(20), default='Em Andamento')  # Em Andamento, Concluída, Aguardando Peças

# Modelo de Troca de Óleo
class TrocaOleo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    horimetro = db.Column(db.Float, nullable=False)
    tipo_oleo = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)

# Modelo de Registro de Horímetro
class RegistroHorimetro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    horas_motor = db.Column(db.Float)
    observacoes = db.Column(db.Text)

# Modelo de Item de Estoque
class ItemEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Float, default=0)
    unidade = db.Column(db.String(20), nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    estoque_minimo = db.Column(db.Float, default=0)
    localizacao = db.Column(db.String(100))
    fornecedor = db.Column(db.String(100))
    data_ultima_compra = db.Column(db.DateTime)
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='item', lazy=True)

# Modelo de Movimentação de Estoque
class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # Entrada, Saída
    quantidade = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    observacao = db.Column(db.Text)

# Configurar o gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return Usuario.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Erro ao carregar usuário: {str(e)}")
        return None

# Criar todas as tabelas do banco de dados
with app.app_context():
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados criadas com sucesso")
        
        # Verificar se já existe um usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            # Criar usuário admin padrão
            admin = Usuario(username='admin', nome='Administrador', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info("Usuário admin criado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas ou usuário admin: {str(e)}")

# Rotas de autenticação
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            user = Usuario.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                flash('Nome de usuário ou senha inválidos')
                return redirect(url_for('login'))
            
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Erro na rota de login: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/logout')
def logout():
    try:
        logout_user()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Erro na rota de logout: {str(e)}")
        return render_template('error.html', error=str(e))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Contagem de colheitadeiras por status
        colheitadeiras_ativas = Colheitadeira.query.filter_by(status='Ativa').count()
        colheitadeiras_manutencao = Colheitadeira.query.filter_by(status='Em Manutenção').count()
        colheitadeiras_inativas = Colheitadeira.query.filter_by(status='Inativa').count()
        
        # Manutenções preventivas pendentes
        manutencoes_pendentes = ManutencaoPreventiva.query.filter_by(status='Pendente').count()
        
        # Manutenções corretivas em andamento
        corretivas_andamento = ManutencaoCorretiva.query.filter_by(status='Em Andamento').count()
        
        # Itens com estoque abaixo do mínimo
        itens_abaixo_minimo = db.session.query(ItemEstoque).filter(ItemEstoque.quantidade < ItemEstoque.estoque_minimo).count()
        
        return render_template('dashboard.html', 
                              colheitadeiras_ativas=colheitadeiras_ativas,
                              colheitadeiras_manutencao=colheitadeiras_manutencao,
                              colheitadeiras_inativas=colheitadeiras_inativas,
                              manutencoes_pendentes=manutencoes_pendentes,
                              corretivas_andamento=corretivas_andamento,
                              itens_abaixo_minimo=itens_abaixo_minimo)
    except Exception as e:
        logger.error(f"Erro na rota de dashboard: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Colheitadeiras
@app.route('/colheitadeiras')
@login_required
def listar_colheitadeiras():
    try:
        colheitadeiras = Colheitadeira.query.all()
        return render_template('colheitadeiras/listar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao listar colheitadeiras: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_colheitadeira():
    try:
        if request.method == 'POST':
            modelo = request.form['modelo']
            ano = int(request.form['ano'])
            numero_frota = request.form['numero_frota']
            status = request.form['status']
            
            colheitadeira = Colheitadeira(
                modelo=modelo,
                ano=ano,
                numero_frota=numero_frota,
                status=status
            )
            
            db.session.add(colheitadeira)
            db.session.commit()
            
            flash('Colheitadeira adicionada com sucesso!')
            return redirect(url_for('listar_colheitadeiras'))
        
        return render_template('colheitadeiras/adicionar.html')
    except Exception as e:
        logger.error(f"Erro ao adicionar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colheitadeira(id):
    try:
        colheitadeira = Colheitadeira.query.get_or_404(id)
        
        if request.method == 'POST':
            colheitadeira.modelo = request.form['modelo']
            colheitadeira.ano = int(request.form['ano'])
            colheitadeira.numero_frota = request.form['numero_frota']
            colheitadeira.status = request.form['status']
            
            db.session.commit()
            
            flash('Colheitadeira atualizada com sucesso!')
            return redirect(url_for('listar_colheitadeiras'))
        
        return render_template('colheitadeiras/editar.html', colheitadeira=colheitadeira)
    except Exception as e:
        logger.error(f"Erro ao editar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/visualizar/<int:id>')
@login_required
def visualizar_colheitadeira(id):
    try:
        colheitadeira = Colheitadeira.query.get_or_404(id)
        
        # Obter o último registro de horímetro
        ultimo_horimetro = RegistroHorimetro.query.filter_by(colheitadeira_id=id).order_by(RegistroHorimetro.data.desc()).first()
        
        # Obter manutenções preventivas pendentes
        manutencoes_preventivas = ManutencaoPreventiva.query.filter_by(colheitadeira_id=id, status='Pendente').all()
        
        # Obter manutenções corretivas em andamento
        manutencoes_corretivas = ManutencaoCorretiva.query.filter_by(colheitadeira_id=id, status='Em Andamento').all()
        
        # Obter última troca de óleo
        ultima_troca_oleo = TrocaOleo.query.filter_by(colheitadeira_id=id).order_by(TrocaOleo.data.desc()).first()
        
        return render_template('colheitadeiras/visualizar.html', 
                              colheitadeira=colheitadeira,
                              ultimo_horimetro=ultimo_horimetro,
                              manutencoes_preventivas=manutencoes_preventivas,
                              manutencoes_corretivas=manutencoes_corretivas,
                              ultima_troca_oleo=ultima_troca_oleo)
    except Exception as e:
        logger.error(f"Erro ao visualizar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Manutenções Preventivas
@app.route('/manutencoes/preventivas')
@login_required
def listar_manutencoes_preventivas():
    try:
        manutencoes = ManutencaoPreventiva.query.all()
        return render_template('manutencoes/preventivas/listar.html', manutencoes=manutencoes)
    except Exception as e:
        logger.error(f"Erro ao listar manutenções preventivas: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/preventivas/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_manutencao_preventiva():
    try:
        colheitadeiras = Colheitadeira.query.all()
        
        if request.method == 'POST':
            colheitadeira_id = request.form['colheitadeira_id']
            descricao = request.form['descricao']
            data_programada = datetime.datetime.strptime(request.form['data_programada'], '%Y-%m-%d')
            horimetro_programado = float(request.form['horimetro_programado']) if request.form['horimetro_programado'] else None
            observacoes = request.form.get('observacoes', '')
            
            manutencao = ManutencaoPreventiva(
                colheitadeira_id=colheitadeira_id,
                descricao=descricao,
                data_programada=data_programada,
                horimetro_programado=horimetro_programado,
                observacoes=observacoes,
                status='Pendente'
            )
            
            db.session.add(manutencao)
            db.session.commit()
            
            flash('Manutenção preventiva agendada com sucesso!')
            return redirect(url_for('listar_manutencoes_preventivas'))
        
        return render_template('manutencoes/preventivas/adicionar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao adicionar manutenção preventiva: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/preventivas/realizar/<int:id>', methods=['GET', 'POST'])
@login_required
def realizar_manutencao_preventiva(id):
    try:
        manutencao = ManutencaoPreventiva.query.get_or_404(id)
        
        if request.method == 'POST':
            manutencao.data_realizada = datetime.datetime.strptime(request.form['data_realizada'], '%Y-%m-%d')
            manutencao.hor
(Content truncated due to size limit. Use line ranges to read in chunks)