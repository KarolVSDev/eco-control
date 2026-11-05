import {
  Component,
  OnInit,
} from '@angular/core';

import {
  finalize,
  forkJoin,
  Subscription,
} from 'rxjs';

import {
  ApiService,
} from '../../core/services/api.service';

import {
  ChartDatum,
  DashboardStats,
} from '../../shared/models/common';


type DashboardFilter =
  | 'status'
  | 'group'
  | 'owner'
  | 'obu'
  | 'au'
  | 'eco_type'
  | 'delay';


@Component({
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
})
export class DashboardComponent
  implements OnInit {

  // =====================================================
  // DADOS
  // =====================================================

  months: string[] = [];

  stats:
    DashboardStats | null = null;

  status: ChartDatum[] = [];

  groups: ChartDatum[] = [];

  owner: ChartDatum[] = [];

  obu: ChartDatum[] = [];

  au: ChartDatum[] = [];

  types: ChartDatum[] = [];

  evolution: ChartDatum[] = [];

  delay: ChartDatum[] = [];

  summary: any[] = [];

  availableYears: number[] = [];

  selectedYear: number | null = null;


  // =====================================================
  // ESTADO GERAL
  // =====================================================

  loading = false;

  loadError = '';


  // =====================================================
  // BACKUP ANUAL
  // =====================================================

  showAnnualBackupWarning = false;

  backupExporting = false;

  backupError = '';


  // =====================================================
  // ESTADO DOS GRÁFICOS
  // =====================================================

  chartLoading:
    Record<
      DashboardFilter,
      boolean
    > = {
      status: false,
      group: false,
      owner: false,
      obu: false,
      au: false,
      eco_type: false,
      delay: false,
    };


  chartErrors:
    Record<
      DashboardFilter,
      string
    > = {
      status: '',
      group: '',
      owner: '',
      obu: '',
      au: '',
      eco_type: '',
      delay: '',
    };


  private chartRequests:
    Partial<
      Record<
        DashboardFilter,
        Subscription
      >
    > = {};


  // =====================================================
  // FILTROS
  // =====================================================

  filters:
    Record<
      DashboardFilter,
      string
    > = {
      status: '',
      group: '',
      owner: '',
      obu: '',
      au: '',
      eco_type: '',
      delay: '',
    };


  constructor(
    private api: ApiService,
  ) {}


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    this.checkAnnualBackupWarning();

    this.loadAvailableYears();
  }


  // =====================================================
  // CARREGAR DASHBOARD
  // =====================================================

  private loadAvailableYears(): void {


    this.loading = true;

    this.loadError = '';


    this.api
      .get<number[]>(
        '/dashboard/years'
      )
      .subscribe({

        next: years => {

          this.availableYears = years;


          const currentYear =
            new Date().getFullYear();


          this.selectedYear =
            years.includes(currentYear)
              ? currentYear
              : years[0] ?? null;


          if (this.selectedYear === null) {

            this.clearDashboardData();
            this.loading = false;

            return;
          }


          this.loadDashboard(
            this.selectedYear
          );
        },


        error: error => {

          console.error(
            'Erro ao carregar anos do Dashboard:',
            error,
          );


          this.loading = false;
          this.loadError =
            'Não foi possível carregar os anos disponíveis. Tente novamente.';
        },
      });
  }


  loadDashboard(year: number): void {

    this.loading = true;

    this.loadError = '';


    forkJoin({

      stats:
        this.api.get<DashboardStats>(
          '/dashboard/stats',
          { year },
        ),

      months:
        this.api.get<string[]>(
          '/dashboard/months',
          { year },
        ),

      status:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/status',
          { year },
        ),

      groups:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/group',
          { year },
        ),

      owner:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/owner',
          { year },
        ),

      obu:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/obu',
          { year },
        ),

      au:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/au',
          { year },
        ),

      types:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/eco_type',
          { year },
        ),

      evolution:
        this.api.get<ChartDatum[]>(
          '/dashboard/evolution',
          { year },
        ),

      delay:
        this.api.get<ChartDatum[]>(
          '/dashboard/delay',
          { year },
        ),

      summary:
        this.api.get<any[]>(
          '/dashboard/monthly-summary',
          { year },
        ),

    })
      .pipe(
        finalize(
          () => {

            this.loading =
              false;
          }
        )
      )
      .subscribe({

        next: response => {

          this.stats =
            response.stats;

          this.months =
            response.months;

          this.status =
            response.status;

          this.groups =
            response.groups;

          this.owner =
            response.owner;

          this.obu =
            response.obu;

          this.au =
            response.au;

          this.types =
            response.types;

          this.evolution =
            response.evolution;

          this.delay =
            response.delay;

          this.summary =
            response.summary;

        },


        error: error => {

          console.error(
            'Erro ao carregar Dashboard:',
            error,
          );


          this.loadError =
            'Não foi possível carregar os dados do Dashboard. Tente novamente.';
        },
      });
  }


  // =====================================================
  // TENTAR NOVAMENTE
  // =====================================================

  retry(): void {

    if (this.selectedYear === null) {

      this.loadAvailableYears();

      return;
    }


    this.loadDashboard(
      this.selectedYear
    );
  }


  // =====================================================
  // FILTRO GLOBAL DE ANO
  // =====================================================

  onGlobalYearChange(event: Event): void {

    const year = Number(
      (event.target as HTMLSelectElement).value
    );


    if (
      !Number.isInteger(year)
      || !this.availableYears.includes(year)
      || year === this.selectedYear
    ) {

      return;
    }


    this.selectedYear = year;

    this.resetLocalMonthFilters();

    this.loadDashboard(year);
  }


  private resetLocalMonthFilters(): void {

    this.cancelChartRequests();

    this.filters = {
      status: '',
      group: '',
      owner: '',
      obu: '',
      au: '',
      eco_type: '',
      delay: '',
    };


    this.chartErrors = {
      status: '',
      group: '',
      owner: '',
      obu: '',
      au: '',
      eco_type: '',
      delay: '',
    };


    this.chartLoading = {
      status: false,
      group: false,
      owner: false,
      obu: false,
      au: false,
      eco_type: false,
      delay: false,
    };
  }


  private cancelChartRequests(): void {

    Object.values(
      this.chartRequests
    ).forEach(
      request => request?.unsubscribe()
    );


    this.chartRequests = {};
  }


  private clearDashboardData(): void {

    this.months = [];
    this.stats = null;
    this.status = [];
    this.groups = [];
    this.owner = [];
    this.obu = [];
    this.au = [];
    this.types = [];
    this.evolution = [];
    this.delay = [];
    this.summary = [];

    this.resetLocalMonthFilters();
  }


  // =====================================================
  // AVISO DE BACKUP ANUAL
  // =====================================================

  private checkAnnualBackupWarning(): void {

    const now =
      new Date();

    const month =
      now.getMonth();


    if (
      month < 9
      ||
      month > 11
    ) {

      this.showAnnualBackupWarning =
        false;

      return;
    }


    const year =
      now.getFullYear();


    const dismissed =
      sessionStorage.getItem(
        `eco-control-backup-warning-${year}`,
      );


    this.showAnnualBackupWarning =
      dismissed !== 'true';
  }


  dismissAnnualBackupWarning(): void {

    const year =
      new Date()
        .getFullYear();


    sessionStorage.setItem(
      `eco-control-backup-warning-${year}`,
      'true',
    );


    this.showAnnualBackupWarning =
      false;
  }


  exportAnnualBackup(): void {

    if (
      this.backupExporting
    ) {

      return;
    }


    this.backupExporting =
      true;

    this.backupError = '';


    this.api
      .getBlob(
        '/ecos/export'
      )
      .pipe(
        finalize(
          () => {

            this.backupExporting =
              false;
          }
        )
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
              '0',
            );


          const day =
            String(
              now.getDate()
            ).padStart(
              2,
              '0',
            );


          link.href =
            url;

          link.download =
            `ECO_CONTROL_BACKUP_${year}-${month}-${day}.xlsx`;


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
        },


        error: error => {

          console.error(
            'Erro ao gerar backup anual:',
            error,
          );


          const detail =
            error.error?.detail;


          this.backupError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível gerar o backup dos dados.';
        },
      });
  }


  // =====================================================
  // RECARREGAR GRÁFICO
  // =====================================================

  reload(
    kind: DashboardFilter,
    month: string,
  ): void {

    if (
      this.chartLoading[
        kind
      ]
      || this.selectedYear === null
    ) {

      return;
    }


    this.filters[
      kind
    ] = month;


    this.chartLoading[
      kind
    ] = true;


    this.chartErrors[
      kind
    ] = '';


    const request =
      kind === 'delay'

        ? this.api
            .get<ChartDatum[]>(
              '/dashboard/delay',
              {
                month,
                year: this.selectedYear,
              },
            )

        : this.api
            .get<ChartDatum[]>(
              `/dashboard/group/${kind}`,
              {
                month,
                year: this.selectedYear,
              },
            );


    this.chartRequests[kind] = request
      .pipe(
        finalize(
          () => {

            this.chartLoading[
              kind
            ] = false;

            delete this.chartRequests[kind];
          }
        )
      )
      .subscribe({

        next: data => {

          this.setChartData(
            kind,
            data,
          );
        },


        error: error => {

          console.error(
            `Erro ao atualizar gráfico ${kind}:`,
            error,
          );


          this.chartErrors[
            kind
          ] =
            'Não foi possível atualizar este gráfico.';
        },
      });
  }


  // =====================================================
  // ATRIBUIR DADOS AO GRÁFICO
  // =====================================================

  private setChartData(
    kind: DashboardFilter,
    data: ChartDatum[],
  ): void {

    switch (
      kind
    ) {

      case 'status':

        this.status =
          data;

        break;


      case 'group':

        this.groups =
          data;

        break;


      case 'owner':

        this.owner =
          data;

        break;


      case 'obu':

        this.obu =
          data;

        break;


      case 'au':

        this.au =
          data;

        break;


      case 'eco_type':

        this.types =
          data;

        break;


      case 'delay':

        this.delay =
          data;

        break;
    }
  }
}
