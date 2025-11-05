import json
import re
import sys
from pathlib import Path

#Aqui ele vai forçar a busca dos arquivos
script_dir = Path(__file__).parent.resolve()

if len(sys.argv) > 1:
    data_dir = Path(sys.argv[1]).expanduser().resolve()
else:
    data_dir = script_dir

IN = None
candidate = data_dir / "dadospreparados.json"
if candidate.exists():
    IN = candidate
else:
    search_root = script_dir.parent
    found = list(search_root.rglob("dadospreparados.json"))
    if found:
        IN = found[0]
#Tratativa de erro se não conseguiu acessar os arquivos
if IN is None:
    raise FileNotFoundError(
        f"dadospreparados.json não encontrado em {data_dir} nem em pastas prováveis.\n"
        "Passe a pasta de dados como argumento, por exemplo:\n"
        "python tokenizacao.py C:\\caminho\\para\\Search-SRI-Football\\JSONs"
    )

#Setou o nome do json que vai ser retornado
OUT = IN.parent / "dados_tokenizados.json"

token_re = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)

with IN.open(encoding='utf-8') as f:
    data = json.load(f)
#Aqui ele contabiliza quantas vezes as palavra exibe, e ordena a exibição de forma que exibe primeiro os termos que mais se repetem em cada documento, além de tokenizar os termos
out = []
for item in data:
    docid = item.get('DocId')
    resumo = item.get('Resumo', '')
    tokens = token_re.findall(resumo)
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    sorted_items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    token_counts_list = [f"{t} , {c}" for t, c in sorted_items]
    out.append({"DocId": docid, "Tokens": token_counts_list})
with OUT.open('w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"{len(out)} documentos tokenizados e gravados em: {OUT}")
