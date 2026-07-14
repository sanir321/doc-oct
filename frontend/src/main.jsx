import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import WizardPage from './pages/WizardPage'
import './index.css'

if (import.meta.env.DEV) {
  import('@reticlehq/browser').then(({ reticle }) => reticle.connect({ session: 'paperai' }))
  import('@reticlehq/react').then(({ install }) => install())
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/generate" element={<WizardPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
