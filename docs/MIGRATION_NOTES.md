# Notas da migração Base44 → Angular/FastAPI/PostgreSQL

## Reuso conceitual
Foram reaproveitados os comportamentos e regras validados do protótipo:
- Dashboard, cards e agrupamentos
- Regra GAP > 14 dias
- Categorias de atraso: No prazo, 1–7, 8–14, >14
- Normalização `trim()` em categorias
- ECO Control e campos principais
- Auditoria ECO History
- Permissões por usuário/campo
- Mapeamento OBU → AU
- Mapeamento Owner → Group
- Tema visual escuro

## O que não foi carregado
- SDK Base44
- React / React Router / React Query
- componentes Radix/shadcn React
- dados sensíveis da planilha

## Decisões
1. Cálculos ECO ficam no FastAPI (`EcoCalculationService`), não no Angular.
2. Auditoria é gerada no backend.
3. Filtros/paginação de histórico são server-side.
4. Dashboard usa endpoints agregados PostgreSQL.
5. Categorias são normalizadas com `strip()` antes de persistir/agrupar.
