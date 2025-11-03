import json
import math
import sys
from pathlib import Path

#Aqui ele força a busca de todos os arquivos
def find_file(name: str) -> Path:
	script_dir = Path(__file__).resolve().parent
	candidates = [
		script_dir / name,
		script_dir.parent / name,
		script_dir / 'JSONs' / name,
		script_dir.parent / 'JSONs' / name,
		Path.cwd() / name,
		Path.cwd() / 'JSONs' / name,
	]
	for p in candidates:
		if p.exists():
			return p
	for ancestor in [script_dir, script_dir.parent, Path.cwd()]:
		js = ancestor / 'JSONs' / name
		if js.exists():
			return js
	raise FileNotFoundError(f"Arquivo não encontrado: {name}. Forneça o caminho com --input se necessário.")
def load_tokenized(path: Path):
	with path.open('r', encoding='utf-8') as f:
		data = json.load(f)
	docs = {}
	for entry in data:
		docid = entry.get('DocId')
		tokens = entry.get('Tokens', [])
		counts = {}
		for t in tokens:
			if isinstance(t, str) and ',' in t:
				left, right = t.rsplit(',', 1)
				token = left.strip()
				try:
					tf = int(right.strip())
				except ValueError:
					try:
						tf = float(right.strip())
					except Exception:
						tf = 0
				counts[token] = tf
			else:
				counts[str(t)] = counts.get(str(t), 0) + 1
		docs[int(docid)] = counts
	return docs

#Aqui ele realiza a parte do calculo do tf-idf, achando os pesos
def compute_tfidf(docs: dict):
	N = len(docs)
	df = {}
	for docid, counts in docs.items():
		for token in counts.keys():
			df[token] = df.get(token, 0) + 1
	idf = {}
	for token, dfv in df.items():
		if dfv > 0:
			idf[token] = math.log(N / dfv) if dfv != 0 else 0.0
		else:
			idf[token] = 0.0
	tfidf_per_doc = {}
	for docid, counts in docs.items():
		scores = {}
		for token, tf in counts.items():
			weight = tf * idf.get(token, 0.0)
			scores[token] = weight
		tfidf_per_doc[docid] = scores
	return tfidf_per_doc, idf

#Aqui ele ordena os pesos e limita pra 5 casas decimais
def top_terms_per_doc(tfidf_per_doc: dict, topk: int = 10):
	out = []
	for docid in sorted(tfidf_per_doc.keys()):
		scores = tfidf_per_doc[docid]
		items = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
		topk_items = items[:topk]
		formatted = [f"{tok} , {weight:.5f}" for tok, weight in topk_items]
		out.append({'DocId': docid, 'Terms': formatted})
	return out

#Agora ele busca as outras informações como autor, titulo, etc e organiza tudo junto de acordo com o seu documento
def main(argv):
	import argparse
	parser = argparse.ArgumentParser(description='Calcular TF-IDF a partir de dados tokenizados.')
	parser.add_argument('--input', '-i', help='Caminho para dados_tokenizados.json (opcional).')
	parser.add_argument('--topk', '-k', type=int, default=10, help='Número de termos significativos por documento (padrão 10).')
	parser.add_argument('--output', '-o', help='Caminho de saída para termos (JSON).')
	args = parser.parse_args(argv)
	try:
		input_path = Path(args.input) if args.input else find_file('dados_tokenizados.json')
	except FileNotFoundError as e:
		print(str(e))
		return 2
	try:
		docs = load_tokenized(input_path)
	except Exception as e:
		print(f"Erro ao ler {input_path}: {e}")
		return 3
	tfidf_per_doc, idf = compute_tfidf(docs)
	topk = args.topk if args.topk and args.topk > 0 else 10
	result = top_terms_per_doc(tfidf_per_doc, topk=topk)
	try:
		meta_path = find_file('metadados.json')
		with meta_path.open('r', encoding='utf-8') as mf:
			metas = json.load(mf)
		meta_map = {int(m.get('DocId')): m for m in metas}
	except Exception:
		meta_map = {}
	enriched = []
	for item in result:
		docid = item['DocId']
		meta = meta_map.get(docid, {})
		titulo = meta.get('Titulo') or meta.get('Título') or ''
		autor = meta.get('Autor') or ''
		termos = item.get('Terms', [])
		enriched.append({
			'DocId': docid,
			'Título': titulo,
			'Autor': autor,
			'TermosSignificativos': termos
		})
	result = enriched
	out_path = Path(args.output) if args.output else (input_path.parent / 'termos_significativos.json')
	with out_path.open('w', encoding='utf-8') as f:
		json.dump(result, f, ensure_ascii=False, indent=2)
	print(f"TF-IDF calculado para {len(docs)} documentos. Top {topk} termos por documento gravados em: {out_path}")
	return 0
if __name__ == '__main__':
	raise SystemExit(main(sys.argv[1:]))

