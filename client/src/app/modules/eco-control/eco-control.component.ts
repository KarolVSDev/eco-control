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
  ECO_TYPE_OPTIONS,
  FIELD_TYPES,
  GROUP_OPTIONS,
  ITEM_TYPE_OPTIONS,
  OBU_OPTIONS,
  STATUS_OPTIONS,
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
  // ESTADOS
  // =====================================================

  loading = false;

  loadError = '';

  cellError = '';

  exporting = false;

  creatingBelow = false;


  // =====================================================
  // BUSCA
  // =====================================================

  search = '';


  // =====================================================
  // FILTROS
  // =====================================================

  status = '';

  filterGroup = '';

  filterObu = '';

  filterItemType = '';

  filterEcoType = '';


  showFilters = false;

  showColumns = false;


  readonly statuses = [
    '',
    ...STATUS_OPTIONS,
  ];

  readonly groups = [
    '',
    ...GROUP_OPTIONS,
  ];

  readonly obus = [
    '',
    ...OBU_OPTIONS,
  ];

  readonly itemTypes = [
    '',
    ...ITEM_TYPE_OPTIONS,
  ];

  readonly ecoTypes = [
    '',
    ...ECO_TYPE_OPTIONS,
  ];


  // =====================================================
  // LINHA SELECIONADA
  // =====================================================

  selectedRow: any = null;


  // =====================================================
  // DRAWER / VISUALIZAÇÃO
  // =====================================================

  viewingRow: any = null;


  // =====================================================
  // EDIÇÃO INLINE
  // =====================================================

  cellSaving =
    new Set<string>();


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

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

          status:
            this.status,

          group:
            this.filterGroup,

          obu:
            this.filterObu,

          item_type:
            this.filterItemType,

          eco_type:
            this.filterEcoType,
        },
      )
      .subscribe({

        next: response => {

          this.rows =
            response.items;

          this.total =
            response.total;


          /*
           * Mantém a linha selecionada
           * caso ela continue na página.
           */

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


          /*
           * Atualiza também o drawer
           * caso a ECO esteja aberta.
           */

          if (this.viewingRow) {

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

    this.load();
  }


  // =====================================================
  // FILTROS
  // =====================================================

  applyFilters(): void {

    this.page = 1;

    this.load();
  }


  changeStatus(): void {

    this.applyFilters();
  }


  clearFilters(): void {

    this.status = '';

    this.filterGroup = '';

    this.filterObu = '';

    this.filterItemType = '';

    this.filterEcoType = '';

    this.page = 1;

    this.load();
  }


  get hasActiveFilters(): boolean {

    return !!(
      this.status ||
      this.filterGroup ||
      this.filterObu ||
      this.filterItemType ||
      this.filterEcoType
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

    /*
     * Clicar novamente na mesma
     * linha remove a seleção.
     */

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


    /*
     * Este endpoint será criado no backend.
     *
     * Ele deverá:
     * - gerar um novo ITEM permanente;
     * - deslocar POSITION das ECOs abaixo;
     * - inserir a nova ECO logo após
     *   a linha selecionada.
     */

    this.api
      .post<any>(
        `/ecos/${this.selectedRow.id}/after`,
        {},
      )
      .subscribe({

        next: created => {

          this.creatingBelow = false;


          /*
           * Recarrega para receber
           * a ordenação oficial.
           */

          this.load();


          /*
           * A nova linha já fica
           * selecionada para edição.
           */

          this.selectedRow =
            created;
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
            typeof detail ===
              'string'

              ? detail

              : 'Não foi possível adicionar a ECO.';
        },
      });
  }


  // =====================================================
  // DRAWER LATERAL
  // =====================================================

  openDetails(
    row: any,
  ): void {

    this.viewingRow =
      row;
  }


  closeDetails(): void {

    this.viewingRow =
      null;
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
  // EDITABILIDADE DAS CÉLULAS
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


          /*
           * Se a mesma ECO estiver
           * aberta no drawer,
           * atualiza os dados exibidos.
           */

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
            typeof detail ===
              'string'

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
            typeof detail ===
              'string'

              ? detail

              : 'Não foi possível excluir a ECO.';
        },
      });
  }


  // =====================================================
  // EXPORTAÇÃO CSV
  // =====================================================

  exportCsv(): void {

    if (
      this.exporting
    ) {

      return;
    }


    this.exporting = true;

    this.cellError = '';


    this.api
      .get<any>(
        '/ecos',
        {

          page: 1,

          page_size: 500,

          search:
            this.search,

          status:
            this.status,

          group:
            this.filterGroup,

          obu:
            this.filterObu,

          item_type:
            this.filterItemType,

          eco_type:
            this.filterEcoType,
        },
      )
      .subscribe({

        next: response => {

          const exportColumns =
            this.visibleColumns;


          const header =
            exportColumns

              .map(
                column =>
                  this.csvValue(
                    column.label
                  )
              )

              .join(';');


          const lines =
            response.items

              .map(
                (row: any) =>

                  exportColumns

                    .map(
                      column =>
                        this.csvValue(
                          this.displayValue(
                            row,
                            column
                          )
                        )
                    )

                    .join(';')
              );


          const csv =
            [
              header,
              ...lines,
            ]
              .join(
                '\r\n'
              );


          const blob =
            new Blob(
              [
                '\uFEFF',
                csv,
              ],
              {
                type:
                  'text/csv;charset=utf-8;',
              },
            );


          const url =
            URL.createObjectURL(
              blob
            );


          const link =
            document.createElement(
              'a'
            );


          link.href =
            url;

          link.download =
            'eco-control.csv';


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


          this.exporting = false;
        },


        error: error => {

          console.error(
            'Erro ao exportar ECOs:',
            error,
          );


          this.exporting = false;


          this.cellError =
            'Não foi possível exportar as ECOs.';
        },
      });
  }


  private csvValue(
    value: unknown,
  ): string {

    if (
      value === null ||
      value === undefined
    ) {

      return '""';
    }


    const text =
      String(value)
        .replace(
          /"/g,
          '""'
        );


    return `"${text}"`;
  }


  // =====================================================
  // PAGINAÇÃO
  // =====================================================

  previousPage(): void {

    if (
      this.page <= 1
    ) {

      return;
    }


    this.page--;


    this.selectedRow =
      null;


    this.load();
  }


  nextPage(): void {

    if (
      this.page >=
      this.pages()
    ) {

      return;
    }


    this.page++;


    this.selectedRow =
      null;


    this.load();
  }


  pages(): number {

    return Math.max(
      1,

      Math.ceil(
        this.total /
        this.pageSize
      ),
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
      column.key ===
        'eco'

      ||

      column.key ===
        'az_eco_no'
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