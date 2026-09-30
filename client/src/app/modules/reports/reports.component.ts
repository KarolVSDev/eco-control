import { Component, OnInit } from '@angular/core';

import { ApiService } from '../../core/services/api.service';

interface HistoryResponse {
  items: any[];
  total: number;
  page: number;
  page_size: number;
}

@Component({
  templateUrl: './reports.component.html',
})
export class ReportsComponent implements OnInit {
  rows: any[] = [];
  total = 0;
  page = 1;
  pageSize = 20;
  eco = '';
  user = '';
  field = '';
  action = '';
  search = '';
  dateStart = '';
  dateEnd = '';
  loading = false;
  exporting = false;
  error = '';

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.get<HistoryResponse>('/history', {
      page: this.page,
      page_size: this.pageSize,
      ...this.filters(),
    }).subscribe({
      next: (response) => {
        this.rows = response.items;
        this.total = response.total;
        this.loading = false;
      },
      error: () => {
        this.error = 'Não foi possível carregar o histórico.';
        this.loading = false;
      },
    });
  }

  exportCsv(): void {
    this.exporting = true;
    this.api.getBlob('/history/export', this.filters()).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'eco-history.csv';
        link.click();
        URL.revokeObjectURL(url);
        this.exporting = false;
      },
      error: () => {
        this.error = 'Não foi possível exportar o histórico.';
        this.exporting = false;
      },
    });
  }

  clear(): void {
    this.eco = '';
    this.user = '';
    this.field = '';
    this.action = '';
    this.search = '';
    this.dateStart = '';
    this.dateEnd = '';
    this.page = 1;
    this.load();
  }

  pages(): number {
    return Math.max(1, Math.ceil(this.total / this.pageSize));
  }

  actionLabel(action: string): string {
    return ({
      created: 'Criada',
      updated: 'Alterada',
      deleted: 'Excluída',
    } as Record<string, string>)[action] || action;
  }

  private filters(): Record<string, string | undefined> {
    return {
      date_start: this.dateStart
        ? `${this.dateStart}T00:00:00`
        : undefined,
      date_end: this.dateEnd
        ? `${this.dateEnd}T23:59:59`
        : undefined,
      user_email: this.user || undefined,
      field: this.field || undefined,
      action: this.action || undefined,
      eco: this.eco || undefined,
      search: this.search || undefined,
    };
  }
}
