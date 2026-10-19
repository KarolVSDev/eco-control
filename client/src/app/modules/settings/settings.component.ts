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


type OwnerImportStatus =
  'NOVO'
  | 'DUPLICADO'
  | 'CONFLITO'
  | 'ERRO';


interface OwnerImportRow {
  excel_row: number;
  owner: string;
  group: string;
  status: OwnerImportStatus;
  message: string;
}


interface OwnerImportPreview {
  total_rows: number;
  new_rows: number;
  duplicate_rows: number;
  conflict_rows: number;
  error_rows: number;
  can_import: boolean;
  rows: OwnerImportRow[];
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


  ownerImportModalOpen = false;

  ownerImportFile: File | null = null;

  ownerImportPreview: OwnerImportPreview | null = null;

  previewingOwnerImport = false;

  importingOwners = false;

  ownerImportError = '';


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


  openOwnerImportModal(): void {

    this.clearMessages();

    this.ownerImportModalOpen = true;
    this.ownerImportFile = null;
    this.ownerImportPreview = null;
    this.ownerImportError = '';
  }


  closeOwnerImportModal(): void {

    if (
      this.previewingOwnerImport
      || this.importingOwners
    ) {
      return;
    }

    this.ownerImportModalOpen = false;
    this.ownerImportFile = null;
    this.ownerImportPreview = null;
    this.ownerImportError = '';
  }


  onOwnerImportFileSelected(event: Event): void {

    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    this.ownerImportFile = null;
    this.ownerImportPreview = null;
    this.ownerImportError = '';

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      this.ownerImportError =
        'Formato inválido. Envie um arquivo .xlsx.';
      input.value = '';
      return;
    }

    if (file.size === 0) {
      this.ownerImportError =
        'O arquivo enviado está vazio.';
      input.value = '';
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      this.ownerImportError =
        'O arquivo excede o limite máximo de 25 MB.';
      input.value = '';
      return;
    }

    this.ownerImportFile = file;
  }


  previewOwnerImport(): void {

    if (
      !this.ownerImportFile
      || this.previewingOwnerImport
      || this.importingOwners
    ) {
      return;
    }

    const formData = new FormData();
    formData.append('file', this.ownerImportFile);

    this.previewingOwnerImport = true;
    this.ownerImportError = '';

    this.api
      .post<OwnerImportPreview>(
        '/settings/owner-group/import/preview',
        formData,
      )
      .subscribe({
        next: response => {
          this.ownerImportPreview = response;
          this.previewingOwnerImport = false;
        },
        error: error => {
          this.ownerImportError = this.ownerImportErrorMessage(
            error,
            'Não foi possível analisar a planilha.',
          );
          this.previewingOwnerImport = false;
        },
      });
  }


  importOwnerGroups(): void {

    if (
      !this.ownerImportFile
      || !this.ownerImportPreview?.can_import
      || this.previewingOwnerImport
      || this.importingOwners
    ) {
      return;
    }

    const formData = new FormData();
    formData.append('file', this.ownerImportFile);

    this.importingOwners = true;
    this.ownerImportError = '';

    this.api
      .post<{
        imported_rows: number;
        duplicate_rows: number;
      }>(
        '/settings/owner-group/import',
        formData,
      )
      .subscribe({
        next: response => {
          const imported = response.imported_rows;
          const duplicates = response.duplicate_rows;

          if (imported === 0) {
            this.success =
              'Nenhum Owner novo foi encontrado.';
          } else {
            const duplicateMessage = duplicates === 1
              ? '1 duplicado foi ignorado.'
              : `${duplicates} duplicados foram ignorados.`;
            const importedMessage = imported === 1
              ? 'Owner importado com sucesso.'
              : 'Owners importados com sucesso.';

            this.success =
              `${imported} ${importedMessage}`
              + (duplicates > 0 ? ` ${duplicateMessage}` : '');
          }

          this.importingOwners = false;
          this.closeOwnerImportModal();
          this.load();
        },
        error: error => {
          this.ownerImportError = this.ownerImportErrorMessage(
            error,
            'Não foi possível importar os Owners.',
          );
          this.importingOwners = false;
        },
      });
  }


  private ownerImportErrorMessage(
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

//   exportSettings(): void {

//     const lines: string[] = [];


//     lines.push(
//       'OBU;AU'
//     );


//     for (
//       const item
//       of this.data.obu_au
//     ) {

//       lines.push(
//         `${item.obu};${item.au}`
//       );
//     }


//     lines.push(
//       ''
//     );

//     lines.push(
//       'OWNER;GROUP'
//     );


//     for (
//       const item
//       of this.data.owner_group
//     ) {

//       lines.push(
//         `${item.owner};${item.group}`
//       );
//     }


//     lines.push(
//       ''
//     );

//     lines.push(
//       'MANAGER'
//     );


//     for (
//       const manager
//       of this.data.managers
//     ) {

//       lines.push(
//         manager.name
//       );
//     }


//     const csv =
//       lines.join(
//         '\r\n'
//       );


//     const blob =
//       new Blob(
//         [
//           '\uFEFF',
//           csv,
//         ],
//         {
//           type:
//             'text/csv;charset=utf-8;',
//         },
//       );


//     const url =
//       URL.createObjectURL(
//         blob
//       );


//     const link =
//       document.createElement(
//         'a'
//       );


//     link.href =
//       url;


//     link.download =
//       'eco-control-configuracoes.csv';


//     document.body
//       .appendChild(
//         link
//       );


//     link.click();


//     document.body
//       .removeChild(
//         link
//       );


//     URL.revokeObjectURL(
//       url
//     );
//   }
}
