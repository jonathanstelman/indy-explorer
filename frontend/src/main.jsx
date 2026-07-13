import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import UnitsProvider from './components/common/UnitsProvider.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <UnitsProvider>
        <App />
      </UnitsProvider>
    </BrowserRouter>
  </StrictMode>,
)
