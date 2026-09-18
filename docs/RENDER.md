# Deploy no Render

O arquivo `render.yaml` na raiz do projeto descreve o deploy como um **Web
Service Python**. O backend FastAPI serve tanto a API quanto o portal em
`frontend/`, incluindo o vídeo da documentação.

## Publicar

1. Envie o repositório para o GitHub.
2. No Render, selecione **New > Blueprint** e conecte o repositório.
3. Confirme o serviço `unico-search-portal` detectado pelo `render.yaml`.
4. Antes do primeiro deploy, informe no painel do Render os valores secretos:

   - `UNICO_ACCOUNT_ID`
   - `UNICO_TENANT`
   - `UNICO_COOKIE` (somente se a sessão da UNICO exigir cookie)

5. Crie o Blueprint. Após finalizar, abra `https://<servico>.onrender.com/health`;
   a resposta esperada contém `"status": "ok"`.

## Configuração definida no arquivo

- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Deploy automático: a cada commit que altere `backend/`, `frontend/` ou
  `render.yaml`.

As variáveis da UNICO usam `sync: false`, portanto seus valores nunca são
gravados no repositório. O plano está configurado como `free`; altere `plan`
no `render.yaml` ou no painel do Render se precisar de maior disponibilidade.
