export const formatCurrency = (
  value: number | null | undefined,
  currencyCode: string = 'USD',
): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value)
}

export const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--'
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 }).format(
    value,
  )
}

export const toTitleCase = (value: string): string =>
  value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
