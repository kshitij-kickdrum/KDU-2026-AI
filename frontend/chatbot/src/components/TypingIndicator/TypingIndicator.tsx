import styles from './TypingIndicator.module.scss';

export default function TypingIndicator() {
  return (
    <div className={styles.wrapper}>
      <span className={styles.dot} style={{ animationDelay: '0ms' }} />
      <span className={styles.dot} style={{ animationDelay: '150ms' }} />
      <span className={styles.dot} style={{ animationDelay: '300ms' }} />
      <span className={styles.label}>Thinking…</span>
    </div>
  );
}
