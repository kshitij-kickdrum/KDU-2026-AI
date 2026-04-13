import type { ReactNode } from 'react'
import { Box, Stack, Typography } from '@mui/material'

export interface KeyValueItem {
  label: string
  value: ReactNode
}

interface KeyValueGridProps {
  items: KeyValueItem[]
  columns?: number
}

export const KeyValueGrid = ({ items, columns = 2 }: KeyValueGridProps) => {
  const templateColumns =
    columns > 1 ? `repeat(${columns}, minmax(0, 1fr))` : 'minmax(0, 1fr)'

  return (
    <Box
      sx={{
        display: 'grid',
        gap: 1.5,
        gridTemplateColumns: { xs: 'minmax(0, 1fr)', sm: templateColumns },
      }}
    >
      {items.map((item) => (
        <Box key={item.label}>
          <Stack spacing={0.25}>
            <Typography variant="caption" color="text.secondary">
              {item.label}
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              {item.value}
            </Typography>
          </Stack>
        </Box>
      ))}
    </Box>
  )
}
