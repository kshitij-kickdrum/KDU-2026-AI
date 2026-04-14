import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import BoltIcon from '@mui/icons-material/Bolt'
import { useRunAgentMutation } from '../../api/api'
import { useAppDispatch, useAppSelector } from '../../store/hooks'
import {
  selectRunDraft,
  selectLastRunResponse,
} from '../../store/selectors'
import {
  addPortfolioRow,
  removePortfolioRow,
  setPortfolioField,
  setRunDraftField,
  setLastRunResponse,
  setActiveThreadId,
} from '../../store/slices/uiSlice'
import { SessionParameters } from './components/SessionParameters'
import { PortfolioHoldings } from './components/PortfolioHoldings'
import styles from './RunAgentPage.module.scss'

const LOADING_STEPS = [
  'Initializing agent...',
  'Fetching stock price...',
  'Analyzing portfolio...',
  'Making trading decision...',
]

export const RunAgentPage = () => {
  const dispatch = useAppDispatch()
  const draft = useAppSelector(selectRunDraft)
  const lastRun = useAppSelector(selectLastRunResponse)

  const [runAgent, { isLoading }] = useRunAgentMutation()
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!draft.symbol.trim()) {
      setError('Please enter a stock symbol.')
      return
    }

    const portfolio = draft.portfolio.map((h) => ({
      ...h,
      symbol: h.symbol.trim().toUpperCase(),
    }))

    const missingSymbol = portfolio.find((h) => !h.symbol)
    if (missingSymbol) {
      setError('Each holding must include a stock symbol.')
      return
    }

    // Validate all holdings have positive values
    const invalid = portfolio.find((h) => h.quantity <= 0 || h.avg_buy_price <= 0)
    if (invalid) {
      setError('All holdings must have quantity and price greater than 0.')
      return
    }

    setError(null)
    const threadId = uuidv4()
    dispatch(setActiveThreadId(threadId))

    // Animate loading steps
    let step = 0
    const interval = setInterval(() => {
      step = (step + 1) % LOADING_STEPS.length
      setLoadingStep(step)
    }, 900)

    try {
      const result = await runAgent({
        thread_id: threadId,
        portfolio,
        currency: draft.currency,
        symbol: draft.symbol,
        prompt: draft.prompt,
      }).unwrap()

      dispatch(setLastRunResponse(result))
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'data' in err
        ? (err as { data?: { message?: string } }).data?.message ?? 'Agent run failed.'
        : 'Agent run failed.'
      setError(msg)
    } finally {
      clearInterval(interval)
      setLoadingStep(0)
    }
  }

  // Compute portfolio total for display
  const portfolioTotal = draft.portfolio.reduce(
    (sum, h) => sum + h.quantity * h.avg_buy_price,
    0,
  )

  return (
    <div className={styles.page}>
      {/* Hero header */}
      <header className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Initiate <span className={styles.heroAccent}>Strategic Agent</span>
        </h1>
        <p className={styles.heroSubtitle}>
          Deploy an autonomous trading session with high-precision stock monitoring and automated execution.
        </p>
      </header>

      {/* Bento grid */}
      <div className={styles.grid}>
        {/* Left column — config */}
        <section className={styles.configCol}>
          <div className={styles.panel}>
            <SessionParameters
              symbol={draft.symbol}
              currency={draft.currency}
              prompt={draft.prompt}
              disabled={isLoading}
              onSymbolChange={(v) => dispatch(setRunDraftField({ field: 'symbol', value: v }))}
              onCurrencyChange={(v) => dispatch(setRunDraftField({ field: 'currency', value: v }))}
              onPromptChange={(v) => dispatch(setRunDraftField({ field: 'prompt', value: v }))}
            />
          </div>

          {error && <div className={styles.errorBanner}>{error}</div>}

          {/* Completed result inline */}
          {lastRun?.status === 'completed' && (
            <div className={styles.resultCard}>
              <div className={styles.resultLabel}>Run Completed</div>
              <div className={styles.resultTotal}>
                ${(lastRun.portfolio_total_usd ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
              {(!lastRun.trade_log || lastRun.trade_log.length === 0) && (
                <div className={styles.resultLabel}>No trade was executed in this run.</div>
              )}
              {lastRun.trade_log && lastRun.trade_log.length > 0 && (
                <div className={styles.tradeLogList}>
                  {lastRun.trade_log.map((entry) => (
                    <div key={entry} className={styles.tradeLogEntry}>{entry}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            className={styles.runBtn}
            onClick={handleRun}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className={styles.loadingText}>
                <span className={styles.loadingDot} />
                {LOADING_STEPS[loadingStep]}
              </span>
            ) : (
              <>
                <BoltIcon fontSize="small" />
                Run Agent
              </>
            )}
          </button>
        </section>

        {/* Right column — portfolio */}
        <section className={styles.portfolioCol}>
          <div className={styles.panel}>
            <PortfolioHoldings
              rows={draft.portfolio}
              disabled={isLoading}
              onAdd={() => dispatch(addPortfolioRow())}
              onRemove={(i) => dispatch(removePortfolioRow(i))}
              onChange={(i, field, value) =>
                dispatch(setPortfolioField({ index: i, field, value }))
              }
            />

            {/* Portfolio total footer */}
            <div className={styles.portfolioFooter}>
              <div>
                <div className={styles.footerLabel}>Total Position Value</div>
                <div className={styles.footerTotal}>
                  ${portfolioTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className={styles.trendBadge}>
                ↑ Live
              </div>
            </div>
          </div>
        </section>
      </div>

    </div>
  )
}
