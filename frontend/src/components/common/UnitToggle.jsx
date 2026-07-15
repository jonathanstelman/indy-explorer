import { Button } from 'antd'
import { useUnits } from '@/hooks/useUnits'
import { COLORS, FONTS } from '@/theme'

export default function UnitToggle({ style }) {
  const { unit, toggleUnit } = useUnits()
  const label = unit === 'metric' ? 'm' : 'ft'
  const nextUnit = unit === 'metric' ? 'imperial' : 'metric'

  return (
    <Button
      type="text"
      onClick={toggleUnit}
      aria-label={`Switch to ${nextUnit} units`}
      style={{
        color: COLORS.error,
        fontFamily: FONTS.mono,
        fontSize: 13,
        fontWeight: 700,
        padding: '0 8px',
        flexShrink: 0,
        lineHeight: 1,
        ...style,
      }}
    >
      {label}
    </Button>
  )
}
