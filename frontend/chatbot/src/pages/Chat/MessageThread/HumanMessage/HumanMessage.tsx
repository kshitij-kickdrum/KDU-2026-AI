import type { ChatMessage } from '../../../../types';
import styles from './HumanMessage.module.scss';

interface HumanMessageProps {
  message: ChatMessage;
  userName: string;
}

export default function HumanMessage({ message, userName }: HumanMessageProps) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.name}>{userName}</span>
      <p className={styles.bubble}>{message.content}</p>
    </div>
  );
}
