# Arquitetura do Sistema — ECO CONTROL

Este documento descreve a arquitetura de software, a separação de responsabilidades em camadas e a infraestrutura de execução da plataforma **ECO CONTROL**.

---

## 1. Visão Geral da Arquitetura

O sistema adota o padrão **SPA (Single Page Application) + API RESTful Desacoplada + Banco de Dados Relacional**, operando inteiramente em contêineres Docker orquestrados.

```text
+-------------------------------------------------------------------------------+
|                               FRONTEND (SPA)                                  |
|                                Angular 17+                                    |
|   [Components / Views] <-> [Services (HTTP Client)] <-> [Guards/Interceptors] |
+-------------------------------------------------------------------------------+
                                       |
                             Requisições HTTP / REST
                             (JSON / Bearer Token)
                                       v
+-------------------------------------------------------------------------------+
|                               BACKEND API                                     |
|                                 FastAPI                                       |
|                                                                               |
|   [Controllers / Routers]  --> Validação e tipagem forte via Pydantic Schemas |
|             |                                                                 |
|             v                                                                 |
|     [Service Layer]        --> Regras de negócio, cálculos e governança ECO   |
|             |                                                                 |
|             v                                                                 |
|    [Repository Layer]      --> Abstração de persistência e isolamento SQL     |
|             |                                                                 |
|             v                                                                 |
|     [ORM: SQLAlchemy]      --> Mapeamento Objeto-Relacional declarativo       |
+-------------------------------------------------------------------------------+
                                       |
                               Driver Assíncrono
                                       v
+-------------------------------------------------------------------------------+
|                            BANCO DE DADOS                                     |
|                            PostgreSQL 15+                                     |
|        Tabelas relacionais, integridade referencial, índices de busca         |
|        Controle de versões e evolução de schema gerenciados via Alembic       |
+-------------------------------------------------------------------------------+