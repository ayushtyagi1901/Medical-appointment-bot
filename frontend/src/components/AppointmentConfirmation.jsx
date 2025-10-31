import React from 'react'
import './AppointmentConfirmation.css'

function AppointmentConfirmation({ details, onClose }) {
  return (
    <div className="confirmation-overlay" onClick={onClose}>
      <div className="confirmation-card" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        <div className="confirmation-icon">✅</div>
        <h2>Appointment Confirmed!</h2>
        <div className="confirmation-content">
          <p className="confirmation-message">{details.message}</p>
          {details.appointment_id && details.appointment_id !== 'N/A' && (
            <div className="appointment-id">
              <strong>Appointment ID:</strong> {details.appointment_id}
            </div>
          )}
        </div>
        <div className="confirmation-footer">
          <p>You will receive a confirmation email shortly.</p>
          <button className="ok-button" onClick={onClose}>OK</button>
        </div>
      </div>
    </div>
  )
}

export default AppointmentConfirmation

