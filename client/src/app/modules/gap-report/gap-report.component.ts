import { Component } from '@angular/core';

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
export class GapReportComponent {
  private readonly initialPeriod = previousWeekPeriod();
  startDate = this.initialPeriod.start;
  endDate = this.initialPeriod.end;
  appliedPeriod = { ...this.initialPeriod };
  validationError = '';

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
  }

  restorePeriod(): void {
    const period = previousWeekPeriod();
    this.startDate = period.start;
    this.endDate = period.end;
    this.applyPeriod();
  }
}
