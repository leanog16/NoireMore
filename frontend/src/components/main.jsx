import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import "../css/index.css";

import UrbanNoirBackground from './UrbanNoirBackground.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <UrbanNoirBackground />
  </StrictMode>,
)
