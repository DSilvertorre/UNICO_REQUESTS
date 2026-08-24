# Envio do HTML para o Grid

## Arquivo correto para upload

Use o arquivo:

```text
Projeto-Busca-de-Candidatos-Grid.zip
```

Esse ZIP foi preparado com os arquivos estaticos na raiz:

```text
index.html
app.js
styles.css
config.js
icons.js
```

Esse formato e o esperado pelo Grid. O erro `invalid_file` acontece quando o
`index.html` fica dentro de uma subpasta, por exemplo `frontend/index.html`.

## Configuracao da busca

O pacote do Grid esta configurado no modo:

```js
mode: "unico-direct"
```

Nesse modo, o HTML chama a UNICO diretamente pelo navegador usando:

- URL da UNICO
- account
- tenant
- token colado na tela

O `apiBaseUrl` fica vazio porque nao sera usado nesse modo.

Se a UNICO bloquear chamadas diretas do navegador por CORS, sera necessario
voltar para o modo com backend interno:

```js
window.SEARCH_PORTAL_CONFIG = {
  mode: "backend",
  apiBaseUrl: "https://endereco-interno-do-backend",
};
```

Nesse caso, o Grid continuara hospedando apenas a tela e o backend FastAPI
ficara responsavel por chamar a UNICO.

## O que nao enviar ao Grid

Nao envie:

- `backend/.env`
- Codigo Python do backend
- Arquivos de teste
- Caches
- ZIP completo do projeto

O token da UNICO continua sendo informado na tela apenas no momento da consulta.
