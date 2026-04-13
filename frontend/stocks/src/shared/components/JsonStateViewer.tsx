import { Box, Typography } from '@mui/material'

interface JsonStateViewerProps {
  data: unknown
}

export const JsonStateViewer = ({ data }: JsonStateViewerProps) => {
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        p: 2,
        borderRadius: 2,
        border: '1px solid rgba(13, 37, 63, 0.1)',
        bgcolor: 'rgba(11, 58, 110, 0.04)',
        overflowX: 'auto',
      }}
    >
      <Typography
        component="code"
        sx={{
          fontFamily: '"Fira Code", "Consolas", monospace',
          fontSize: '0.8rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {JSON.stringify(data, null, 2)}
      </Typography>
    </Box>
  )
}
