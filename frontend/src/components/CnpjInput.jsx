import React, { forwardRef, useState, useCallback } from 'react'
import { formatCnpj } from '../utils/cnpj'

const CnpjInput = forwardRef(function CnpjInput(
  { value = '', onChange, error, className = '', ...rest },
  ref
) {
  const [touched, setTouched] = useState(false)

  const handleChange = useCallback(
    (e) => {
      const raw = e.target.value.replace(/\D/g, '').slice(0, 14)
      const formatted = formatCnpj(raw)
      if (onChange) {
        onChange(formatted)
      }
    },
    [onChange]
  )

  const handleBlur = useCallback(() => {
    setTouched(true)
  }, [])

  const showError = touched && error
  const inputClass = [
    'cnpj-input',
    showError ? 'cnpj-input--error' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <input
      ref={ref}
      type="text"
      inputMode="numeric"
      className={inputClass}
      placeholder="00.000.000/0000-00"
      value={value}
      onChange={handleChange}
      onBlur={handleBlur}
      maxLength={18}
      autoComplete="off"
      aria-label="CNPJ"
      aria-invalid={showError ? 'true' : 'false'}
      {...rest}
    />
  )
})

export default CnpjInput
