from flask import Flask, render_template, request, flash
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# Adiciona a pasta Lógica ao path (garante que os módulos sejam encontrados)
sys.path.append(os.path.join(os.path.dirname(__file__), "Logica"))

# Importa os módulos de busca (esses são funções nos seus arquivos)
from Logica.busca_booleana import busca_booleana
from Logica.busca_espaco_vetorial import busca_espaco_vetorial

app = Flask(__name__)
app.secret_key = "troque_essa_chave_em_producao"


# Helpers de caminho / execução
BASE_DIR = Path(__file__).parent.resolve()
JSONS_DIR = BASE_DIR / "JSONs"

def localizar_json(nome_arquivo: str) -> str:
    caminho = JSONS_DIR / nome_arquivo
    if caminho.exists():
        return str(caminho)
    # fallback procurado por segurança (subpastas relativas)
    alt = BASE_DIR / nome_arquivo
    if alt.exists():
        return str(alt)
    raise FileNotFoundError(f"{nome_arquivo} não encontrado em {JSONS_DIR} nem em {BASE_DIR}")

def executar_script(nome_script: str):
    """Executa um script python dentro da pasta Logica (sem importar)."""
    path_script = BASE_DIR / "Logica" / nome_script
    if not path_script.exists():
        raise FileNotFoundError(f"Script {nome_script} não encontrado em {path_script}")
    print(f"Executando {nome_script} ...")
    subprocess.run([sys.executable, str(path_script)], check=True)
    print(f"{nome_script} finalizado.")


# Carregamento/Preparação dos JSONs

# caminhos esperados
PATH_DADOS_PREPARADOS = JSONS_DIR / "dadospreparados.json"
PATH_DADOS_TOKENIZADOS = JSONS_DIR / "dados_tokenizados.json"
PATH_TERMS = JSONS_DIR / "termos_significativos.json"
PATH_METADADOS = JSONS_DIR / "metadados.json"

# Executa preparacao/tokenizacao se necessário
if not PATH_DADOS_PREPARADOS.exists():
    try:
        executar_script("preparacao.py")
    except Exception as e:
        print("Erro ao executar preparacao.py:", e)

if not PATH_DADOS_TOKENIZADOS.exists():
    try:
        executar_script("tokenizacao.py")
    except Exception as e:
        print("Erro ao executar tokenizacao.py:", e)

# Carrega arrays JSON
def carregar_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

try:
    documentos_preparados = carregar_json(PATH_DADOS_PREPARADOS)
except Exception as e:
    documentos_preparados = []
    print("Erro ao ler dadospreparados.json:", e)

try:
    metadados = carregar_json(PATH_METADADOS)
except Exception as e:
    metadados = []
    print("Erro ao ler metadados.json:", e)

# Mapas para acesso rápido
META_MAP = {int(m.get("DocId")): m for m in metadados} if metadados else {}
PREP_MAP = {int(d.get("DocId")): d for d in documentos_preparados} if documentos_preparados else {}


# Utilitários para resultado
def snippet_from_doc(doc_id: int, max_chars: int = 250) -> str:
    """Tenta extrair um trecho do resumo (prioriza metadados, senão dados preparados)."""
    meta = META_MAP.get(doc_id, {})
    full = meta.get("Resumo") or meta.get("ResumoCompleto") or ""
    if not full:
        prep = PREP_MAP.get(doc_id, {})
        full = prep.get("Resumo", "")
    if not full:
        return ""
    if len(full) <= max_chars:
        return full
    # corta respeitando palavra
    cut = full[:max_chars].rsplit(" ", 1)[0]
    return cut + " ..."

def make_result_entry(doc_id: int, score: Optional[float] = None) -> Dict:
    meta = META_MAP.get(doc_id, {})
    title = meta.get("Titulo") or meta.get("Título") or meta.get("Título") or meta.get("Título")  # tenta variações
    if not title:
        title = meta.get("Título") or meta.get("Titulo") or meta.get("title") or f"Doc {doc_id}"
    author = meta.get("Autor") or meta.get("author") or "Autor desconhecido"
    snippet = snippet_from_doc(doc_id)
    entry = {
        "DocId": int(doc_id),
        "Título": title,
        "Autor": author,
        "Resumo": snippet
    }
    if score is not None:
        entry["score"] = float(score)
    return entry


# Rotas Flask
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/resultados", methods=["POST"])
def resultados():
    consulta = request.form.get("consulta", "").strip()
    modelo = request.form.get("modelo", "booleano")

    if not consulta:
        flash("Por favor, digite uma consulta.")
        return render_template("index.html")

    resultados_list = []

    try:
        if modelo == "booleano":
            # busca_booleana espera uma string query e path (ou dict)
            path_tokens = localizar_json("dados_tokenizados.json")
            bool_map = busca_booleana(consulta, path_tokens)  # retorna dict {docid: bool}
            matched_ids = [doc_id for doc_id, ok in bool_map.items() if ok]
            # monta lista com metadados e snippets
            resultados_list = [make_result_entry(doc_id) for doc_id in matched_ids]
        else:
            # busca vetorial espera query string e termos_path (caminho para termos_significativos.json)
            termos_path = localizar_json("termos_significativos.json")
            vet_results = busca_espaco_vetorial(consulta, termos_path, metadados_path=localizar_json("metadados.json"), top_k=50)
            # vet_results é lista de {DocId, score, Título?}
            resultados_list = []
            for r in vet_results:
                doc_id = int(r.get("DocId"))
                score = r.get("score", 0.0)
                entry = make_result_entry(doc_id, score=score)
                resultados_list.append(entry)
    except FileNotFoundError as fe:
        flash(str(fe))
        return render_template("index.html")
    except Exception as e:
        # erro geral: exibe mensagem e retorna à home
        print("Erro ao executar busca:", e)
        flash("Ocorreu um erro ao processar a busca. Verifique os logs.")
        return render_template("index.html")

    # Ordena resultados por score se presente (desc), senão mantém ordem
    resultados_list.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    return render_template("resultados.html", resultados=resultados_list, consulta=consulta, modelo=modelo)

@app.route("/detalhes/<int:doc_id>")
def detalhes(doc_id: int):
    # procura informação completa nos metadados (preferencial) e em dados preparados
    meta = META_MAP.get(doc_id, {})
    prep = PREP_MAP.get(doc_id, {})
    if not meta and not prep:
        return render_template("detalhes.html", doc=None)
    # monta objeto de exibição
    doc = {}
    doc['DocId'] = doc_id
    doc['Título'] = meta.get("Titulo") or meta.get("Título") or prep.get("Título") or meta.get("title") or f"Doc {doc_id}"
    doc['Autor'] = meta.get("Autor") or meta.get("author") or ""
    # preferir resumo original dos metadados, caso não exista usar o resumo preparado (limpo)
    doc['Resumo'] = meta.get("Resumo") or prep.get("Resumo") or ""
    if meta.get("TermosSignificativos"):
        doc['TermosSignificativos'] = meta.get("TermosSignificativos")
    # score, se existir (por exemplo vindo de busca vetorial)
    # (não guardamos score globalmente; ele vem apenas junto com resultados)
    return render_template("detalhes.html", doc=doc)


# Run
if __name__ == "__main__":
    print(f"{len(documentos_preparados)} documentos preparados carregados.")
    app.run(debug=True)

