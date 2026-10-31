import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface GapReportItem {
  id: string;
  eco: string | null;
  eco_type: string | null;
  az_eco_creation_date: string | null;
  effective_date: string | null;
  approval_date: string;
  gap_14d: number | null;
  gap_14d_note: string | null;
  requires_gap_14d_note: boolean;
}

export interface GapReportResponse {
  start_date: string;
  end_date: string;
  total: number;
  items: GapReportItem[];
}

export function formatReportDate(value: string | null): string {
  if (!value) return '-';
  const [year, month, day] = value.split('-');
  return `${day}/${month}/${year}`;
}

export function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function previousWeekPeriod(today = new Date()): { start: string; end: string } {
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const daysSinceMonday = (monday.getDay() + 6) % 7;
  monday.setDate(monday.getDate() - daysSinceMonday - 7);
  const saturday = new Date(monday);
  saturday.setDate(saturday.getDate() + 5);
  return { start: formatLocalDate(monday), end: formatLocalDate(saturday) };
}

@Component({
  selector: 'app-gap-report',
  templateUrl: './gap-report.component.html',
  styleUrls: ['./gap-report.component.css'],
})
export class GapReportComponent implements OnInit, OnDestroy {
  private readonly initialPeriod = previousWeekPeriod();
  startDate = this.initialPeriod.start;
  endDate = this.initialPeriod.end;
  appliedPeriod = { ...this.initialPeriod };
  validationError = '';
  loading = false;
  loadError = '';
  exporting = false;
  exportError = '';
  items: GapReportItem[] = [];
  total = 0;
  noteDrafts: Record<string, string> = {};
  savingNoteIds = new Set<string>();
  noteErrors: Record<string, string> = {};
  noteSuccess: Record<string, string> = {};
  readonly formatDate = formatReportDate;
  private loadSubscription?: Subscription;
  private readonly saves = new Subscription();

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.loadReport();
  }

  ngOnDestroy(): void {
    this.loadSubscription?.unsubscribe();
    this.saves.unsubscribe();
  }

  loadReport(): void {
    this.loadSubscription?.unsubscribe();
    this.loading = true;
    this.loadError = '';
    this.items = [];
    this.total = 0;
    this.noteErrors = {};
    this.noteSuccess = {};
    this.loadSubscription = this.api.get<GapReportResponse>('/reports/gap', {
      start_date: this.appliedPeriod.start,
      end_date: this.appliedPeriod.end,
    }).subscribe({
      next: response => {
        this.items = response.items;
        this.total = response.total;
        for (const item of this.items) {
          if (!this.savingNoteIds.has(item.id)) {
            this.noteDrafts[item.id] = item.gap_14d_note ?? '';
          }
        }
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.loadError = 'Não foi possível carregar o relatório. Tente novamente.';
      },
    });
  }

  saveNote(item: GapReportItem): void {
    if (this.savingNoteIds.has(item.id)) return;
    const note = (this.noteDrafts[item.id] ?? '').trim() || null;
    delete this.noteErrors[item.id];
    delete this.noteSuccess[item.id];
    if (item.requires_gap_14d_note && !note) {
      this.noteErrors[item.id] = 'Justificativa necessária';
      return;
    }
    this.savingNoteIds.add(item.id);
    this.saves.add(this.api.patch<{ gap_14d_note: string | null }>(
      `/ecos/${item.id}`, { gap_14d_note: note },
    ).subscribe({
      next: updated => {
        this.savingNoteIds.delete(item.id);
        const current = this.items.find(row => row.id === item.id);
        if (current) current.gap_14d_note = updated.gap_14d_note;
        this.noteDrafts[item.id] = updated.gap_14d_note ?? '';
        this.noteSuccess[item.id] = 'Justificativa salva.';
      },
      error: () => {
        this.savingNoteIds.delete(item.id);
        this.noteErrors[item.id] = 'Não foi possível salvar a justificativa.';
      },
    }));
  }

  exportReport(): void {
    if (this.exporting || this.loading || this.loadError || this.total === 0 || this.savingNoteIds.size > 0) return;
    const period = { ...this.appliedPeriod };
    this.exporting = true;
    this.exportError = '';
    this.saves.add(this.api.getBlob('/reports/gap/export', {
      start_date: period.start,
      end_date: period.end,
    }).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `relatorio_gap_${period.start}_${period.end}.xlsx`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        this.exporting = false;
      },
      error: () => {
        this.exporting = false;
        this.exportError = 'Não foi possível exportar o relatório. Tente novamente.';
      },
    }));
  }

  applyPeriod(): void {
    if (!this.startDate || !this.endDate) {
      this.validationError = 'Informe a data inicial e a data final.';
      return;
    }
    if (this.startDate > this.endDate) {
      this.validationError = 'Data inicial não pode ser posterior à data final.';
      return;
    }
    this.validationError = '';
    this.appliedPeriod = { start: this.startDate, end: this.endDate };
    this.loadReport();
  }

  restorePeriod(): void {
    const period = previousWeekPeriod();
    this.startDate = period.start;
    this.endDate = period.end;
    this.applyPeriod();
  }
}
