import React from 'react'

export default function GlassCard({
  variant = 'default',
  hover = false,
  className = '',
  children,
  ...rest
}) {
  const variantClass =
    variant === 'elevated'
      ? 'glass-card--elevated'
      : variant === 'gold'
        ? 'glass-card--gold'
        : ''

  const hoverClass = hover ? 'glass-card--hover' : ''

  const classes = ['glass-card', variantClass, hoverClass, className]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  )
}
