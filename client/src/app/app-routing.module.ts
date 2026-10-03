import { NgModule } from '@angular/core';
import {
  RouterModule,
  Routes,
} from '@angular/router';

import {
  MainLayoutComponent,
} from './layouts/main-layout/main-layout.component';

import {
  authGuard,
} from './core/guards/auth.guard';

import {
  adminGuard,
} from './core/guards/admin.guard';

import {
  historyGuard,
} from './core/guards/history.guard';


const routes: Routes = [

  // =========================
  // LOGIN
  // =========================
  {
    path: 'login',
    loadChildren: () =>
      import('./modules/auth/auth.module')
        .then(m => m.AuthModule),
  },

  // =========================
  // ÁREA AUTENTICADA
  // =========================
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],

    children: [

      // Dashboard
      {
        path: '',
        loadChildren: () =>
          import(
            './modules/dashboard/dashboard.module'
          ).then(
            m => m.DashboardModule
          ),
      },

      // ECO Control
      {
        path: 'eco-control',
        loadChildren: () =>
          import(
            './modules/eco-control/eco-control.module'
          ).then(
            m => m.EcoControlModule
          ),
      },

      // Relatórios / Histórico
      // Só acessa quem possuir
      // can_view_history
      {
        path: 'relatorios',
        canActivate: [historyGuard],
        loadChildren: () =>
          import(
            './modules/reports/reports.module'
          ).then(
            m => m.ReportsModule
          ),
      },

      // =========================
      // SOMENTE ADMIN
      // =========================

      {
        path: 'usuarios',
        canActivate: [adminGuard],
        loadChildren: () =>
          import(
            './modules/users/users.module'
          ).then(
            m => m.UsersModule
          ),
      },

      {
        path: 'permissoes',
        canActivate: [adminGuard],
        loadChildren: () =>
          import(
            './modules/permissions/permissions.module'
          ).then(
            m => m.PermissionsModule
          ),
      },

      {
        path: 'configuracoes',
        canActivate: [adminGuard],
        loadChildren: () =>
          import(
            './modules/settings/settings.module'
          ).then(
            m => m.SettingsModule
          ),
      },
    ],
  },

  // =========================
  // ROTA NÃO ENCONTRADA
  // =========================
  {
    path: '**',
    redirectTo: '',
  },
];


@NgModule({
  imports: [
    RouterModule.forRoot(
      routes
    ),
  ],

  exports: [
    RouterModule,
  ],
})
export class AppRoutingModule {}