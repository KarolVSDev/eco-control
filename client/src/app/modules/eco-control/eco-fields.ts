export const FIELD_TYPES = {
  TEXT: 'text',
  MONO: 'mono',
  TEXTAREA: 'textarea',
  SELECT: 'select',
  DATE: 'date',
  BOOL_YN: 'bool_yn',
  BADGE_STATUS: 'badge_status',

  CALC_TEXT: 'calc_text',
  CALC_BOOL: 'calc_bool',
  CALC_NUMBER: 'calc_number',
} as const;


export type EcoFieldType =
  typeof FIELD_TYPES[
    keyof typeof FIELD_TYPES
  ];


export interface EcoColumn {
  key: string;
  label: string;
  type: EcoFieldType;

  options?: readonly string[];
  sticky?: boolean;
}


export interface EcoColumnGroup {
  key: string;
  label: string;
  columns: readonly EcoColumn[];
}


// =====================================================
// OPTIONS
// =====================================================

export const GROUP_OPTIONS = [
  'BOM',
  'DEV',
  'HW',
  'MEC',
] as const;


export const ITEM_TYPE_OPTIONS = [
  'MEC',
  'DEV',
  'ELET',
] as const;


export const ECO_TYPE_OPTIONS = [
  'LOCAL',
  'TOOL',
  'TEMP',
  'DC-ECO',
  'SOFTWARE',
  'REGULAR',
  'DESENHO - IMPRESSOS/BOX',
  'DESENHO - NÃO APLICADA A AZ',
  'DESENHO - ENVIADA E-MAIL',
  'DESENHO',
] as const;


export const YES_NO_OPTIONS = [
  'YES',
  'NO',
] as const;


export const STATUS_OPTIONS = [
  'WORKING',
  'ON HOLD',
  'WAITING HZ/IN/ND',
  'MEC/HW ANALISYS',
  'COUNCIL MEETING',
  'PROCESSING',
  'SPOC ON APPROVAL',
  'WAITING NEW ECO TO FIX BOM',
  'REJECTED',
  'RELEASED',
  'TO BE CANCELLED',
  'CANCELLED',
] as const;


export const RECEB_OPTIONS = [
  'NORMAL',
  'MISSING 1',
  'MISSING 2',
] as const;


export const ORIGEM_APPROVAL_OPTIONS = [
  'HQ',
  'ND',
  'RC',
  'HZ',
  'HQ/HZ',
  'IN',
  'MISSING',
  'NA',
] as const;


export const OBU_OPTIONS = [
  'NW1',
  'NWD',
  'NW9',
  'NWW',
  'NW4',
  'NW5',
  'NWU',
  'NWX',
  'NWH',
  'NYE',
  'NWV',
  'NWK',
  'NWE',
  'NWZ',
] as const;


// =====================================================
// COLUMN GROUPS
// A ordem abaixo é a mesma do Base44.
// =====================================================

export const COLUMN_GROUPS:
  readonly EcoColumnGroup[] = [

  // ===================================================
  // 1. IDENTIFICAÇÃO
  // ===================================================
  {
    key: 'identificacao',
    label: 'IDENTIFICAÇÃO',

    columns: [
      {
        key: 'gap',
        label: 'GAP',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'item',
        label: 'ITEM',
        type: FIELD_TYPES.CALC_NUMBER,
        sticky: true,
      },
      {
        key: 'month',
        label: 'MONTH',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'product',
        label: 'Product',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'au',
        label: 'AU',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'obu',
        label: 'OBU',
        type: FIELD_TYPES.SELECT,
        options: OBU_OPTIONS,
      },
    ],
  },


  // ===================================================
  // 2. CLASSIFICAÇÃO
  // ===================================================
  {
    key: 'classificacao',
    label: 'CLASSIFICAÇÃO',

    columns: [
      {
        key: 'group',
        label: 'GROUP',
        type: FIELD_TYPES.SELECT,
        options: GROUP_OPTIONS,
      },
      {
        key: 'owner',
        label: 'OWNER',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'item_type',
        label: 'ITEM TYPE',
        type: FIELD_TYPES.SELECT,
        options: ITEM_TYPE_OPTIONS,
      },
      {
        key: 'eco_type',
        label: 'ECO TYPE',
        type: FIELD_TYPES.SELECT,
        options: ECO_TYPE_OPTIONS,
      },
      {
        key: 'change_bom',
        label: 'CHANGE BOM?',
        type: FIELD_TYPES.BOOL_YN,
        options: YES_NO_OPTIONS,
      },
      {
        key: 'status',
        label: 'STATUS',
        type: FIELD_TYPES.BADGE_STATUS,
        options: STATUS_OPTIONS,
      },
      {
        key: 'receb',
        label: 'RECEB.',
        type: FIELD_TYPES.SELECT,
        options: RECEB_OPTIONS,
      },
    ],
  },


  // ===================================================
  // 3. ECO HQ
  // ===================================================
  {
    key: 'eco_hq',
    label: 'ECO HQ',

    columns: [
      {
        key: 'eco',
        label: 'ECO',
        type: FIELD_TYPES.MONO,
      },
      {
        key: 'change_reason',
        label: 'CHANGE REASON',
        type: FIELD_TYPES.TEXTAREA,
      },
      {
        key: 'hq_eco_release_date',
        label: 'HQ ECO RELEASE DATE',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'az_eco_register_date',
        label: 'AZ ECO REGISTER DATE',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'auto_ecr',
        label: 'Auto ECR?',
        type: FIELD_TYPES.BOOL_YN,
        options: YES_NO_OPTIONS,
      },
      {
        key: 'delay_eco_register',
        label: '1-Delay ECO Register',
        type: FIELD_TYPES.CALC_NUMBER,
      },
      {
        key: 'eco_registration_week',
        label: 'ECO REGISTRATION WEEK',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'council_meeting_week',
        label: 'Council meeting Week',
        type: FIELD_TYPES.TEXT,
      },
    ],
  },


  // ===================================================
  // 4. ORIGEM
  // ===================================================
  {
    key: 'origem',
    label: 'ORIGEM',

    columns: [
      {
        key: 'hz_in_kr_eco_1',
        label: 'HZ/IN/KR ECO(1)',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'hz_sh_in_receive_date_1',
        label: 'HZ/SH/IN RECEIVE DATE (1)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'eco_origem_1',
        label: 'ECO Origem (1)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'hz_in_kr_eco_2',
        label: 'HZ/IN/KR ECO(2)',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'hz_sh_in_receive_date_2',
        label: 'HZ/SH/IN RECEIVE DATE (2)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'eco_origem_2',
        label: 'ECO Origem (2)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'hz_in_kr_eco_3',
        label: 'HZ/IN/KR ECO(3)',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'hz_sh_in_receive_date_3',
        label: 'HZ/SH/IN RECEIVE DATE (3)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'eco_origem_3',
        label: 'ECO Origem (3)',
        type: FIELD_TYPES.CALC_NUMBER,
      },
    ],
  },


  // ===================================================
  // 5. AZ ECO
  // ===================================================
  {
    key: 'az_eco',
    label: 'AZ ECO',

    columns: [
      {
        key: 'az_eco_no',
        label: 'AZ_ECO_NO.',
        type: FIELD_TYPES.MONO,
      },
      {
        key: 'change_reason2',
        label: 'Change reason2',
        type: FIELD_TYPES.TEXTAREA,
      },
      {
        key: 'change_bom_az',
        label: 'Change BOM? AZ',
        type: FIELD_TYPES.BOOL_YN,
        options: YES_NO_OPTIONS,
      },
      {
        key: 'az_eco_creation_date',
        label: 'AZ ECO CREATION DATE',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_start_az_eco',
        label: 'GAP Start AZ ECO',
        type: FIELD_TYPES.CALC_NUMBER,
      },
      {
        key: 'contar_eco_emitida_1_dias',
        label: 'Contar Eco emitida > 1 dias',
        type: FIELD_TYPES.CALC_BOOL,
      },
      {
        key: 'gap_agreement',
        label: 'GAP AGREEMENT',
        type: FIELD_TYPES.CALC_NUMBER,
      },
    ],
  },


  // ===================================================
  // 6. AGREEMENT OTHER DEPTS
  // ===================================================
  {
    key: 'agreement',
    label: 'AGREEMENT OTHER DEPTS',

    columns: [
      {
        key: 'agreement_start_1',
        label:
          'AGREEMENT OTHER DEPTS START (1)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'agreement_finish_1',
        label:
          'AGREEMENT OTHER DEPTS FINSHI (1)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_agreement_1',
        label:
          'GAP AGREEMENT OTHER DEPTS (1)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'agreement_start_2',
        label:
          'AGREEMENT OTHER DEPTS START (2)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'agreement_finish_2',
        label:
          'AGREEMENT OTHER DEPTS FINSHI (2)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_agreement_2',
        label:
          'GAP AGREEMENT OTHER DEPTS (2)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'agreement_start_3',
        label:
          'AGREEMENT OTHER DEPTS START (3)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'agreement_finish_3',
        label:
          'AGREEMENT OTHER DEPTS FINSHI (3)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_agreement_3',
        label:
          'GAP AGREEMENT OTHER DEPTS (3)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'gap_total_agreement',
        label:
          'GAP TOTAL AGREEMENT OTHER DEPTS',
        type: FIELD_TYPES.CALC_NUMBER,
      },
    ],
  },


  // ===================================================
  // 7. R&D APPROVAL
  // ===================================================
  {
    key: 'rd_approval',
    label: 'R&D APPROVAL',

    columns: [
      {
        key: 'second_aprov_rd',
        label: '2ST APROV R&D',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'second_aprov_rd_start_1',
        label: '2ST APROV R&D START (1)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'second_aprov_rd_finish_1',
        label: '2ST APROV R&D FINISH (1)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_2st_1',
        label: 'GAP 2ST APROV R&D (1)',
        type: FIELD_TYPES.CALC_NUMBER,
      },

      {
        key: 'second_aprov_rd_start_2',
        label: '2ST APROV R&D START (2)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'second_aprov_rd_finish_2',
        label: '2ST APROV R&D FINISH (2)',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'gap_2st_2',
        label: 'GAP 2ST APROV R&D (2)',
        type: FIELD_TYPES.CALC_NUMBER,
      },
      {
        key: 'gap_total_2st',
        label: 'GAP TOTAL 2ST APROV R&D',
        type: FIELD_TYPES.CALC_NUMBER,
      },
    ],
  },


  // ===================================================
  // 8. RELEASE
  // ===================================================
  {
    key: 'release',
    label: 'RELEASE',

    columns: [
      {
        key: 'eco_release_week',
        label: 'ECO release week',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'az_gap',
        label: 'AZ Gap',
        type: FIELD_TYPES.CALC_NUMBER,
      },
      {
        key: 'contar_eco_7',
        label:
          'Contar Eco concluída > 7 dias',
        type: FIELD_TYPES.CALC_BOOL,
      },
      {
        key: 'contar_eco_10',
        label:
          'Contar Eco concluída > 10 dias',
        type: FIELD_TYPES.CALC_BOOL,
      },
      {
        key: 'total_gap',
        label: 'Total Gap',
        type: FIELD_TYPES.CALC_NUMBER,
      },
      {
        key: 'release_month',
        label: 'RELEASE MONTH',
        type: FIELD_TYPES.CALC_TEXT,
      },
      {
        key: 'release_year',
        label: 'RELEASE YEAR',
        type: FIELD_TYPES.CALC_TEXT,
      },
    ],
  },


  // ===================================================
  // 9. ADICIONAIS
  // ===================================================
  {
    key: 'adicionais',
    label: 'ADICIONAIS',

    columns: [
      {
        key: 'change_reason_az',
        label: 'CHANGE REASON AZ',
        type: FIELD_TYPES.TEXTAREA,
      },
      {
        key: 'model_az',
        label: 'MODEL AZ',
        type: FIELD_TYPES.TEXTAREA,
      },
      {
        key: 'new_model',
        label:
          'New Model?(Check in NPI plan 26Y)',
        type: FIELD_TYPES.BOOL_YN,
        options: YES_NO_OPTIONS,
      },
      {
        key: 'origem_approval',
        label: 'Origem approval',
        type: FIELD_TYPES.SELECT,
        options: ORIGEM_APPROVAL_OPTIONS,
      },
      {
        key: 'event',
        label: 'Event',
        type: FIELD_TYPES.BOOL_YN,
        options: YES_NO_OPTIONS,
      },
      {
        key: 'comments',
        label: 'COMMENTS',
        type: FIELD_TYPES.TEXTAREA,
      },
    ],
  },


  // ===================================================
  // 10. SET ECO
  // ===================================================
  {
    key: 'set_eco',
    label: 'SET ECO (somente BM/NWK)',

    columns: [
      {
        key: 'set_eco',
        label: 'SET ECO',
        type: FIELD_TYPES.TEXT,
      },
      {
        key: 'set_eco_register_date',
        label: 'SET ECO REGISTER DATE',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'set_eco_release_date',
        label: 'SET ECO RELEASE DATE',
        type: FIELD_TYPES.DATE,
      },
      {
        key: 'set_eco_change_reason',
        label: 'SET ECO CHANGE REASON',
        type: FIELD_TYPES.TEXTAREA,
      },
      {
        key: 'set_eco_model',
        label: 'SET ECO MODEL',
        type: FIELD_TYPES.TEXT,
      },
    ],
  },
];


// =====================================================
// HELPERS
// =====================================================

export const ALL_COLUMNS:
  readonly EcoColumn[] =
  COLUMN_GROUPS.flatMap(
    group => group.columns
  );


export const FIELD_LABELS:
  Readonly<Record<string, string>> =
  Object.fromEntries(
    ALL_COLUMNS.map(
      column => [
        column.key,
        column.label,
      ]
    )
  );


export const CALCULATED_TYPES:
  readonly EcoFieldType[] = [
    FIELD_TYPES.CALC_TEXT,
    FIELD_TYPES.CALC_BOOL,
    FIELD_TYPES.CALC_NUMBER,
  ];


export const CALCULATED_COLUMNS =
  ALL_COLUMNS.filter(
    column =>
      CALCULATED_TYPES.includes(
        column.type
      )
  );


export const EDITABLE_COLUMNS =
  ALL_COLUMNS.filter(
    column =>
      !CALCULATED_TYPES.includes(
        column.type
      )
  );


export const CALCULATED_KEYS =
  CALCULATED_COLUMNS.map(
    column => column.key
  );


export const EDITABLE_KEYS =
  EDITABLE_COLUMNS.map(
    column => column.key
  );


export function isCalculatedField(
  column: EcoColumn,
): boolean {
  return CALCULATED_TYPES.includes(
    column.type
  );
}


export function isSetEcoRow(
  row: {
    obu?: string | null;
  },
): boolean {
  return row.obu === 'NWK';
}