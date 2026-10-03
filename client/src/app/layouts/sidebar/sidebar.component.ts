import {
  Component,
  OnInit,
} from '@angular/core';

import {
  Router,
} from '@angular/router';

import {
  AuthService,
} from '../../core/services/auth.service';

import {
  EcoPermissionService,
} from '../../core/services/eco-permission.service';


interface NavLink {
  to: string;
  icon: string;
  label: string;

  adminOnly?: boolean;
  historyOnly?: boolean;
}


@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css'],
})
export class SidebarComponent
  implements OnInit {

  links: NavLink[] = [
    {
      to: '/',
      icon: '▦',
      label: 'Dashboard',
    },
    {
      to: '/eco-control',
      icon: '▤',
      label: 'ECO Control',
    },
    {
      to: '/relatorios',
      icon: '▥',
      label: 'Relatórios',
      historyOnly: true,
    },
    {
      to: '/usuarios',
      icon: '♙',
      label: 'Usuários',
      adminOnly: true,
    },
    {
      to: '/permissoes',
      icon: '♢',
      label: 'Permissões',
      adminOnly: true,
    },
    {
      to: '/configuracoes',
      icon: '⚙',
      label: 'Configurações',
      adminOnly: true,
    },
  ];


  constructor(
    public auth: AuthService,
    public permissions: EcoPermissionService,
    private router: Router,
  ) {}


  ngOnInit(): void {
    this.permissions
      .load()
      .subscribe({
        error: error => {
          console.error(
            'Erro ao carregar permissões do menu:',
            error,
          );
        },
      });
  }


  canShow(
    link: NavLink,
  ): boolean {

    if (
      link.adminOnly
    ) {
      return this.auth.isAdmin;
    }


    if (
      link.historyOnly
    ) {
      return (
        this.auth.isAdmin ||
        (
          this.permissions.loaded &&
          this.permissions.canViewHistory
        )
      );
    }


    return true;
  }


  logout(): void {
    this.auth.logout();

    this.router.navigate([
      '/login',
    ]);
  }
}