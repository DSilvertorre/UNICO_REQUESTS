/*
 * Esta configuracao e copiada somente para o artefato do GitHub Pages.
 * Nao coloque tokens, cookies, ACCOUNT_ID ou TENANT neste arquivo.
 */
window.SEARCH_PORTAL_CONFIG = {
  mode: "unico-direct",
  unico: {
    // Troque pelo URL de PRODUCAO do webhook publicado pelo n8n.
    url: "https://SEU-N8N.exemplo.com/webhook/unico-search",

    // Valores sentinela: o proxy n8n ignora estes campos e injeta os segredos
    // no servidor. Eles existem somente para manter o frontend em modo proxy.
    account: "server-managed",
    tenant: "server-managed",
  },
};
