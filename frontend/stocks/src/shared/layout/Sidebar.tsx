import MonitoringIcon from '@mui/icons-material/MonitorHeart'
import styles from './Sidebar.module.scss'

interface SidebarProps {
  onNewTrade: () => void
}

const NAV_ITEMS = [
  { icon: <MonitoringIcon fontSize="small" />, label: 'Analytics', active: true },
]

export const Sidebar = ({ onNewTrade }: SidebarProps) => (
  <aside className={styles.sidebar}>
    <div className={styles.profile}>
      <div className={styles.avatar}>AT</div>
      <div>
        <div className={styles.name}>Alpha Trader</div>
        <div className={styles.role}>Pro Account</div>
      </div>
    </div>

    <nav className={styles.nav}>
      {NAV_ITEMS.map((item) => (
        <button
          key={item.label}
          className={`${styles.navItem} ${item.active ? styles.navItemActive : ''}`}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>

    <div className={styles.footer}>
      <button className={styles.newTradeBtn} onClick={onNewTrade}>
        New Trade
      </button>
    </div>
  </aside>
)
