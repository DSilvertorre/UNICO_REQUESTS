# Backend de Busca de Candidatos

## O que este backend faz

O servidor entrega o HTML e executa as consultas do UNICO People sem depender
do BigQuery. A busca de `Processos Seletivos SP` continua disponível no código,
mas permanece opcional até a etapa de teste das bases internas.

Endpoints:

```text
GET /
GET /health
GET /unico/config
POST /unico/search
GET /bases
GET /bases/processos-seletivos-sp
POST /search/processos-seletivos-sp
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

## Configuração BigQuery

Quando os testes das bases internas começarem, defina a tabela:

```powershell
$env:BQ_PROCESSOS_SELETIVOS_SP_TABLE="seu-projeto.seu_dataset.processos_seletivos_sp"
```

O Google BigQuery usa as credenciais padrão do ambiente.

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
