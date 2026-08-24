# Conexao das Tabelas com o HTML

## Objetivo

Este documento define como o HTML deve se conectar as tabelas das bases internas. As bases possuem colunas diferentes, por isso cada uma ficara em uma pagina propria e carregara suas tabelas, filtros e colunas de forma independente.

Bases internas:

- `Consolidado`
- `Perifericos`
- `Processos Seletivos SP`
- `Processo Online`
- `GO Live & Takeover`

A pagina `UNICO People` nao usa este mesmo fluxo, pois consulta a endpoint da UNICO.

## Regra principal

O HTML nao deve misturar tabelas de bases diferentes. O usuario escolhe uma pagina de base e, dentro dela, escolhe as tabelas/abas disponiveis para aquela base.

Exemplo:

- Na pagina `Consolidado`, o filtro `Selecione as tabelas` mostra apenas tabelas/abas do Consolidado.
- Na pagina `Perifericos`, o filtro mostra apenas tabelas/abas de Perifericos.
- A tabela de resultado exibe as colunas reais da base selecionada.

A experiencia deve continuar parecida com o programa antigo: o usuario cola CPFs, nomes ou emails, seleciona tabelas, consulta e recebe uma tabela estilo planilha. A diferenca e que a busca e a indexacao passam a ficar no backend, nao em arquivos `.js` carregados no navegador.

## Fluxo de carregamento

1. Usuario abre uma pagina de base.
2. HTML chama o backend para buscar metadados da base.
3. Backend retorna tabelas/abas e colunas disponiveis.
4. HTML monta filtros e cabecalho da tabela.
5. Usuario informa CPF, nome ou email.
6. HTML envia a busca ao backend.
7. Backend consulta somente a base e as tabelas selecionadas.
8. Backend retorna colunas e resultados.
9. HTML renderiza a tabela.

## Endpoints sugeridos

```text
GET /health
GET /bases
GET /bases/{base}
POST /search/{base}
POST /search/unico
```

## Metadados da base

Endpoint:

```text
GET /bases/{base}
```

Resposta esperada:

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

## Consulta

Endpoint:

```text
POST /search/{base}
```

Payload:

```json
{
  "tipo": "cpf",
  "entradas": ["12345678900", "98765432100"],
  "tabelas": ["cravinhos", "cotia"],
  "status": ["Encontrado"],
  "colunas": "todas"
}
```

Antes de consultar, o backend deve aplicar as mesmas normalizacoes usadas no programa antigo:

- CPF: remover pontuacao, remover decimal `.0` vindo do Excel e completar com zero a esquerda quando aplicavel.
- Email: converter para minusculo e remover espacos externos.
- Nome: remover acentos, converter para minusculo e compactar espacos.
- Entradas repetidas na mesma consulta devem ser ignoradas.

Resposta:

```json
{
  "base": "consolidado",
  "tabelas_consultadas": ["cravinhos", "cotia"],
  "total_consultado": 2,
  "total_encontrado": 1,
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
      "tabela": "Cravinhos",
      "nome": "Nome Exemplo",
      "cpf": "12345678900",
      "email": "exemplo@email.com",
      "link_aba": "https://..."
    }
  ],
  "erros": []
}
```

## Duplicados

Com excecao da `UNICO People`, nao havera tratamento de duplicados.

Se uma busca encontrar mais de uma linha nas planilhas, o backend deve devolver todas as linhas encontradas e o HTML deve exibir todas.

Isso preserva a comparacao direta com as planilhas.

## Modo resumo e todas as colunas

O HTML deve manter dois modos de visualizacao:

- `Resumo`: mostra apenas colunas principais da base.
- `Todas as colunas`: mostra todas as colunas retornadas.

Como cada base possui colunas diferentes, as colunas de resumo devem vir do backend nos metadados da base.

## Link da aba

Na tela:

- O campo `link_aba` deve aparecer como botao `Abrir link`.

Ao copiar tabela:

- O valor copiado deve ser a URL real.
- Nao copiar o texto `Abrir link`.

## Copia da tabela

O botao `Copiar tabela` deve usar a mesma ordem de colunas exibida na tela.

Para colunas do tipo `link`, o HTML deve copiar o valor real do link.

## Comportamento esperado por pagina

Cada pagina deve:

- Carregar apenas as tabelas da sua base.
- Mostrar apenas filtros validos para aquela base.
- Renderizar as colunas retornadas pelo backend.
- Enviar a consulta apenas para o endpoint da propria base.
- Exibir todas as linhas retornadas, sem consolidar resultados.
