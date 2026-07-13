import { useState } from 'react'
import { UnitsContext } from '@/hooks/useUnits'

const STORAGE_KEY = 'indy-units'

export default function UnitsProvider({ children }) {
  const [unit, setUnit] = useState(() => localStorage.getItem(STORAGE_KEY) === 'metric' ? 'metric' : 'imperial')

  function toggleUnit() {
    setUnit(prev => {
      const next = prev === 'imperial' ? 'metric' : 'imperial'
      localStorage.setItem(STORAGE_KEY, next)
      return next
    })
  }

  return (
    <UnitsContext.Provider value={{ unit, toggleUnit }}>
      {children}
    </UnitsContext.Provider>
  )
}
