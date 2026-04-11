import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { removeToast } from '../../features/chat/chatSlice';
import Toast from './Toast';
import styles from './ToastContainer.module.scss';

export default function ToastContainer() {
  const dispatch = useAppDispatch();
  const toasts = useAppSelector((state) => state.chat.toasts);

  const handleDismiss = useCallback(
    (id: string) => dispatch(removeToast(id)),
    [dispatch],
  );

  if (toasts.length === 0) return null;

  return (
    <div className={styles.container} aria-live="polite">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}
