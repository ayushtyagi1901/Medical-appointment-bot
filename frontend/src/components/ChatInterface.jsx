import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import AppointmentConfirmation from './AppointmentConfirmation'
import './ChatInterface.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm your appointment scheduling assistant. I can help you book an appointment or answer questions about our clinic. How can I assist you today?"
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [appointmentDetails, setAppointmentDetails] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to chat
    const newMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)

    try {
      // Prepare conversation history
      const conversationHistory = newMessages
        .slice(0, -1) // Exclude the current message
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }))

      // Call API
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message: userMessage,
        conversation_history: conversationHistory
      })

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        intent: response.data.intent
      }
      setMessages([...newMessages, assistantMessage])

      // Check if appointment was booked (look for appointment ID in response)
      const appointmentIdMatch = response.data.response.match(/appointment ID is ([a-f0-9-]+)/i)
      if (appointmentIdMatch || response.data.response.toLowerCase().includes('successfully booked')) {
        // Extract appointment details from response
        setAppointmentDetails({
          message: response.data.response,
          appointment_id: appointmentIdMatch ? appointmentIdMatch[1] : 'N/A'
        })
      }

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again or contact us directly at +1 (415) 555-0123.'
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleCloseConfirmation = () => {
    setAppointmentDetails(null)
  }

  return (
    <div className="chat-container">
      {appointmentDetails && (
        <AppointmentConfirmation
          details={appointmentDetails}
          onClose={handleCloseConfirmation}
        />
      )}
      
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'assistant' && (
                <div className="message-avatar">🤖</div>
              )}
              <div className="message-text">
                {msg.content}
                {msg.intent && (
                  <span className="message-intent">{msg.intent}</span>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="message-avatar">👤</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="message-avatar">🤖</div>
              <div className="message-text loading">
                <span className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message here..."
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-button"
        >
          {loading ? '⏳' : '➤'}
        </button>
      </form>
    </div>
  )
}

export default ChatInterface

