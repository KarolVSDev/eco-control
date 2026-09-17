import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpParams,
} from '@angular/common/http';

import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  constructor(
    private http: HttpClient,
  ) {}

  get<T>(
    path: string,
    params: Record<
      string,
      string | number | undefined
    > = {},
  ) {
    let httpParams = new HttpParams();

    Object.entries(params).forEach(
      ([key, value]) => {
        if (
          value !== undefined &&
          value !== ''
        ) {
          httpParams = httpParams.set(
            key,
            String(value),
          );
        }
      },
    );

    return this.http.get<T>(
      `${environment.apiUrl}${path}`,
      {
        params: httpParams,
      },
    );
  }

  post<T>(
    path: string,
    body: unknown,
  ) {
    return this.http.post<T>(
      `${environment.apiUrl}${path}`,
      body,
    );
  }

  put<T>(
    path: string,
    body: unknown,
  ) {
    return this.http.put<T>(
      `${environment.apiUrl}${path}`,
      body,
    );
  }

  patch<T>(
    path: string,
    body: unknown,
  ) {
    return this.http.patch<T>(
      `${environment.apiUrl}${path}`,
      body,
    );
  }

  delete<T = unknown>(
    path: string,
  ) {
    return this.http.delete<T>(
      `${environment.apiUrl}${path}`,
    );
  }
}