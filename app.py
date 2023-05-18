from flask import Flask, render_template, request, session, redirect,jsonify
from flask_socketio import SocketIO,emit

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
socketio = SocketIO(app)

# Fila de senhas
fila_normal = []
fila_prioridade = []
senha_atual = None
guiche_atual = None
historico_chamados = []

proximo_numero_normal = 1
proximo_numero_prioridade = 1

@app.route('/', methods=['GET', 'POST'])
def index():
    global senha_atual, proximo_numero_normal, proximo_numero_prioridade

    if request.method == 'POST':
        if 'senha' in request.form:
            senha = request.form['senha']
            if senha == 'normal':
                fila_normal.append('N' + str(proximo_numero_normal))
                senha_atual = fila_normal[-1] if fila_normal else None
                proximo_numero_normal += 1  # Incrementa o número da próxima senha normal
            elif senha == 'prioridade':
                fila_prioridade.append('P' + str(proximo_numero_prioridade))
                senha_atual = fila_prioridade[-1] if fila_prioridade else None
                proximo_numero_prioridade += 1  # Incrementa o número da próxima senha de prioridade
    print(senha_atual)

    return render_template('index.html', fila_normal=fila_normal, fila_prioridade=fila_prioridade, senha_atual=senha_atual)


# Rota para operador fazer login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['guiche'] = request.form['guiche']
        session['nome'] = request.form['nome']
        return redirect('/operador')
    return render_template('login.html')

# Rota para operador chamar próxima senha
@app.route('/operador', methods=['GET', 'POST'])
def operator():
    if 'guiche' not in session:
        return redirect('/login')
    
    global senha_atual, guiche_atual, historico_chamados
    
    if request.method == 'POST':
        if len(fila_prioridade) > 0:
            senha_atual = fila_prioridade.pop(0)
        elif len(fila_normal) > 0:
            senha_atual = fila_normal.pop(0)
        
        if senha_atual is not None:
            historico_chamados.insert(0, (senha_atual, session['guiche']))
            if len(historico_chamados) > 3:
                historico_chamados = historico_chamados[:3]
            
            emit('senha_atualizada', {'senha_atual': senha_atual}, broadcast=True, namespace='/')  # Emitir evento
            
    return render_template('operator.html', senha_atual=senha_atual, guiche=session['guiche'], fila_normal=fila_normal, fila_prioridade=fila_prioridade)



# Rota para visualização da ficha atual e histórico de chamados
@app.route('/ficha_atual', methods=['GET'])
def ficha_atual():
    senha_atual = None
    guiche = session.get('guiche')
    historico = []

    if senha_atual is not None:
        historico.append((senha_atual, guiche))

    for chamado in historico_chamados:
        historico.append(chamado)

    return render_template('ficha_atual.html', senha_atual=senha_atual, guiche=guiche, historico=historico)



@app.route('/verificar_mudanca_historico')
def verificar_mudanca_historico():
    historico_antigo = session.get('historico_antigo', 0)
    historico_novo = len(historico_chamados)
    session['historico_antigo'] = historico_novo

    return jsonify(historico_antigo=historico_antigo, historico_novo=historico_novo)


@app.route('/comparar_historico')
def comparar_historico():
    return render_template('comparar_historico.html')


if __name__ == '__main__':
    app.static_folder = 'static'
    socketio.run(app, host='0.0.0.0', port=5000)
