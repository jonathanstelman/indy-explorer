import { createContext, useContext } from 'react'

export const UnitsContext = createContext(null)

export function useUnits() {
  const ctx = useContext(UnitsContext)
  if (!ctx) throw new Error('useUnits must be used within a UnitsProvider')
  return ctx
}
