import React from 'react'
import { Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell'
import SearchPage from './pages/SearchPage'
import ResultPage from './pages/ResultPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/resultado/:cnpj" element={<ResultPage />} />
      </Routes>
    </AppShell>
  )
}
