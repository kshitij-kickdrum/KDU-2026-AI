import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import DeleteIcon from '@mui/icons-material/Delete'
import type { HoldingModel } from '../../../api/types'
import styles from './PortfolioHoldings.module.scss'

interface Props {
  rows: HoldingModel[]
  disabled: boolean
  onAdd: () => void
  onRemove: (index: number) => void
  onChange: (index: number, field: keyof HoldingModel, value: string | number) => void
}

export const PortfolioHoldings = ({ rows, disabled, onAdd, onRemove, onChange }: Props) => (
  <div className={styles.wrapper}>
    <div className={styles.header}>
      <span className={styles.title}>
        <span className={styles.titleIcon}>◈</span>
        {' '}Portfolio Holdings
      </span>
      <button className={styles.addBtn} onClick={onAdd} disabled={disabled}>
        <AddCircleOutlineIcon sx={{ fontSize: 14 }} />
        Add Holding
      </button>
    </div>

    <div className={styles.list}>
      {rows.map((row, i) => (
        <div key={i} className={styles.row}>
          <div className={styles.symbolCol}>
            <span className={styles.colLabel}>Symbol</span>
            <input
              className={styles.input}
              value={row.symbol}
              placeholder="Enter symbol"
              disabled={disabled}
              onChange={(e) => onChange(i, 'symbol', e.target.value.toUpperCase())}
            />
          </div>
          <div className={styles.numCol}>
            <span className={styles.colLabel}>Quantity</span>
            <input
              className={styles.input}
              type="number"
              value={row.quantity === 0 ? '' : row.quantity}
              min={0}
              disabled={disabled}
              onFocus={(e) => e.currentTarget.select()}
              onChange={(e) => onChange(i, 'quantity', e.target.value)}
            />
          </div>
          <div className={styles.numCol}>
            <span className={styles.colLabel}>Avg Buy Price (cost/share)</span>
            <input
              className={styles.input}
              type="number"
              value={row.avg_buy_price === 0 ? '' : row.avg_buy_price}
              min={0}
              disabled={disabled}
              onFocus={(e) => e.currentTarget.select()}
              onChange={(e) => onChange(i, 'avg_buy_price', e.target.value)}
            />
          </div>
          <button
            className={styles.deleteBtn}
            onClick={() => onRemove(i)}
            disabled={disabled}
          >
            <DeleteIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
      ))}

      {/* Add row placeholder */}
      <button className={styles.addRowPlaceholder} onClick={onAdd} disabled={disabled}>
        <AddCircleOutlineIcon sx={{ fontSize: 16 }} />
        Click to add new holding record
      </button>
    </div>
  </div>
)
