import {
  Component,
  OnInit,
} from '@angular/core';

import {
  ApiService,
} from '../../core/services/api.service';


interface ObuAuMapping {
  id: string;
  obu: string;
  au: string;
}


interface OwnerGroupMapping {
  id: string;
  owner: string;
  group: string;
}


interface Manager {
  id: string;
  name: string;
}


@Component({
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
})
export class SettingsComponent
  implements OnInit {

  data = {
    obu_au: [] as ObuAuMapping[],
    owner_group: [] as OwnerGroupMapping[],
    managers: [] as Manager[],
  };


  loading = false;

  error = '';

  success = '';


  // =====================================================
  // OBU → AU
  // =====================================================

  obuOptions = [
    'NW1',
    'NWD',
    'NW9',
    'NWW',
    'NW4',
    'NW5',
    'NWU',
    'NWX',
    'NWH',
    'NYE',
    'NWV',
    'NWK',
    'NWE',
    'NWZ',
  ];


  auOptions = [
    'GLZ',
    'GMZ',
    'LMZ',
    'PNZ',
    'PGZ',
  ];


  newObu = '';

  newAu = '';


  editingObuAu:
    ObuAuMapping | null = null;


  editObu = '';

  editAu = '';


  // =====================================================
  // OWNER → GROUP
  // =====================================================

  groupOptions = [
    'BOM',
    'DEV',
    'HW',
    'MEC',
  ];


  newOwner = '';

  newGroup = 'BOM';


  // =====================================================
  // MANAGER
  // =====================================================

  newManager = '';


  constructor(
    private api: ApiService,
  ) {}


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    this.load();
  }


  // =====================================================
  // LOAD
  // =====================================================

  load(): void {

    this.loading = true;

    this.error = '';


    this.api
      .get<any>(
        '/settings'
      )
      .subscribe({

        next: response => {

          this.data = response;

          this.loading = false;
        },


        error: error => {

          console.error(
            'Erro ao carregar configurações:',
            error,
          );


          this.error =
            'Não foi possível carregar as configurações.';


          this.loading = false;
        },
      });
  }


  // =====================================================
  // MENSAGENS
  // =====================================================

  private clearMessages(): void {

    this.error = '';

    this.success = '';
  }


  private apiError(
    error: any,
    fallback: string,
  ): void {

    const detail =
      error?.error?.detail;


    this.error =
      typeof detail === 'string'
        ? detail
        : fallback;
  }


  // =====================================================
  // OBU → AU - CRIAR
  // =====================================================

  addObuAu(): void {

    this.clearMessages();


    if (
      !this.newObu
      ||
      !this.newAu
    ) {

      this.error =
        'Selecione um OBU e um AU.';

      return;
    }


    this.api
      .post<ObuAuMapping>(
        '/settings/obu-au',
        {
          obu:
            this.newObu,

          au:
            this.newAu,
        },
      )
      .subscribe({

        next: () => {

          this.success =
            'Relação OBU → AU adicionada com sucesso.';


          this.newObu = '';

          this.newAu = '';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível adicionar a relação OBU → AU.',
          );
        },
      });
  }


  // =====================================================
  // OBU → AU - EDITAR
  // =====================================================

  startEditObuAu(
    item: ObuAuMapping,
  ): void {

    this.clearMessages();


    this.editingObuAu =
      item;


    this.editObu =
      item.obu;


    this.editAu =
      item.au;
  }


  cancelEditObuAu(): void {

    this.editingObuAu =
      null;


    this.editObu = '';

    this.editAu = '';
  }


  saveObuAu(): void {

    if (
      !this.editingObuAu
    ) {

      return;
    }


    if (
      !this.editObu
      ||
      !this.editAu
    ) {

      this.error =
        'Selecione um OBU e um AU.';

      return;
    }


    const id =
      this.editingObuAu.id;


    this.clearMessages();


    this.api
      .put<ObuAuMapping>(
        `/settings/obu-au/${id}`,
        {
          obu:
            this.editObu,

          au:
            this.editAu,
        },
      )
      .subscribe({

        next: () => {

          this.success =
            'Relação OBU → AU atualizada com sucesso.';


          this.cancelEditObuAu();

          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível atualizar a relação OBU → AU.',
          );
        },
      });
  }


  // =====================================================
  // OBU → AU - EXCLUIR
  // =====================================================

  deleteObuAu(
    item: ObuAuMapping,
  ): void {

    const confirmed =
      confirm(
        `Excluir a relação ${item.obu} → ${item.au}?`
      );


    if (
      !confirmed
    ) {

      return;
    }


    this.clearMessages();


    this.api
      .delete(
        `/settings/obu-au/${item.id}`
      )
      .subscribe({

        next: () => {

          this.success =
            'Relação OBU → AU excluída.';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível excluir a relação OBU → AU.',
          );
        },
      });
  }


  // =====================================================
  // OWNER → GROUP - CRIAR
  // =====================================================

  addOwnerGroup(): void {

    this.clearMessages();


    const owner =
      this.newOwner.trim();


    if (
      !owner
      ||
      !this.newGroup
    ) {

      this.error =
        'Informe o owner e selecione o grupo.';

      return;
    }


    this.api
      .post<OwnerGroupMapping>(
        '/settings/owner-group',
        {
          owner:
            owner,

          group:
            this.newGroup,
        },
      )
      .subscribe({

        next: () => {

          this.success =
            'Relação Owner → Group adicionada com sucesso.';


          this.newOwner = '';

          this.newGroup = 'BOM';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível adicionar a relação Owner → Group.',
          );
        },
      });
  }


  // =====================================================
  // OWNER → GROUP - EXCLUIR
  // =====================================================

  deleteOwnerGroup(
    item: OwnerGroupMapping,
  ): void {

    const confirmed =
      confirm(
        `Excluir a relação ${item.owner} → ${item.group}?`
      );


    if (
      !confirmed
    ) {

      return;
    }


    this.clearMessages();


    this.api
      .delete(
        `/settings/owner-group/${item.id}`
      )
      .subscribe({

        next: () => {

          this.success =
            'Relação Owner → Group excluída.';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível excluir a relação Owner → Group.',
          );
        },
      });
  }


  // =====================================================
  // MANAGER - CRIAR
  // =====================================================

  addManager(): void {

    this.clearMessages();


    const name =
      this.newManager.trim();


    if (
      !name
    ) {

      this.error =
        'Informe o nome do gerente.';

      return;
    }


    this.api
      .post<Manager>(
        '/settings/managers',
        {
          name:
            name,
        },
      )
      .subscribe({

        next: () => {

          this.success =
            'Gerente adicionado com sucesso.';


          this.newManager = '';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível adicionar o gerente.',
          );
        },
      });
  }


  // =====================================================
  // MANAGER - EXCLUIR
  // =====================================================

  deleteManager(
    manager: Manager,
  ): void {

    const confirmed =
      confirm(
        `Excluir o gerente ${manager.name}?`
      );


    if (
      !confirmed
    ) {

      return;
    }


    this.clearMessages();


    this.api
      .delete(
        `/settings/managers/${manager.id}`
      )
      .subscribe({

        next: () => {

          this.success =
            'Gerente excluído.';


          this.load();
        },


        error: error => {

          this.apiError(
            error,
            'Não foi possível excluir o gerente.',
          );
        },
      });
  }


  // =====================================================
  // EXPORTAR CONFIGURAÇÕES
  // =====================================================

  exportSettings(): void {

    const lines: string[] = [];


    lines.push(
      'OBU;AU'
    );


    for (
      const item
      of this.data.obu_au
    ) {

      lines.push(
        `${item.obu};${item.au}`
      );
    }


    lines.push(
      ''
    );

    lines.push(
      'OWNER;GROUP'
    );


    for (
      const item
      of this.data.owner_group
    ) {

      lines.push(
        `${item.owner};${item.group}`
      );
    }


    lines.push(
      ''
    );

    lines.push(
      'MANAGER'
    );


    for (
      const manager
      of this.data.managers
    ) {

      lines.push(
        manager.name
      );
    }


    const csv =
      lines.join(
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
      'eco-control-configuracoes.csv';


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
  }
}