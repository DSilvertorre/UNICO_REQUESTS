# Alternativa: GitHub Pages + n8n

Esta pasta prepara uma publicacao **alternativa**. Ela nao altera os arquivos
usados pelo Render: o GitHub Actions cria uma copia temporaria de `frontend/`
e substitui apenas o `config.js` dentro do artefato do GitHub Pages.

## Arquitetura

```text
Navegador -> GitHub Pages -> webhook protegido do n8n -> UNICO
```

O frontend envia uma credencial temporaria no cabecalho `Authorization` para o
webhook. O n8n encaminha essa credencial para a UNICO e injeta `ACCOUNT_ID`,
`TENANT` e, se necessario, o cookie. Esses tres valores nunca vao para o
GitHub Pages.

> O n8n deve estar acessivel por HTTPS e protegido por SSO, VPN ou proxy
> corporativo. Um webhook publico sem essa protecao permitiria que qualquer
> pessoa usasse o proxy.

## 1. Preparar o n8n

1. Confirme com o administrador que a instancia permite webhooks HTTPS,
   CORS e variaveis de ambiente (ou um cofre de credenciais equivalente).
2. Crie as variaveis secretas na instancia:

   ```text
   UNICO_ACCOUNT_ID
   UNICO_TENANT
   UNICO_COOKIE              # somente se realmente necessario
   ```

   Nunca crie `UNICO_TOKEN`: a credencial e temporaria e vem do usuario.
3. Importe `n8n-workflow-template.json` pelo menu **Workflows > Import from
   File**.
4. No no **Consultar UNICO**, confira os campos `account`, `tenant`,
   `authorization` e `q`. Algumas instalacoes corporativas desativam `$env`;
   nesse caso, selecione o cofre de credenciais da empresa no no HTTP Request
   e mapeie os mesmos campos sem inserir segredos no workflow.
5. Desative o salvamento de dados de execucao com sucesso e com erro. O modelo
   ja solicita isso, mas confirme nas configuracoes do workflow.
6. Ative o workflow e copie o **Production URL** do webhook (nunca o Test URL).
7. Configure CORS no proxy/reverse proxy do n8n para aceitar apenas a origem do
   seu GitHub Pages. Permita `GET` e os cabecalhos `Authorization`, `Content-Type`
   e `Accept`.

## 2. Configurar o frontend estatico

1. Abra `config.js` nesta pasta.
2. Substitua apenas `https://SEU-N8N.exemplo.com/webhook/unico-search` pelo
   Production URL do webhook.
3. Nao preencha os valores `server-managed`; eles sao sentinelas publicas e o
   n8n os ignora.
4. Faca commit e push. O workflow do GitHub gera e publica o site.

## 3. Habilitar GitHub Pages

1. No repositorio, abra **Settings > Pages**.
2. Em **Build and deployment**, escolha **GitHub Actions**.
3. Em **Actions**, execute o workflow **Publicar portal UNICO no GitHub Pages**
   ou envie o commit para `master`.
4. Copie a URL publicada e cadastre-a como origem permitida no proxy do n8n.
5. Teste uma busca com uma credencial temporaria valida.

## Validacao e seguranca

- O GitHub Pages e estatico: ele nao protege usuarios sozinho. Use apenas uma
  organizacao/ambiente corporativo que aplique SSO, VPN ou proxy de acesso.
- Nao coloque segredos em `frontend/`, neste `config.js`, GitHub Actions ou
  variaveis comuns do repositorio. Use apenas secrets/credential vault do n8n.
- O webhook deve ignorar `account` e `tenant` enviados pelo navegador e usar
  exclusivamente os valores mantidos no servidor.
- Depois de ativar, execute a auditoria de seguranca do n8n e confira que o
  webhook nao esta listado como desprotegido.

## Limites desta opcao

O frontend continua enviando uma chamada por entrada. Consultas grandes sao
sequenciais e dependem dos limites da UNICO e da capacidade do n8n. Para uso
intenso, acrescente fila, rate limit e autenticacao corporativa antes de abrir
para muitos usuarios.
