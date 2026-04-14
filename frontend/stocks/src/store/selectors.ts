import type { RootState } from './store'

export const selectCurrentPage    = (state: RootState) => state.ui.currentPage
export const selectRunDraft       = (state: RootState) => state.ui.runDraft
export const selectActiveThreadId = (state: RootState) => state.ui.activeThreadId
export const selectLastRunResponse    = (state: RootState) => state.ui.lastRunResponse
export const selectLastApproveResponse = (state: RootState) => state.ui.lastApproveResponse
export const selectSessionHistorySearch = (state: RootState) => state.ui.sessionHistorySearch
