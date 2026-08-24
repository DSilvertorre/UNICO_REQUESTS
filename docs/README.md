# Indice da Documentacao

## Documentos finais

- `../DOCUMENTACAO_DO_PROJETO.md`: visao geral, arquitetura, regras do HTML, UNICO People, tutorial e criterios de aceite.
- `../AUDITORIA_DO_PROJETO.md`: auditoria da estrutura, pontos corretos, ajustes feitos e recomendacoes sem lista de prioridade.
- `conexao-bigquery-html.md`: explicacao de como conectar BigQuery, backend/API interna e HTML.
- `conexao-tabelas-html.md`: contrato recomendado para conectar as tabelas das bases internas ao HTML.
- `logica-busca-antiga-adaptada.md`: como reaproveitar a logica do programa antigo com a nova estrutura por bases.

## Documentos de contexto

Os arquivos abaixo foram usados como contexto inicial do prompt e devem ser mantidos como referencia:

- `../# Projeto de busca de candidatos.txt`
- `../# HTML.txt`
- `../# UNICO.txt`
- `../UNICO_miro.py`
- `../candidatos-grid-automacao-split-33k-js.zip`
- `../Fluxograma/`

## Decisoes ja incorporadas

- As bases internas ficam separadas por pagina porque possuem colunas diferentes.
- As bases internas sao `Consolidado`, `Perifericos`, `Processos Seletivos SP`, `Processo Online` e `GO Live & Takeover`.
- A pagina `UNICO People` segue fluxo proprio.
- Com excecao da `UNICO People`, nao havera tratamento de duplicados.
- A atualizacao das tabelas ja esta estruturada; o foco atual e a conexao das tabelas com o HTML.
- O sistema sera usado em ambiente fechado pela equipe autorizada.
- A nova busca deve manter comportamento parecido com o programa antigo, mas usando paginas por base e backend/API interna.
