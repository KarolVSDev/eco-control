import {
  Component,
  OnInit,
  inject,
} from '@angular/core';

import {
  FormBuilder,
  Validators,
} from '@angular/forms';

import {
  ApiService,
} from '../../core/services/api.service';

import {
  AuthService,
} from '../../core/services/auth.service';


interface UserRow {
  id: string;
  full_name: string;
  email: string;
  role: string;
  active: boolean;
}


@Component({
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent
  implements OnInit {

  private readonly api =
    inject(ApiService);

  private readonly fb =
    inject(FormBuilder);

  readonly auth =
    inject(AuthService);


  // =====================================================
  // DADOS
  // =====================================================

  rows: UserRow[] = [];


  // =====================================================
  // ESTADOS
  // =====================================================

  showForm = false;

  loading = false;

  resettingPassword = false;

  deletingUserId:
    string | null = null;


  error = '';

  success = '';


  // =====================================================
  // USUÁRIO SELECIONADO PARA REDEFINIR SENHA
  // =====================================================

  passwordUser:
    UserRow | null = null;


  // =====================================================
  // FORMULÁRIO DE NOVO USUÁRIO
  // =====================================================

  form = this.fb.nonNullable.group({

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

    role: [
      'analyst',
      Validators.required,
    ],

    active: [
      true,
    ],
  });


  // =====================================================
  // FORMULÁRIO DE REDEFINIÇÃO DE SENHA
  // =====================================================

  passwordForm =
    this.fb.nonNullable.group({

      new_password: [
        '',
        [
          Validators.required,
          Validators.minLength(6),
        ],
      ],

      confirm_password: [
        '',
        [
          Validators.required,
          Validators.minLength(6),
        ],
      ],
    });


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    this.loadUsers();
  }


  // =====================================================
  // CARREGAR USUÁRIOS
  // =====================================================

  loadUsers(): void {

    this.error = '';


    this.api
      .get<UserRow[]>(
        '/users'
      )
      .subscribe({

        next: data => {

          this.rows =
            data;
        },


        error: error => {

          console.error(
            'Erro ao carregar usuários:',
            error,
          );


          this.error =
            'Não foi possível carregar os usuários.';
        },
      });
  }


  // =====================================================
  // ABRIR / FECHAR FORMULÁRIO DE NOVO USUÁRIO
  // =====================================================

  toggleForm(): void {

    this.showForm =
      !this.showForm;


    this.error = '';

    this.success = '';


    if (
      !this.showForm
    ) {

      this.resetForm();
    }
  }


  // =====================================================
  // CRIAR USUÁRIO
  // =====================================================

  submit(): void {

    if (
      this.form.invalid
    ) {

      this.form
        .markAllAsTouched();

      return;
    }


    if (
      this.loading
    ) {

      return;
    }


    this.loading = true;

    this.error = '';

    this.success = '';


    this.api
      .post<UserRow>(
        '/users',
        this.form.getRawValue(),
      )
      .subscribe({

        next: () => {

          this.success =
            'Usuário criado com sucesso.';


          this.loading = false;

          this.showForm = false;


          this.resetForm();

          this.loadUsers();
        },


        error: err => {

          this.loading = false;


          const detail =
            err.error?.detail;


          this.error =
            typeof detail ===
              'string'

              ? detail

              : 'Não foi possível criar o usuário.';
        },
      });
  }


  // =====================================================
  // ABRIR MODAL DE REDEFINIÇÃO DE SENHA
  // =====================================================

  openPasswordReset(
    user: UserRow,
  ): void {

    this.passwordUser =
      user;


    this.passwordForm.reset({
      new_password: '',
      confirm_password: '',
    });


    this.error = '';

    this.success = '';
  }


  // =====================================================
  // FECHAR MODAL DE REDEFINIÇÃO DE SENHA
  // =====================================================

  closePasswordReset(): void {

    if (
      this.resettingPassword
    ) {

      return;
    }


    this.passwordUser =
      null;


    this.passwordForm.reset({
      new_password: '',
      confirm_password: '',
    });
  }


  // =====================================================
  // REDEFINIR SENHA PELO ADMIN
  // =====================================================

  resetPassword(): void {

    if (
      !this.passwordUser
    ) {

      return;
    }


    if (
      this.passwordForm.invalid
    ) {

      this.passwordForm
        .markAllAsTouched();

      return;
    }


    const {
      new_password,
      confirm_password,
    } =
      this.passwordForm
        .getRawValue();


    // -----------------------------------------------------
    // CONFIRMAÇÃO DA SENHA
    // -----------------------------------------------------

    if (
      new_password !==
      confirm_password
    ) {

      this.error =
        'As senhas informadas não coincidem.';

      return;
    }


    if (
      this.resettingPassword
    ) {

      return;
    }


    const user =
      this.passwordUser;


    this.resettingPassword =
      true;

    this.error = '';

    this.success = '';


    this.api
      .patch<{
        message: string;
      }>(
        `/users/${user.id}/password`,
        {
          new_password:
            new_password,
        },
      )
      .subscribe({

        next: response => {

          this.resettingPassword =
            false;


          this.passwordUser =
            null;


          this.passwordForm.reset({
            new_password: '',
            confirm_password: '',
          });


          this.success =
            response.message
            ||
            `Senha de ${user.full_name} redefinida com sucesso.`;
        },


        error: err => {

          this.resettingPassword =
            false;


          const detail =
            err.error?.detail;


          this.error =
            typeof detail ===
              'string'

              ? detail

              : 'Não foi possível redefinir a senha.';
        },
      });
  }


  // =====================================================
  // VERIFICAR SE É O USUÁRIO LOGADO
  // =====================================================

  isCurrentUser(
    user: UserRow,
  ): boolean {

    return (
      this.auth.user?.id
      === user.id
    );
  }


  // =====================================================
  // EXCLUIR USUÁRIO
  // =====================================================

  deleteUser(
    user: UserRow,
  ): void {

    // Segurança adicional no frontend.
    // O backend também bloqueia autoexclusão.

    if (
      this.isCurrentUser(
        user
      )
    ) {

      this.error =
        'Você não pode excluir a própria conta.';

      return;
    }


    if (
      this.deletingUserId
    ) {

      return;
    }


    const confirmed =
      confirm(
        `Deseja realmente excluir o usuário "${user.full_name}"?\n\nEsta ação não poderá ser desfeita.`
      );


    if (
      !confirmed
    ) {

      return;
    }


    this.deletingUserId =
      user.id;

    this.error = '';

    this.success = '';


    this.api
      .delete(
        `/users/${user.id}`
      )
      .subscribe({

        next: () => {

          this.deletingUserId =
            null;


          this.success =
            `Usuário ${user.full_name} excluído com sucesso.`;


          this.loadUsers();
        },


        error: err => {

          this.deletingUserId =
            null;


          const detail =
            err.error?.detail;


          this.error =
            typeof detail ===
              'string'

              ? detail

              : 'Não foi possível excluir o usuário.';
        },
      });
  }


  // =====================================================
  // VERIFICAR SE USUÁRIO ESTÁ SENDO EXCLUÍDO
  // =====================================================

  isDeleting(
    user: UserRow,
  ): boolean {

    return (
      this.deletingUserId
      === user.id
    );
  }


  // =====================================================
  // RESET DO FORMULÁRIO DE CRIAÇÃO
  // =====================================================

  private resetForm(): void {

    this.form.reset({

      full_name: '',

      email: '',

      password: '',

      role: 'analyst',

      active: true,
    });
  }
}