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
          <Link to="/dashboard" className={isActive('/dashboard')}>
            Dashboard
          </Link>
          <Link to="/auth/login" className={isActive('/auth/login')}>
            Login
          </Link>
          <Link to="/auth/register" className={isActive('/auth/register')}>
            Register
          </Link>
          <Link to="/audio" className={isActive('/audio')}>
            Audio Processing
          </Link>
          <Link to="/auth/test" className={isActive('/auth/test')}>
            Test MF
          </Link>
        </div>
      </div>
    </nav>
  )
}