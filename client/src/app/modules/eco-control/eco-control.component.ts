import {
  Component,
  OnInit,
  inject,
} from '@angular/core';

import {
  FormControl,
  FormGroup,
} from '@angular/forms';

import { ApiService } from '../../core/services/api.service';

import {
  EcoPermissionService,
} from '../../core/services/eco-permission.service';

import {
  COLUMN_GROUPS,
  EDITABLE_COLUMNS,
  EcoColumn,
  EcoColumnGroup,
  FIELD_TYPES,
  STATUS_OPTIONS,
  isCalculatedField,
} from './eco-fields';


interface EditableGroup
  extends Omit<EcoColumnGroup, 'columns'> {
  columns: readonly EcoColumn[];
}


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


  /*
   * Essas listas não podem mais ser readonly
   * como valor fixo, porque serão filtradas
   * pelas permissões do usuário.
   */
  columnGroups:
    readonly EcoColumnGroup[] = [];

  columns:
    readonly EcoColumn[] = [];

  editableGroups:
    readonly EditableGroup[] = [];


  rows: any[] = [];

  total = 0;

  page = 1;
  pageSize = 25;

  search = '';
  status = '';

  editing: any = undefined;

  saving = false;
  saveError = '';


  readonly statuses = [
    '',
    ...STATUS_OPTIONS,
  ];


  form = this.createForm();


  /*
   * Primeiro carregamos as permissões.
   * Só depois montamos a tabela e carregamos
   * as ECOs.
   */
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

          /*
           * Em caso de erro:
           * - campos ficam visíveis por padrão;
           * - edição continua restrita.
           */
          this.applyPermissions();
          this.load();
        },
      });
  }


  /*
   * Cria controles para todos os campos
   * editáveis existentes no ECO Control.
   */
  private createForm(): FormGroup {
    const controls:
      Record<
        string,
        FormControl<string | null>
      > = {};


    for (
      const column
      of EDITABLE_COLUMNS
    ) {
      controls[column.key] =
        new FormControl<string | null>(
          null
        );
    }


    return new FormGroup(
      controls
    );
  }


  /*
   * Aplica permissões de visualização e edição.
   */
  private applyPermissions(): void {

    /*
     * COLUNAS DA TABELA
     *
     * Campos sem permissão de visualizar
     * simplesmente deixam de fazer parte
     * da tabela.
     */
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


    /*
     * CAMPOS DO FORMULÁRIO
     *
     * Calculados continuam fora.
     * Campos sem can_view também ficam fora.
     */
    this.editableGroups =
      COLUMN_GROUPS
        .map(group => ({
          ...group,

          columns:
            group.columns.filter(
              column =>
                !isCalculatedField(
                  column
                )
                &&
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


    /*
     * EDITABILIDADE
     *
     * O campo pode aparecer no formulário,
     * mas fica desabilitado se o analista
     * possuir apenas permissão de leitura.
     */
    for (
      const column
      of EDITABLE_COLUMNS
    ) {
      const control =
        this.form.get(
          column.key
        );


      if (!control) {
        continue;
      }


      if (
        this.permissions
          .canEdit(
            column.key
          )
      ) {
        control.enable({
          emitEvent: false,
        });

      } else {
        control.disable({
          emitEvent: false,
        });
      }
    }
  }


  private resetForm(): void {
    this.form.reset();


    this.form.patchValue({
      item_type: 'MEC',
      eco_type: 'REGULAR',
      status: 'WORKING',
    });


    this.saveError = '';
  }


  load(): void {
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
        },
      )
      .subscribe({
        next: response => {
          this.rows =
            response.items;

          this.total =
            response.total;
        },

        error: error => {
          console.error(
            'Erro ao carregar ECOs:',
            error,
          );
        },
      });
  }


  searchEcos(): void {
    this.page = 1;
    this.load();
  }


  changeStatus(): void {
    this.page = 1;
    this.load();
  }


  /*
   * Abre criação ou edição.
   */
  open(
    row: any = null,
  ): void {

    /*
     * Se estiver tentando criar uma ECO
     * e não tiver permissão, não abre.
     */
    if (
      !row &&
      !this.permissions
        .canCreateEco
    ) {
      return;
    }


    this.resetForm();


    /*
     * EDIÇÃO
     */
    if (row) {
      this.editing = row;


      const values:
        Record<
          string,
          string | null
        > = {};


      for (
        const column
        of EDITABLE_COLUMNS
      ) {
        const value =
          row[column.key];


        values[column.key] =
          value === undefined ||
          value === null
            ? null
            : String(value);
      }


      this.form.patchValue(
        values
      );


      return;
    }


    /*
     * NOVA ECO
     */
    this.editing = {};
  }


  closeModal(): void {
    this.editing =
      undefined;

    this.resetForm();
  }


  save(): void {
    if (this.saving) {
      return;
    }


    this.saving = true;
    this.saveError = '';


    const raw =
      this.form.getRawValue();


    const body:
      Record<
        string,
        unknown
      > = {};


    /*
     * Não enviamos campos desabilitados.
     *
     * Isso evita que um campo somente leitura
     * seja enviado de volta ao backend.
     */
    for (
      const column
      of EDITABLE_COLUMNS
    ) {
      const control =
        this.form.get(
          column.key
        );


      if (
        !control ||
        control.disabled
      ) {
        continue;
      }


      const value =
        raw[column.key];


      body[column.key] =
        value === ''
          ? null
          : value;
    }


    const request =
      this.editing?.id

        ? this.api.patch(
            `/ecos/${this.editing.id}`,
            body,
          )

        : this.api.post(
            '/ecos',
            body,
          );


    request.subscribe({
      next: () => {
        this.saving = false;

        this.closeModal();

        this.load();
      },


      error: error => {
        this.saving = false;


        const detail =
          error.error?.detail;


        if (
          typeof detail ===
          'string'
        ) {
          this.saveError =
            detail;

        } else {
          this.saveError =
            'Não foi possível salvar a ECO.';
        }


        console.error(
          'Erro ao salvar ECO:',
          error,
        );
      },
    });
  }


  remove(row: any): void {

    /*
     * Camada extra no Angular.
     * O botão também ficará oculto no HTML.
     */
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
          this.load();
        },

        error: error => {
          console.error(
            'Erro ao excluir ECO:',
            error,
          );
        },
      });
  }


  previousPage(): void {
    if (
      this.page <= 1
    ) {
      return;
    }


    this.page--;

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


  /*
   * Indica se o usuário possui permissão
   * para editar pelo menos um campo.
   *
   * Usaremos isso para mostrar/esconder
   * o botão Editar.
   */
  get canEditAny(): boolean {

    if (
      this.permissions
        .isAdmin
    ) {
      return true;
    }


    return EDITABLE_COLUMNS
      .some(
        column =>
          this.permissions
            .canEdit(
              column.key
            )
      );
  }


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


    return String(value);
  }


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
    group:
      EditableGroup |
      EcoColumnGroup,
  ): string {

    return group.key;
  }
}