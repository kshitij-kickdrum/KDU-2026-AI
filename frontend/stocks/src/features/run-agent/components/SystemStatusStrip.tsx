import MemoryIcon from '@mui/icons-material/Memory'
import SpeedIcon from '@mui/icons-material/Speed'
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser'
import styles from './SystemStatusStrip.module.scss'

const STATUS_ITEMS = [
  { icon: <MemoryIcon fontSize="small" />, label: 'Agent Core', value: 'V4.2 Quantum-Ready', color: 'cyan' },
  { icon: <SpeedIcon fontSize="small" />, label: 'Execution Latency', value: '1.2ms (Ultra-Low)', color: 'green' },
  { icon: <VerifiedUserIcon fontSize="small" />, label: 'Risk Guard', value: 'Enabled (Standard)', color: 'blue' },
]

export const SystemStatusStrip = () => (
  <div className={styles.strip}>
    {STATUS_ITEMS.map((item) => (
      <div key={item.label} className={styles.card}>
        <div className={`${styles.iconBox} ${styles[item.color]}`}>
          {item.icon}
        </div>
        <div>
          <div className={styles.label}>{item.label}</div>
          <div className={styles.value}>{item.value}</div>
        </div>
      </div>
    ))}
  </div>
)
