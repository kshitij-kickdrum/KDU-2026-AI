import { Chip } from '@mui/material'

type StatusTone =
  | 'healthy'
  | 'completed'
  | 'awaiting'
  | 'cancelled'
  | 'error'
  | 'in_progress'
  | 'neutral'

interface StatusChipProps {
  label: string
  tone?: StatusTone
}

const colorByTone: Record<StatusTone, 'success' | 'warning' | 'error' | 'default'> =
  {
    healthy: 'success',
    completed: 'success',
    awaiting: 'warning',
    cancelled: 'default',
    error: 'error',
    in_progress: 'warning',
    neutral: 'default',
  }

export const StatusChip = ({ label, tone = 'neutral' }: StatusChipProps) => (
  <Chip
    label={label}
    color={colorByTone[tone]}
    size="small"
    sx={{ fontWeight: 600, letterSpacing: '0.01em' }}
  />
)
