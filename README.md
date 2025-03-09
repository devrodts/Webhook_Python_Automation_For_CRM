# Commel Automações - Distribuição de Leads

Este projeto tem como objetivo receber, organizar e distribuir leads (principalmente oriundos do Facebook) para consultores específicos, além de enviar esses leads ao RD Station para acompanhamento e registro de oportunidades de vendas.

## Tecnologias Utilizadas

- **Python 3.9**: Linguagem principal do projeto.  
- **Flask**: Microframework para criação de APIs e gerenciamento de rotas.  
- **Redis**: Banco de dados em memória utilizado para contagem de leads, controle de distribuição e lock de concorrência.  
- **Docker e Docker Compose**: Facilita a criação de contêineres e o gerenciamento das dependências.  
- **GitHub Actions**: Automatiza o processo de deploy em um servidor remoto (VPS).  
- **rdstation (Pacote Personalizado)**: Integração com a API da RD Station para criação de contatos e deals.

## Arquivos Principais

- **`facebook_lead_distribuition_rd.py`**  
  - Arquivo principal do Flask que recebe requisições em `/webhook`, registra leads no Redis, distribui aos consultores e cria registros na RD Station.  
  - Expõe uma rota `/stats` para visualizar estatísticas de distribuição e uma rota `/reset-db` para reiniciar os contadores de leads e redis.

- **`requirements.txt`**  
  - Lista de dependências para o projeto.

- **`docker-compose.yml`**  
  - Configura o serviço para rodar em contêiner Docker, mapeando a porta interna da aplicação (5000) para a porta 9500 no host.

- **`.github/workflows/deploy-prod.yml`**  
  - Contém o pipeline de deploy contínuo via GitHub Actions. Sempre que há um push na branch `master`, o repositório é atualizado na VPS e a aplicação é recriada.

## Como Executar Localmente

1. **Pré-requisitos**:
   - [Docker](https://www.docker.com/) instalado.
   - [Docker Compose](https://docs.docker.com/compose/) instalado.

2. **Clonar o Repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd <pasta-do-repositorio>
   ```

3. **Criar um arquivo `.env` (opcional)**:
   - Defina a variável de ambiente `RD_TOKEN` para autenticação na RD Station.  
   - O Docker Compose já exporta `RD_TOKEN=673a95db89fd130013b15373` como exemplo, mas você pode sobrescrever com seu próprio token.

4. **Construir e Executar os Contêineres**:
   ```bash
   docker-compose up -d --build
   ```

5. **Acessar a Aplicação**:
   - A aplicação Flask estará rodando em [http://localhost:9500](http://localhost:9500).

## Rotas Importantes

- **`POST /webhook`**  
  Recebe os dados do lead em formato JSON. Exemplo de payload:
  ```json
  {
    "name": "Nome do Lead",
    "email": "email@example.com",
    "phone": ["+55 11 9xxxx-xxxx"],
    "horario_contato": "Manhã",
    "valor_investimento": "5000",
    "preferencia_contato": "Telefone"
  }
  ```
  Este endpoint registra o lead no Redis, distribui para um consultor e cria um negócio na RD Station.

- **`GET /stats`**  
  Retorna estatísticas como total de leads e contagem de leads por consultor.

- **`GET /reset-db?token=sadasd46a4d65sa1d321a3sd1sa23dVv0askL`**  
  Reseta todos os contadores do Redis (somente se o token for válido).

## Estrutura de Distribuição

- Há várias equipes (lists) definidas no código, cada equipe com vários consultores.  
- A distribuição segue um balanceamento interno: cada lead incrementa o contador e designa automaticamente o consultor da vez.

## Observações

- O arquivo `restart.sh` exemplifica como reiniciar o serviço no sistema operacional host, utilizando `systemctl`.  
- Para deploy automatizado, basta configurar corretamente os segredos (chaves SSH, usuário e host) no repositório do GitHub para que a Action em `.github/workflows/deploy-prod.yml` funcione.
