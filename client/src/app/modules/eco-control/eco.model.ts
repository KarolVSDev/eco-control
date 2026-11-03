// ECO fields are supplied dynamically according to field permissions.
export interface Eco {
  [key: string]: any;
  id: string;
  eco?: string | null;
  status?: string | null;
  item?: number | null;
  title?: string | null;
}
