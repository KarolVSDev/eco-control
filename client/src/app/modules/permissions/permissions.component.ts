import {
  Component,
  OnInit,
  inject,
} from '@angular/core';

import {
  FormBuilder,
  Validators,
} from '@angular/forms';

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
  templateUrl: './permissions-redesigned.component.html',
  styleUrls: ['./permissions.component.css'],
})
export class PermissionsComponent
  implements OnInit {

  private readonly api =
    inject(ApiService);

  private readonly fb =
    inject(FormBuilder);


  users: User[] = [];

  selectedEmail = '';

  showCreateForm = false;
  creatingUser = false;

  createUserError = '';
  createUserSuccess = '';

  createUserForm =
    this.fb.nonNullable.group({
      full_name: [
        '',
        [
          Validators.required,
          Validators.minLength(2),
        ],
      ],
      email: [
        '',
        [
          Validators.required,
          Validators.email,
        ],
      ],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(6),
        ],
      ],
    });

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

  selectedGroupKey = '';

  fieldSearch = '';


  get selectedUser(): User | undefined {
    return this.users.find(
      user => user.email === this.selectedEmail
    );
  }


  get activeGroup(): PermissionGroup | undefined {
    return (
      this.permissionGroups.find(
        group =>
          group.key === this.selectedGroupKey
      )
      ?? this.permissionGroups[0]
    );
  }


  get filteredActiveFields(): FieldPermission[] {

    const fields =
      this.activeGroup?.fields ?? [];

    const search =
      this.fieldSearch
        .trim()
        .toLowerCase();


    if (!search) {
      return fields;
    }


    return fields.filter(
      field =>
        field.label
          .toLowerCase()
          .includes(search)
        ||
        field.field_key
          .toLowerCase()
          .includes(search)
    );
  }


  get totalFields(): number {
    return this.permissionGroups
      .reduce(
        (total, group) =>
          total + group.fields.length,
        0
      );
  }


  get totalViewableFields(): number {
    return this.permissionGroups
      .flatMap(
        group => group.fields
      )
      .filter(
        field => field.can_view
      )
      .length;
  }


  get totalEditableFields(): number {
    return this.permissionGroups
      .flatMap(
        group => group.fields
      )
      .filter(
        field => field.can_edit
      )
      .length;
  }


  ngOnInit(): void {

    this.selectedGroupKey =
      this.permissionGroups[0]?.key
      ?? '';

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


  toggleCreateForm(): void {
    this.showCreateForm =
      !this.showCreateForm;

    this.createUserError = '';
    this.createUserSuccess = '';

    if (!this.showCreateForm) {
      this.createUserForm.reset();
    }
  }


  createAnalyst(): void {
    if (this.createUserForm.invalid) {
      this.createUserForm
        .markAllAsTouched();
      return;
    }

    if (this.creatingUser) {
      return;
    }

    this.creatingUser = true;
    this.createUserError = '';
    this.createUserSuccess = '';

    this.api
      .post<User>(
        '/users',
        {
          ...this.createUserForm
            .getRawValue(),
          role: 'analyst',
          active: true,
        },
      )
      .subscribe({
        next: user => {
          this.users = [
            ...this.users,
            user,
          ];
          this.selectedEmail = user.email;
          this.showCreateForm = false;
          this.creatingUser = false;
          this.createUserForm.reset();
          this.createUserSuccess =
            'Analista cadastrado. Permissões padrão carregadas.';
          this.loadPermissions();
        },
        error: err => {
          this.creatingUser = false;

          const detail =
            err.error?.detail;

          this.createUserError =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível cadastrar o analista.';
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
        `/permissions/${encodeURIComponent(
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
          if (
            !this.permissionGroups.some(
              group =>
                group.key ===
                this.selectedGroupKey
            )
          ) {

            this.selectedGroupKey =
              this.permissionGroups[0]?.key
              ?? '';
          }


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
        `/permissions/${encodeURIComponent(
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

  selectGroup(
    groupKey: string,
  ): void {

    this.selectedGroupKey =
      groupKey;

    this.fieldSearch = '';
  }


  restoreDefaults(): void {

    const confirmed =
      confirm(
        'Restaurar as permissões padrão deste analista? As alterações só serão aplicadas após clicar em Salvar alterações.'
      );


    if (!confirmed) {
      return;
    }


    this.general = {
      can_create_eco: false,
      can_bulk_edit: false,
      can_view_history: true,
    };


    this.permissionGroups =
      this.buildPermissionGroups();


    this.selectedGroupKey =
      this.permissionGroups[0]?.key
      ?? '';


    this.fieldSearch = '';

    this.success = '';

    this.error = '';
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