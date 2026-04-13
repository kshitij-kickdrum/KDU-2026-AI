import type { Currency, HoldingModel } from '../../api/types'

export const DEFAULT_CURRENCY: Currency = 'USD'

export const DEFAULT_HOLDING_ROW: HoldingModel = {
  symbol: '',
  quantity: 0,
  avg_buy_price: 0,
}

export const LOCAL_STORAGE_DRAFT_KEY = 'stock-trading-ui.run-draft.v1'
