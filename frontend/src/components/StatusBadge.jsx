import React from 'react'

export default function StatusBadge({
  variant = 'info',
  children,
  className = '',
  ...rest
}) {
  const classes = ['status-badge', `status-badge--${variant}`, className]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={classes} {...rest}>
      {children}
    </span>
  )
}
