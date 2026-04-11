import type { RefObject } from 'react';
import { useAppSelector } from '../../../store/hooks';
import HumanMessage from './HumanMessage/HumanMessage';
import AIMessage from './AIMessage/AIMessage';
import TypingIndicator from '../../../components/TypingIndicator/TypingIndicator';
import styles from './MessageThread.module.scss';

interface MessageThreadProps {
  readonly threadRef: RefObject<HTMLDivElement | null>;
}

export default function MessageThread({ threadRef }: MessageThreadProps) {
  const messages = useAppSelector((state) => state.chat.messages);
  const isLoading = useAppSelector((state) => state.chat.isLoading);
  const profile = useAppSelector((state) => state.auth.profile);

  return (
    <div className={styles.thread} ref={threadRef}>
      {messages.map((msg) =>
        msg.role === 'human' ? (
          <HumanMessage
            key={msg.id}
            message={msg}
            userName={profile?.name ?? 'You'}
          />
        ) : (
          <AIMessage key={msg.id} message={msg} />
        )
      )}

      {isLoading && <TypingIndicator />}
    </div>
  );
}
