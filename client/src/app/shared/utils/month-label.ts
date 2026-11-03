const MONTH_LABELS: Readonly<Record<string, string>> = {
  JAN: 'JAN',
  FEB: 'FEV',
  MAR: 'MAR',
  APR: 'ABR',
  MAY: 'MAI',
  JUN: 'JUN',
  JUL: 'JUL',
  AUG: 'AGO',
  SEP: 'SET',
  OCT: 'OUT',
  NOV: 'NOV',
  DEC: 'DEZ',
  FEV: 'FEV',
  ABR: 'ABR',
  MAI: 'MAI',
  AGO: 'AGO',
  SET: 'SET',
  OUT: 'OUT',
  DEZ: 'DEZ',
};


export function monthLabel(value: unknown): string {
  if (typeof value !== 'string') {
    return value === null || value === undefined
      ? ''
      : String(value);
  }

  const normalized = value.trim().toUpperCase();

  return MONTH_LABELS[normalized] ?? value;
}
