# Segurança do repositório

## Arquivos que não devem ser versionados

- `backend/.env` e qualquer outro arquivo `.env` real.
- Tokens, cookies ou credenciais temporárias da UNICO.
- Chaves privadas e arquivos de conta de serviço Google.
- Logs do servidor e respostas JSON contendo dados pessoais.
- Exportações de planilhas, resultados de consultas e arquivos ZIP locais.

## Configuração segura

Use `backend/.env.example` somente como modelo. Os valores reais devem ser
configurados localmente ou no gerenciador de segredos do ambiente de hospedagem.

Antes de publicar, confirme que nenhum CPF, e-mail, telefone, token ou
credencial foi incluído.

## Incidente de exposição

Caso um segredo seja publicado, revogue ou renove a credencial imediatamente.
Apagar o arquivo em um commit posterior não remove o segredo do histórico Git.
