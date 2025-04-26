import os
import zipfile
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, Usuario, Colheitadeira, ManutencaoPreventiva, ManutencaoCorretiva, RegistroHorimetro, TrocaOleo, ItemEstoque, MovimentacaoEstoque
import config

app = Flask(__name__)
app.config.from_object(config)

# Configuração do banco de dados
db.init_app(app)

# Configuração do login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rotas de autenticação
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Contagem de colheitadeiras
    total_colheitadeiras = Colheitadeira.query.count()
    
    # Manutenções pendentes
    manutencoes_preventivas_pendentes = ManutencaoPreventiva.query.filter_by(status='Pendente').count()
    manutencoes_corretivas_em_andamento = ManutencaoCorretiva.query.filter_by(status='Em Andamento').count()
    
    # Próximas trocas de óleo
    proximas_trocas = TrocaOleo.query.order_by(TrocaOleo.proxima_troca).limit(5).all()
    
    # Alertas de estoque
    alertas_estoque = ItemEstoque.query.filter(ItemEstoque.quantidade <= ItemEstoque.quantidade_minima).count()
    
    # Últimos registros de horímetro
    ultimos_registros = RegistroHorimetro.query.order_by(RegistroHorimetro.data.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          total_colheitadeiras=total_colheitadeiras,
                          manutencoes_preventivas_pendentes=manutencoes_preventivas_pendentes,
                          manutencoes_corretivas_em_andamento=manutencoes_corretivas_em_andamento,
                          proximas_trocas=proximas_trocas,
                          alertas_estoque=alertas_estoque,
                          ultimos_registros=ultimos_registros)

# Rotas para Colheitadeiras
@app.route('/colheitadeiras')
@login_required
def listar_colheitadeiras():
    colheitadeiras = Colheitadeira.query.all()
    return render_template('colheitadeiras/listar.html', colheitadeiras=colheitadeiras)

@app.route('/colheitadeiras/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_colheitadeira():
    if request.method == 'POST':
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        numero_frota = request.form.get('numero_frota')
        status = request.form.get('status')
        
        colheitadeira = Colheitadeira(
            modelo=modelo,
            ano=ano,
            numero_frota=numero_frota,
            status=status
        )
        
        db.session.add(colheitadeira)
        db.session.commit()
        
        flash('Colheitadeira adicionada com sucesso!', 'success')
        return redirect(url_for('listar_colheitadeiras'))
    
    return render_template('colheitadeiras/adicionar.html')

@app.route('/colheitadeiras/<int:id>')
@login_required
def visualizar_colheitadeira(id):
    colheitadeira = Colheitadeira.query.get_or_404(id)
    
    # Obter manutenções preventivas
    manutencoes_preventivas = ManutencaoPreventiva.query.filter_by(colheitadeira_id=id).all()
    
    # Obter manutenções corretivas
    manutencoes_corretivas = ManutencaoCorretiva.query.filter_by(colheitadeira_id=id).all()
    
    # Obter registros de horímetro
    registros_horimetro = RegistroHorimetro.query.filter_by(colheitadeira_id=id).order_by(RegistroHorimetro.data.desc()).all()
    
    # Obter trocas de óleo
    trocas_oleo = TrocaOleo.query.filter_by(colheitadeira_id=id).order_by(TrocaOleo.data.desc()).all()
    
    return render_template('colheitadeiras/visualizar.html', 
                          colheitadeira=colheitadeira,
                          manutencoes_preventivas=manutencoes_preventivas,
                          manutencoes_corretivas=manutencoes_corretivas,
                          registros_horimetro=registros_horimetro,
                          trocas_oleo=trocas_oleo)

@app.route('/colheitadeiras/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colheitadeira(id):
    colheitadeira = Colheitadeira.query.get_or_404(id)
    
    if request.method == 'POST':
        colheitadeira.modelo = request.form.get('modelo')
        colheitadeira.ano = request.form.get('ano')
        colheitadeira.numero_frota = request.form.get('numero_frota')
        colheitadeira.status = request.form.get('status')
        
        db.session.commit()
        
        flash('Colheitadeira atualizada com sucesso!', 'success')
        return redirect(url_for('listar_colheitadeiras'))
    
    return render_template('colheitadeiras/editar.html', colheitadeira=colheitadeira)

# Rotas para Manutenções Preventivas
@app.route('/manutencoes/preventivas')
@login_required
def listar_manutencoes_preventivas():
    manutencoes = ManutencaoPreventiva.query.all()
    return render_template('manutencoes/preventivas/listar.html', manutencoes=manutencoes)

@app.route('/manutencoes/preventivas/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_manutencao_preventiva():
    colheitadeiras = Colheitadeira.query.all()
    
    if request.method == 'POST':
        colheitadeira_id = request.form.get('colheitadeira_id')
        descricao = request.form.get('descricao')
        data_agendada = request.form.get('data_agendada')
        horimetro_agendado = request.form.get('horimetro_agendado')
        
        manutencao = ManutencaoPreventiva(
            colheitadeira_id=colheitadeira_id,
            descricao=descricao,
            data_agendada=data_agendada,
            horimetro_agendado=horimetro_agendado,
            status='Pendente'
        )
        
        db.session.add(manutencao)
        db.session.commit()
        
        flash('Manutenção preventiva agendada com sucesso!', 'success')
        return redirect(url_for('listar_manutencoes_preventivas'))
    
    return render_template('manutencoes/preventivas/adicionar.html', colheitadeiras=colheitadeiras)

@app.route('/manutencoes/preventivas/realizar/<int:id>', methods=['GET', 'POST'])
@login_required
def realizar_manutencao_preventiva(id):
    manutencao = ManutencaoPreventiva.query.get_or_404(id)
    
    if request.method == 'POST':
        manutencao.data_realizacao = request.form.get('data_realizacao')
        manutencao.observacoes = request.form.get('observacoes')
        manutencao.status = 'Realizada'
        
        # Atualizar status da colheitadeira
        colheitadeira = Colheitadeira.query.get(manutencao.colheitadeira_id)
        colheitadeira.status = 'Ativa'
        
        db.session.commit()
        
        flash('Manutenção preventiva realizada com sucesso!', 'success')
        return redirect(url_for('listar_manutencoes_preventivas'))
    
    return render_template('manutencoes/preventivas/realizar.html', manutencao=manutencao)

# Rotas para Manutenções Corretivas
@app.route('/manutencoes/corretivas')
@login_required
def listar_manutencoes_corretivas():
    manutencoes = ManutencaoCorretiva.query.all()
    return render_template('manutencoes/corretivas/listar.html', manutencoes=manutencoes)

@app.route('/manutencoes/corretivas/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_manutencao_corretiva():
    colheitadeiras = Colheitadeira.query.all()
    
    if request.method == 'POST':
        colheitadeira_id = request.form.get('colheitadeira_id')
        descricao_falha = request.form.get('descricao_falha')
        data_inicio = request.form.get('data_inicio')
        
        manutencao = ManutencaoCorretiva(
            colheitadeira_id=colheitadeira_id,
            descricao_falha=descricao_falha,
            data_inicio=data_inicio,
            status='Em Andamento'
        )
        
        db.session.add(manutencao)
        
        # Atualizar status da colheitadeira
        colheitadeira = Colheitadeira.query.get(colheitadeira_id)
        colheitadeira.status = 'Em Manutenção'
        
        db.session.commit()
        
        flash('Manutenção corretiva registrada com sucesso!', 'success')
        return redirect(url_for('listar_manutencoes_corretivas'))
    
    return render_template('manutencoes/corretivas/adicionar.html', colheitadeiras=colheitadeiras)

@app.route('/manutencoes/corretivas/concluir/<int:id>', methods=['GET', 'POST'])
@login_required
def concluir_manutencao_corretiva(id):
    manutencao = ManutencaoCorretiva.query.get_or_404(id)
    itens_estoque = ItemEstoque.query.all()
    
    if request.method == 'POST':
        manutencao.data_conclusao = request.form.get('data_conclusao')
        manutencao.solucao = request.form.get('solucao')
        manutencao.pecas_substituidas = request.form.get('pecas_substituidas')
        manutencao.status = 'Concluída'
        
        # Atualizar status da colheitadeira
        colheitadeira = Colheitadeira.query.get(manutencao.colheitadeira_id)
        colheitadeira.status = 'Ativa'
        
        # Registrar uso de peças do estoque
        pecas_ids = request.form.getlist('peca_id')
        quantidades = request.form.getlist('quantidade')
        
        for i in range(len(pecas_ids)):
            if pecas_ids[i] and quantidades[i]:
                peca_id = int(pecas_ids[i])
                quantidade = int(quantidades[i])
                
                item = ItemEstoque.query.get(peca_id)
                if item and item.quantidade >= quantidade:
                    item.quantidade -= quantidade
                    
                    # Registrar movimentação
                    movimentacao = MovimentacaoEstoque(
                        item_id=peca_id,
                        tipo='Saída',
                        quantidade=quantidade,
                        data=datetime.now(),
                        observacao=f'Utilizado na manutenção corretiva #{manutencao.id}'
                    )
                    db.session.add(movimentacao)
        
        db.session.commit()
        
        flash('Manutenção corretiva concluída com sucesso!', 'success')
        return redirect(url_for('listar_manutencoes_corretivas'))
    
    return render_template('manutencoes/corretivas/concluir.html', manutencao=manutencao, itens_estoque=itens_estoque)

# Rotas para Registros de Horímetro
@app.route('/registros-horimetro')
@login_required
def listar_registros_horimetro():
    registros = RegistroHorimetro.query.order_by(RegistroHorimetro.data.desc()).all()
    return render_template('registros_horimetro/listar.html', registros=registros)

@app.route('/registros-horimetro/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_registro_horimetro():
    colheitadeiras = Colheitadeira.query.all()
    
    if request.method == 'POST':
        colheitadeira_id = request.form.get('colheitadeira_id')
        valor = request.form.get('valor')
        data = request.form.get('data')
        
        registro = RegistroHorimetro(
            colheitadeira_id=colheitadeira_id,
            valor=valor,
            data=data
        )
        
        db.session.add(registro)
        db.session.commit()
        
        # Verificar se há manutenções preventivas agendadas por horímetro
        manutencoes = ManutencaoPreventiva.query.filter_by(
            colheitadeira_id=colheitadeira_id,
            status='Pendente'
        ).filter(
            ManutencaoPreventiva.horimetro_agendado <= valor
        ).all()
        
        if manutencoes:
            flash(f'Atenção: Existem {len(manutencoes)} manutenções preventivas pendentes que atingiram o valor de horímetro programado!', 'warning')
        
        flash('Registro de horímetro adicionado com sucesso!', 'success')
        return redirect(url_for('listar_registros_horimetro'))
    
    return render_template('registros_horimetro/adicionar.html', colheitadeiras=colheitadeiras)

# Rotas para Trocas de Óleo
@app.route('/trocas-oleo')
@login_required
def listar_trocas_oleo():
    trocas = TrocaOleo.query.order_by(TrocaOleo.data.desc()).all()
    return render_template('trocas_oleo/listar.html', trocas=trocas)

@app.route('/trocas-oleo/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_troca_oleo():
    colheitadeiras = Colheitadeira.query.all()
    
    if request.method == 'POST':
        colheitadeira_id = request.form.get('colheitadeira_id')
        data = request.form.get('data')
        horimetro = request.form.get('horimetro')
        tipo_oleo = request.form.get('tipo_oleo')
        quantidade = request.form.get('quantidade')
        proxima_troca = request.form.get('proxima_troca')
        
        troca = TrocaOleo(
            colheitadeira_id=colheitadeira_id,
            data=data,
            horimetro=horimetro,
            tipo_oleo=tipo_oleo,
            quantidade=quantidade,
            proxima_troca=proxima_troca
        )
        
        db.session.add(troca)
        
        # Registrar saída do óleo do estoque
        item_oleo = ItemEstoque.query.filter_by(nome=tipo_oleo).first()
        if item_oleo and item_oleo.quantidade >= float(quantidade):
            item_oleo.quantidade -= float(quantidade)
            
            # Registrar movimentação
            movimentacao = MovimentacaoEstoque(
                item_id=item_oleo.id,
                tipo='Saída',
                quantidade=float(quantidade),
                data=datetime.now(),
                observacao=f'Utilizado na troca de óleo da colheitadeira #{colheitadeira_id}'
            )
            db.session.add(movimentacao)
        
        db.session.commit()
        
        flash('Troca de óleo registrada com sucesso!', 'success')
        return redirect(url_for('listar_trocas_oleo'))
    
    return render_template('trocas_oleo/adicionar.html', colheitadeiras=colheitadeiras)

# Rotas para Estoque
@app.route('/estoque')
@login_required
def listar_estoque():
    itens = ItemEstoque.query.all()
    return render_template('estoque/listar.html', itens=itens)

@app.route('/estoque/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_item_estoque():
    if request.method == 'POST':
        nome = request.form.get('nome')
        codigo = request.form.get('codigo')
        categoria = request.form.get('categoria')
        quantidade = request.form.get('quantidade')
        quantidade_minima = request.form.get('quantidade_minima')
        unidade = request.form.get('unidade')
        localizacao = request.form.get('localizacao')
        
        item = ItemEstoque(
            nome=nome,
            codigo=codigo,
            categoria=categoria,
            quantidade=quantidade,
            quantidade_minima=quantidade_minima,
            unidade=unidade,
            localizacao=localizacao
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('
(Content truncated due to size limit. Use line ranges to read in chunks)