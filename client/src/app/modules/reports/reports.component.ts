import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { EcoPermissionService } from '../../core/services/eco-permission.service';

@Component({ templateUrl: './reports.component.html' })
export class ReportsComponent implements OnInit {
  rows: any[] = [];
  total = 0;
  page = 1;
  pageSize = 20;

  eco = '';
  user = '';
  field = '';
  action = '';
  dateStart = '';
  dateEnd = '';

  actions: string[] = [];

  loading = false;
  error = '';
  exporting = false;

  constructor(
    private api: ApiService,
    public permissions: EcoPermissionService,
  ) {}

  ngOnInit(): void {
    this.permissions.load().subscribe({
      next: () => this.init(),
      error: () => this.init(),
    });
  }

  private init(): void {
    if (!this.permissions.canViewHistory) return;
    this.loadActions();
    this.load();
  }

  private params() {
    return {
      page: this.page,
      page_size: this.pageSize,
      eco: this.eco,
      user_email: this.user,
      field: this.field,
      action: this.action,
      date_start: this.dateStart ? this.dateStart + 'T00:00:00' : undefined,
      date_end: this.dateEnd ? this.dateEnd + 'T23:59:59' : undefined,
    };
  }

  loadActions(): void {
    this.api.get<string[]>('/history/actions').subscribe({
      next: a => (this.actions = a),
      error: () => {},
    });
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.get<any>('/history', this.params()).subscribe({
      next: r => {
        this.rows = r.items;
        this.total = r.total;
        this.loading = false;
      },
      error: () => {
        this.error = 'Não foi possível carregar o histórico.';
        this.loading = false;
      },
    });
  }

  clear(): void {
    this.eco = this.user = this.field = this.action = this.dateStart = this.dateEnd = '';
    this.page = 1;
    this.load();
  }

  pages(): number {
    return Math.max(1, Math.ceil(this.total / this.pageSize));
  }

  export(): void {
    this.exporting = true;
    this.api.getBlob('/history/export', this.params()).subscribe({
      next: blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'historico.csv';
        a.click();
        window.URL.revokeObjectURL(url);
        this.exporting = false;
      },
      error: () => {
        this.error = 'Não foi possível exportar o histórico.';
        this.exporting = false;
      },
    });
  }
}
