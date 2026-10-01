import {
  Component,
  OnInit,
  inject,
} from '@angular/core';

import {
  ApiService,
} from '../../core/services/api.service';

import {
  EcoPermissionService,
} from '../../core/services/eco-permission.service';

import {
  COLUMN_GROUPS,
  EcoColumn,
  EcoColumnGroup,
  FIELD_TYPES,
  YES_NO_OPTIONS,
  isCalculatedField,
} from './eco-fields';


@Component({
  templateUrl: './eco-control.component.html',
  styleUrls: ['./eco-control.component.css'],
})
export class EcoControlComponent
  implements OnInit {

  private readonly api =
    inject(ApiService);

  readonly permissions =
    inject(EcoPermissionService);

  readonly fieldTypes =
    FIELD_TYPES;


  // =====================================================
  // COLUNAS
  // =====================================================

  columnGroups:
    readonly EcoColumnGroup[] = [];

  columns:
    readonly EcoColumn[] = [];

  hiddenColumns =
    new Set<string>();


  // =====================================================
  // DADOS
  // =====================================================

  rows: any[] = [];

  total = 0;

  page = 1;

  pageSize = 25;


  // =====================================================
  // OWNERS CONFIGURADOS
  // =====================================================

  ownerOptions: string[] = [];

  ownerGroupMap:
    Record<string, string> = {};


  // =====================================================
  // ESTADOS
  // =====================================================

  loading = false;

  loadError = '';

  cellError = '';

  exporting = false;

  creatingBelow = false;

  deletingAll = false;


  // =====================================================
  // IMPORTAÇÃO XLSX
  // =====================================================

  importModalOpen = false;

  importFile: File | null = null;

  importPreview: any = null;

  importResult: any = null;

  previewingImport = false;

  importingFile = false;

  importError = '';

  importSuccess = '';


  // =====================================================
  // BUSCA
  // =====================================================

  search = '';


  // =====================================================
  // FILTROS
  // =====================================================

  columnFilters:
    Record<string, string> = {};

  filterDrafts:
    Record<string, string> = {};

  openFilterKey:
    string | null = null;

  showColumns = false;

  readonly monthFilterOptions = [
    'JAN',
    'FEB',
    'MAR',
    'APR',
    'MAY',
    'JUN',
    'JUL',
    'AUG',
    'SEP',
    'OCT',
    'NOV',
    'DEC',
  ];


  // =====================================================
  // LINHA SELECIONADA
  // =====================================================

  selectedRow: any = null;


  // =====================================================
  // DRAWER
  // =====================================================

  viewingRow: any = null;

  drawerEditing = false;

  drawerSaving = false;

  drawerError = '';

  drawerSuccess = '';

  drawerDraft:
    Record<string, any> = {};


  // =====================================================
  // EDIÇÃO INLINE
  // =====================================================

  cellSaving =
    new Set<string>();


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    this.loadOwnerOptions();

    this.permissions
      .load()
      .subscribe({

        next: () => {

          this.applyPermissions();

          this.load();
        },

        error: error => {

          console.error(
            'Erro ao carregar permissões:',
            error,
          );

          this.applyPermissions();

          this.load();
        },
      });
  }


  // =====================================================
  // PERMISSÕES
  // =====================================================

  private applyPermissions(): void {

    this.columnGroups =
      COLUMN_GROUPS

        .map(group => ({

          ...group,

          columns:
            group.columns.filter(
              column =>
                this.permissions
                  .canView(
                    column.key
                  )
            ),
        }))

        .filter(
          group =>
            group.columns.length > 0
        );


    this.columns =
      this.columnGroups
        .flatMap(
          group =>
            group.columns
        );


    for (
      const key
      of Array.from(
        this.hiddenColumns
      )
    ) {

      const exists =
        this.columns.some(
          column =>
            column.key === key
        );


      if (!exists) {

        this.hiddenColumns
          .delete(
            key
          );
      }
    }


    const allowedKeys =
      new Set(
        this.columns.map(
          column =>
            column.key
        )
      );


    for (
      const key
      of Object.keys(
        this.columnFilters
      )
    ) {

      if (
        !allowedKeys.has(
          key
        )
      ) {

        delete this.columnFilters[
          key
        ];
      }
    }


    for (
      const key
      of Object.keys(
        this.filterDrafts
      )
    ) {

      if (
        !allowedKeys.has(
          key
        )
      ) {

        delete this.filterDrafts[
          key
        ];
      }
    }
  }


  // =====================================================
  // CARREGAR ECOS
  // =====================================================

  load(): void {

    this.loading = true;

    this.loadError = '';

    this.cellError = '';


    this.api
      .get<any>(
        '/ecos',
        {
          page:
            this.page,

          page_size:
            this.pageSize,

          search:
            this.search,

          column_filters:
            this.columnFiltersParam(),
        },
      )
      .subscribe({

        next: response => {


          this.rows =
            response.items;

          this.total =
            response.total;


          if (this.selectedRow) {

            const selected =
              this.rows.find(
                row =>
                  row.id ===
                  this.selectedRow.id
              );


            this.selectedRow =
              selected || null;
          }


          if (
            this.viewingRow
            &&
            !this.drawerEditing
          ) {

            const updated =
              this.rows.find(
                row =>
                  row.id ===
                  this.viewingRow.id
              );


            if (updated) {

              this.viewingRow =
                updated;
            }
          }


          this.loading = false;
        },


        error: error => {

          console.error(
            'Erro ao carregar ECOs:',
            error,
          );


          this.loadError =
            'Não foi possível carregar as ECOs. Tente novamente.';


          this.loading = false;
        },
      });
  }


  // =====================================================
  // BUSCA
  // =====================================================

  searchEcos(): void {

    this.page = 1;

    this.selectedRow = null;

    this.load();
  }


  // =====================================================
  // FILTROS
  // =====================================================

  applyFilters(): void {

    this.page = 1;

    this.selectedRow = null;

    this.load();
  }


  clearFilters(): void {

    this.columnFilters = {};

    this.filterDrafts = {};

    this.openFilterKey = null;

    this.page = 1;

    this.selectedRow = null;

    this.load();
  }


  get hasActiveFilters():
    boolean {

    return (
      Object.keys(
        this.columnFilters
      ).length > 0
    );
  }


  // =====================================================
  // FILTROS NO CABEÇALHO
  // =====================================================

  isFilterableColumn(
    _column: EcoColumn,
  ): boolean {

    return true;
  }


  toggleColumnFilter(
    columnKey: string,
    event: Event,
  ): void {

    event.stopPropagation();


    if (
      this.openFilterKey ===
      columnKey
    ) {

      this.openFilterKey = null;

      return;
    }


    this.filterDrafts[
      columnKey
    ] =
      this.columnFilters[
        columnKey
      ] ?? '';


    this.openFilterKey =
      columnKey;
  }


  getFilterValue(
    columnKey: string,
  ): string {

    return (
      this.columnFilters[
        columnKey
      ]
      ??
      ''
    );
  }


  getFilterOptions(
    columnKey: string,
  ): readonly string[] {

    const column =
      this.columns.find(
        item =>
          item.key ===
          columnKey
      );


    if (!column) {

      return [];
    }


    if (
      column.key ===
      'month'
    ) {

      return (
        this.monthFilterOptions
      );
    }


    if (
      column.key ===
      'owner'
      &&
      this.ownerOptions.length > 0
    ) {

      return (
        this.ownerOptions
      );
    }


    if (
      column.type ===
      FIELD_TYPES.BOOL_YN
      ||
      column.type ===
      FIELD_TYPES.CALC_BOOL
    ) {

      return (
        YES_NO_OPTIONS
      );
    }


    if (
      column.options
      &&
      column.options.length > 0
    ) {

      return (
        column.options
      );
    }


    return [];
  }


  hasFilterOptions(
    columnKey: string,
  ): boolean {

    return (
      this.getFilterOptions(
        columnKey
      ).length > 0
    );
  }


  getFilterInputType(
    column: EcoColumn,
  ): 'text' | 'date' | 'number' {

    if (
      column.type ===
      FIELD_TYPES.DATE
    ) {

      return 'date';
    }


    if (
      column.type ===
      FIELD_TYPES.CALC_NUMBER
      ||
      column.key ===
      'item'
    ) {

      return 'number';
    }


    return 'text';
  }


  getFilterPlaceholder(
    column: EcoColumn,
  ): string {

    if (
      column.type ===
      FIELD_TYPES.DATE
    ) {

      return '';
    }


    if (
      column.type ===
      FIELD_TYPES.CALC_NUMBER
      ||
      column.key ===
      'item'
    ) {

      return 'Digite o valor';
    }


    return (
      `Buscar em ${column.label}`
    );
  }


  setColumnFilter(
    columnKey: string,
    value: string,
  ): void {

    const normalized =
      String(
        value ?? ''
      ).trim();


    if (normalized) {

      this.columnFilters[
        columnKey
      ] = normalized;

    } else {

      delete this.columnFilters[
        columnKey
      ];
    }


    this.filterDrafts[
      columnKey
    ] = normalized;


    this.openFilterKey = null;

    this.applyFilters();
  }


  applyColumnFilter(
    columnKey: string,
  ): void {

    const value =
      this.filterDrafts[
        columnKey
      ] ?? '';


    this.setColumnFilter(
      columnKey,
      value,
    );
  }


  clearColumnFilter(
    columnKey: string,
  ): void {

    delete this.columnFilters[
      columnKey
    ];

    delete this.filterDrafts[
      columnKey
    ];


    this.openFilterKey = null;

    this.applyFilters();
  }


  filterEmpty(
    columnKey: string,
  ): void {

    this.setColumnFilter(
      columnKey,
      '__empty__',
    );
  }


  filterNotEmpty(
    columnKey: string,
  ): void {

    this.setColumnFilter(
      columnKey,
      '__not_empty__',
    );
  }


  private columnFiltersParam():
    string | undefined {

    const activeFilters =
      Object.fromEntries(

        Object.entries(
          this.columnFilters
        )

          .filter(
            ([
              key,
              value,
            ]) => {

              return (
                !!key
                &&
                value !== null
                &&
                value !== undefined
                &&
                String(
                  value
                ).trim() !== ''
              );
            }
          )
      );


    if (
      Object.keys(
        activeFilters
      ).length === 0
    ) {

      return undefined;
    }


    return JSON.stringify(
      activeFilters
    );
  }


  // =====================================================
  // COLUNAS VISÍVEIS
  // =====================================================

  get visibleColumns():
    readonly EcoColumn[] {

    return this.columns.filter(
      column =>
        !this.hiddenColumns.has(
          column.key
        )
    );
  }


  get visibleColumnGroups():
    readonly EcoColumnGroup[] {

    return this.columnGroups

      .map(group => ({

        ...group,

        columns:
          group.columns.filter(
            column =>
              !this.hiddenColumns
                .has(
                  column.key
                )
          ),
      }))

      .filter(
        group =>
          group.columns.length > 0
      );
  }


  isColumnVisible(
    column: EcoColumn,
  ): boolean {

    return (
      !this.hiddenColumns.has(
        column.key
      )
    );
  }


  toggleColumn(
    column: EcoColumn,
  ): void {

    if (
      this.hiddenColumns.has(
        column.key
      )
    ) {

      this.hiddenColumns.delete(
        column.key
      );

    } else {

      this.hiddenColumns.add(
        column.key
      );
    }
  }


  // =====================================================
  // SELEÇÃO DA LINHA
  // =====================================================

  isRowSelected(
    row: any,
  ): boolean {

    return (
      this.selectedRow?.id ===
      row.id
    );
  }


  selectRow(
    row: any,
  ): void {

    if (
      this.selectedRow?.id ===
      row.id
    ) {

      this.selectedRow = null;

      return;
    }


    this.selectedRow =
      row;
  }


  toggleRow(
    row: any,
    checked: boolean,
  ): void {

    if (checked) {

      this.selectedRow =
        row;

    } else if (
      this.selectedRow?.id ===
      row.id
    ) {

      this.selectedRow =
        null;
    }
  }


  get selectedItem():
    number | null {

    return (
      this.selectedRow?.item ??
      null
    );
  }


  // =====================================================
  // ADICIONAR ABAIXO DA ECO SELECIONADA
  // =====================================================

  addBelowSelected(): void {

    if (
      !this.permissions
        .canCreateEco
    ) {

      return;
    }


    if (
      !this.selectedRow
    ) {

      this.cellError =
        'Selecione uma ECO para adicionar uma nova linha abaixo dela.';

      return;
    }


    if (
      this.creatingBelow
    ) {

      return;
    }


    this.creatingBelow = true;

    this.cellError = '';


    this.api
      .post<any>(
        `/ecos/${this.selectedRow.id}/after`,
        {},
      )
      .subscribe({

        next: created => {

          this.creatingBelow = false;

          this.selectedRow =
            created;

          this.load();
        },


        error: error => {

          console.error(
            'Erro ao adicionar ECO abaixo:',
            error,
          );


          this.creatingBelow = false;


          const detail =
            error.error?.detail;


          this.cellError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível adicionar a ECO.';
        },
      });
  }


  // =====================================================
  // DRAWER
  // =====================================================

  openDetails(
    row: any,
  ): void {

    this.viewingRow =
      row;

    this.drawerEditing =
      false;

    this.drawerSaving =
      false;

    this.drawerError = '';

    this.drawerSuccess = '';

    this.drawerDraft = {};
  }


  closeDetails(): void {

    if (
      this.drawerSaving
    ) {

      return;
    }


    this.viewingRow =
      null;

    this.drawerEditing =
      false;

    this.drawerError = '';

    this.drawerSuccess = '';

    this.drawerDraft = {};
  }


  // =====================================================
  // DRAWER - PERMISSÃO DE EDIÇÃO
  // =====================================================

  get canEditDrawer(): boolean {

    return this.columns.some(
      column =>
        this.isColumnEditable(
          column
        )
    );
  }


  // =====================================================
  // DRAWER - INICIAR EDIÇÃO
  // =====================================================

  startDrawerEdit(): void {

    if (
      !this.viewingRow
      ||
      !this.canEditDrawer
    ) {

      return;
    }


    this.drawerError = '';

    this.drawerSuccess = '';


    this.drawerDraft =
      this.buildDrawerDraft(
        this.viewingRow
      );


    this.drawerEditing =
      true;
  }


  // =====================================================
  // DRAWER - CANCELAR EDIÇÃO
  // =====================================================

  cancelDrawerEdit(): void {

    if (
      this.drawerSaving
    ) {

      return;
    }


    this.drawerEditing =
      false;

    this.drawerError = '';

    this.drawerSuccess = '';

    this.drawerDraft = {};
  }


  // =====================================================
  // DRAWER - CRIAR RASCUNHO
  // =====================================================

  private buildDrawerDraft(
    row: any,
  ): Record<string, any> {

    const draft:
      Record<string, any> = {};


    for (
      const column
      of this.columns
    ) {

      const value =
        row?.[column.key];


      draft[column.key] =
        value === null ||
        value === undefined
          ? ''
          : value;
    }


    return draft;
  }


  // =====================================================
  // DRAWER - VALOR
  // =====================================================

  drawerValue(
    column: EcoColumn,
  ): any {

    if (
      this.drawerEditing
    ) {

      return (
        this.drawerDraft[
          column.key
        ] ?? ''
      );
    }


    return (
      this.viewingRow?.[
        column.key
      ] ?? ''
    );
  }


  // =====================================================
  // DRAWER - ALTERAR VALOR
  // =====================================================

  setDrawerValue(
    column: EcoColumn,
    value: any,
  ): void {

    if (
      !this.drawerEditing
      ||
      !this.isColumnEditable(
        column
      )
    ) {

      return;
    }


    this.drawerDraft[
      column.key
    ] = value;


    if (
      column.key === 'owner'
    ) {

      const owner = String(
        value ?? ''
      ).trim();

      const mappedGroup =
        this.ownerGroupMap[
          owner
        ];

      if (mappedGroup) {

        this.drawerDraft[
          'group'
        ] = mappedGroup;
      }
    }
  }


  // =====================================================
  // DRAWER - DETECTAR ALTERAÇÕES
  // =====================================================

  get drawerHasChanges(): boolean {

    if (
      !this.drawerEditing
      ||
      !this.viewingRow
    ) {

      return false;
    }


    return this.columns.some(
      column => {

        if (
          !this.isColumnEditable(
            column
          )
        ) {

          return false;
        }


        const oldValue =
          this.viewingRow[
            column.key
          ] ?? '';


        const newValue =
          this.drawerDraft[
            column.key
          ] ?? '';


        return (
          String(oldValue)
          !==
          String(newValue)
        );
      }
    );
  }


  // =====================================================
  // DRAWER - SALVAR ALTERAÇÕES
  // =====================================================

  saveDrawerChanges(): void {

    if (
      !this.viewingRow
      ||
      !this.drawerEditing
      ||
      this.drawerSaving
    ) {

      return;
    }


    const changes:
      Record<string, any> = {};


    for (
      const column
      of this.columns
    ) {

      if (
        !this.isColumnEditable(
          column
        )
      ) {

        continue;
      }


      const previousValue =
        this.viewingRow[
          column.key
        ] ?? null;


      let newValue =
        this.drawerDraft[
          column.key
        ];


      if (
        newValue === ''
      ) {

        newValue = null;
      }


      if (
        String(
          previousValue ?? ''
        )
        ===
        String(
          newValue ?? ''
        )
      ) {

        continue;
      }


      changes[
        column.key
      ] = newValue;
    }


    if (
      Object.keys(
        changes
      ).length === 0
    ) {

      this.drawerEditing =
        false;

      this.drawerDraft = {};

      this.drawerSuccess =
        'Nenhuma alteração foi realizada.';

      return;
    }


    const id =
      this.viewingRow.id;


    this.drawerSaving =
      true;

    this.drawerError = '';

    this.drawerSuccess = '';


    this.api
      .patch<any>(
        `/ecos/${id}`,
        changes,
      )
      .subscribe({

        next: updated => {

          this.drawerSaving =
            false;


          this.viewingRow =
            updated;


          const row =
            this.rows.find(
              item =>
                item.id === id
            );


          if (row) {

            Object.assign(
              row,
              updated
            );
          }


          if (
            this.selectedRow?.id
            === id
          ) {

            this.selectedRow =
              row || updated;
          }


          this.drawerEditing =
            false;

          this.drawerDraft = {};

          this.drawerSuccess =
            'Alterações salvas com sucesso.';
        },


        error: error => {

          console.error(
            'Erro ao salvar alterações da ECO:',
            error,
          );


          this.drawerSaving =
            false;


          const detail =
            error.error?.detail;


          this.drawerError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível salvar as alterações.';
        },
      });
  }


  // =====================================================
  // OWNERS
  // =====================================================

  loadOwnerOptions(): void {

    this.api
      .get<
        {
          owner: string;
          group: string;
        }[]
      >(
        '/settings/owner-options'
      )
      .subscribe({

        next: items => {

          this.ownerOptions =
            items

              .map(
                item =>
                  item.owner
              )

              .filter(
                owner =>
                  !!owner
              );


          this.ownerGroupMap =
            Object.fromEntries(
              items
                .filter(
                  item =>
                    !!item.owner
                    &&
                    !!item.group
                )
                .map(
                  item => [
                    item.owner,
                    item.group,
                  ]
                )
            );
        },


        error: error => {

          console.error(
            'Erro ao carregar owners:',
            error,
          );

          this.ownerOptions = [];

          this.ownerGroupMap = {};
        },
      });
  }


  isOwnerColumn(
    column: EcoColumn,
  ): boolean {

    return (
      column.key ===
      'owner'
    );
  }


  // =====================================================
  // STATUS
  // =====================================================

  statusClass(
    status: string | null | undefined,
  ): string {

    const normalized =
      String(
        status || ''
      )
        .trim()
        .toUpperCase();


    switch (normalized) {

      case 'RELEASED':
        return 'status-released';

      case 'CANCELLED':
        return 'status-cancelled';

      case 'REJECTED':
        return 'status-rejected';

      case 'WORKING':
        return 'status-working';

      case 'ON HOLD':
        return 'status-hold';

      case 'PROCESSING':
        return 'status-processing';

      default:
        return 'status-default';
    }
  }


  // =====================================================
  // EDITABILIDADE
  // =====================================================

  isColumnEditable(
    column: EcoColumn,
  ): boolean {

    if (
      isCalculatedField(
        column
      )
    ) {

      return false;
    }


    return (
      this.permissions
        .canEdit(
          column.key
        )
    );
  }


  isCellSaving(
    row: any,
    column: EcoColumn,
  ): boolean {

    const key =
      `${row.id}:${column.key}`;


    return (
      this.cellSaving.has(
        key
      )
    );
  }


  // =====================================================
  // EDIÇÃO INLINE
  // =====================================================

  updateCell(
    row: any,
    column: EcoColumn,
    event: Event,
  ): void {

    if (
      !this.isColumnEditable(
        column
      )
    ) {

      return;
    }


    const element =
      event.target as
        HTMLInputElement |
        HTMLSelectElement;


    const rawValue =
      element.value;


    const value =
      rawValue === ''
        ? null
        : rawValue;


    const previousValue =
      row[column.key] ??
      null;


    if (
      String(
        previousValue ?? ''
      )
      ===
      String(
        value ?? ''
      )
    ) {

      return;
    }


    const cellKey =
      `${row.id}:${column.key}`;


    this.cellSaving.add(
      cellKey
    );


    this.cellError = '';


    this.api
      .patch<any>(
        `/ecos/${row.id}`,
        {
          [column.key]:
            value,
        },
      )
      .subscribe({

        next: updated => {

          Object.assign(
            row,
            updated
          );


          if (
            this.viewingRow?.id ===
            row.id
          ) {

            this.viewingRow =
              row;
          }


          if (
            this.selectedRow?.id ===
            row.id
          ) {

            this.selectedRow =
              row;
          }


          this.cellSaving.delete(
            cellKey
          );
        },


        error: error => {

          console.error(
            'Erro ao atualizar campo:',
            error,
          );


          this.cellSaving.delete(
            cellKey
          );


          const detail =
            error.error?.detail;


          this.cellError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível atualizar o campo.';


          element.value =
            previousValue === null ||
            previousValue === undefined
              ? ''
              : String(
                  previousValue
                );
        },
      });
  }


  // =====================================================
  // EXCLUIR ECO
  // =====================================================

  remove(
    row: any,
  ): void {

    if (
      !this.permissions
        .isAdmin
    ) {

      return;
    }


    const identifier =
      row.eco ||
      row.item;


    const confirmed =
      confirm(
        `Excluir ECO ${identifier}?`
      );


    if (!confirmed) {

      return;
    }


    this.api
      .delete(
        `/ecos/${row.id}`,
      )
      .subscribe({

        next: () => {

          if (
            this.selectedRow?.id ===
            row.id
          ) {

            this.selectedRow =
              null;
          }


          if (
            this.viewingRow?.id ===
            row.id
          ) {

            this.viewingRow =
              null;

            this.drawerEditing =
              false;

            this.drawerDraft = {};
          }


          this.load();
        },


        error: error => {

          console.error(
            'Erro ao excluir ECO:',
            error,
          );


          const detail =
            error.error?.detail;


          this.cellError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível excluir a ECO.';
        },
      });
  }


  // =====================================================
  // EXCLUIR TODAS AS ECOS
  // =====================================================

  deleteAllEcos(): void {

    if (
      !this.permissions.isAdmin
      ||
      this.deletingAll
      ||
      this.total === 0
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        `Tem certeza que deseja excluir todas as ${this.total} ECOs?\n\n`
        +
        'Esta ação não poderá ser desfeita.'
      );

    if (!confirmed) {
      return;
    }

    const confirmation =
      window.prompt(
        'Para confirmar, digite:\n\nEXCLUIR TUDO'
      );

    if (
      confirmation !==
      'EXCLUIR TUDO'
    ) {
      return;
    }

    this.deletingAll = true;
    this.cellError = '';

    this.api
      .delete<{
        deleted_rows: number;
      }>(
        '/ecos/bulk/all'
      )
      .subscribe({
        next: response => {
          this.deletingAll = false;
          this.selectedRow = null;
          this.viewingRow = null;
          this.page = 1;

          console.log(
            `${response.deleted_rows} ECOs excluídas.`
          );

          this.load();
        },
        error: error => {
          console.error(
            'Erro ao excluir todas as ECOs:',
            error,
          );

          this.deletingAll = false;

          const detail = error?.error?.detail;
          this.cellError = (
            typeof detail === 'string'
              ? detail
              : 'Não foi possível excluir todas as ECOs.'
          );
        },
      });
  }


  // =====================================================
  // IMPORTAÇÃO XLSX - ABRIR
  // =====================================================

  openImportModal(): void {

    if (
      !this.permissions.canBulkEdit
    ) {
      return;
    }

    this.importModalOpen = true;

    this.importFile = null;
    this.importPreview = null;
    this.importResult = null;

    this.importError = '';
    this.importSuccess = '';
  }


  closeImportModal(): void {

    if (
      this.previewingImport
      ||
      this.importingFile
    ) {
      return;
    }

    this.importModalOpen = false;
    this.importFile = null;
    this.importPreview = null;
    this.importResult = null;
    this.importError = '';
    this.importSuccess = '';
  }


  onImportFileSelected(
    event: Event,
  ): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    this.importFile = null;
    this.importPreview = null;
    this.importResult = null;
    this.importError = '';
    this.importSuccess = '';

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      this.importError = 'Formato inválido. Envie um arquivo .xlsx.';
      input.value = '';
      return;
    }

    if (file.size === 0) {
      this.importError = 'O arquivo enviado está vazio.';
      input.value = '';
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      this.importError = 'O arquivo excede o limite máximo de 25 MB.';
      input.value = '';
      return;
    }

    this.importFile = file;
  }


  previewImport(): void {

    if (
      !this.importFile
      ||
      this.previewingImport
      ||
      !this.permissions.canBulkEdit
    ) {
      return;
    }

    const formData = new FormData();
    formData.append('file', this.importFile);

    this.previewingImport = true;
    this.importError = '';
    this.importSuccess = '';

    this.api
      .post<any>(
        '/ecos/import/preview',
        formData,
      )
      .subscribe({
        next: response => {
          this.importPreview = response;
          this.previewingImport = false;
        },
        error: error => {
          console.error(
            'Erro ao analisar planilha:',
            error,
          );
          this.importError = this.importErrorMessage(
            error,
            'Não foi possível analisar a planilha.',
          );
          this.previewingImport = false;
        },
      });
  }


  confirmImport(): void {

    if (
      !this.importFile
      ||
      !this.importPreview?.can_import
      ||
      this.importingFile
      ||
      !this.permissions.canBulkEdit
    ) {
      return;
    }

    const formData = new FormData();
    formData.append('file', this.importFile);

    this.importingFile = true;
    this.importError = '';
    this.importSuccess = '';

    this.api
      .post<any>(
        '/ecos/import',
        formData,
      )
      .subscribe({
        next: response => {
          this.importResult = response;
          this.importPreview = null;
          this.importSuccess = (
            `${response.imported_rows} ECO(s) importada(s) com sucesso.`
          );
          this.importingFile = false;
          this.load();
        },
        error: error => {
          console.error(
            'Erro ao importar planilha:',
            error,
          );
          this.importError = this.importErrorMessage(
            error,
            'Não foi possível importar a planilha.',
          );
          this.importingFile = false;
        },
      });
  }


  private importErrorMessage(
    error: any,
    fallback: string,
  ): string {
    const detail = error?.error?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (typeof detail?.message === 'string') {
      return detail.message;
    }

    return fallback;
  }


  // =====================================================
  // EXPORTAÇÃO EXCEL
  // =====================================================

  exportExcel(): void {

    if (
      this.exporting
    ) {

      return;
    }


    this.exporting = true;

    this.cellError = '';


    this.api
      .getBlob(
        '/ecos/export',
        {
          search:
            this.search,

          column_filters:
            this.columnFiltersParam(),
        },
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(
              blob
            );


          const link =
            document.createElement(
              'a'
            );


          const now =
            new Date();


          const year =
            now.getFullYear();


          const month =
            String(
              now.getMonth() + 1
            ).padStart(
              2,
              '0'
            );


          const day =
            String(
              now.getDate()
            ).padStart(
              2,
              '0'
            );


          link.href =
            url;


          link.download =
            `ECO_CONTROL_${year}-${month}-${day}.xlsx`;


          document.body
            .appendChild(
              link
            );


          link.click();


          document.body
            .removeChild(
              link
            );


          URL.revokeObjectURL(
            url
          );


          this.exporting =
            false;
        },


        error: error => {

          console.error(
            'Erro ao exportar Excel:',
            error,
          );


          this.exporting =
            false;


          const detail =
            error.error?.detail;


          this.cellError =
            typeof detail ===
            'string'
              ? detail
              : 'Não foi possível exportar as ECOs para Excel.';
        },
      });
  }


  // =====================================================
  // PAGINAÇÃO
  // =====================================================

  previousPage(): void {

    if (
      this.page <= 1
      ||
      this.loading
    ) {

      return;
    }


    this.page--;

    this.selectedRow = null;

    this.load();
  }


  nextPage(): void {

    if (
      this.page >=
      this.pages()
      ||
      this.loading
    ) {

      return;
    }


    this.page++;

    this.selectedRow = null;

    this.load();
  }


  pages(): number {

    return Math.max(
      1,
      Math.ceil(
        this.total /
        this.pageSize
      )
    );
  }


  // =====================================================
  // EXIBIÇÃO
  // =====================================================

  displayValue(
    row: any,
    column: EcoColumn,
  ): string {

    const value =
      row?.[column.key];


    if (
      value === null ||
      value === undefined ||
      value === ''
    ) {

      return '-';
    }


    if (
      typeof value ===
      'boolean'
    ) {

      return value
        ? 'YES'
        : 'NO';
    }


    return String(
      value
    );
  }


  // =====================================================
  // HELPERS
  // =====================================================

  isBooleanColumn(
    column: EcoColumn,
  ): boolean {

    return (
      column.type ===
      FIELD_TYPES.CALC_BOOL
    );
  }


  isStatusColumn(
    column: EcoColumn,
  ): boolean {

    return (
      column.key ===
      'status'
    );
  }


  isEcoColumn(
    column: EcoColumn,
  ): boolean {

    return (
      column.key === 'eco'
      ||
      column.key === 'az_eco_no'
    );
  }


  trackColumn(
    _index: number,
    column: EcoColumn,
  ): string {

    return column.key;
  }


  trackRow(
    _index: number,
    row: any,
  ): string {

    return row.id;
  }


  trackGroup(
    _index: number,
    group: EcoColumnGroup,
  ): string {

    return group.key;
  }
}