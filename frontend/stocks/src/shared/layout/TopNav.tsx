import SensorsIcon from '@mui/icons-material/Sensors'
import { IconButton } from '@mui/material'
import styles from './TopNav.module.scss'

interface TopNavProps {
  activePage: 'run-agent' | 'trade-approval' | 'session-history'
  onNavigate: (page: 'run-agent' | 'trade-approval' | 'session-history') => void
}

export const TopNav = ({ activePage, onNavigate }: TopNavProps) => (
  <nav className={styles.nav}>
    <div className={styles.left}>
      <span className={styles.logo}>Stock Trading Agent</span>
      <div className={styles.links}>
        <button
          className={`${styles.link} ${activePage === 'run-agent' ? styles.active : ''}`}
          onClick={() => onNavigate('run-agent')}
        >
          Run Agent
        </button>
        <button
          className={`${styles.link} ${activePage === 'trade-approval' ? styles.active : ''}`}
          onClick={() => onNavigate('trade-approval')}
        >
          Trade Approval
        </button>
        <button
          className={`${styles.link} ${activePage === 'session-history' ? styles.active : ''}`}
          onClick={() => onNavigate('session-history')}
        >
          Session History
        </button>
      </div>
    </div>
    <div className={styles.right}>
      <IconButton className={styles.iconBtn} size="small">
        <SensorsIcon fontSize="small" />
      </IconButton>
    </div>
  </nav>
)
