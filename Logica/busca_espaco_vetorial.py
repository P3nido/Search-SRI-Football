import json
import os
import math
import re
from typing import Dict, List, Tuple, Optional

#Normalização novamente pra garantir que não há maiusculo e caractere especial
def _normalize(term: str) -> str:
    m = re.findall(r"\w+", term, flags=re.UNICODE)
    return m[0].lower() if m else ""

#Aqui ele carrega os termos significativos e armazena os outros parametros como nome do arquivo, id etc
def _load_term_vectors(path: str) -> Dict[int, Dict[str, float]]:
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    docs = {}
    for entry in raw:
        doc_id = entry.get('DocId')
        terms = entry.get('TermosSignificativos', [])
        vec = {}
        for t in terms:
            if isinstance(t, str):
                parts = t.split(',')
                term = parts[0].strip()
                weight = 0.0
                if len(parts) > 1:
                    try:
                        weight = float(parts[1].strip())
                    except Exception:
                        weight = 0.0
                nt = _normalize(term)
                if nt:
                    vec[nt] = weight
        if doc_id is not None:
            docs[int(doc_id)] = vec
    return docs


def _compute_doc_norms(doc_vectors: Dict[int, Dict[str, float]]) -> Dict[int, float]:
    norms = {}
    for doc_id, vec in doc_vectors.items():
        s = sum(w * w for w in vec.values())
        norms[doc_id] = math.sqrt(s) if s > 0 else 0.0
    return norms


def _build_query_vector(query: str) -> Dict[str, float]:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    q = [t.lower() for t in tokens]
    vec: Dict[str, float] = {}
    for t in q:
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec

#Essa função faz o calculo de similaridade que a Cristina passou no slide
def _cosine_similarity(query_vec: Dict[str, float], doc_vec: Dict[str, float], doc_norm: float) -> float:
    if not query_vec or not doc_vec:
        return 0.0
    dot = 0.0
    for term, qw in query_vec.items():
        dw = doc_vec.get(term, 0.0)
        if dw:
            dot += qw * dw
    q_norm = math.sqrt(sum(v * v for v in query_vec.values()))
    if q_norm == 0 or doc_norm == 0:
        return 0.0
    return dot / (q_norm * doc_norm)

#Aqui ele faz a busca inicial dos JSONs após receber os valores do cálculo de similaridade
def _find_file_with_fallback(path: str, default_rel: str) -> str:
    tried = []
    if os.path.exists(path):
        return path
    tried.append(path)
    fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), default_rel))
    if os.path.exists(fallback):
        return fallback
    tried.append(fallback)
    fallback2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', default_rel))
    if os.path.exists(fallback2):
        return fallback2
    tried.append(fallback2)
    raise FileNotFoundError(f"Arquivo não encontrado. Caminhos testados: {tried}")


#Após verificar os as buscas, aqui ele realmente faz a busca com o cálculo vetorial, ordenando o que possui maior score
def busca_espaco_vetorial(query: str, termos_path: str, metadados_path: Optional[str] = None, top_k: Optional[int] = None) -> List[Dict]:
    termos_file = _find_file_with_fallback(termos_path, os.path.join('..', 'JSONs', 'termos_significativos.json'))
    doc_vectors = _load_term_vectors(termos_file)
    doc_norms = _compute_doc_norms(doc_vectors)
    query_vec = _build_query_vector(query)

    results = []
    for doc_id, vec in doc_vectors.items():
        score = _cosine_similarity(query_vec, vec, doc_norms.get(doc_id, 0.0))
        results.append({'DocId': doc_id, 'score': score})

    results.sort(key=lambda x: x['score'], reverse=True)

    if metadados_path:
        meta_file = _find_file_with_fallback(metadados_path, os.path.join('..', 'JSONs', 'metadados.json'))
        with open(meta_file, 'r', encoding='utf-8') as f:
            metas = json.load(f)
        meta_map = {int(m.get('DocId')): m for m in metas}
        for r in results:
            m = meta_map.get(r['DocId'])
            r['Título'] = m.get('Titulo') if m else None

    if top_k:
        results = results[:top_k]

    return results
