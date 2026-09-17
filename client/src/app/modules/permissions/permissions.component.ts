import {
  Component,
  OnInit,
  inject,
} from '@angular/core';

import { ApiService } from '../../core/services/api.service';

import {
  COLUMN_GROUPS,
  EDITABLE_COLUMNS,
} from '../eco-control/eco-fields';


interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  active: boolean;
}


interface FieldPermission {
  field_key: string;
  label: string;
  can_view: boolean;
  can_edit: boolean;
}


interface PermissionGroup {
  key: string;
  label: string;
  fields: FieldPermission[];
}


@Component({
  templateUrl: './permissions.component.html',
})
export class PermissionsComponent
  implements OnInit {

  private readonly api =
    inject(ApiService);


  users: User[] = [];

  selectedEmail = '';

  loading = false;
  saving = false;

  error = '';
  success = '';


  general = {
    can_create_eco: false,
    can_bulk_edit: false,
    can_view_history: true,
  };


  permissionGroups:
    PermissionGroup[] =
    this.buildPermissionGroups();


  ngOnInit(): void {
    this.loadUsers();
  }


  private buildPermissionGroups(
    savedPermissions:
      Array<{
        field_key: string;
        can_view: boolean;
        can_edit: boolean;
      }> = [],
  ): PermissionGroup[] {

    const editableKeys =
      new Set(
        EDITABLE_COLUMNS.map(
          column => column.key
        )
      );


    const savedMap =
      new Map(
        savedPermissions.map(
          permission => [
            permission.field_key,
            permission,
          ]
        )
      );


    return COLUMN_GROUPS
      .map(group => {

        const fields =
          group.columns
            .filter(
              column =>
                editableKeys.has(
                  column.key
                )
            )
            .map(column => {

              const saved =
                savedMap.get(
                  column.key
                );

              return {
                field_key:
                  column.key,

                label:
                  column.label,

                can_view:
                  saved?.can_view
                  ?? true,

                can_edit:
                  saved?.can_edit
                  ?? false,
              };
            });


        return {
          key: group.key,
          label: group.label,
          fields,
        };
      })
      .filter(
        group =>
          group.fields.length > 0
      );
  }


  loadUsers(): void {
    this.error = '';

    this.api
      .get<User[]>('/users')
      .subscribe({
        next: users => {

          this.users =
            users.filter(
              user =>
                user.role ===
                  'analyst'
                &&
                user.active
            );


          if (
            this.users.length > 0
          ) {
            this.selectedEmail =
              this.users[0].email;

            this.loadPermissions();
          }
        },

        error: () => {
          this.error =
            'Não foi possível carregar os analistas.';
        },
      });
  }


  loadPermissions(): void {
    if (!this.selectedEmail) {
      return;
    }

    this.loading = true;

    this.error = '';
    this.success = '';


    this.api
      .get<any>(
        `/permissions/${
          encodeURIComponent(
            this.selectedEmail
          )
        }`
      )
      .subscribe({
        next: data => {

          this.general = {
            can_create_eco:
              data.general
                ?.can_create_eco
              ?? false,

            can_bulk_edit:
              data.general
                ?.can_bulk_edit
              ?? false,

            can_view_history:
              data.general
                ?.can_view_history
              ?? true,
          };


          this.permissionGroups =
            this.buildPermissionGroups(
              data.fields ?? []
            );


          this.loading = false;
        },

        error: error => {
          this.loading = false;

          this.error =
            error.error?.detail
            ||
            'Não foi possível carregar as permissões.';
        },
      });
  }


  onViewChange(
    field: FieldPermission,
  ): void {

    if (!field.can_view) {
      field.can_edit = false;
    }
  }


  onEditChange(
    field: FieldPermission,
  ): void {

    if (field.can_edit) {
      field.can_view = true;
    }
  }


  save(): void {
    if (!this.selectedEmail) {
      return;
    }

    this.saving = true;

    this.error = '';
    this.success = '';


    const fields =
      this.permissionGroups
        .flatMap(
          group =>
            group.fields
        )
        .map(
          field => ({
            field_key:
              field.field_key,

            can_view:
              field.can_view,

            can_edit:
              field.can_edit,
          })
        );


    const body = {
      general:
        this.general,

      fields,
    };


    this.api
      .put(
        `/permissions/${
          encodeURIComponent(
            this.selectedEmail
          )
        }`,
        body,
      )
      .subscribe({
        next: () => {

          this.saving = false;

          this.success =
            'Permissões salvas com sucesso.';
        },

        error: error => {

          this.saving = false;

          this.error =
            error.error?.detail
            ||
            'Não foi possível salvar as permissões.';
        },
      });
  }


  trackGroup(
    _index: number,
    group: PermissionGroup,
  ): string {
    return group.key;
  }


  trackField(
    _index: number,
    field: FieldPermission,
  ): string {
    return field.field_key;
  }
}