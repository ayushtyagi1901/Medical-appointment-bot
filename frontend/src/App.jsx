import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <h1>🏥 HealthCare Plus Clinic</h1>
        <p>Appointment Scheduling Assistant</p>
      </header>
      <main className="app-main">
        <ChatInterface />
      </main>
    </div>
  )
}

export default App

