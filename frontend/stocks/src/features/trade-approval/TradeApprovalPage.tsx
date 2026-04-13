import { useState } from 'react'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser'
import CancelIcon from '@mui/icons-material/Cancel'
import { useApproveTradeMutation, useGetThreadStateQuery } from '../../api/api'
import { useAppDispatch, useAppSelector } from '../../store/hooks'
import { selectActiveThreadId, selectLastRunResponse } from '../../store/selectors'
import { setLastApproveResponse, navigateTo } from '../../store/slices/uiSlice'
import styles from './TradeApprovalPage.module.scss'

type TraceLine = {
  step: string
  tag: '[AI]' | '[TOOL]' | '[TOOL_DECISION]' | '[EVENT]'
  tagColor: 'cyan' | 'green' | 'blue'
  text: string
}

type GraphNodeKey =
  | 'portfolio_node'
  | 'inr_convert_node'
  | 'eur_convert_node'
  | 'tool_decision_node'
  | 'fetch_price_node'
  | 'buy_decision_node'
  | 'human_approval_node'
  | 'execute_trade_node'
  | 'END'

type GraphState = 'executed' | 'pending' | 'skipped'

type GraphNode = {
  key: GraphNodeKey
  label: string
  description: string
  state: GraphState
}

type GraphEdge = {
  from: GraphNodeKey
  to: GraphNodeKey
  label: string
  state: GraphState
}

export const TradeApprovalPage = () => {
  const dispatch = useAppDispatch()
  const threadId = useAppSelector(selectActiveThreadId)
  const lastRun = useAppSelector(selectLastRunResponse)
  const [approveTrade, { isLoading }] = useApproveTradeMutation()
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<'approved' | 'rejected' | null>(null)

  const { data: threadState } = useGetThreadStateQuery(threadId, {
    skip: !threadId,
    pollingInterval: 2000,
  })

  const state = threadState?.state
  const rawMessages = state?.messages
  const messages = Array.isArray(rawMessages) ? rawMessages : []

  const traceLines: TraceLine[] = messages.slice(-8).map((message, index) => {
    const m = message as {
      type?: string
      content?: unknown
      tool_calls?: Array<{ name?: string }>
      name?: string
    }
    const hasToolCalls = Array.isArray(m.tool_calls) && m.tool_calls.length > 0
    const contentText = typeof m.content === 'string' ? m.content.trim() : ''

    if (m.type === 'tool') {
      return {
        step: `STEP ${String(index + 1).padStart(2, '0')}`,
        tag: '[TOOL]',
        tagColor: 'green',
        text: contentText || `Tool response from ${m.name ?? 'unknown tool'}`,
      }
    }

    if (hasToolCalls) {
      const calledTools = m.tool_calls
        .map((toolCall) => toolCall.name)
        .filter((name): name is string => Boolean(name))
        .join(', ')
      return {
        step: `STEP ${String(index + 1).padStart(2, '0')}`,
        tag: '[TOOL_DECISION]',
        tagColor: 'blue',
        text: calledTools ? `Model requested: ${calledTools}` : 'Model requested a tool call',
      }
    }

    return {
      step: `STEP ${String(index + 1).padStart(2, '0')}`,
      tag: '[AI]',
      tagColor: 'cyan',
      text: contentText || 'Agent updated decision state',
    }
  })

  if (traceLines.length === 0) {
    traceLines.push({
      step: 'STEP 01',
      tag: '[EVENT]',
      tagColor: 'blue',
      text: 'No execution trace lines available yet for this session.',
    })
  }

  const hasToolResponse = messages.some((message) => {
    const m = message as { type?: string }
    return m.type === 'tool'
  })

  const pendingAction = (state?.pending_action ?? lastRun?.pending_action ?? 'buy') as 'buy' | 'sell'
  const hasPendingTrade = pendingAction === 'buy' || pendingAction === 'sell'
  const actionApproved = Boolean(state?.action_approved)
  const tradeExecuted = Array.isArray(state?.trade_log) && state.trade_log.length > 0
  const isAwaitingApproval = threadState?.status === 'awaiting_approval' || (hasPendingTrade && !actionApproved)

  const selectedCurrency = state?.currency ?? lastRun?.currency ?? 'USD'

  const graphNodes: GraphNode[] = [
    {
      key: 'portfolio_node',
      label: 'portfolio_node',
      description: 'Calculates portfolio total in USD.',
      state: 'executed',
    },
    {
      key: 'inr_convert_node',
      label: 'inr_convert_node',
      description: 'Converts USD total to INR.',
      state: selectedCurrency === 'INR' ? 'executed' : 'skipped',
    },
    {
      key: 'eur_convert_node',
      label: 'eur_convert_node',
      description: 'Converts USD total to EUR.',
      state: selectedCurrency === 'EUR' ? 'executed' : 'skipped',
    },
    {
      key: 'tool_decision_node',
      label: 'tool_decision_node',
      description: 'LLM decides whether to call stock-price tool.',
      state: 'executed',
    },
    {
      key: 'fetch_price_node',
      label: 'fetch_price_node',
      description: 'Calls fetch_stock_price tool when requested.',
      state: hasToolResponse ? 'executed' : 'skipped',
    },
    {
      key: 'buy_decision_node',
      label: 'buy_decision_node',
      description: 'LLM produces BUY or SELL recommendation.',
      state: hasPendingTrade ? 'executed' : 'skipped',
    },
    {
      key: 'human_approval_node',
      label: 'human_approval_node',
      description: 'Waits for operator approval to continue.',
      state: hasPendingTrade ? (isAwaitingApproval ? 'pending' : 'executed') : 'skipped',
    },
    {
      key: 'execute_trade_node',
      label: 'execute_trade_node',
      description: 'Executes approved trade and writes trade log.',
      state: tradeExecuted || actionApproved ? 'executed' : 'skipped',
    },
    {
      key: 'END',
      label: 'END',
      description: 'Graph reaches terminal state.',
      state: tradeExecuted || actionApproved ? 'executed' : 'pending',
    },
  ]

  const graphEdges: GraphEdge[] = [
    {
      from: 'portfolio_node',
      to: 'inr_convert_node',
      label: 'currency == INR',
      state: selectedCurrency === 'INR' ? 'executed' : 'skipped',
    },
    {
      from: 'portfolio_node',
      to: 'eur_convert_node',
      label: 'currency == EUR',
      state: selectedCurrency === 'EUR' ? 'executed' : 'skipped',
    },
    {
      from: 'portfolio_node',
      to: 'tool_decision_node',
      label: 'currency == USD',
      state: selectedCurrency === 'USD' ? 'executed' : 'skipped',
    },
    {
      from: 'inr_convert_node',
      to: 'tool_decision_node',
      label: 'after INR conversion',
      state: selectedCurrency === 'INR' ? 'executed' : 'skipped',
    },
    {
      from: 'eur_convert_node',
      to: 'tool_decision_node',
      label: 'after EUR conversion',
      state: selectedCurrency === 'EUR' ? 'executed' : 'skipped',
    },
    {
      from: 'tool_decision_node',
      to: 'fetch_price_node',
      label: 'tool requested',
      state: hasToolResponse ? 'executed' : 'skipped',
    },
    {
      from: 'tool_decision_node',
      to: 'buy_decision_node',
      label: 'no tool requested',
      state: hasToolResponse ? 'skipped' : 'executed',
    },
    {
      from: 'fetch_price_node',
      to: 'buy_decision_node',
      label: 'after tool result',
      state: hasToolResponse ? 'executed' : 'skipped',
    },
    {
      from: 'buy_decision_node',
      to: 'human_approval_node',
      label: 'pending_action in {buy,sell}',
      state: hasPendingTrade ? (isAwaitingApproval ? 'pending' : 'executed') : 'skipped',
    },
    {
      from: 'human_approval_node',
      to: 'execute_trade_node',
      label: 'approved',
      state: actionApproved || tradeExecuted ? 'executed' : 'pending',
    },
    {
      from: 'execute_trade_node',
      to: 'END',
      label: 'trade logged',
      state: tradeExecuted ? 'executed' : 'pending',
    },
  ]

  const isBuy = pendingAction === 'buy'

  const handleDecision = async (approved: boolean) => {
    setError(null)
    try {
      const res = await approveTrade({ thread_id: threadId, approved }).unwrap()
      dispatch(setLastApproveResponse(res))
      setResult(approved ? 'approved' : 'rejected')
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'data' in err
        ? (err as { data?: { message?: string } }).data?.message ?? 'Action failed.'
        : 'Action failed.'
      setError(msg)
    }
  }

  if (result) {
    return (
      <div className={styles.page}>
        <div className={styles.resultScreen}>
          <div className={`${styles.resultIcon} ${result === 'approved' ? styles.approved : styles.rejected}`}>
            {result === 'approved' ? <VerifiedUserIcon sx={{ fontSize: 48 }} /> : <CancelIcon sx={{ fontSize: 48 }} />}
          </div>
          <h2 className={styles.resultTitle}>
            {result === 'approved' ? 'Trade Executed' : 'Trade Cancelled'}
          </h2>
          <p className={styles.resultSub}>
            {result === 'approved'
              ? 'Your trade has been logged successfully.'
              : 'The trade was rejected. No action was taken.'}
          </p>
          <button className={styles.backBtn} onClick={() => dispatch(navigateTo('run-agent'))}>
            Start New Run
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      {/* Status banner */}
      <div className={styles.statusBanner}>
        <div className={styles.bannerLeft}>
          <span className={styles.pulseDot} />
          <span className={styles.bannerStatus}>Status: Pending Verification</span>
        </div>
        <div className={styles.bannerRight}>
          Session: {threadId ? threadId.slice(0, 18) + '...' : '—'}
        </div>
      </div>

      <div className={styles.grid}>
        {/* Recommendation card */}
        <div className={styles.recommendationCard}>
          <div className={styles.recHeader}>
            <div>
              <h1 className={styles.recTitle}>The agent recommends:</h1>
              <div className={styles.recAction}>
                {pendingAction.toUpperCase()} {lastRun?.pending_action ? '' : '—'}
              </div>
            </div>
            <div className={styles.recIcon}>
              {isBuy
                ? <TrendingUpIcon sx={{ fontSize: 48, color: 'var(--tertiary)' }} />
                : <TrendingDownIcon sx={{ fontSize: 48, color: 'var(--error)' }} />}
            </div>
          </div>

          {/* AI reasoning terminal */}
          <div className={styles.terminal}>
            <div className={styles.terminalBar}>
              <div className={styles.terminalDots}>
                <span className={styles.dot} style={{ background: 'rgba(255,180,171,0.5)' }} />
                <span className={styles.dot} style={{ background: 'rgba(0,253,155,0.5)' }} />
                <span className={styles.dot} style={{ background: 'rgba(165,231,255,0.5)' }} />
              </div>
              <span className={styles.terminalLabel}>Agent execution trace</span>
            </div>
            <div className={styles.terminalBody}>
              {traceLines.map((line) => (
                <div key={`${line.step}-${line.tag}-${line.text}`} className={styles.logLine}>
                  <span className={styles.logTime}>{line.step}</span>
                  <span className={`${styles.logTag} ${styles[line.tagColor]}`}>{line.tag}</span>
                  <span className={styles.logText}>{line.text}</span>
                </div>
              ))}
              {threadState?.status === 'awaiting_approval' && (
                <div className={`${styles.logLine} ${styles.blinking}`}>
                  <span className={styles.logTime}>PENDING</span>
                  <span className={styles.logTag}>_</span>
                  <span className={styles.logText}>Awaiting operator authorization...</span>
                </div>
              )}
            </div>
          </div>

          <div className={styles.graphPanel}>
            <div className={styles.graphHeader}>
              <h3 className={styles.graphTitle}>LangGraph Execution Map</h3>
              <p className={styles.graphSub}>Full node and edge traversal for this run.</p>
            </div>

            <div className={styles.graphColumns}>
              <div className={styles.graphColumn}>
                <span className={styles.graphLabel}>Nodes</span>
                <div className={styles.graphList}>
                  {graphNodes.map((node) => (
                    <div key={node.key} className={`${styles.graphItem} ${styles[node.state]}`}>
                      <div className={styles.graphItemTop}>
                        <span className={styles.graphItemName}>{node.label}</span>
                        <span className={styles.graphBadge}>{node.state.toUpperCase()}</span>
                      </div>
                      <p className={styles.graphItemDesc}>{node.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.graphColumn}>
                <span className={styles.graphLabel}>Edges</span>
                <div className={styles.graphList}>
                  {graphEdges.map((edge) => (
                    <div key={`${edge.from}-${edge.to}-${edge.label}`} className={`${styles.graphItem} ${styles[edge.state]}`}>
                      <div className={styles.graphItemTop}>
                        <span className={styles.graphItemName}>{edge.from} -&gt; {edge.to}</span>
                        <span className={styles.graphBadge}>{edge.state.toUpperCase()}</span>
                      </div>
                      <p className={styles.graphItemDesc}>{edge.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action panel */}
        <div className={styles.actionPanel}>
          <div>
            <h3 className={styles.actionTitle}>Execution Authorization</h3>
            <p className={styles.actionDesc}>
              Review the agent's recommendation and authorize or reject the trade.
            </p>
          </div>

          <div className={styles.summaryGrid}>
            <div className={styles.summaryItem}>
              <span className={styles.summaryLabel}>Portfolio (USD)</span>
              <span className={styles.summaryValue}>
                ${Number(state?.portfolio_total_usd ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            {typeof state?.portfolio_total_converted === 'number' && (
              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Portfolio (Preferred)</span>
                <span className={styles.summaryValue}>
                  {Number(state.portfolio_total_converted).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
            )}
            {typeof state?.exchange_rate === 'number' && (
              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Exchange Rate</span>
                <span className={styles.summaryValue}>{state.exchange_rate.toFixed(4)}</span>
              </div>
            )}
          </div>

          {error && <div className={styles.errorBanner}>{error}</div>}

          <div className={styles.actionBtns}>
            <button
              className={styles.approveBtn}
              onClick={() => handleDecision(true)}
              disabled={isLoading}
            >
              <VerifiedUserIcon fontSize="small" />
              Approve Trade
            </button>
            <button
              className={styles.rejectBtn}
              onClick={() => handleDecision(false)}
              disabled={isLoading}
            >
              <CancelIcon fontSize="small" />
              Reject Trade
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
