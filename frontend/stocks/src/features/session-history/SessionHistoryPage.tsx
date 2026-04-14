import { useState } from 'react'
import SearchIcon from '@mui/icons-material/Search'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos'
import { useGetSessionsQuery, useLazyGetSessionStateQuery } from '../../api/api'
import { useAppDispatch, useAppSelector } from '../../store/hooks'
import { selectSessionHistorySearch } from '../../store/selectors'
import { setSessionHistorySearch } from '../../store/slices/uiSlice'
import styles from './SessionHistoryPage.module.scss'

const STATUS_LABELS: Record<string, string> = {
  completed: 'Completed',
  awaiting_approval: 'Awaiting Approval',
  in_progress: 'In Progress',
}

const STATUS_STYLE: Record<string, string> = {
  completed: 'statusCompleted',
  awaiting_approval: 'statusPending',
  in_progress: 'statusInProgress',
}

const formatMessageContent = (content: unknown): string => {
  const formatObject = (value: Record<string, unknown>): string => {
    if (typeof value.price === 'number') {
      return `Price fetched: $${value.price.toFixed(2)}`
    }
    if (typeof value.text === 'string' && value.text.trim()) {
      return value.text
    }
    return JSON.stringify(value)
  }

  if (typeof content === 'string') {
    const raw = content.trim()
    if (!raw) return ''

    try {
      const parsed = JSON.parse(raw) as unknown
      if (parsed && typeof parsed === 'object') {
        return formatObject(parsed as Record<string, unknown>)
      }
    } catch {
      // Not JSON, keep as plain text.
    }
    return raw
  }

  if (content && typeof content === 'object') {
    return formatObject(content as Record<string, unknown>)
  }

  return String(content ?? '')
}

export const SessionHistoryPage = () => {
  const dispatch = useAppDispatch()
  const search = useAppSelector(selectSessionHistorySearch)
  const { data: sessionsData } = useGetSessionsQuery(20)
  const [fetchState, { data, isFetching, error }] = useLazyGetSessionStateQuery()
  const [searched, setSearched] = useState(false)
  const [lookedUpSessionRef, setLookedUpSessionRef] = useState('')

  const handleLookUp = async () => {
    const sessionRef = search.trim()
    if (!sessionRef) return
    setLookedUpSessionRef(sessionRef)
    setSearched(true)
    await fetchState(sessionRef)
  }

  const handleSelectRecent = async (sessionRef: string) => {
    dispatch(setSessionHistorySearch(sessionRef))
    setLookedUpSessionRef(sessionRef)
    setSearched(true)
    await fetchState(sessionRef)
  }

  const session = data
  const recentSessions = sessionsData?.sessions ?? []

  const messages = Array.isArray(session?.state.messages) ? session?.state.messages : []

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Session History</h1>
        <p className={styles.subtitle}>Retrieve and analyze high-precision execution logs.</p>
      </header>

      {/* Search */}
      <section className={styles.searchSection}>
        <div className={styles.searchBar}>
          <SearchIcon className={styles.searchIcon} fontSize="small" />
          <input
            className={styles.searchInput}
            placeholder="Search Session Ref (e.g. 9f3a1c0d6b2e)"
            value={search}
            onChange={(e) => dispatch(setSessionHistorySearch(e.target.value))}
            onKeyDown={(e) => e.key === 'Enter' && handleLookUp()}
          />
          <button className={styles.lookUpBtn} onClick={handleLookUp} disabled={isFetching}>
            {isFetching ? 'Looking up...' : 'Look Up'}
          </button>
        </div>
      </section>

      {/* Results */}
      <div className={styles.resultsGrid}>
        <div className={styles.resultsWrap}>
          {isFetching && (
            <div className={styles.notFound}>
              <span>Looking up session...</span>
              <p>Fetching latest state for {lookedUpSessionRef}.</p>
            </div>
          )}

          {!isFetching && error && searched && (
            <div className={styles.notFound}>
              <span>Session not found.</span>
              <p>Check the session reference and try again.</p>
            </div>
          )}

          {!isFetching && !error && session && (
            <div className={styles.resultCard}>
                <div className={styles.resultCardTop}>
                  <div>
                    <div className={styles.activeLabel}>
                      <span className={styles.activeDot} />
                      {' '}Session State
                    </div>
                    <h2 className={styles.sessionId}>Session Ref {'#'}{session.session_ref}</h2>
                  </div>
                  <div className={`${styles.statusBadge} ${styles[STATUS_STYLE[session.status] ?? 'statusCompleted']}`}>
                    <CheckCircleIcon sx={{ fontSize: 14 }} />
                    {STATUS_LABELS[session.status] ?? session.status}
                  </div>
                </div>

                {/* Financial summary */}
                <div className={styles.financialGrid}>
                  <div className={styles.financialCard}>
                    <span className={styles.financialLabel}>Portfolio Total (USD)</span>
                    <div className={styles.financialValue}>
                      ${(session.state.portfolio_total_usd ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  {session.state.portfolio_total_converted != null && (
                    <div className={styles.financialCard}>
                      <span className={styles.financialLabel}>
                        Currency Conversion ({session.state.currency})
                      </span>
                      <div className={styles.financialValue}>
                        {session.state.currency === 'INR' ? '₹' : '€'}
                        {(session.state.portfolio_total_converted).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        <span className={styles.rateLabel}>
                          Rate: {session.state.exchange_rate?.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Conversation messages */}
                {messages.length > 0 && (
                  <div className={styles.tradeLog}>
                    <h3 className={styles.tradeLogTitle}>Conversation Messages</h3>
                    <div className={styles.timeline}>
                      {messages.slice(-10).map((rawMessage, i) => {
                        const message = rawMessage as { type?: string; content?: unknown }
                        const content = formatMessageContent(message.content)
                        const type = message.type ?? 'event'
                        const isHuman = type === 'human'
                        return (
                          <div key={`${type}-${i}`} className={styles.timelineItem}>
                            <div className={`${styles.timelineDot} ${isHuman ? styles.dotBlue : styles.dotGreen}`} />
                            <div className={styles.timelineContent}>
                              <p className={styles.timelineAction}>{content || `${type.toUpperCase()} message`}</p>
                              <span className={styles.timelineTime}>{type.toUpperCase()}</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Trade log timeline */}
                {session.state.trade_log && session.state.trade_log.length > 0 && (
                  <div className={styles.tradeLog}>
                    <h3 className={styles.tradeLogTitle}>Trade Execution Log</h3>
                    <div className={styles.timeline}>
                      {session.state.trade_log.map((entry, i) => {
                        const isBuy = entry.toLowerCase().includes('buy')
                        return (
                          <div key={`${entry}-${i}`} className={styles.timelineItem}>
                            <div className={`${styles.timelineDot} ${isBuy ? styles.dotGreen : styles.dotRed}`} />
                            <div className={styles.timelineContent}>
                              <p className={styles.timelineAction}>{entry.split(' - ')[1] ?? entry}</p>
                              <span className={styles.timelineTime}>
                                {entry.split('T')[1]?.slice(0, 8) ?? ''}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {(!session.state.trade_log || session.state.trade_log.length === 0) && (
                  <div className={styles.noTradeLog}>No trade entries recorded for this session yet.</div>
                )}

                {session.state.error && (
                  <div className={styles.errorNote}>Error: {session.state.error}</div>
                )}
              </div>
            )}

          {!isFetching && !error && searched && !session && (
            <div className={styles.notFound}>
              <span>No session data found.</span>
              <p>Try another session reference.</p>
            </div>
          )}

          {!isFetching && !searched && !session && (
            <div className={styles.notFound}>
              <span>Select a recent session.</span>
              <p>Pick one from the right panel or search by session reference.</p>
            </div>
          )}
        </div>

        <div className={styles.sidebar}>
          <h3 className={styles.sidebarTitle}>Recent Sessions</h3>
          {recentSessions.length === 0 && (
            <div className={styles.notFound}>
              <span>No sessions yet.</span>
              <p>Run the agent to create session history.</p>
            </div>
          )}
          {recentSessions.map((row) => (
            <button
              key={row.session_ref}
              className={styles.historyCard}
              onClick={() => handleSelectRecent(row.session_ref)}
            >
              <div className={styles.historyCardTop}>
                <span className={styles.historyId}>#{row.session_ref}</span>
                <span className={`${styles.historyStatus} ${styles[STATUS_STYLE[row.status] ?? 'statusCompleted']}`}>
                  {STATUS_LABELS[row.status] ?? row.status}
                </span>
              </div>
              <div className={styles.historyCardBottom}>
                <div>
                  <div className={styles.historyValue}>
                    ${(row.portfolio_total_usd ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                  <div className={styles.historyDate}>
                    {new Date(row.updated_at).toLocaleString()}
                  </div>
                </div>
                <ArrowForwardIosIcon sx={{ fontSize: 14, color: 'var(--outline)' }} />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
