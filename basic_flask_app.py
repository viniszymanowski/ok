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
        return f"Erro: {str(e)}"

@app.route('/logout')
def logout():
    try:
        logout_user()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Erro na rota de logout: {str(e)}")
        return f"Erro: {str(e)}"

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Contagem de colheitadeiras por status
        colheitadeiras_ativas = Colheitadeira.query.filter_by(status='Ativa').count()
        colheitadeiras_manutencao = Colheitadeira.query.filter_by(status='Em Manutenção').count()
        colheitadeiras_inativas = Colheitadeira.query.filter_by(status='Inativa').count()
        
        return render_template('dashboard.html', 
                              colheitadeiras_ativas=colheitadeiras_ativas,
                              colheitadeiras_manutencao=colheitadeiras_manutencao,
                              colheitadeiras_inativas=colheitadeiras_inativas)
    except Exception as e:
        logger.error(f"Erro na rota de dashboard: {str(e)}")
        return f"Erro: {str(e)}"

# Rotas para Colheitadeiras
@app.route('/colheitadeiras')
@login_required
def listar_colheitadeiras():
    try:
        colheitadeiras = Colheitadeira.query.all()
        return render_template('colheitadeiras/listar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao listar colheitadeiras: {str(e)}")
        return f"Erro: {str(e)}"

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
        return f"Erro: {str(e)}"

# Página de erro básica
@app.errorhandler(404)
def page_not_found(e):
    return "Página não encontrada", 404

@app.errorhandler(500)
def internal_server_error(e):
    return f"Erro interno do servidor: {str(e)}", 500

# Criar template de login básico
with app.app_context():
    try:
        os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
        login_template_path = os.path.join(app.root_path, 'templates', 'login.html')
        if not os.path.exists(login_template_path):
            with open(login_template_path, 'w') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Login - Sistema de Manutenção de Colheitadeiras</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            width: 300px;
        }
        .login-container h2 {
            text-align: center;
            color: #367C2B;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
        }
        .form-group input {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .btn {
            background-color: #367C2B;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
        }
        .btn:hover {
            background-color: #2A6021;
        }
        .flash-messages {
            margin-bottom: 15px;
        }
        .flash-message {
            padding: 10px;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 4px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Sistema de Manutenção de Colheitadeiras</h2>
        
        {% with messages = get_flashed_messages() %}
        {% if messages %}
        <div class="flash-messages">
            {% for message in messages %}
            <div class="flash-message">{{ message }}</div>
            {% endfor %}
        </div>
        {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Usuário:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Entrar</button>
        </form>
    </div>
</body>
</html>
                """)
    except Exception as e:
        logger.error(f"Erro ao criar template de login: {str(e)}")

# Criar template de dashboard básico
with app.app_context():
    try:
        os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
        dashboard_template_path = os.path.join(app.root_path, 'templates', 'dashboard.html')
        if not os.path.exists(dashboard_template_path):
            with open(dashboard_template_path, 'w') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Sistema de Manutenção de Colheitadeiras</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .header {
            background-color: #367C2B;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
        }
        .header a {
            color: white;
            text-decoration: none;
        }
        .container {
            padding: 20px;
        }
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        .card h2 {
            margin-top: 0;
            color: #367C2B;
        }
        .card-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .menu {
            background-color: #333;
            overflow: hidden;
        }
        .menu a {
            float: left;
            display: block;
            color: white;
            text-align: center;
            padding: 14px 16px;
            text-decoration: none;
        }
        .menu a:hover {
            background-color: #ddd;
            color: black;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Sistema de Manutenção de Colheitadeiras</h1>
        <a href="{{ url_for('logout') }}">Sair</a>
    </div>
    
    <div class="menu">
        <a href="{{ url_for('dashboard') }}">Dashboard</a>
        <a href="{{ url_for('listar_colheitadeiras') }}">Colheitadeiras</a>
    </div>
    
    <div class="container">
        <h2>Dashboard</h2>
        
        <div class="dashboard-cards">
            <div class="card">
                <h2>Colheitadeiras Ativas</h2>
                <div class="card-value">{{ colheitadeiras_ativas }}</div>
            </div>
            
            <div class="card">
                <h2>Colheitadeiras em Manutenção</h2>
                <div class="card-value">{{ colheitadeiras_manutencao }}</div>
            </div>
            
            <div class="card">
                <h2>Colheitadeiras Inativas</h2>
                <div class="card-value">{{ colheitadeiras_inativas }}</div>
            </div>
        </div>
    </div>
</body>
</html>
                """)
    except Exception as e:
        logger.error(f"Erro ao criar template de dashboard: {str(e)}")

# Criar diretório e template para colheitadeiras
with app.app_context():
    try:
        os.makedirs(os.path.join(app.root_path, 'templates', 'colheitadeiras'), exist_ok=True)
        listar_template_path = os.path.join(app.root_path, 'templates', 'colheitadeiras', 'listar.html')
        if not os.path.exists(listar_template_path):
            with open(listar_template_path, 'w') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Colheitadeiras - Sistema de Manutenção</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .header {
            background-color: #367C2B;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
        }
        .header a {
            color: white;
            text-decoration: none;
        }
        .container {
            padding: 20px;
        }
        .menu {
            background-color: #333;
            overflow: hidden;
        }
        .menu a {
            float: left;
            display: block;
            color: white;
            text-align: center;
            padding: 14px 16px;
            text-decoration: none;
        }
        .menu a:hover {
            background-color: #ddd;
            color: black;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #367C2B;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .btn {
            display: inline-block;
            background-color: #367C2B;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }
        .btn:hover {
            background-color: #2A6021;
        }
        .flash-messages {
            margin-bottom: 15px;
        }
        .flash-message {
            padding: 10px;
            background-color: #d4edda;
            color: #155724;
            border-radius: 4px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
   
(Content truncated due to size limit. Use line ranges to read in chunks)