import { forwardRef, useCallback } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry, themeQuartz } from 'ag-grid-community'
import { COLORS, FONTS, withAlpha } from '@/theme'

ModuleRegistry.registerModules([AllCommunityModule])

const nullFmt = p => p.value != null ? p.value : '—'
const numFmt  = p => p.value != null ? Number(p.value).toLocaleString() : '—'

function BoolCell({ value }) {
  if (value === true)  return <span style={{ color: COLORS.bgHeader }}>✓</span>
  if (value === false) return <span style={{ color: COLORS.neutral  }}>✗</span>
  return <span style={{ color: COLORS.textMuted }}>—</span>
}

function LinkCell({ value }) {
  if (!value) return <span style={{ color: COLORS.textMuted }}>—</span>
  return (
    <a
      href={value}
      target="_blank"
      rel="noreferrer"
      onClick={e => e.stopPropagation()}
      style={{ color: COLORS.accentPurple }}
    >
      {value}
    </a>
  )
}

const DEFAULT_COL_DEF = {
  sortable: true,
  resizable: true,
  filter: false,
  minWidth: 60,
  valueFormatter: nullFmt,
  cellStyle: params => params.value == null ? { color: COLORS.neutral } : null,
}

export const COLUMN_DEFS = [
  // Identity
  { field: 'name',          headerName: 'Resort',   pinned: 'left', width: 190, valueFormatter: nullFmt, cellStyle: { fontWeight: 600 } },
  { field: 'city',          headerName: 'City',     width: 110 },
  { field: 'state',         headerName: 'State',    width: 120 },
  { field: 'country',       headerName: 'Country',  width: 120 },
  { field: 'region',        headerName: 'Region',   width: 100 },
  { field: 'location_name', headerName: 'Location', width: 120 },

  // Elevation
  { field: 'vertical',           headerName: 'Vertical (ft)', width: 106, valueFormatter: numFmt },
  { field: 'vertical_summit_ft', headerName: 'Summit (ft)',   width: 100, valueFormatter: numFmt },
  { field: 'vertical_base_ft',   headerName: 'Base (ft)',     width: 88,  valueFormatter: numFmt },
  { field: 'vertical_meters',    headerName: 'Vertical (m)',  width: 108, valueFormatter: numFmt },

  // Size
  { field: 'acres',           headerName: 'Acres',             width: 78,  valueFormatter: numFmt },
  { field: 'num_trails',      headerName: 'Trails',            width: 72,  valueFormatter: numFmt },
  { field: 'num_trails_xc',   headerName: 'Trails (XC)',       width: 100, valueFormatter: numFmt },
  { field: 'num_lifts',       headerName: 'Lifts',             width: 64,  valueFormatter: numFmt },
  { field: 'trail_length_mi', headerName: 'Trail Length XC (mi)', width: 138, valueFormatter: numFmt },
  { field: 'trail_length_km', headerName: 'Trail Length XC (km)', width: 138, valueFormatter: numFmt },

  // Difficulty
  { field: 'difficulty_beginner',        headerName: 'Beginner (%)',        width: 120, valueFormatter: numFmt },
  { field: 'difficulty_intermediate',    headerName: 'Intermediate (%)',    width: 136, valueFormatter: numFmt },
  { field: 'difficulty_advanced',        headerName: 'Advanced (%)',        width: 120, valueFormatter: numFmt },
  { field: 'difficulty_beginner_xc',     headerName: 'Beginner XC (%)',     width: 132, valueFormatter: numFmt },
  { field: 'difficulty_intermediate_xc', headerName: 'Intermediate XC (%)', width: 152, valueFormatter: numFmt },
  { field: 'difficulty_advanced_xc',     headerName: 'Advanced XC (%)',     width: 132, valueFormatter: numFmt },

  // Snow
  { field: 'snowfall_average_in', headerName: 'Avg Snowfall (in)', width: 138, valueFormatter: numFmt },
  { field: 'snowfall_high_in',    headerName: 'Max Snowfall (in)', width: 138, valueFormatter: numFmt },

  // Features
  { field: 'has_alpine',        headerName: 'Alpine',        width: 74,  cellRenderer: BoolCell },
  { field: 'has_cross_country', headerName: 'XC',            width: 54,  cellRenderer: BoolCell },
  { field: 'has_night_skiing',  headerName: 'Night Skiing',  width: 108, cellRenderer: BoolCell },
  { field: 'has_terrain_parks', headerName: 'Terrain Parks', width: 116, cellRenderer: BoolCell },
  { field: 'is_dog_friendly',   headerName: 'Dog Friendly',  width: 110, cellRenderer: BoolCell },
  { field: 'has_snowshoeing',   headerName: 'Snowshoeing',   width: 120, cellRenderer: BoolCell },
  { field: 'ltt_available',     headerName: 'Learn to Turn', width: 122, cellRenderer: BoolCell },
  { field: 'is_allied',         headerName: 'Allied',        width: 74,  cellRenderer: BoolCell },

  // Blackout
  { field: 'blackout_count',     headerName: 'Blackout Dates', width: 122, valueFormatter: numFmt },
  { field: 'ltt_blackout_count', headerName: 'Learn to Turn Blackouts', width: 180, valueFormatter: numFmt },

  // Reservations
  { field: 'reservation_status', headerName: 'Reservations',    width: 120 },
  { field: 'reservation_url',    headerName: 'Reservation URL', width: 150, cellRenderer: LinkCell },

  // Peak Rankings — summary
  { field: 'pr_total',         headerName: 'Peak Score',    width: 104, valueFormatter: numFmt },
  { field: 'pr_overall_rank',  headerName: 'Peak Rank',     width: 100, valueFormatter: numFmt },
  { field: 'pr_regional_rank', headerName: 'Regional Rank', width: 120, valueFormatter: numFmt },
  { field: 'pr_region',        headerName: 'PR Region',     width: 96 },

  // Peak Rankings — subcategories
  { field: 'pr_snow',               headerName: 'PR Snow',        width: 86,  valueFormatter: numFmt },
  { field: 'pr_resiliency',         headerName: 'PR Resiliency',  width: 132, valueFormatter: numFmt },
  { field: 'pr_size',               headerName: 'PR Size',        width: 80,  valueFormatter: numFmt },
  { field: 'pr_terrain_diversity',  headerName: 'PR Terrain',     width: 96,  valueFormatter: numFmt },
  { field: 'pr_challenge',          headerName: 'PR Challenge',   width: 124, valueFormatter: numFmt },
  { field: 'pr_lifts',              headerName: 'PR Lifts',       width: 82,  valueFormatter: numFmt },
  { field: 'pr_crowd_flow',         headerName: 'PR Crowd Flow',  width: 132, valueFormatter: numFmt },
  { field: 'pr_facilities',         headerName: 'PR Facilities',  width: 120, valueFormatter: numFmt },
  { field: 'pr_navigation',         headerName: 'PR Navigation',  width: 132, valueFormatter: numFmt },
  { field: 'pr_mountain_aesthetic', headerName: 'PR Aesthetic',   width: 120, valueFormatter: numFmt },
  { field: 'pr_lodging',            headerName: 'PR Lodging',     width: 112 },
  { field: 'pr_apres_ski',          headerName: 'PR Après Ski',   width: 124 },
  { field: 'pr_access_road',        headerName: 'PR Access Road', width: 140 },
  { field: 'pr_ability_low',        headerName: 'Ability Low',    width: 100 },
  { field: 'pr_ability_high',       headerName: 'Ability High',   width: 100 },
  { field: 'pr_nearest_cities',     headerName: 'Nearest Cities', width: 126 },
  { field: 'pr_pass_affiliation',   headerName: 'Pass Affiliation', width: 142 },

  // Links
  { field: 'indy_page', headerName: 'Indy Page', width: 450, cellRenderer: LinkCell },
  { field: 'website',   headerName: 'Website',   width: 360, cellRenderer: LinkCell },
]

export const HEADER_BY_FIELD = Object.fromEntries(COLUMN_DEFS.map(c => [c.field, c.headerName]))

export const COL_GROUPS = [
  { label: 'Location',      fields: ['city', 'state', 'country', 'region', 'location_name'] },
  { label: 'Elevation',     fields: ['vertical', 'vertical_summit_ft', 'vertical_base_ft', 'vertical_meters'] },
  // Select Columns renders each group as a 2-col CSS grid with default (row-wise) auto-flow —
  // items fill left-to-right then wrap, so a field and its XC counterpart must be adjacent
  // AND start on an even index to land side by side in the same row (col1/col2), not just be
  // next to each other in the flat array.
  { label: 'Size',          fields: ['acres', 'num_lifts', 'num_trails', 'num_trails_xc', 'trail_length_mi', 'trail_length_km'] },
  { label: 'Difficulty',    fields: ['difficulty_beginner', 'difficulty_beginner_xc', 'difficulty_intermediate', 'difficulty_intermediate_xc', 'difficulty_advanced', 'difficulty_advanced_xc'] },
  { label: 'Snow',          fields: ['snowfall_average_in', 'snowfall_high_in'] },
  { label: 'Features',      fields: ['has_alpine', 'has_cross_country', 'has_night_skiing', 'has_terrain_parks', 'is_dog_friendly', 'has_snowshoeing', 'ltt_available', 'is_allied'] },
  { label: 'Blackout',      fields: ['blackout_count', 'ltt_blackout_count'] },
  { label: 'Reservations',  fields: ['reservation_status', 'reservation_url'] },
  { label: 'Peak Rankings', fields: ['pr_total', 'pr_overall_rank', 'pr_regional_rank', 'pr_region', 'pr_snow', 'pr_resiliency', 'pr_size', 'pr_terrain_diversity', 'pr_challenge', 'pr_lifts', 'pr_crowd_flow', 'pr_facilities', 'pr_navigation', 'pr_mountain_aesthetic', 'pr_lodging', 'pr_apres_ski', 'pr_access_road', 'pr_ability_low', 'pr_ability_high', 'pr_nearest_cities', 'pr_pass_affiliation'] },
  { label: 'Links',         fields: ['indy_page', 'website'] },
]

const GRID_THEME = themeQuartz.withParams({
  fontFamily:                   FONTS.sans,
  fontSize:                     14,
  rowHeight:                    25,
  headerHeight:                 25,
  cellHorizontalPadding:        11,
  wrapperBorderRadius:          0,
  borderColor:                  COLORS.border,
  columnBorder:                 false,
  headerColumnBorder:           false,
  headerColumnResizeHandleColor: 'transparent',
  rowHoverColor:                COLORS.success,
  selectedRowBackgroundColor:   withAlpha(COLORS.neutral, 0.15),
  headerBackgroundColor:        COLORS.bgMidtone,
  headerCellHoverBackgroundColor: COLORS.neutral,
  headerTextColor:              COLORS.bgBase,
  headerFontWeight:             700,
})

const ResortTable = forwardRef(function ResortTable({ resorts, onRowClick, columnDefs = COLUMN_DEFS }, ref) {
  const onRowClicked = useCallback(({ data }) => onRowClick(data.resort_id), [onRowClick])

  return (
    <div style={{ height: '100%' }}>
      <AgGridReact
        ref={ref}
        theme={GRID_THEME}
        rowData={resorts}
        columnDefs={columnDefs}
        defaultColDef={DEFAULT_COL_DEF}
        getRowId={({ data }) => data.resort_id}
        onRowClicked={onRowClicked}
        rowStyle={{ cursor: 'pointer' }}
        suppressCellFocus
        animateRows={false}
      />
    </div>
  )
})

export default ResortTable
