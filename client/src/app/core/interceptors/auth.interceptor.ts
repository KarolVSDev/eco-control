import {
  Injectable,
} from '@angular/core';

import {
  HttpErrorResponse,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';

import {
  Router,
} from '@angular/router';

import {
  catchError,
  throwError,
} from 'rxjs';

import {
  AuthService,
} from '../services/auth.service';


@Injectable()
export class AuthInterceptor
  implements HttpInterceptor {

  constructor(
    private auth: AuthService,
    private router: Router,
  ) {}


  intercept(
    req: HttpRequest<any>,
    next: HttpHandler,
  ) {

    const token =
      this.auth.token;


    const request = token
      ? req.clone({
          setHeaders: {
            Authorization:
              `Bearer ${token}`,
          },
        })
      : req;


    return next
      .handle(request)
      .pipe(
        catchError(
          (
            error:
              HttpErrorResponse,
          ) => {

            if (
              error.status === 401
            ) {

              this.auth.logout();

              this.router.navigate([
                '/login',
              ]);
            }


            return throwError(
              () => error
            );
          },
        ),
      );
  }
}