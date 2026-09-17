import {
  Injectable,
  inject,
} from '@angular/core';

import {
  tap,
} from 'rxjs';

import { ApiService } from './api.service';
import { AuthService } from './auth.service';


interface FieldPermission {
  field_key: string;
  can_view: boolean;
  can_edit: boolean;
}


interface GeneralPermissions {
  can_create_eco: boolean;
  can_bulk_edit: boolean;
  can_view_history: boolean;
}


interface PermissionResponse {
  role: string;

  general: GeneralPermissions;

  fields: FieldPermission[];
}


@Injectable({
  providedIn: 'root',
})
export class EcoPermissionService {

  private readonly api =
    inject(ApiService);

  private readonly auth =
    inject(AuthService);


  private fieldPermissions =
    new Map<
      string,
      FieldPermission
    >();


  private generalPermissions:
    GeneralPermissions = {
      can_create_eco: false,
      can_bulk_edit: false,
      can_view_history: true,
    };


  loaded = false;


  load() {
    return this.api
      .get<PermissionResponse>(
        '/auth/permissions'
      )
      .pipe(
        tap(response => {

          this.generalPermissions =
            response.general;


          this.fieldPermissions =
            new Map(
              response.fields.map(
                permission => [
                  permission.field_key,
                  permission,
                ]
              )
            );


          this.loaded = true;
        })
      );
  }


  get isAdmin(): boolean {
    return this.auth.isAdmin;
  }


  canView(
    fieldKey: string,
  ): boolean {

    if (this.isAdmin) {
      return true;
    }

    const permission =
      this.fieldPermissions.get(
        fieldKey
      );


    // Mesmo comportamento do Base44:
    // sem configuração explícita,
    // visualizar fica permitido.
    return permission
      ? permission.can_view !== false
      : true;
  }


  canEdit(
    fieldKey: string,
  ): boolean {

    if (this.isAdmin) {
      return true;
    }

    const permission =
      this.fieldPermissions.get(
        fieldKey
      );

    return !!(
      permission &&
      permission.can_edit
    );
  }


  get canCreateEco(): boolean {
    return (
      this.isAdmin ||
      this.generalPermissions
        .can_create_eco
    );
  }


  get canBulkEdit(): boolean {
    return (
      this.isAdmin ||
      this.generalPermissions
        .can_bulk_edit
    );
  }


  get canViewHistory(): boolean {
    return (
      this.isAdmin ||
      this.generalPermissions
        .can_view_history !== false
    );
  }
}