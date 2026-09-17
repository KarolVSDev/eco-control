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


interface UserRow {
  id: string;
  full_name: string;
  email: string;
  role: string;
  active: boolean;
}


@Component({
  templateUrl: './users.component.html',
})
export class UsersComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  rows: UserRow[] = [];

  showForm = false;
  loading = false;

  error = '';
  success = '';

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


  ngOnInit(): void {
    this.loadUsers();
  }


  loadUsers(): void {
    this.api
      .get<UserRow[]>('/users')
      .subscribe({
        next: (data) => {
          this.rows = data;
        },

        error: () => {
          this.error =
            'Não foi possível carregar os usuários.';
        },
      });
  }


  toggleForm(): void {
    this.showForm = !this.showForm;

    this.error = '';
    this.success = '';

    if (!this.showForm) {
      this.resetForm();
    }
  }


  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
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

        error: (err) => {
          this.loading = false;

          const detail =
            err.error?.detail;

          this.error =
            typeof detail === 'string'
              ? detail
              : 'Não foi possível criar o usuário.';
        },
      });
  }


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