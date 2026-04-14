import type { PropsWithChildren, ReactNode } from 'react'
import { Box, Paper, Stack, Typography } from '@mui/material'

interface SectionCardProps extends PropsWithChildren {
  title: string
  subtitle?: string
  action?: ReactNode
}

export const SectionCard = ({
  title,
  subtitle,
  action,
  children,
}: SectionCardProps) => {
  return (
    <Paper elevation={0} sx={{ p: { xs: 2, md: 2.5 } }}>
      <Stack
        direction="row"
        alignItems="flex-start"
        justifyContent="space-between"
        spacing={2}
        sx={{ mb: 2.5 }}
      >
        <Box>
          <Typography variant="h6">{title}</Typography>
          {subtitle ? (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {subtitle}
            </Typography>
          ) : null}
        </Box>
        {action}
      </Stack>
      {children}
    </Paper>
  )
}
