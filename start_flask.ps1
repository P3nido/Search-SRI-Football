# Ativa o ambiente virtual
.\venv\Scripts\Activate

# Limpa todos os __pycache__ e .pyc
Write-Host "Limpando cache..."
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue

# Roda o Flask com debug e reload
Write-Host "Iniciando Flask..."
python app.py
