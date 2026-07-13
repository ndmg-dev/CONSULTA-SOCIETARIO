import React from 'react'
import Button from './Button'

export default function EmptyState({
  icon = '📭',
  title = 'Nenhum resultado',
  description = '',
  action,
  className = '',
}) {
  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state__icon" aria-hidden="true">
        {icon}
      </div>
      <h3 className="empty-state__title">{title}</h3>
      {description && (
        <p className="empty-state__description">{description}</p>
      )}
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}
