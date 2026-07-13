import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function Header() {
  const location = useLocation()

  return (
    <header className="header">
      <Link to="/" className="header__logo-area">
        <svg
          className="header__logo-icon"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M4 24C4 24 8 8 16 8C24 8 28 24 28 24"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M8 24C8 24 11 12 16 12C21 12 24 24 24 24"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            opacity="0.6"
          />
          <path
            d="M12 24C12 24 13.5 16 16 16C18.5 16 20 24 20 24"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            fill="none"
            opacity="0.35"
          />
        </svg>
        <span className="header__logo-text">Consulta Societária</span>
      </Link>
      <nav className="header__nav">
        <Link
          to="/"
          className={`header__nav-link${location.pathname === '/' ? ' header__nav-link--active' : ''}`}
        >
          Início
        </Link>
        <a
          href="https://mendoncagalvao.com.br"
          className="header__nav-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          Sobre
        </a>
      </nav>
    </header>
  )
}
