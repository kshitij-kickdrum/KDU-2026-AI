import { useEffect } from 'react';
import { Error as ErrorIcon, WarningAmber as WarningAmberIcon, CheckCircle as CheckCircleIcon, Close as CloseIcon } from '@mui/icons-material';
import type { Toast as ToastType } from '../../types';
import styles from './Toast.module.scss';

const AUTO_DISMISS_MS = 4000;

const ICON_MAP = {
  error:   <ErrorIcon fontSize="small" />,
  warning: <WarningAmberIcon fontSize="small" />,
  success: <CheckCircleIcon fontSize="small" />,
};

interface ToastProps {
  readonly toast: ToastType;
  readonly onDismiss: (id: string) => void;
}

export default function Toast({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div className={`${styles.toast} ${styles[toast.variant]}`} role="alert">
      <span className={styles.icon}>{ICON_MAP[toast.variant]}</span>
      <p className={styles.message}>{toast.message}</p>
      <button
        className={styles.closeBtn}
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
      >
        <CloseIcon fontSize="small" />
      </button>
    </div>
  );
}
