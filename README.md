# Portal de Busca de Candidatos

Portal interno para consultas de candidatos na UNICO People e, progressivamente,
nas bases corporativas armazenadas no BigQuery.

## Estrutura

- `frontend/`: interface HTML, estilos, ícones e comportamento da aplicação.
- `backend/`: API FastAPI, integração UNICO, preparação para BigQuery e testes.
- `docs/`: documentação de conexão e regras do sistema.

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

## Testes

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest tests
```
