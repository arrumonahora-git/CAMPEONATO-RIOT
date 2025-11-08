import json
import random
import os
from flask import Flask, request, jsonify, render_template

# --- Configurações/SDK Mercado Pago (Simplificado para este arquivo) ---
# Importe as funções de lógica e armazenamento dos módulos separados.
# Para este exemplo, usarei funções mockadas (de exemplo) e o token MP
# de teste para simular o ambiente da resposta anterior.

# Tente importar o SDK do Mercado Pago
try:
    import mercadopago
    MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-4028934087122957-091918-25cc9b5921a9c1b767605e28b3d44e48-188258998"
    sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
except ImportError:
    mercadopago = None

ARQUIVO_DADOS = 'torneio_lol_data.json'

# --- Funções Mock (Substitua por 'storage.py' e 'tournament.py' reais) ---
def salvar_torneio(torneio):
    """Salva os dados do torneio (Mock)."""
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(torneio, f, indent=4)
    return True

def carregar_torneio():
    """Carrega os dados do torneio (Mock)."""
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def criar_novo_torneio(nome):
    """Cria novo torneio (Mock)."""
    torneio = {"nome": nome, "jogadores": [], "partidas": [], "premios": {}, "rodada_atual": 0}
    salvar_torneio(torneio)
    return torneio

def adicionar_jogador_internamente(torneio, nome_jogador):
    """Adiciona jogador (Mock)."""
    if nome_jogador not in torneio["jogadores"]:
        torneio["jogadores"].append(nome_jogador)
        torneio["premios"][nome_jogador] = 0
        salvar_torneio(torneio)
        return True
    return False

def gerar_chaveamento_internamente(torneio):
    """Gera chaveamento (Mock - Lógica simplificada)."""
    jogadores_ativos = torneio["jogadores"]
    if len(jogadores_ativos) < 2:
        return {"status": "erro", "mensagem": "Mínimo de 2 jogadores."}
    random.shuffle(jogadores_ativos)
    torneio["partidas"] = [{"jogador1": jogadores_ativos[0], "jogador2": jogadores_ativos[1]}]
    torneio["rodada_atual"] += 1
    salvar_torneio(torneio)
    return {"status": "sucesso", "mensagem": "Chaveamento gerado!"}

def registrar_vencedor_internamente(torneio, vencedor, premio):
    """Registra vencedor (Mock - Lógica simplificada)."""
    if vencedor in torneio["jogadores"]:
        torneio["premios"][vencedor] += premio
        torneio["partidas"] = [] # Limpa a rodada
        salvar_torneio(torneio)
        return {"status": "sucesso", "mensagem": f"Vencedor {vencedor} registrado!"}
    return {"status": "erro", "mensagem": "Vencedor inválido."}

# --- Configuração Flask ---
app = Flask(__name__)

# --- Rotas do Flask (JSON/API) ---

@app.route('/')
def index():
    torneio = carregar_torneio() or criar_novo_torneio("Novo Torneio")
    # Usa render_template para carregar o arquivo templates/index.html
    return render_template('index.html', torneio=torneio)

@app.route('/criar-torneio', methods=['POST'])
def criar_torneio_route():
    dados = request.json
    nome = dados.get("nome", "Novo Torneio")
    criar_novo_torneio(nome)
    return jsonify({"status": "sucesso", "mensagem": f"Torneio '{nome}' criado com sucesso!"})

@app.route('/adicionar-jogador', methods=['POST'])
def adicionar_jogador_route():
    dados = request.json
    nome_jogador = dados.get("nome_jogador")
    email = dados.get("email")
    valor = dados.get("valor")

    if not nome_jogador or not email or not valor:
        return jsonify({"status": "erro", "mensagem": "Dados faltando."})

    torneio = carregar_torneio()
    if not torneio:
        return jsonify({"status": "erro", "mensagem": "Nenhum torneio ativo."})

    if not mercadopago:
        # Se o MP não estiver instalado, apenas adiciona o jogador
        adicionar_jogador_internamente(torneio, nome_jogador)
        return jsonify({"status": "sucesso", "mensagem": f"Jogador {nome_jogador} adicionado. (Pagamento ignorado: MP não instalado)"})

    try:
        # Lógica de Pagamento do Mercado Pago (inclusa na sua versão original)
        pagamento_data = {
            "transaction_amount": float(valor),
            "description": f"Inscrição Campeonato LoL - {nome_jogador}",
            "payment_method_id": "pix",
            "payer": {"email": email}
        }
        pagamento_response = sdk.payment().create(pagamento_data)
        
        if pagamento_response["status"] == 201:
            adicionar_jogador_internamente(torneio, nome_jogador)
            response_data = {
                "status": "sucesso",
                "mensagem": f"Pagamento criado. Player adicionado.",
                "id": pagamento_response['response']['id']
            }
            if 'point_of_interaction' in pagamento_response['response']:
                 # Retorna dados do QR Code para o JS
                response
                _data['point_of_interaction'] = pagamento_response['response']['point_of_interaction']
            return jsonify(response_data)
        else:
            return jsonify({"status": "erro", "mensagem": f"Erro MP: {pagamento_response['response']['message']}"})

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro no pagamento: {str(e)}."})


@app.route('/gerar-chaveamento', methods=['POST'])
def gerar_chaveamento_route():
    torneio = carregar_torneio()
    if not torneio:
        return jsonify({"status": "erro", "mensagem": "Nenhum torneio ativo."})
    return jsonify(gerar_chaveamento_internamente(torneio))

@app.route('/registrar-vencedor', methods=['POST'])
def registrar_vencedor_route():
    dados = request.json
    vencedor = dados.get("vencedor")
    premio = dados.get("premio")

    if not vencedor or premio is None:
        return jsonify({"status": "erro", "mensagem": "Dados faltando."})

    torneio = carregar_torneio()
    if not torneio:
        return jsonify({"status": "erro", "mensagem": "Nenhum torneio ativo."})
    
    return jsonify(registrar_vencedor_internamente(torneio, vencedor, float(premio)))

# --- Bloco de execução ---
if __name__ == '__main__':
    if not os.path.exists(ARQUIVO_DADOS):
        criar_novo_torneio("Torneio LoL Inicial")
    app.run(host='0.0.0.0', port=5000, debug=True)