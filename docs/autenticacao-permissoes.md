# Autenticação, Autorização e Matriz de Permissões — ECO CONTROL

Este documento detalha o fluxo de segurança implementado entre o cliente Angular e a API FastAPI, abordando a emissão de JWT, o controle de acesso baseado em papéis (RBAC) e as restrições de edição por campo.

---

## 1. Fluxo de Autenticação (OAuth2 Password Bearer com JWT)

O ciclo de autenticação ocorre de ponta a ponta em 5 etapas:

```text
[Frontend Angular]                            [Backend FastAPI]
        |                                             |
        |--- 1. POST /api/v1/auth/login ------------->| (Verifica hash de senha)
        |<-- 2. Retorna HTTP 200 { access_token } ----| (Gera JWT assinado HS256)
        |                                             |
(Guarda token no sessionStorage)                      |
        |                                             |
        |--- 3. Requisições subsequentes com Header ->| (Extrai via Depends)
        |       Authorization: Bearer <token>         | (Valida assinatura e expiração)
        |<-- 4. HTTP 200 / 401 / 403 -----------------|
```

### Injeção no Frontend (Angular HttpInterceptor)
O Angular intercepta todas as chamadas HTTP que saem da aplicação e anexa o cabeçalho:
```typescript
request = request.clone({
  setHeaders: {
    Authorization: `Bearer ${token}`
  }
});
```

---

## 2. Tratamento dos Códigos de Erro de Segurança

* **`HTTP 401 Unauthorized`:**
  * **Causa:** Cabeçalho de autorização ausente, token malformado, chave criptográfica inválida, sessão expirada (`exp`) ou login incorreto.
  * **Ação do Sistema:** O interceptor limpa a sessão local e redireciona automaticamente o usuário para a tela `/login`.
* **`HTTP 403 Forbidden`:**
  * **Causa:** O usuário está devidamente autenticado, porém seu perfil (`role`) não tem permissão para a funcionalidade ou para editar o campo em questão.
  * **Ação do Sistema:** O backend bloqueia a operação e o frontend exibe alerta visual de acesso negado.

---

## 3. Perfis de Usuário (RBAC)

O sistema define dois papéis operacionais:

1. **`admin` (Administrador):**
   * Acesso total às configurações e módulos do sistema.
   * Criação e gestão de contas de usuários.
   * Homologação de exceções e alteração de qualquer campo da ECO (inclusive orçamentos).
   * Disparo manual de reprocessamento em lote.
2. **`analyst` (Analista de Engenharia):**
   * Acesso operacional diário (visualização de dashboards e listagem de ECOs).
   * Resolução de pendências em ECOs ambíguas (preenchimento de datas ou justificativas).
   * Sem permissão para alterar orçamentos homologados ou gerenciar contas de outros usuários.

---

## 4. Matriz de Permissões Gerais

| Recurso / Operação | `admin` | `analyst` |
| :--- | :---: | :---: |
| Visualizar Dashboard e Métricas | Sim | Sim |
| Listar e Visualizar Detalhes das ECOs | Sim | Sim |
| Consultar Histórico de Alterações / Auditoria | Sim | Sim |
| Resolver Pendências (Campos Ausentes) | Sim | Sim |
| Homologar ECO Rejeitada Manualmente | Sim | Não |
| Alterar Estimativa de Orçamento Homologada | Sim | Não |
| Criar e Desativar Contas de Usuários | Sim | Não |
| Forçar Reprocessamento de Lote | Sim | Não |

---

## 5. Permissões Granulares por Campo da ECO

A camada de serviço (`Service Layer`) valida os atributos do payload antes de persistir alterações na base:

* **Campos Somente Leitura (Imutáveis via API):**
  * `Codigo_ECO`: Identificador vindo da matriz original.
  * `Data_Recebimento`: Carimbo temporal de ingestão do registro.
  * `Aplicabilidade_Manaus`: Calculado exclusivamente pelas regras de sufixos homologados (`WZ`, `WR`, `WP`, `BRA`).
* **Campos Editáveis por `analyst` e `admin`:**
  * `Justificativa_Tecnica`: Permite complemento técnico durante análise humana.
  * `Data_Implementacao_Alvo`: Permite preenchimento quando o campo vier ausente (Cenário Ambíguo).
  * `Status_Atual`: Transição de status operacionais para conclusão.
* **Campos Editáveis Exclusivamente por `admin`:**
  * `Estimativa_Orcamento`: Travado para analistas operacionais para evitar divergências financeiras.
  * `Categoria_Mudanca`: Reclassificação da categoria estrutural do produto.