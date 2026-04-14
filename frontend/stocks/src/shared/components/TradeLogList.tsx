import { List, ListItem, ListItemText, Typography } from '@mui/material'

interface TradeLogListProps {
  logs: string[]
}

export const TradeLogList = ({ logs }: TradeLogListProps) => {
  if (!logs.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        No trades logged yet.
      </Typography>
    )
  }

  return (
    <List dense disablePadding>
      {logs.map((entry) => (
        <ListItem
          key={entry}
          disableGutters
          sx={{ py: 0.8, borderBottom: '1px dashed rgba(13, 37, 63, 0.12)' }}
        >
          <ListItemText
            primary={entry}
            primaryTypographyProps={{ variant: 'body2', sx: { fontWeight: 500 } }}
          />
        </ListItem>
      ))}
    </List>
  )
}
