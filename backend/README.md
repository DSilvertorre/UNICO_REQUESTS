# Backend UNICO People

## O que este backend faz

O servidor entrega o HTML e executa exclusivamente as consultas do UNICO People.

Endpoints:

```text
GET /
GET /health
GET /unico/config
POST /unico/search
```

## Configuração UNICO

Crie `backend/.env` a partir de `backend/.env.example`:

```env
UNICO_ACCOUNT_ID=id_da_conta
UNICO_TENANT=tenant_da_conta
UNICO_COOKIE=
```

`UNICO_COOKIE` é opcional e deve ser preenchido somente quando a sessão exigir.
A credencial de autorização é informada na própria tela e não é salva.

## Rodar localmente

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra o sistema em:

```text
http://127.0.0.1:8000
```

A documentação técnica da API fica em:

```text
http://127.0.0.1:8000/docs
```

## Exemplo de consulta UNICO

```json
{
  "tipo": "auto",
  "entradas": ["12345678900", "nome exemplo", "email@exemplo.com"],
  "credencial": "token_de_autorizacao",
  "dias": 30
}
```

## Testes

```powershell
cd backend
pip install -r requirements-dev.txt
pytest tests
```
