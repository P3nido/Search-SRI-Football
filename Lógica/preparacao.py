import json
import re
import sys
from pathlib import Path


# Busca os arquivos do backend
script_dir = Path(__file__).parent.resolve()
if len(sys.argv) > 1:
    data_dir = Path(sys.argv[1]).expanduser().resolve()
else:
    data_dir = script_dir

METADATA = None
candidate = data_dir / "metadados.json"
if candidate.exists():
    METADATA = candidate
else:
    search_root = script_dir.parent
    found = list(search_root.rglob("metadados.json"))
    if found:
        METADATA = found[0]

if METADATA is None:
    raise FileNotFoundError(
        f"metadados.json não encontrado em {data_dir} nem nas pastas acima.\n"
        "Passe a pasta de dados como primeiro argumento, por exemplo:\n"
        "python preparacao.py C:\\caminho\\para\\Search-SRI-Football\\JSONs"
    )

#Define o nome do json que vai retornar os dados após a preparação do mesmo
data_dir = METADATA.parent
OUT = data_dir / "dadospreparados.json"

#Força a busca do arquivo stopwords.txt NÃO ALTERAR O NOME E NEM A POSIÇÃO DELE !
STOPWORDS = None
candidates = [script_dir, script_dir.parent, data_dir, data_dir.parent]
for p in candidates:
    try:
        if p and (p / "stopwords.txt").exists():
            STOPWORDS = p / "stopwords.txt"
            break
    except Exception:
        continue
if STOPWORDS is None:
    found_sw = list(script_dir.parent.rglob("stopwords.txt"))
    if found_sw:
        STOPWORDS = found_sw[0]
#Trataiva de erro se caso não achou o arquivo
if STOPWORDS is None:
    raise FileNotFoundError(
        f"stopwords.txt não encontrado próximo ao script ({script_dir}) nem em pastas prováveis."
    )
print(f"Usando metadados: {METADATA}")
print(f"Usando stopwords: {STOPWORDS}")
print(f"Gravando saída em: {OUT}")

#Aqui ele vai remover as stopwords e transformam todas em letra minúscula para facilitar a busca posteriormente
with STOPWORDS.open(encoding='utf-8') as f:
    stops = {line.strip().lower() for line in f if line.strip()}
with METADATA.open(encoding='utf-8') as f:
    data = json.load(f)
processed = []
word_re = re.compile(r"\b\w+\b", flags=re.UNICODE)
for item in data:
    docid = item.get('DocId')
    resumo = item.get('Resumo','')
    texto = resumo.lower()
    tokens = word_re.findall(texto)
    filtered = [t for t in tokens if t not in stops]
    new_text = ' '.join(filtered)
    processed.append({"DocId": docid, "Resumo": new_text})
with OUT.open('w', encoding='utf-8') as f:
    json.dump(processed, f, ensure_ascii=False, indent=2)

print(f"{len(processed)} resumos foram preparados e enviados para: {OUT}")
