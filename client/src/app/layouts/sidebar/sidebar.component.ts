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
  route: string;
  icon: NavIcon;
  label: string;

  adminOnly?: boolean;
  historyOnly?: boolean;
}

interface MenuSection {
  title: string;
  items: NavLink[];
}

type NavIcon =
  | 'layout-dashboard'
  | 'file-text'
  | 'history'
  | 'users'
  | 'shield'
  | 'settings';


@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css'],
})
export class SidebarComponent
  implements OnInit {

  menuSections: MenuSection[] = [
    {
      title: 'VISÃO GERAL',
      items: [
        {
          label: 'Dashboard',
          icon: 'layout-dashboard',
          route: '/dashboard',
        },
      ],
    },
    {
      title: 'GESTÃO',
      items: [
        {
          label: 'ECO Control',
          icon: 'file-text',
          route: '/eco-control',
        },
        {
          label: 'Histórico',
          icon: 'history',
          route: '/historico-alteracoes',
          historyOnly: true,
        },
      ],
    },
    {
      title: 'ADMINISTRAÇÃO',
      items: [
        {
          label: 'Usuários',
          icon: 'users',
          route: '/usuarios',
          adminOnly: true,
        },
        {
          label: 'Permissões',
          icon: 'shield',
          route: '/permissoes',
          adminOnly: true,
        },
        {
          label: 'Configurações',
          icon: 'settings',
          route: '/configuracoes',
          adminOnly: true,
        },
      ],
    },
  ];

  private readonly iconSymbols: Record<NavIcon, string> = {
    'layout-dashboard': '▦',
    'file-text': '▤',
    history: '↺',
    users: '♙',
    shield: '♢',
    settings: '⚙',
  };


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


  canShowSection(
    section: MenuSection,
  ): boolean {
    return section.items.some(
      item => this.canShow(
        item,
      ),
    );
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


  iconSymbol(
    icon: NavIcon,
  ): string {
    return this.iconSymbols[icon];
  }


  logout(): void {
    this.auth.logout();

    this.router.navigate([
      '/login',
    ]);
  }
}
