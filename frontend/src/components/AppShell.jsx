import React from 'react'
import Header from './Header'

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <Header />
      <main className="page-container">
        {children}
      </main>
    </div>
  )
}
