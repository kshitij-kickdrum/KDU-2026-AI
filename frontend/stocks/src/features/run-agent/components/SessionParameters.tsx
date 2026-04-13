import { useState, useRef, useEffect } from 'react'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import SearchIcon from '@mui/icons-material/Search'
import { useLazySearchSymbolsQuery } from '../../../api/api'
import type { Currency } from '../../../api/types'
import styles from './SessionParameters.module.scss'

interface Props {
  symbol: string
  currency: Currency
  prompt: string
  disabled: boolean
  onSymbolChange: (v: string) => void
  onCurrencyChange: (v: Currency) => void
  onPromptChange: (v: string) => void
}

export const SessionParameters = ({
  symbol,
  currency,
  prompt,
  disabled,
  onSymbolChange,
  onCurrencyChange,
  onPromptChange,
}: Props) => {
  const [query, setQuery] = useState(symbol)
  const [open, setOpen] = useState(false)
  const [searchSymbols, { data, isFetching }] = useLazySearchSymbolsQuery()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Sync query when symbol changes externally
  useEffect(() => { setQuery(symbol) }, [symbol])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleQueryChange = (v: string) => {
    setQuery(v)
    onSymbolChange(v.toUpperCase())
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (v.trim().length >= 1) {
      debounceRef.current = setTimeout(() => {
        searchSymbols(v.trim())
        setOpen(true)
      }, 350)
    } else {
      setOpen(false)
    }
  }

  const handleSelect = (sym: string) => {
    setQuery(sym)
    onSymbolChange(sym)
    setOpen(false)
  }

  const formatPrice = (price?: number | null) => {
    if (price == null || Number.isNaN(price)) return null
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price)
  }

  const results = data?.result ?? []
  const selectedResult = results.find((r) => r.symbol === symbol || r.symbol === query.toUpperCase())
  const selectedPriceLabel = formatPrice(selectedResult?.price)

  return (
    <div className={styles.wrapper}>
      <h2 className={styles.sectionTitle}>
        <span className={styles.sectionIcon}>⚙</span>
        {' '}Session Parameters
      </h2>

      <div className={styles.fields}>
        {/* Currency */}
        <div className={styles.field}>
          <label className={styles.label} htmlFor="execution-currency">Execution Currency</label>
          <div className={styles.selectWrapper}>
            <select
              id="execution-currency"
              className={styles.select}
              value={currency}
              disabled={disabled}
              onChange={(e) => onCurrencyChange(e.target.value as Currency)}
            >
              <option value="USD">USD — United States Dollar</option>
              <option value="INR">INR — Indian Rupee</option>
              <option value="EUR">EUR — Euro</option>
            </select>
            <ExpandMoreIcon className={styles.selectIcon} fontSize="small" />
          </div>
        </div>

        {/* Strategy prompt */}
        <div className={styles.field}>
          <label className={styles.label} htmlFor="strategy-prompt">User Prompt</label>
          <input
            id="strategy-prompt"
            className={styles.input}
            value={prompt}
            placeholder="Optional: e.g. Favor momentum over mean reversion"
            disabled={disabled}
            onChange={(e) => onPromptChange(e.target.value)}
          />
        </div>

        {/* Symbol search */}
        <div className={styles.field} ref={wrapperRef}>
          <label className={styles.label} htmlFor="primary-ticker">Primary Ticker</label>
          <div className={styles.inputWrapper}>
            <SearchIcon className={styles.searchIcon} fontSize="small" />
            <input
              id="primary-ticker"
              className={styles.input}
              value={query}
              placeholder="Search symbol (e.g. AAPL)"
              disabled={disabled}
              onChange={(e) => handleQueryChange(e.target.value)}
              onFocus={() => query.length >= 1 && results.length > 0 && setOpen(true)}
              autoComplete="off"
            />
            {isFetching && <span className={styles.spinner} />}
            {!isFetching && symbol && (
              <div className={styles.priceIndicator}>
                <span className={styles.priceLabel}>{selectedPriceLabel ?? 'N/A'}</span>
              </div>
            )}
          </div>

          {/* Dropdown */}
          {open && results.length > 0 && (
            <div className={styles.dropdown}>
              {results.map((r) => (
                <button
                  key={r.symbol}
                  className={styles.dropdownItem}
                  onMouseDown={() => handleSelect(r.symbol)}
                >
                  <span className={styles.dropdownSymbol}>{r.symbol}</span>
                  <span className={styles.dropdownDesc}>{r.description}</span>
                  <span className={styles.dropdownPrice}>{formatPrice(r.price) ?? 'N/A'}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
