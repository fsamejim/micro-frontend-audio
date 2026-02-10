import { Link, useLocation } from 'react-router-dom'
import { useAuthState } from '../hooks/useAuthState'
import './Navbar.css'

export function Navbar() {
  const location = useLocation()
  const { isAuthenticated, logout } = useAuthState()

  const isActive = (path: string) => {
    return location.pathname.startsWith(path) ? 'nav-link active' : 'nav-link'
  }

  const handleLogout = (e: React.MouseEvent) => {
    e.preventDefault()
    logout()
  }

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          Micro Frontend Audio
        </Link>
        <div className="nav-links">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className={isActive('/dashboard')}>
                Dashboard
              </Link>
              <Link to="/audio" className={isActive('/audio')}>
                Audio Processing
              </Link>
              <button onClick={handleLogout} className="nav-link logout-btn">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/auth/login" className={isActive('/auth/login')}>
                Login
              </Link>
              <Link to="/auth/register" className={isActive('/auth/register')}>
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
