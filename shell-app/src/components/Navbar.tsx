import { Link, useLocation } from 'react-router-dom'
import './Navbar.css'

export function Navbar() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname.startsWith(path) ? 'nav-link active' : 'nav-link'
  }

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          Micro Frontend Audio
        </Link>
        <div className="nav-links">
          <Link to="/auth" className={isActive('/auth')}>
            Authentication
          </Link>
          <Link to="/audio" className={isActive('/audio')}>
            Audio Processing
          </Link>
          <Link to="/dashboard" className={isActive('/dashboard')}>
            Dashboard
          </Link>
        </div>
      </div>
    </nav>
  )
}