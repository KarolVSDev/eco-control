import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { SharedModule } from '../../shared/shared.module';
import { PermissionsComponent } from './permissions.component';

@NgModule({
  declarations: [
    PermissionsComponent,
  ],
  imports: [
    SharedModule,
    FormsModule,
    RouterModule.forChild([
      {
        path: '',
        component: PermissionsComponent,
      },
    ]),
  ],
})
export class PermissionsModule {}