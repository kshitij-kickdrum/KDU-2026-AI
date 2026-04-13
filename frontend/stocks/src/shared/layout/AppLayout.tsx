import type { ReactNode } from 'react'
import { TopNav } from './TopNav'
import { Sidebar } from './Sidebar'
import styles from './AppLayout.module.scss'

interface AppLayoutProps {
  children: ReactNode
  activePage: 'run-agent' | 'trade-approval' | 'session-history'
  onNavigate: (page: 'run-agent' | 'trade-approval' | 'session-history') => void
  onNewTrade: () => void
}

export const AppLayout = ({ children, activePage, onNavigate, onNewTrade }: AppLayoutProps) => (
  <div className={styles.root}>
    <TopNav activePage={activePage} onNavigate={onNavigate} />
    <Sidebar onNewTrade={onNewTrade} />
    <main className={styles.main}>
      {children}
    </main>
    {/* Background glow blobs */}
    <div className={styles.glowLeft} />
    <div className={styles.glowRight} />
  </div>
)
