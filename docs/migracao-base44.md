# Histórico de Migração: Do Protótipo Base44 para a Arquitetura ECO CONTROL

Este documento formaliza as motivações técnicas, as limitações identificadas no protótipo legado construído na plataforma **Base44** e as decisões de engenharia aplicadas na migração para a arquitetura de produção em **Angular + FastAPI + PostgreSQL**.

---

## 1. Origem das Regras e Limitações do Base44

No início do projeto, a validação de conceito e os fluxos de tela foram prototipados utilizando a ferramenta no-code **Base44** (`https://app.base44.com/apps/6a9ecde379eeb1349ffaf079/editor/preview`).

Embora o protótipo tenha permitido validar visualmente a necessidade das regras de negócio, a arquitetura no-code apresentou gargalos intransponíveis para a operação real:
* **Falta de Controle Transacional:** Inexistência de controle transacional rigoroso para concorrência de leitura e escrita.
* **Validação Frágil:** Dificuldade em garantir tipagem estática e regras de domínio rigorosas (bloqueio de orçamentos negativos, datas nulas e validações avançadas de regex em lote).
* **Acoplamento Extremo:** Regras de negócio misturadas diretamente nos elementos visuais dos formulários.
* **Impossibilidade de Testes Automatizados e CI/CD:** Inviabilidade de integrar suítes de testes unitários com Pytest e esteiras automatizadas de integração contínua.

---

## 2. Estratégia de Migração por Camadas

A migração foi dividida em três frentes técnicas de desacoplamento:

### 2.1. Frontend: Base44 -> Angular 17+
* **Formulários Estáticos -> Formulários Reativos:** Os formulários do Base44 foram convertidos em componentes com `ReactiveFormsModule`, garantindo validações em tempo real no lado do cliente antes do envio da requisição.
* **Controle de Acesso em Rotas:** Introdução de `Route Guards` e `HttpInterceptors` que tratam a expiração do token JWT e redirecionam o usuário de forma transparente.
* **Interface Dinâmica:** Dashboards analíticos com métricas consolidadas consumindo endpoints dedicados da API.

### 2.2. Backend: Base44 -> FastAPI (Padrão Três Camadas)
* **Lógicas Dispersas -> Camada de Serviço (`Service`):** Todo o cálculo de sufixos homologados de Manaus, matrizes de conversão (`OBU -> AU`, `Owner -> Group`) e regras de fallback foi transferido para a camada `Service`.
* **Tipagem Estática com Pydantic:** Os dados de entrada e saída passaram a ser auditados por schemas de validação rigorosos, retornando `HTTP 422` imediato caso haja inconsistência de tipos ou regras de domínio violadas.
* **Trilha de Auditoria:** Implementação automática de histórico em banco de dados a cada modificação feita em uma ECO.

### 2.3. Banco de Dados: Base44 -> PostgreSQL + Alembic
* **Planilhas Desnormalizadas -> Modelo Relacional Normalizado:** O esquema de dados foi normalizado em tabelas com chaves primárias, índices de busca e restrições de integridade referencial (`FOREIGN KEY`).
* **Constraints de Banco:** Garantia de que valores inconsistentes (ex.: orçamentos negativos) sejam bloqueados no nível de banco de dados.
* **Controle de Versão de Esquema:** Adoção do **Alembic** para versionamento de migrações, viabilizando recriação idêntica de bancos em contêineres de desenvolvimento, homologação e produção.