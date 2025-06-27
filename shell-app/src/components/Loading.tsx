import './Loading.css'

export function Loading() {
  return (
    <div className="loading-container">
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
      <p className="loading-text">Loading microfrontend...</p>
    </div>
  )
}