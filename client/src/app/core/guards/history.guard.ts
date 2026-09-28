import { inject } from '@angular/core';
import {
  CanActivateFn,
  Router,
} from '@angular/router';

import {
  catchError,
  map,
  of,
} from 'rxjs';

import {
  EcoPermissionService,
} from '../services/eco-permission.service';


export const historyGuard: CanActivateFn = () => {

  const permissions =
    inject(EcoPermissionService);

  const router =
    inject(Router);


  return permissions
    .load()
    .pipe(
      map(() => {

        if (
          permissions.canViewHistory
        ) {
          return true;
        }

        return router
          .createUrlTree(['/']);
      }),

      catchError(() => {
        return of(
          router.createUrlTree(['/'])
        );
      }),
    );
};