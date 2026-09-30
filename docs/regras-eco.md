# Regras de Negócio e Governança de ECOs — ECO CONTROL

Este documento detalha as regras de negócio, taxonomia de dados, fluxos de decisão do Gateway e matrizes de conversão de domínio para o ciclo de vida das Ordens de Mudança de Engenharia (ECOs) no sistema **ECO CONTROL**.

---

## 1. Grupos de Campos da ECO

Os atributos de controle de uma ECO são distribuídos em quatro grupos lógicos fundamentais:

### 1.1. Grupo 1: Identificação e Solicitação
* **`Codigo_ECO`**: Identificador alfanumérico único da ordem de mudança gerado na matriz (ex.: `ECO-00125`).
* **`Data_Recebimento`**: Carimbo de data/hora oficial da captura do arquivo ou e-mail de notificação.
* **`Area_Solicitante`**: Departamento de engenharia de origem (ex.: *Engenharia de Produto*).
* **`Nome_Engenheiro_Responsavel`**: Nome completo do engenheiro solicitante encarregado da modificação.
* **`Email_Solicitante`**: Endereço corporativo válido para notificações e confirmações.

### 1.2. Grupo 2: Dados Técnicos de Engenharia
* **`Titulo_Alteracao`**: Resumo textual da alteração técnica proposta.
* **`Codigo_Item_Afetado`**: Part Number ou código do componente em intervenção (ex.: `PN-7788.WZ`).
* **`Categoria_Mudanca`**: Categoria homologada da mudança (`DisplayMedia`, `Canal de PC` ou `Módulos`).
* **`Justificativa_Tecnica`**: Fundamentação técnica para a intervenção no produto/processo.

### 1.3. Grupo 3: Custos e Impacto Financeiro
* **`Estimativa_Orcamento`**: Custo financeiro estimado em dólares americanos (USD), sujeito à restrição de valor maior ou igual a zero (`>= 0.0`).
* **`Impacto_Custos`**: Classificação categórica do peso financeiro (`Baixo`, `Médio` ou `Alto`).

### 1.4. Grupo 4: Planejamento e Unidade Fabril
* **`Unidade_Fabril`**: Planta de execução da manufatura (padrão de referência: `Manaus`).
* **`Data_Implementacao_Alvo`**: Data prevista para corte/aplicação física na linha de produção.
* **`Status_Atual`**: Situação corrente da ordem no fluxo (`PROCESSADO_SUCESSO`, `PENDENTE_VALIDACAO_HUMANA`, `REJEITADO_DADO_INVALIDO`).

---

## 2. Classificação: Campos Editáveis vs. Campos Calculados

### 2.1. Campos Editáveis (Manipulação via Interface Web)
* **`Justificativa_Tecnica`**: Pode receber complementos e anotações durante a triagem operacional por analistas e administradores.
* **`Data_Implementacao_Alvo`**: Permite preenchimento manual em casos de triagem humana quando a data de corte vier ausente na notificação da matriz (Cenário Ambíguo).
* **`Status_Atual`**: Editável na transição de status para resolução de pendências operacionais.
* **`Estimativa_Orcamento`**: Editável **exclusivamente por usuários com perfil `admin`** mediante homologação prévia de renegociação de custos.

### 2.2. Campos Calculados (Automatizados via `Service Layer`)
* **`Aplicabilidade_Manaus`**:
  * Determinado pela verificação de sufixos homologados de Manaus nos Part Numbers do BOM Change: `WZ`, `WR`, `WP` e `BRA`.
  * Regex oficial de validação: `r'\..{1}(WZ|WR|WP|BRA)'`.
  * **Regra de Fallback via BEN**: Caso o campo `Applied Models` venha vazio no NPDM, o Gateway consulta os *Part Numbers* afetados diretamente na base do BEN aplicando a mesma regex.
* **`Impacto_Custos`**:
  * Atribuído automaticamente pela camada de serviço com base no valor da `Estimativa_Orcamento`:
    * Menor que $1.000\text{ USD}$: `Baixo`.
    * De $1.000\text{ USD}$ a $10.000\text{ USD}$: `Médio`.
    * Superior a $10.000\text{ USD}$: `Alto`.
* **`Status_Validacao_Gateway`**:
  * **`PROSSEGUIR_SISTEMA`**: Todos os 15 campos mestres estão presentes, válidos e com regras de negócio atendidas.
  * **`VALIDACAO_HUMANA`**: Identificada ausência de dado passível de complemento operacional (ex.: data de implementação alvo ausente).
  * **`REJEITAR_E_REGISTRAR`**: Identificada inconsistência estrutural ou violação de integridade (ex.: orçamento negativo de $-500\text{ USD}$ ou categoria não homologada).

---

## 3. Matrizes de Mapeamento de Domínio

### 3.1. Mapeamento OBU -> AU (Unidades de Negócio)
Converte a Unidade de Negócio de Origem (*Origin Business Unit*) recebida da matriz para a Unidade de Aplicação Fabril (*Application Unit*):

| OBU de Origem (Matriz) | AU de Aplicação (Sistema) | Planta Industrial | Aplicabilidade Manaus |
| :--- | :--- | :--- | :---: |
| `OBU_DISP` | `AU_DISPLAY_MEDIA` | Planta Manaus | Sim |
| `OBU_PC` | `AU_PC_CHANNEL` | Planta Manaus | Sim |
| `OBU_MOD` | `AU_MODULES` | Planta Manaus | Sim |
| `OBU_GEN` | `AU_GENERAL_ENG` | Planta Manaus | Análise Manual Necessária |
| `OBU_OUT` | `AU_OUTRAS_UNIDADES` | Outras Plantas | Não |

### 3.2. Mapeamento Owner -> Group (Roteamento de Responsabilidades)
Direciona a ordem para a fila de atendimento do grupo técnico competente com base na área ou especialidade do solicitante:

| Papel / Área do Solicitante (Owner) | Grupo Técnico Atribuído (Group) | Fila de Atendimento |
| :--- | :--- | :--- |
| Engenheiro de Layout / Painel | `GRP_ENG_ELETRONICA` | Fila Eletrônica & PCB |
| Engenheiro de Estrutura / Gabinete | `GRP_ENG_MECANICA` | Fila Mecânica & Moldes |
| Engenheiro de Processos Fabris | `GRP_ENG_PROCESSO` | Fila Manufatura & Montagem |
| Analista de Qualidade e Confiabilidade | `GRP_QUALIDADE_FABRIL` | Fila Qualidade & Testes |

---

## 4. Regras de Permissão de Edição por Papel

| Campo da ECO | Perfil `admin` | Perfil `analyst` | Observação / Restrição |
| :--- | :---: | :---: | :--- |
| `Codigo_ECO` | Leitura | Leitura | Imutável (chave de origem) |
| `Data_Recebimento` | Leitura | Leitura | Imutável (carimbo de ingestão) |
| `Aplicabilidade_Manaus` | Leitura | Leitura | Imutável (calculado via Regex/BEN) |
| `Justificativa_Tecnica` | Edição | Edição | Permitido complemento na triagem |
| `Data_Implementacao_Alvo` | Edição | Edição | Preenchimento em caso de pendência |
| `Status_Atual` | Edição | Edição | Transição para resolução humana |
| `Estimativa_Orcamento` | Edição | Leitura | Travado para analista operacional |
| `Categoria_Mudanca` | Edição | Leitura | Alteração restrita à governança |