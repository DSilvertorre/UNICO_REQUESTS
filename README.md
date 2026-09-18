# Portal UNICO People

Portal interno para consultar candidatos exclusivamente na UNICO People.

## Estrutura

- `frontend/`: páginas da UNICO People e documentação operacional.
- `backend/`: API FastAPI e integração com a UNICO.
- `docs/`: instruções de publicação estática no Grid.
- `render.yaml`: configuração de deploy do portal completo no Render.

## Execução local

1. Copie `backend/.env.example` para `backend/.env`.
2. Preencha as variáveis locais no novo arquivo `.env`.
3. Instale as dependências e inicie o servidor:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. Abra `http://127.0.0.1:8000/#/unico`.

## Segurança

Nunca envie ao GitHub o arquivo `backend/.env`, tokens da UNICO, cookies,
credenciais Google, chaves privadas ou logs. O `.gitignore` já bloqueia esses
arquivos; consulte também `SECURITY.md`.

## Deploy no Render

Consulte [docs/RENDER.md](docs/RENDER.md). As variáveis da UNICO devem ser
configuradas diretamente no painel do Render, nunca no repositório.

## Testes

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest tests
```
