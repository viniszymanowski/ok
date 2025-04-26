# Guia de Implantação Simplificada do Sistema de Manutenção de Colheitadeiras

Este guia visual passo a passo foi criado para facilitar a implantação do Sistema de Controle de Manutenção de Colheitadeiras John Deere na plataforma Render, com o mínimo de intervenção manual possível.

## Pré-requisitos
- Acesso à internet
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- O arquivo ZIP do sistema que foi fornecido

## Implantação em 5 Cliques Simples

### Passo 1: Acessar o Render
1. Abra seu navegador e acesse [render.com](https://render.com)
2. Clique em "Sign Up" no canto superior direito (ou faça login se já tiver uma conta)
3. Você pode se registrar usando seu email, conta Google ou GitHub

### Passo 2: Criar um Novo Serviço Web
1. No Dashboard do Render, clique no botão azul "New +" no canto superior direito
2. Selecione "Web Service" nas opções apresentadas

### Passo 3: Configurar o Serviço
1. Na seção "Deploy from my computer", clique em "Upload Files"
2. Selecione o arquivo ZIP do sistema que você baixou
3. Preencha os seguintes campos:
   - **Nome**: sistema-manutencao-colheitadeiras (ou outro nome de sua preferência)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plano**: Free

4. Em "Advanced", adicione as seguintes variáveis de ambiente:
   - Nome: `FLASK_APP` | Valor: `app.py`
   - Nome: `FLASK_ENV` | Valor: `production`
   - Nome: `SECRET_KEY` | Valor: `sistema_manutencao_secret_key`

5. Clique no botão "Create Web Service" na parte inferior da página

### Passo 4: Inicializar o Banco de Dados
1. Quando a implantação estiver concluída (isso pode levar alguns minutos), vá para a seção "Shell" do seu serviço
2. Execute o comando: `python init_db.py`
3. Aguarde a confirmação de que o banco de dados foi inicializado com sucesso

### Passo 5: Acessar o Sistema
1. Volte para a página principal do seu serviço no Render
2. Clique no link fornecido (algo como https://sistema-manutencao-colheitadeiras.onrender.com)
3. Faça login usando as credenciais:
   - **Administrador**: admin / admin123
   - **Técnico**: tecnico / tecnico123
   - **Operador**: operador / operador123

## Solução de Problemas Comuns

### Erro "Application Error" ao acessar o site
- **Causa**: O serviço pode estar iniciando após período de inatividade
- **Solução**: Aguarde 1-2 minutos e atualize a página
- **Alternativa**: Acesse a página "Logs" no Render para verificar o status

### Erro durante a implantação
- **Causa**: Problemas com o formato do arquivo ZIP ou dependências
- **Solução**: Verifique os logs de erro no Render e certifique-se de que o ZIP contém diretamente os arquivos do projeto

### Erro ao inicializar o banco de dados
- **Causa**: Problemas de permissão ou banco de dados já existente
- **Solução**: Execute `rm instance/sistema.db` seguido de `python init_db.py`

### Lentidão no primeiro acesso
- **Causa**: No plano gratuito, o serviço fica inativo após períodos sem uso
- **Solução**: O primeiro acesso após inatividade pode levar até 30 segundos para responder

## Suporte Técnico
Se você encontrar qualquer dificuldade durante o processo de implantação, entre em contato pelo email sistema.manutencao.agricola@gmail.com para obter assistência personalizada.
