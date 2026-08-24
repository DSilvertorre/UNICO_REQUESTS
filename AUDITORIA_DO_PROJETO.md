# Auditoria do Projeto de Busca de Candidatos

## 1. Resumo executivo

O projeto tem uma boa direcao geral: centralizar buscas que hoje dependem de varias planilhas, permitir consulta em massa por CPF, nome ou email e entregar uma tabela facil de copiar. A separacao conceitual entre planilhas, ETL Python, BigQuery, backend interno e dashboard HTML tambem esta correta.

O principal ponto de atencao e transformar os documentos de contexto em uma estrutura de implementacao clara para o HTML. A atualizacao das tabelas ja esta estruturada; portanto, o foco agora deve ser a conexao entre as tabelas existentes, o backend/API interna e as paginas do dashboard.

## 2. O que esta correto na estrutura

### 2.1 Separacao em camadas

A arquitetura proposta esta bem orientada:

- Planilhas originais como fonte.
- ETL Python para extrair, transformar e carregar dados.
- BigQuery como camada de armazenamento consolidado.
- Backend interno como camada de regras e consulta.
- HTML Dashboard como interface para o usuario.

Essa separacao evita que o HTML consulte planilhas diretamente e facilita manutencao, seguranca e escalabilidade.

### 2.2 Uso de BigQuery

O BigQuery faz sentido para o tipo de problema, principalmente se houver muitas planilhas, muitas abas e crescimento no volume de candidatos.

Pontos positivos:

- Permite consolidar varias fontes.
- Facilita busca em massa.
- Permite criar tabelas especificas para busca.
- Ajuda a controlar historico de atualizacao.

### 2.3 Ideia de indice de busca

Uma camada de indice de busca continua sendo uma boa decisao, mas ela deve respeitar a separacao por base. Como as bases possuem colunas diferentes, o indice pode ajudar a localizar candidatos sem obrigar todas as paginas a usarem o mesmo formato de tabela.

Exemplo de uso correto:

- CPF sem pontuacao.
- Email em letras minusculas.
- Nome normalizado sem acentos para busca aproximada.

### 2.4 Pagina de documentacao dentro do HTML

Ter uma pagina de Documentacao no proprio dashboard e correto, porque o usuario operacional provavelmente precisara consultar instrucoes enquanto usa o sistema.

### 2.5 Regras especificas para UNICO People

A separacao da pagina UNICO People das demais bases esta correta. Ela tem uma origem diferente, depende de credencial, possui limite de requisicao e exige interpretacao de JSON.

### 2.6 Separacao das bases por pagina

A decisao de separar as bases em paginas tambem esta correta. Cada base possui tabelas e colunas diferentes, entao a interface nao deve tentar encaixar tudo em uma unica tabela padrao.

Bases internas:

- `Consolidado`
- `Perifericos`
- `Processos Seletivos SP`
- `Processo Online`
- `GO Live & Takeover`

### 2.7 Resultado em formato de tabela

Entregar resultados como tabela e uma boa escolha para o fluxo da equipe, porque o destino natural parece ser Excel ou Google Sheets.

### 2.8 Botao `Abrir link`

Mostrar `Abrir link` na tela e copiar a URL real na area de transferencia e uma boa regra de experiencia do usuario. Mantem a interface limpa sem prejudicar quem precisa colar os dados em planilha.

## 3. O que parece errado, incompleto ou arriscado

### 3.1 O projeto ainda nao tem estrutura real de pastas

Hoje existem documentos soltos e imagens de fluxograma, mas ainda nao ha uma estrutura tecnica do projeto.

Problema:

- Fica dificil separar frontend, backend, ETL, documentacao e testes.
- O projeto pode crescer desorganizado rapidamente.

Recomendacao:

```text
Projeto Busca de candidatos/
  docs/
  fluxogramas/
  frontend/
  backend/
  etl/
  database/
  tests/
  config/
```

### 3.2 Documentos de contexto precisam ficar organizados

Os arquivos `# HTML.txt`, `# Projeto de busca de candidatos.txt` e `# UNICO.txt` devem ser tratados como documentos de contexto do prompt, nao como documentacao final do sistema.

Problema:

- Eles misturam ideia, requisitos, exemplos e regras.
- Podem continuar existindo como referencia, mas nao devem guiar sozinhos a implementacao.

Recomendacao:

- Manter os arquivos originais como contexto.
- Criar documentos finais organizados em `docs/`.
- Usar a documentacao final como fonte principal para desenvolvimento.

### 3.3 Mistura entre requisito, arquitetura e tutorial

Os documentos originais misturam:

- Ideia do produto.
- Regras de tela.
- Regras de API.
- Regras de negocio.
- Tutorial.
- Backlog.

Problema:

- A equipe pode implementar uma regra no lugar errado.
- Fica dificil transformar isso em tarefas tecnicas.

Recomendacao:

Separar em documentos diferentes:

- Documento de produto.
- Documento tecnico.
- Documento de API.
- Documento de regras da UNICO.
- Manual do usuario.

### 3.4 Modelo de dados precisa refletir bases separadas

As tabelas devem representar as bases reais do projeto, pois cada base tem colunas diferentes.

Problema:

- A documentacao anterior sugeria uma estrutura generica demais.
- Uma unica tabela consolidada pode esconder diferencas importantes entre bases.
- O HTML precisa saber quais colunas renderizar para cada pagina.

Recomendacao:

Trabalhar com tabelas ou views por base:

- `Consolidado`
- `Perifericos`
- `Processos Seletivos SP`
- `Processo Online`
- `GO Live & Takeover`

Cada base deve informar ao HTML:

- Nome das tabelas/abas disponiveis.
- Colunas exibiveis.
- Colunas copiaveis.
- Colunas pesquisaveis.
- Campo de link da aba, quando existir.

### 3.5 Ambiente fechado e cuidado operacional com dados

O sistema sera hospedado em ambiente fechado e acessado apenas pela equipe autorizada. Isso reduz o risco de exposicao externa, mas ainda e importante manter alguns cuidados operacionais para evitar vazamento acidental dentro do proprio fluxo de trabalho.

Cuidados recomendados:

- Nao gravar credenciais em logs.
- Evitar expor token em mensagens de erro.
- Manter acesso restrito ao ambiente fechado.
- Registrar erros tecnicos sem copiar dados completos desnecessarios.

### 3.6 Credencial da UNICO no HTML

O documento atual pede que o usuario adicione a credencial/token na pagina HTML.

Como o sistema sera usado em ambiente fechado, esse fluxo pode ser mantido se for necessario para a operacao. Ainda assim, a melhor estrutura tecnica e fazer o HTML enviar a consulta para o backend e deixar o backend executar a chamada para a UNICO.

Recomendacao:

- O campo de credencial pode existir na pagina UNICO.
- O HTML nao deve chamar a endpoint da UNICO diretamente.
- O backend deve receber a credencial somente para executar a consulta.
- O backend deve controlar limite de requisicao, erros e resposta padronizada.

Desenho recomendado:

```text
HTML -> Backend interno autenticado -> Servico UNICO
```

### 3.7 Endpoint da UNICO esta incompleta

A endpoint registrada e:

```text
https://admin.acessorh.com.br/svc2/search/people?account
```

Problema:

- Nao ha definicao dos parametros obrigatorios.
- Nao ha exemplo de headers.
- Nao ha contrato de request.
- Nao ha contrato de erro.

Recomendacao:

Documentar:

- Metodo HTTP.
- Headers.
- Query params.
- Body, se houver.
- Exemplos de busca por CPF, nome e email.
- Codigos de erro esperados.

### 3.8 Regra de status da UNICO precisa confirmacao

O mapeamento atual diz:

- `Archived` = Arquivado
- `Completed` = Mesa de analise
- `Pending + total = 2` = Pendente
- `Pending + total = 1` = Nao iniciado

Problema:

- No JSON de exemplo o valor aparece como `archived` em minusculo.
- Nao esta claro se `total` usado para status e `status.overview.total` ou outro total.
- "Mesa de analise" e "Em analise" aparecem como termos parecidos, mas nao totalmente padronizados.

Recomendacao:

- Padronizar tudo em minusculo internamente.
- Confirmar a origem exata do `total`.
- Escolher um termo unico: `Mesa de analise` ou `Em analise`.

### 3.9 Regra de pendencias da UNICO

A regra antiga do script `UNICO_miro.py` deve ser usada como referencia para a nova implementacao.

Regra validada pelo contexto antigo:

- Para status `Arquivado`, pendencias em branco.
- Para status `Mesa de analise`, retornar `Assinatura de documento`.
- Para status `Pendente`, listar documentos em que `code != 220` ou `exist == false`.
- Para status `Nao iniciado`, retornar `Todos os documentos`.

Ponto de atencao:

- Para manter algo parecido com o funcionamento anterior, a nova versao deve seguir `code != 220` ou `exist == false`.

### 3.10 Busca por nome

Buscar por nome pode retornar mais de uma linha, e isso sera aceito porque a regra das bases internas e comparar diretamente com as planilhas.

Comportamento esperado:

- CPF, nome e email sao tipos de busca disponiveis.
- Se nome retornar mais de um resultado, o HTML deve exibir todas as linhas encontradas.
- A responsabilidade da tela e mostrar claramente a origem, a tabela/aba e as colunas da base.
- Nao havera consolidacao ou escolha automatica de melhor registro nas bases internas.

### 3.11 Duplicidades nas bases internas

Com excecao da UNICO People, nao havera tratamento de duplicados. Essa decisao deve permanecer documentada porque o objetivo das bases internas e comparar diretamente com o conteudo das planilhas.

Regra:

- Se o mesmo CPF, nome ou email aparecer em mais de uma linha, o sistema exibe as linhas encontradas.
- Nao consolidar registros automaticamente.
- Nao escolher uma base como mais importante que outra.
- A UNICO continua sendo a unica pagina com regra propria de ocorrencias e escolha do melhor status.

### 3.12 Falta contrato da API interna

O backend interno foi previsto, mas nao ha endpoints definidos.

Recomendacao minima:

```text
GET /health
GET /bases
GET /bases/{base}
POST /search/{base}
POST /search/unico
```

Tambem e necessario definir formato padrao de resposta com `colunas` e `resultados`, para que o HTML consiga montar tabelas diferentes para cada base.

### 3.13 Atualizacao das tabelas

A atualizacao das tabelas ja esta estruturada fora do escopo imediato desta documentacao. O foco daqui para frente deve ser conectar essas tabelas ao HTML de forma correta.

Ponto de atencao:

- O HTML precisa saber quais bases existem.
- Cada base precisa expor suas tabelas/abas.
- Cada tabela/aba precisa informar suas colunas.
- A busca deve retornar linhas no formato esperado por aquela pagina.

### 3.14 Falta estrategia de testes

O backlog cita testes, mas ainda nao ha plano.

Testes necessarios:

- Normalizacao de CPF.
- Normalizacao de email.
- Busca exata por CPF.
- Busca por nome retornando mais de uma linha.
- Filtros de tabela.
- Copia de tabela.
- Link visual versus link copiado.
- Token ausente na UNICO.
- Token invalido na UNICO.
- Rate limit da UNICO.
- Interpretacao de status e pendencias.

## 4. Melhorias recomendadas

### 4.1 Criar estrutura oficial do projeto

Sugestao:

```text
docs/
  documentacao-do-projeto.md
  auditoria-do-projeto.md
  conexao-tabelas-html.md
  requisitos-html.md
  regras-unico.md
  api-interna.md

frontend/
  src/
  public/

backend/
  app/
  tests/

etl/
  jobs/
  tests/

database/
  bigquery/
    schemas/
    queries/

config/
  exemplo.env
```

### 4.2 Definir contrato das bases para o HTML

Como cada base possui colunas diferentes, o melhor caminho e criar um contrato de metadados. Esse contrato informa ao HTML o que existe em cada pagina antes da consulta acontecer.

Exemplo de resposta para listar bases:

```json
{
  "bases": [
    {
      "id": "consolidado",
      "nome": "Consolidado"
    },
    {
      "id": "perifericos",
      "nome": "Perifericos"
    },
    {
      "id": "processos_seletivos_sp",
      "nome": "Processos Seletivos SP"
    },
    {
      "id": "processo_online",
      "nome": "Processo Online"
    },
    {
      "id": "go_live_takeover",
      "nome": "GO Live & Takeover"
    }
  ]
}
```

Exemplo de resposta para metadados de uma base:

```json
{
  "base": "consolidado",
  "nome": "Consolidado",
  "tabelas": [
    {
      "id": "cravinhos",
      "nome": "Cravinhos",
      "colunas": [
        { "id": "nome", "rotulo": "Nome", "pesquisavel": true, "copiavel": true },
        { "id": "cpf", "rotulo": "CPF", "pesquisavel": true, "copiavel": true },
        { "id": "email", "rotulo": "Email", "pesquisavel": true, "copiavel": true },
        { "id": "link_aba", "rotulo": "Link da aba", "pesquisavel": false, "copiavel": true, "tipo": "link" }
      ]
    }
  ]
}
```

Esse formato resolve a pergunta "como podemos fazer isso?": o HTML nao precisa conhecer previamente todas as colunas de todas as bases. Ele pergunta ao backend quais tabelas e colunas existem para a pagina aberta e monta a tela dinamicamente.

### 4.3 Criar contrato padrao de busca

Exemplo:

```json
{
  "query_id": "uuid",
  "base": "consolidado",
  "tabelas_consultadas": ["cravinhos"],
  "total_consultado": 10,
  "total_encontrado": 8,
  "colunas": [
    { "id": "nome", "rotulo": "Nome" },
    { "id": "cpf", "rotulo": "CPF" },
    { "id": "email", "rotulo": "Email" },
    { "id": "link_aba", "rotulo": "Link da aba", "tipo": "link" }
  ],
  "resultados": [
    {
      "entrada": "12345678900",
      "tipo": "cpf",
      "status_busca": "Encontrado",
      "nome": "Nome Exemplo",
      "cpf": "12345678900",
      "email": "exemplo@email.com",
      "tabela": "Cravinhos",
      "link_aba": "https://..."
    }
  ],
  "erros": []
}
```

Para as bases internas, se houver linhas duplicadas na origem, todas as linhas retornam em `resultados`. A API nao deve consolidar esses registros.

### 4.4 Como conectar as tabelas no HTML

Fluxo recomendado:

1. O usuario abre uma pagina, por exemplo `Consolidado`.
2. O HTML chama `GET /bases/consolidado`.
3. O backend retorna tabelas/abas e colunas da base.
4. O HTML monta o filtro `Selecione as tabelas` com as tabelas retornadas.
5. O usuario informa nomes, CPFs ou emails e clica em `Consultar`.
6. O HTML chama `POST /search/consolidado`.
7. O backend consulta somente as tabelas selecionadas daquela base.
8. O backend devolve `colunas` e `resultados`.
9. O HTML renderiza a tabela usando a lista de `colunas`.
10. O botao `Copiar tabela` usa os mesmos dados, mas troca botoes de link pela URL real.

Esse fluxo substitui o modelo antigo em que o HTML carregava `manifest.js` e grandes arquivos `.js` com todos os dados. A experiencia do usuario pode ser parecida, mas os dados passam a vir do backend conforme a base aberta.

Endpoints sugeridos:

```text
GET /health
GET /bases
GET /bases/{base}
POST /search/{base}
POST /search/unico
```

Payload sugerido para consulta:

```json
{
  "tipo": "cpf",
  "entradas": ["12345678900", "98765432100"],
  "tabelas": ["cravinhos", "cotia"],
  "status": ["Encontrado"],
  "colunas": "todas"
}
```

### 4.5 Integracao UNICO no backend

Mesmo em ambiente fechado, a UNICO deve passar pelo backend para manter a regra de limite de requisicao e padronizar o retorno.

Regras:

- O HTML envia as entradas, filtros, data limite e credencial preenchida.
- O backend faz a chamada para a UNICO.
- O backend respeita 15 requisicoes por segundo e 2000 por execucao.
- O backend transforma o JSON da UNICO em tabela.
- O HTML recebe o mesmo formato geral de `colunas` e `resultados`.

### 4.6 Padronizar nomes

Padronizacoes recomendadas:

- `UNICO People`, nao alternar entre `UNICO`, `UNICO PEOPLE` e `Página UNICO`.
- `Em analise` ou `Mesa de analise`, escolher um.
- `Numero de ocorrencias`, sem alternar com `N° de ocorrencias`.
- `Pendencias`, com grafia unica nos campos internos.

### 4.7 Melhorar UX da busca em massa

Adicionar:

- Contador de entradas coladas.
- Indicador de progresso.
- Indicador de encontrados/nao encontrados.
- Mensagem quando a busca passar do limite permitido.
- Exportacao CSV/XLSX, alem de copiar tabela.
- Destaque visual para linhas com pendencias.

### 4.8 Criar observabilidade operacional

Registrar:

- Quem consultou.
- Quando consultou.
- Quantos itens foram consultados.
- Qual base foi consultada.
- Tempo de resposta.
- Erros.

Evitar registrar:

- Token.
- Credenciais.
- Dados completos desnecessarios.

## 5. Conclusao

A estrutura conceitual esta correta e bem encaminhada. A decisao de usar ETL, BigQuery, backend e dashboard e adequada para substituir buscas manuais em planilhas.

O melhor caminho agora e organizar os documentos finais e implementar a conexao entre as tabelas e o HTML. As bases internas devem ficar separadas por pagina, cada uma exibindo suas proprias colunas e retornando os resultados como aparecem nas planilhas. A UNICO permanece como fluxo especial, com regra propria de ocorrencias, status, pendencias e limite de requisicao.
