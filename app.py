import os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# ==========================================
# BANCO DE DADOS (RAILWAY / POSTGRES)
# ==========================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Fallback para teste local
        db_url = "postgresql://postgres:VXpSeGRxpZZVgLWEuSsxSPLFqvfHMOzU@postgres.railway.internal:5432/railway"
    try:
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Erro no banco: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id SERIAL PRIMARY KEY,
                data_registro DATE DEFAULT CURRENT_DATE,
                valor_total NUMERIC(10, 2) NOT NULL,
                observacao TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insumos (
                id SERIAL PRIMARY KEY,
                data_compra DATE DEFAULT CURRENT_DATE,
                descricao TEXT NOT NULL,
                valor_total NUMERIC(10, 2) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()

init_db()

# ==========================================
# HTML + CSS (TAILWIND) + JAVASCRIPT EM UMA STRING
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PizzaControl Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Oculta as abas que não estão ativas */
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body class="bg-gray-100 text-gray-800 font-sans antialiased p-4 md:p-8">

    <div class="max-w-5xl mx-auto">
        <header class="mb-8 text-center md:text-left">
            <h1 class="text-4xl font-bold text-red-600 flex justify-center md:justify-start items-center gap-2">
                🍕 PizzaControl Pro
            </h1>
            <p class="text-gray-500 mt-2">Controle Diário de Insumos e Vendas</p>
        </header>

        <nav class="flex space-x-4 mb-6 border-b-2 border-gray-200 pb-2 overflow-x-auto">
            <button onclick="openTab('dash')" class="tab-btn font-semibold text-red-600 border-b-2 border-red-600 px-2 py-1 focus:outline-none whitespace-nowrap" id="btn-dash">📊 Painel</button>
            <button onclick="openTab('vendas')" class="tab-btn font-semibold text-gray-500 px-2 py-1 hover:text-red-500 focus:outline-none whitespace-nowrap" id="btn-vendas">📸 Vendas</button>
            <button onclick="openTab('insumos')" class="tab-btn font-semibold text-gray-500 px-2 py-1 hover:text-red-500 focus:outline-none whitespace-nowrap" id="btn-insumos">🛒 Insumos</button>
        </nav>

        <div id="dash" class="tab-content active">
            <h2 class="text-2xl font-bold mb-4">Resumo do Mês</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
                    <h3 class="text-gray-500 text-sm">Faturamento (Mês)</h3>
                    <p class="text-3xl font-bold text-gray-800">R$ {{ "%.2f"|format(total_vendas) }}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-red-500">
                    <h3 class="text-gray-500 text-sm">Custos c/ Insumos (Mês)</h3>
                    <p class="text-3xl font-bold text-gray-800">R$ {{ "%.2f"|format(total_insumos) }}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500">
                    <h3 class="text-gray-500 text-sm">Lucro Líquido</h3>
                    <p class="text-3xl font-bold text-gray-800">R$ {{ "%.2f"|format(total_vendas - total_insumos) }}</p>
                </div>
            </div>

            <h2 class="text-xl font-bold mb-4">Últimas Movimentações</h2>
            <div class="bg-white rounded-lg shadow-md overflow-x-auto">
                <table class="min-w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-800 text-white">
                            <th class="py-3 px-4 border-b">Data</th>
                            <th class="py-3 px-4 border-b">Tipo</th>
                            <th class="py-3 px-4 border-b">Descrição/Obs</th>
                            <th class="py-3 px-4 border-b">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for mov in movimentacoes %}
                        <tr class="hover:bg-gray-50 border-b">
                            <td class="py-3 px-4">{{ mov.data }}</td>
                            <td class="py-3 px-4">
                                {% if mov.tipo == 'Venda' %}
                                    <span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">{{ mov.tipo }}</span>
                                {% else %}
                                    <span class="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">{{ mov.tipo }}</span>
                                {% endif %}
                            </td>
                            <td class="py-3 px-4 truncate max-w-xs">{{ mov.descricao }}</td>
                            <td class="py-3 px-4 font-semibold text-gray-700">R$ {{ "%.2f"|format(mov.valor_total) }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" class="py-4 text-center text-gray-500">Nenhuma movimentação registrada.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div id="vendas" class="tab-content">
            <div class="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Registrar Venda / Fechamento</h2>
                
                <form action="/add_venda" method="POST" enctype="multipart/form-data" class="space-y-4">
                    <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition">
                        <label class="cursor-pointer block">
                            <span class="text-4xl">📸</span>
                            <span class="block mt-2 text-sm font-semibold text-gray-700">Tirar Foto do Relatório</span>
                            <input type="file" name="foto_relatorio" accept="image/*" capture="environment" class="hidden">
                        </label>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Data do Fechamento</label>
                            <input type="date" name="data" required class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Valor Total (R$)</label>
                            <input type="number" name="valor" step="0.01" required placeholder="0.00" class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2">
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">Observações (Opcional)</label>
                        <textarea name="observacao" rows="3" placeholder="Ex: R$200 no pix..." class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2"></textarea>
                    </div>

                    <button type="submit" class="w-full bg-red-600 text-white font-bold py-3 px-4 rounded hover:bg-red-700 transition">
                        Salvar Venda
                    </button>
                </form>
            </div>
        </div>

        <div id="insumos" class="tab-content">
            <div class="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Registrar Compra de Insumo</h2>
                
                <form action="/add_insumo" method="POST" enctype="multipart/form-data" class="space-y-4">
                    <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition">
                        <label class="cursor-pointer block">
                            <span class="text-4xl">🧾</span>
                            <span class="block mt-2 text-sm font-semibold text-gray-700">Tirar Foto do Cupom Fiscal</span>
                            <input type="file" name="foto_cupom" accept="image/*" capture="environment" class="hidden">
                        </label>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Data da Compra</label>
                            <input type="date" name="data" required class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Valor Total da Nota (R$)</label>
                            <input type="number" name="valor" step="0.01" required placeholder="0.00" class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2">
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">Descrição</label>
                        <input type="text" name="descricao" required placeholder="Ex: Compra de Muçarela e Tomate" class="mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 border p-2">
                    </div>

                    <button type="submit" class="w-full bg-gray-800 text-white font-bold py-3 px-4 rounded hover:bg-gray-900 transition">
                        Registrar Custo
                    </button>
                </form>
            </div>
        </div>
    </div>

    <script>
        function openTab(tabName) {
            // Esconde todo o conteudo
            var contents = document.getElementsByClassName("tab-content");
            for (var i = 0; i < contents.length; i++) {
                contents[i].style.display = "none";
            }
            
            // Tira o foco (cor vermelha) dos botoes
            var btns = document.getElementsByClassName("tab-btn");
            for (var i = 0; i < btns.length; i++) {
                btns[i].classList.remove("text-red-600", "border-b-2", "border-red-600");
                btns[i].classList.add("text-gray-500");
            }
            
            // Mostra o conteudo atual e acende o botao
            document.getElementById(tabName).style.display = "block";
            document.getElementById("btn-" + tabName).classList.add("text-red-600", "border-b-2", "border-red-600");
            document.getElementById("btn-" + tabName).classList.remove("text-gray-500");
        }
        
        // Define a data de hoje nos inputs de data automaticamente
        document.addEventListener('DOMContentLoaded', (event) => {
            let today = new Date().toISOString().split('T')[0];
            document.querySelectorAll('input[type="date"]').forEach(el => el.value = today);
        });
    </script>
</body>
</html>
"""

# ==========================================
# ROTAS DO BACKEND (FLASK)
# ==========================================

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "Aguardando configuração do Banco de Dados..."
    
    cur = conn.cursor()
    
    # Cálculos do Mês Atual
    cur.execute("""
        SELECT COALESCE(SUM(valor_total), 0) as total FROM vendas 
        WHERE EXTRACT(MONTH FROM data_registro) = EXTRACT(MONTH FROM CURRENT_DATE)
    """)
    total_vendas = cur.fetchone()['total']
    
    cur.execute("""
        SELECT COALESCE(SUM(valor_total), 0) as total FROM insumos 
        WHERE EXTRACT(MONTH FROM data_compra) = EXTRACT(MONTH FROM CURRENT_DATE)
    """)
    total_insumos = cur.fetchone()['total']
    
    # Histórico unificado (limite de 10)
    cur.execute("""
        SELECT data_registro as data, 'Venda' as tipo, observacao as descricao, valor_total 
        FROM vendas 
        UNION ALL 
        SELECT data_compra as data, 'Insumo' as tipo, descricao, valor_total 
        FROM insumos 
        ORDER BY data DESC LIMIT 10
    """)
    movimentacoes = cur.fetchall()
    
    cur.close()
    conn.close()

    # Renderiza o HTML gigante ali de cima passando os dados do Python
    return render_template_string(HTML_TEMPLATE, 
                                  total_vendas=total_vendas, 
                                  total_insumos=total_insumos, 
                                  movimentacoes=movimentacoes)

@app.route('/add_venda', methods=['POST'])
def add_venda():
    data = request.form.get('data')
    valor = request.form.get('valor')
    obs = request.form.get('observacao')
    # A foto vem aqui: foto = request.files.get('foto_relatorio')
    # Aqui você conectaria com a API do Gemini futuramente
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vendas (data_registro, valor_total, observacao) VALUES (%s, %s, %s)",
        (data, valor, obs)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/add_insumo', methods=['POST'])
def add_insumo():
    data = request.form.get('data')
    valor = request.form.get('valor')
    descricao = request.form.get('descricao')
    # A foto vem aqui: foto = request.files.get('foto_cupom')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO insumos (data_compra, descricao, valor_total) VALUES (%s, %s, %s)",
        (data, descricao, valor)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('index'))

# Ponto de entrada para rodar localmente ou no servidor
if __name__ == '__main__':
    # O Railway passa a porta dinamicamente na variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
