import { forwardRef, useCallback, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry, themeQuartz } from 'ag-grid-community'
import { COLORS, FONTS, withAlpha } from '@/theme'
import { COLUMN_DEFS, nullFmt } from '@/components/resortTableColumns'

ModuleRegistry.registerModules([AllCommunityModule])

const DEFAULT_COL_DEF = {
  sortable: true,
  resizable: true,
  filter: false,
  minWidth: 60,
  valueFormatter: nullFmt,
  cellStyle: params => params.value == null ? { color: COLORS.neutral } : null,
}

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

const ResortTable = forwardRef(function ResortTable({ resorts, onRowClick, columnDefs = COLUMN_DEFS, unit = 'imperial' }, ref) {
  const onRowClicked = useCallback(({ data }) => onRowClick(data.resort_id), [onRowClick])

  // headerValueGetter/valueFormatter read `unit` off grid context rather than props, so a
  // toggle needs an explicit refresh — AG Grid doesn't re-derive header/cell text on its own.
  useEffect(() => {
    const api = ref?.current?.api
    if (!api) return
    api.refreshHeader()
    api.refreshCells({ force: true })
  }, [unit, ref])

  return (
    <div style={{ height: '100%' }}>
      <AgGridReact
        ref={ref}
        theme={GRID_THEME}
        rowData={resorts}
        columnDefs={columnDefs}
        defaultColDef={DEFAULT_COL_DEF}
        context={{ unit }}
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
