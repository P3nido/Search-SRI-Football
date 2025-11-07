import json
import re
import os
from typing import Dict, Set, List, Union

#Aqui ele so puxa o json com as palavras ja tokenizadas
def _load_tokenized_docs(path: str) -> Dict[int, Set[str]]:
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    docs = {}
    for entry in raw:
        doc_id = entry.get('DocId')
        tokens_list = entry.get('Tokens', [])
        token_set = set()
        for t in tokens_list:
            if isinstance(t, str):
                parts = t.split(',')
                word = parts[0].strip().lower()
                m = re.findall(r"\w+", word, flags=re.UNICODE)
                if m:
                    token_set.add(m[0])
        if doc_id is not None:
            docs[int(doc_id)] = token_set
    return docs

# Aqui ele vai setar as funções para AND, OR e NOT e o sinal de parêntense como prioridade de calculo, pro usuário poder utilizar eles na pesquisa
def _tokenize_query(query: str) -> List[str]:
    q = query
    q = q.replace('&&', ' AND ')
    q = q.replace('||', ' OR ')
    q = re.sub(r"!\s*", 'NOT ', q)
    tokens = re.findall(r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|[^\s()]+", q, flags=re.IGNORECASE)
    return [t for t in tokens if t.strip()]

# Normalização do termo pra garantir que não vai dar problema com a busca
def _normalize_term(term: str) -> str:
    m = re.findall(r"\w+", term, flags=re.UNICODE)
    return m[0].lower() if m else ""


#Aqui ele le o NOT, AND, OR e os parêntenses e aplica a lógica de cada um
def _infix_to_postfix(tokens: List[str]) -> List[str]:
    prec = {'NOT': 3, 'AND': 2, 'OR': 1}
    output = []
    stack = []

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        up = tok.upper()
        if tok == '(':
            stack.append(tok)
        elif tok == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        elif up in ('AND', 'OR', 'NOT'):
            while stack:
                top = stack[-1]
                if top == '(':
                    break
                top_up = top.upper()
                if (prec.get(top_up, 0) > prec.get(up, 0)) or (prec.get(top_up, 0) == prec.get(up, 0) and up != 'NOT'):
                    output.append(stack.pop())
                else:
                    break
            stack.append(up)
        else:
            nt = _normalize_term(tok)
            output.append(nt)
        i += 1

    while stack:
        output.append(stack.pop())

    return output

#Após converter a lógica de cada um, aqui ele faz a comparação e retorna se ele é true ou false
def _eval_postfix_for_doc(postfix: List[str], doc_tokens: Set[str]) -> bool:
    st: List[bool] = []
    for tok in postfix:
        up = tok.upper()
        if up == 'AND':
            if len(st) < 2:
                return False
            b = st.pop()
            a = st.pop()
            st.append(a and b)
        elif up == 'OR':
            if len(st) < 2:
                return False
            b = st.pop()
            a = st.pop()
            st.append(a or b)
        elif up == 'NOT':
            if len(st) < 1:
                return False
            a = st.pop()
            st.append(not a)
        else:
            if not tok:
                st.append(False)
            else:
                st.append(tok in doc_tokens)

    return bool(st and st[-1])

#Aqui ele realmente realiza a busca no documento dados_tokenizados.json, a parte logica já está feita
def busca_booleana(query: str, tokenized_docs: Union[str, Dict[int, Set[str]]]) -> Dict[int, bool]:

    if isinstance(tokenized_docs, str):
        path = tokenized_docs
        tried = []
        if os.path.isabs(path) or os.path.exists(path):
            tried.append(path)
        else:
            tried.append(path)

        fallback1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'JSONs', 'dados_tokenizados.json'))
        tried.append(fallback1)
        fallback2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'JSONs', 'dados_tokenizados.json'))
        tried.append(fallback2)

        found = None
        for p in tried:
            if p and os.path.exists(p):
                found = p
                break

        if not found:
            raise FileNotFoundError(f"Arquivo de tokens não encontrado. Tente passar o caminho correto. Caminhos testados: {tried}")

        docs = _load_tokenized_docs(found)
    else:
        docs = tokenized_docs

    tokens = _tokenize_query(query)
    if not tokens:
        return {doc_id: False for doc_id in docs.keys()}

    postfix = _infix_to_postfix(tokens)

    results = {}
    for doc_id, tokset in docs.items():
        results[doc_id] = _eval_postfix_for_doc(postfix, tokset)

    return results
