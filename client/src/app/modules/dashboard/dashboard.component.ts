import {
  Component,
  OnInit,
} from '@angular/core';

import {
  finalize,
  forkJoin,
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


  // =====================================================
  // ESTADO GERAL
  // =====================================================

  loading = false;

  loadError = '';


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

    this.loadDashboard();
  }


  // =====================================================
  // CARREGAR DASHBOARD
  // =====================================================

  loadDashboard(): void {

    if (
      this.loading
    ) {

      return;
    }


    this.loading = true;

    this.loadError = '';


    forkJoin({

      stats:
        this.api.get<DashboardStats>(
          '/dashboard/stats'
        ),

      months:
        this.api.get<string[]>(
          '/dashboard/months'
        ),

      status:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/status'
        ),

      groups:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/group'
        ),

      owner:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/owner'
        ),

      obu:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/obu'
        ),

      au:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/au'
        ),

      types:
        this.api.get<ChartDatum[]>(
          '/dashboard/group/eco_type'
        ),

      evolution:
        this.api.get<ChartDatum[]>(
          '/dashboard/evolution'
        ),

      delay:
        this.api.get<ChartDatum[]>(
          '/dashboard/delay'
        ),

      summary:
        this.api.get<any[]>(
          '/dashboard/monthly-summary'
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

    this.loadDashboard();
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
              },
            )

        : this.api
            .get<ChartDatum[]>(
              `/dashboard/group/${kind}`,
              {
                month,
              },
            );


    request
      .pipe(
        finalize(
          () => {

            this.chartLoading[
              kind
            ] = false;
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