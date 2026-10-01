import {
  Component,
  OnInit,
} from '@angular/core';

import {
  finalize,
} from 'rxjs';

import {
  ApiService,
} from '../../core/services/api.service';


interface HistoryRow {
  id: string;

  eco_id: string | null;

  eco_code: string | null;

  item: number | null;

  field_key: string;

  field_label: string;

  old_value: string | null;

  new_value: string | null;

  user_email: string;

  user_name: string | null;

  action:
    | 'created'
    | 'updated'
    | 'deleted'
    | string;

  created_at: string;
}


interface HistoryResponse {
  items: HistoryRow[];

  total: number;

  page: number;

  page_size: number;
}


@Component({
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css'],
})
export class ReportsComponent
  implements OnInit {

  // =====================================================
  // DADOS
  // =====================================================

  rows: HistoryRow[] = [];

  total = 0;

  page = 1;

  pageSize = 20;


  // =====================================================
  // FILTROS
  // =====================================================

  eco = '';

  user = '';

  field = '';

  action = '';

  search = '';

  dateStart = '';

  dateEnd = '';


  // =====================================================
  // ESTADOS
  // =====================================================

  loading = false;

  exporting = false;

  error = '';

  validationError = '';


  constructor(
    private readonly api:
      ApiService,
  ) {}


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    this.load();
  }


  // =====================================================
  // CARREGAR HISTÓRICO
  // =====================================================

  load(): void {

    if (
      this.loading
    ) {

      return;
    }


    if (
      !this.validateDates()
    ) {

      return;
    }


    this.loading = true;

    this.error = '';


    this.api
      .get<HistoryResponse>(
        '/history',
        {
          page:
            this.page,

          page_size:
            this.pageSize,

          ...this.filters(),
        },
      )
      .pipe(
        finalize(
          () => {

            this.loading =
              false;
          },
        ),
      )
      .subscribe({

        next: response => {

          this.rows =
            response.items;

          this.total =
            response.total;

          this.page =
            response.page;

          this.pageSize =
            response.page_size;


          const totalPages =
            this.pages();


          if (
            this.page >
            totalPages
          ) {

            this.page =
              totalPages;

            this.load();
          }
        },


        error: error => {

          console.error(
            'Erro ao carregar histórico:',
            error,
          );


          this.error =
            'Não foi possível carregar o histórico. Tente novamente.';
        },
      });
  }


  // =====================================================
  // APLICAR FILTROS
  // =====================================================

  applyFilters(): void {

    if (
      !this.validateDates()
    ) {

      return;
    }


    this.page = 1;

    this.load();
  }


  // =====================================================
  // LIMPAR FILTROS
  // =====================================================

  clear(): void {

    this.eco = '';

    this.user = '';

    this.field = '';

    this.action = '';

    this.search = '';

    this.dateStart = '';

    this.dateEnd = '';

    this.page = 1;

    this.validationError = '';

    this.error = '';


    this.load();
  }


  // =====================================================
  // RETRY
  // =====================================================

  retry(): void {

    this.load();
  }


  // =====================================================
  // EXPORTAÇÃO CSV
  // =====================================================

  exportCsv(): void {

    if (
      this.exporting
      ||
      this.loading
    ) {

      return;
    }


    if (
      !this.validateDates()
    ) {

      return;
    }


    this.exporting = true;

    this.error = '';


    this.api
      .getBlob(
        '/history/export',
        this.filters(),
      )
      .pipe(
        finalize(
          () => {

            this.exporting =
              false;
          },
        ),
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(
              blob,
            );


          const link =
            document.createElement(
              'a',
            );


          link.href =
            url;

          // link.download =
          //   'eco-history.csv';
          const today =
            new Date()
              .toISOString()
              .slice(
                0,
                10,
              );


          link.download =
            `historico-eco-control-${today}.csv`;


          document.body.appendChild(
            link,
          );


          link.click();

          link.remove();


          URL.revokeObjectURL(
            url,
          );
        },


        error: error => {

          console.error(
            'Erro ao exportar histórico:',
            error,
          );


          this.error =
            'Não foi possível exportar o histórico.';
        },
      });
  }


  // =====================================================
  // PAGINAÇÃO
  // =====================================================

  pages(): number {

    return Math.max(
      1,
      Math.ceil(
        this.total /
        this.pageSize,
      ),
    );
  }


  previousPage(): void {

    if (
      this.loading
      ||
      this.page <= 1
    ) {

      return;
    }


    this.page -= 1;

    this.load();
  }


  nextPage(): void {

    if (
      this.loading
      ||
      this.page >=
        this.pages()
    ) {

      return;
    }


    this.page += 1;

    this.load();
  }


  changePageSize(): void {

    this.page = 1;

    this.load();
  }


  // =====================================================
  // AÇÃO
  // =====================================================

  actionLabel(
    action: string,
  ): string {

    const labels:
      Record<
        string,
        string
      > = {

      created:
        'Criada',

      updated:
        'Alterada',

      deleted:
        'Excluída',
    };


    return (
      labels[action]
      ||
      action
      ||
      '—'
    );
  }


  // =====================================================
  // IDENTIFICAÇÃO DO USUÁRIO
  // =====================================================

  userLabel(
    row: HistoryRow,
  ): string {

    return (
      row.user_name
      ||
      row.user_email
      ||
      '—'
    );
  }


  // =====================================================
  // ECO
  // =====================================================

  ecoLabel(
    row: HistoryRow,
  ): string {

    return (
      row.eco_code
      ||
      '—'
    );
  }


  // =====================================================
  // ITEM
  // =====================================================

  itemLabel(
    row: HistoryRow,
  ): string {

    if (
      row.item === null
      ||
      row.item === undefined
    ) {

      return '—';
    }


    return String(
      row.item,
    );
  }


  // =====================================================
  // VALORES DO HISTÓRICO
  // =====================================================

  historyValue(
    value:
      string |
      null |
      undefined,
  ): string {

    if (
      value === null
      ||
      value === undefined
      ||
      value === ''
    ) {

      return '—';
    }


    return value;
  }


  // =====================================================
  // VALIDAÇÃO DE DATAS
  // =====================================================

  private validateDates():
    boolean {

    this.validationError = '';


    if (
      this.dateStart
      &&
      this.dateEnd
      &&
      this.dateStart >
        this.dateEnd
    ) {

      this.validationError =
        'A data inicial não pode ser posterior à data final.';


      return false;
    }


    return true;
  }


  // =====================================================
  // FILTROS DA API
  // =====================================================

  private filters():
    Record<
      string,
      string |
      undefined
    > {

    return {

      date_start:
        this.dateStart
          ? `${this.dateStart}T00:00:00`
          : undefined,

      date_end:
        this.dateEnd
          ? `${this.dateEnd}T23:59:59`
          : undefined,

      user_email:
        this.cleanFilter(
          this.user,
        ),

      field:
        this.cleanFilter(
          this.field,
        ),

      action:
        this.action
        ||
        undefined,

      eco:
        this.cleanFilter(
          this.eco,
        ),

      search:
        this.cleanFilter(
          this.search,
        ),
    };
  }


  // =====================================================
  // NORMALIZAÇÃO DOS FILTROS
  // =====================================================

  private cleanFilter(
    value: string,
  ): string | undefined {

    const normalized =
      value.trim();


    return (
      normalized
      ||
      undefined
    );
  }
}