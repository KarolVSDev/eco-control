import { Component, inject } from '@angular/core';
import {
  FormBuilder,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  error = '';
  loading = false;

  form = this.fb.nonNullable.group({
    email: [
      'admin@eco.com',
      [
        Validators.required,
        Validators.email,
      ],
    ],

    password: [
      'admin123',
      Validators.required,
    ],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.error = '';
    this.loading = true;

    const {
      email,
      password,
    } = this.form.getRawValue();

    this.auth
      .login(email, password)
      .subscribe({
        next: () => {
          this.loading = false;
          this.router.navigate(['/']);
        },

        error: (e) => {
          const detail = e.error?.detail;

          if (typeof detail === 'string') {
            this.error = detail;
          } else if (
            Array.isArray(detail) &&
            detail.length > 0
          ) {
            this.error =
              detail[0]?.msg ??
              'Dados inválidos';
          } else {
            this.error =
              'Falha ao realizar login';
          }

          this.loading = false;
        },
      });
  }
}