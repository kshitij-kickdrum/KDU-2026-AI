import { useAppDispatch, useAppSelector } from './store/hooks'
import { useGetHealthQuery } from './api/api'
import { selectCurrentPage } from './store/selectors'
import { navigateTo, resetRun } from './store/slices/uiSlice'
import { AppLayout } from './shared/layout/AppLayout'
import { RunAgentPage } from './features/run-agent/RunAgentPage'
import { TradeApprovalPage } from './features/trade-approval/TradeApprovalPage'
import { SessionHistoryPage } from './features/session-history/SessionHistoryPage'

function App() {
  const dispatch = useAppDispatch()
  const currentPage = useAppSelector(selectCurrentPage)

  // Intentional startup call to verify backend connectivity on reload.
  useGetHealthQuery()

  const handleNavigate = (page: 'run-agent' | 'trade-approval' | 'session-history') => {
    dispatch(navigateTo(page))
  }

  const handleNewTrade = () => {
    dispatch(resetRun())
  }

  let activePage: 'run-agent' | 'trade-approval' | 'session-history' = 'run-agent'
  if (currentPage === 'trade-approval') {
    activePage = 'trade-approval'
  } else if (currentPage === 'session-history') {
    activePage = 'session-history'
  }

  return (
    <AppLayout
      activePage={activePage}
      onNavigate={handleNavigate}
      onNewTrade={handleNewTrade}
    >
      {currentPage === 'run-agent' && <RunAgentPage />}
      {currentPage === 'trade-approval' && <TradeApprovalPage />}
      {currentPage === 'session-history' && <SessionHistoryPage />}
    </AppLayout>
  )
}

export default App
