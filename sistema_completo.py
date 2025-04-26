from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
import logging
import json
from functools import wraps

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sistema_manutencao_agricola_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)
        
    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Colheitadeira(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    numero_serie = db.Column(db.String(50), unique=True, nullable=False)
    numero_frota = db.Column(db.String(20), unique=True, nullable=False)
    data_aquisicao = db.Column(db.Date, nullable=False)
    ultima_manutencao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Operacional')
    horimetro_atual = db.Column(db.Float, default=0)
    observacoes = db.Column(db.Text, nullable=True)
    
    manutencoes_preventivas = db.relationship('ManutencaoPreventiva', backref='colheitadeira', lazy=True)
    manutencoes_corretivas = db.relationship('ManutencaoCorretiva', backref='colheitadeira', lazy=True)
    trocas_oleo = db.relationship('TrocaOleo', backref='colheitadeira', lazy=True)
    registros_horimetro = db.relationship('RegistroHorimetro', backref='colheitadeira', lazy=True)

class ManutencaoPreventiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_planejada = db.Column(db.Date, nullable=False)
    horimetro_planejado = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='Pendente')
    data_realizada = db.Column(db.Date, nullable=True)
    responsavel = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

class ManutencaoCorretiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    descricao_falha = db.Column(db.Text, nullable=False)
    data_registro = db.Column(db.Date, nullable=False)
    horimetro = db.Column(db.Float, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    data_conclusao = db.Column(db.Date, nullable=True)
    solucao = db.Column(db.Text, nullable=True)
    pecas_substituidas = db.Column(db.Text, nullable=True)
    responsavel = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

class TrocaOleo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    tipo_oleo = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    data_troca = db.Column(db.Date, nullable=False)
    horimetro = db.Column(db.Float, nullable=False)
    proxima_troca = db.Column(db.Float, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

class RegistroHorimetro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    data_registro = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

class ItemEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(50), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Float, default=0)
    estoque_minimo = db.Column(db.Float, default=0)
    valor_unitario = db.Column(db.Float, default=0)
    localizacao = db.Column(db.String(100), nullable=True)
    fornecedor = db.Column(db.String(100), nullable=True)
    data_atualizacao = db.Column(db.Date, default=datetime.datetime.now().date())
    observacoes = db.Column(db.Text, nullable=True)
    
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='item', lazy=True)

class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # Entrada ou Saída
    quantidade = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    observacao = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rotas
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha):
            login_user(usuario)
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos!')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Contagem de colheitadeiras por status
        total_colheitadeiras = Colheitadeira.query.count()
        colheitadeiras_operacionais = Colheitadeira.query.filter_by(status='Operacional').count()
        colheitadeiras_manutencao = Colheitadeira.query.filter_by(status='Em Manutenção').count()
        colheitadeiras_inativas = Colheitadeira.query.filter_by(status='Inativa').count()
        
        # Manutenções pendentes
        manutencoes_preventivas_pendentes = ManutencaoPreventiva.query.filter_by(status='Pendente').count()
        manutencoes_corretivas_pendentes = ManutencaoCorretiva.query.filter_by(status='Pendente').count()
        
        # Próximas trocas de óleo
        proximas_trocas = db.session.query(
            Colheitadeira.numero_frota,
            Colheitadeira.modelo,
            TrocaOleo.tipo_oleo,
            TrocaOleo.proxima_troca,
            Colheitadeira.horimetro_atual
        ).join(TrocaOleo).filter(
            TrocaOleo.proxima_troca - Colheitadeira.horimetro_atual <= 100
        ).order_by(
            (TrocaOleo.proxima_troca - Colheitadeira.horimetro_atual)
        ).limit(5).all()
        
        # Itens com estoque baixo
        itens_estoque_baixo = ItemEstoque.query.filter(
            ItemEstoque.quantidade <= ItemEstoque.estoque_minimo
        ).count()
        
        return render_template(
            'dashboard.html',
            total_colheitadeiras=total_colheitadeiras,
            colheitadeiras_operacionais=colheitadeiras_operacionais,
            colheitadeiras_manutencao=colheitadeiras_manutencao,
            colheitadeiras_inativas=colheitadeiras_inativas,
            manutencoes_preventivas_pendentes=manutencoes_preventivas_pendentes,
            manutencoes_corretivas_pendentes=manutencoes_corretivas_pendentes,
            proximas_trocas=proximas_trocas,
            itens_estoque_baixo=itens_estoque_baixo
        )
    except Exception as e:
        logger.error(f"Erro no dashboard: {str(e)}")
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
            numero_serie = request.form['numero_serie']
            numero_frota = request.form['numero_frota']
            data_aquisicao = datetime.datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d')
            horimetro_atual = float(request.form['horimetro_atual'])
            status = request.form['status']
            observacoes = request.form.get('observacoes', '')
            
            colheitadeira = Colheitadeira(
                modelo=modelo,
                ano=ano,
                numero_serie=numero_serie,
                numero_frota=numero_frota,
                data_aquisicao=data_aquisicao,
                horimetro_atual=horimetro_atual,
                status=status,
                observacoes=observacoes
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
            colheitadeira.numero_serie = request.form['numero_serie']
            colheitadeira.numero_frota = request.form['numero_frota']
            colheitadeira.data_aquisicao = datetime.datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d')
            colheitadeira.horimetro_atual = float(request.form['horimetro_atual'])
            colheitadeira.status = request.form['status']
            colheitadeira.observacoes = request.form.get('observacoes', '')
            
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
        
        # Obter manutenções preventivas
        manutencoes_preventivas = ManutencaoPreventiva.query.filter_by(colheitadeira_id=id).order_by(ManutencaoPreventiva.data_planejada.desc()).all()
        
        # Obter manutenções corretivas
        manutencoes_corretivas = ManutencaoCorretiva.query.filter_by(colheitadeira_id=id).order_by(ManutencaoCorretiva.data_registro.desc()).all()
        
        # Obter trocas de óleo
        trocas_oleo = TrocaOleo.query.filter_by(colheitadeira_id=id).order_by(TrocaOleo.data_troca.desc()).all()
        
        # Obter registros de horímetro
        registros_horimetro = RegistroHorimetro.query.filter_by(colheitadeira_id=id).order_by(RegistroHorimetro.data_registro.desc()).all()
        
        return render_template(
            'colheitadeiras/visualizar.html',
            colheitadeira=colheitadeira,
            manutencoes_preventivas=manutencoes_preventivas,
            manutencoes_corretivas=manutencoes_corretivas,
            trocas_oleo=trocas_oleo,
            registros_horimetro=registros_horimetro
        )
    except Exception as e:
        logger.error(f"Erro ao visualizar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Manutenções Preventivas
@app.route('/manutencoes/preventivas')
@login_required
def listar_manutencoes_preventivas():
    try:
        manutencoes = db.session.query(
            ManutencaoPreventiva,
            Colheitadeira.numero_frota,
            Colheitadeira.modelo
        ).join(Colheitadeira).order_by(ManutencaoPreventiva.data_planejada).all()
        
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
            tipo = request.form['tipo']
            descricao = request.form['descricao']
            data_planejada = datetime.datetime.strptime(request.form['data_planejada'], '%Y-%m-%d')
            horimetro_planejado = float(request.form['horimetro_planejado']) if request.form['horimetro_planejado'] else None
            observacoes = request.form.get('observacoes', '')
            
            manutencao = ManutencaoPreventiva(
                colheitadeira_id=colheitadeira_id,
                tipo=tipo,
                descricao=descricao,
                data_planejada=data_planejada,
                horimetro_planejado=horimetro_planejado,
                status='Pendente',
                observacoes=observacoes
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
        colheitadeira = Colheitadeira.query.get(manutencao.colheitadei
(Content truncated due to size limit. Use line ranges to read in chunks)