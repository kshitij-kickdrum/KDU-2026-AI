import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { ApproveResponse, Currency, HoldingModel, RunResponse } from '../../api/types'
import { DEFAULT_CURRENCY, DEFAULT_HOLDING_ROW } from '../../shared/constants/defaults'

export type AppPage = 'run-agent' | 'trade-approval' | 'session-history'

export interface RunDraft {
  symbol: string
  currency: Currency
  prompt: string
  portfolio: HoldingModel[]
}

export interface UiState {
  currentPage: AppPage
  runDraft: RunDraft
  activeThreadId: string
  lastRunResponse: RunResponse | null
  lastApproveResponse: ApproveResponse | null
  sessionHistorySearch: string
}

const createRunDraft = (): RunDraft => ({
  symbol: '',
  currency: DEFAULT_CURRENCY,
  prompt: '',
  portfolio: [{ ...DEFAULT_HOLDING_ROW }],
})

const initialState: UiState = {
  currentPage: 'run-agent',
  runDraft: createRunDraft(),
  activeThreadId: '',
  lastRunResponse: null,
  lastApproveResponse: null,
  sessionHistorySearch: '',
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    navigateTo: (state, action: PayloadAction<AppPage>) => {
      state.currentPage = action.payload
    },
    setRunDraftField: (
      state,
      action: PayloadAction<{ field: 'symbol' | 'currency' | 'prompt'; value: string }>,
    ) => {
      const { field, value } = action.payload
      if (field === 'currency') {
        state.runDraft.currency = value as Currency
      } else {
        state.runDraft[field] = value
      }
    },
    addPortfolioRow: (state) => {
      state.runDraft.portfolio.push({ ...DEFAULT_HOLDING_ROW })
    },
    removePortfolioRow: (state, action: PayloadAction<number>) => {
      if (state.runDraft.portfolio.length === 1) {
        state.runDraft.portfolio = [{ ...DEFAULT_HOLDING_ROW }]
        return
      }
      state.runDraft.portfolio = state.runDraft.portfolio.filter(
        (_, i) => i !== action.payload,
      )
    },
    setPortfolioField: (
      state,
      action: PayloadAction<{ index: number; field: keyof HoldingModel; value: string | number }>,
    ) => {
      const { index, field, value } = action.payload
      const row = state.runDraft.portfolio[index]
      if (!row) return
      if (field === 'quantity' || field === 'avg_buy_price') {
        row[field] = Number(value)
      } else {
        row[field] = String(value)
      }
    },
    setActiveThreadId: (state, action: PayloadAction<string>) => {
      state.activeThreadId = action.payload
    },
    setLastRunResponse: (state, action: PayloadAction<RunResponse | null>) => {
      state.lastRunResponse = action.payload
      state.lastApproveResponse = null
      if (action.payload?.thread_id) {
        state.activeThreadId = action.payload.thread_id
      }
      // Auto-navigate to approval page if trade is pending
      if (action.payload?.status === 'awaiting_approval') {
        state.currentPage = 'trade-approval'
      }
    },
    setLastApproveResponse: (state, action: PayloadAction<ApproveResponse | null>) => {
      state.lastApproveResponse = action.payload
      if (!action.payload) {
        return
      }

      if (action.payload.portfolio && action.payload.portfolio.length > 0) {
        state.runDraft.portfolio = action.payload.portfolio.map((holding) => ({
          symbol: holding.symbol,
          quantity: Number(holding.quantity),
          avg_buy_price: Number(holding.avg_buy_price),
        }))
      }

      if (action.payload.currency) {
        state.runDraft.currency = action.payload.currency
      }

      if (state.lastRunResponse) {
        state.lastRunResponse = {
          ...state.lastRunResponse,
          status: 'completed',
          trade_log: action.payload.trade_log,
          portfolio_total_usd:
            action.payload.portfolio_total_usd ?? state.lastRunResponse.portfolio_total_usd,
          portfolio_total_converted:
            action.payload.portfolio_total_converted ?? state.lastRunResponse.portfolio_total_converted,
          currency: action.payload.currency ?? state.lastRunResponse.currency,
        }
      }
    },
    setSessionHistorySearch: (state, action: PayloadAction<string>) => {
      state.sessionHistorySearch = action.payload
    },
    resetRun: (state) => {
      state.runDraft = createRunDraft()
      state.activeThreadId = ''
      state.lastRunResponse = null
      state.lastApproveResponse = null
      state.currentPage = 'run-agent'
    },
  },
})

export const {
  navigateTo,
  setRunDraftField,
  addPortfolioRow,
  removePortfolioRow,
  setPortfolioField,
  setActiveThreadId,
  setLastRunResponse,
  setLastApproveResponse,
  setSessionHistorySearch,
  resetRun,
} = uiSlice.actions

export const uiReducer = uiSlice.reducer
