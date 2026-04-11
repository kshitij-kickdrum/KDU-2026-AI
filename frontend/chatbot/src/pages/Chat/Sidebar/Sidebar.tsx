import {
  AutoAwesome as AutoAwesomeIcon,
  ChatBubbleOutlined as ChatBubbleOutlineIcon,
  AddComment as AddCommentIcon,
} from '@mui/icons-material';
import { useCreateSessionMutation, useDeleteSessionMutation, useGetSessionsQuery } from '../../../api/api';
import { addToast, clearMessages, setSessionId } from '../../../features/chat/chatSlice';
import { clearImageState } from '../../../features/imageAnalysis/imageSlice';
import {
  clearStoredSession,
  generateSessionId,
  setStoredSession,
} from '../../../hooks/useSession';
import { generateMessageId } from '../../../helpers/messageHelpers';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import type { SessionSummary } from '../../../types';
import styles from './Sidebar.module.scss';

interface SidebarProps {
  sessionId: string;
}

export default function Sidebar({ sessionId }: SidebarProps) {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.auth.profile);
  const messages = useAppSelector((state) => state.chat.messages);
  const [createSession] = useCreateSessionMutation();
  const [deleteSession, { isLoading }] = useDeleteSessionMutation();
  const { data: sessionList } = useGetSessionsQuery(profile?.user_id ?? '', {
    skip: !profile,
  });

  const sessionSummaries = sessionList?.sessions ?? [];
  const activePlaceholder: SessionSummary | null =
    sessionId && !sessionSummaries.some((item) => item.session_id === sessionId)
      ? {
          session_id: sessionId,
          title: 'New chat',
          preview: '',
          created_at: Date.now(),
          updated_at: Date.now(),
          message_count: 0,
        }
      : null;
  const visibleSessions = activePlaceholder
    ? [activePlaceholder, ...sessionSummaries]
    : sessionSummaries;

  async function startNewChat() {
    if (!profile) return;

    const newId = generateSessionId();
    setStoredSession(newId, profile.user_id);
    dispatch(clearMessages());
    dispatch(clearImageState());
    dispatch(setSessionId(newId));

    try {
      await createSession({ user_id: profile.user_id, session_id: newId }).unwrap();
    } catch {
      dispatch(addToast({
        id: generateMessageId(),
        message: 'Could not create a new session on the server.',
        variant: 'warning',
      }));
    }
  }

  function handleSessionSelect(nextSessionId: string) {
    if (!profile || nextSessionId === sessionId) return;

    setStoredSession(nextSessionId, profile.user_id);
    dispatch(clearMessages());
    dispatch(clearImageState());
    dispatch(setSessionId(nextSessionId));
  }

  async function handleClearSession() {
    if (!profile || !sessionId) return;

    try {
      await deleteSession({ user_id: profile.user_id, session_id: sessionId }).unwrap();
    } catch {
      // Keep the UX moving even if the backend clear fails.
    } finally {
      clearStoredSession(profile.user_id);
      dispatch(clearMessages());
      dispatch(clearImageState());

      const newId = generateSessionId();
      setStoredSession(newId, profile.user_id);
      dispatch(setSessionId(newId));
      try {
        await createSession({ user_id: profile.user_id, session_id: newId }).unwrap();
      } catch {
        dispatch(addToast({
          id: generateMessageId(),
          message: 'Could not create a fresh session on the server.',
          variant: 'warning',
        }));
      }
      dispatch(addToast({
        id: generateMessageId(),
        message: 'Session cleared.',
        variant: 'success',
      }));
    }
  }

  return (
    <aside className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <h2 className={styles.sidebarTitle}>Recents</h2>
        <span className={styles.messageCount}>{visibleSessions.length} chats</span>
      </div>

      <button className={styles.newChatBtn} onClick={() => { void startNewChat(); }} type="button">
        <AddCommentIcon fontSize="small" />
        New Chat
      </button>

      <div className={styles.historyList}>
        {visibleSessions.length === 0 ? (
          <div className={styles.emptyState}>
            <AutoAwesomeIcon fontSize="small" />
            <span>Your past chats will appear here.</span>
          </div>
        ) : (
          visibleSessions.map((item) => (
            <button
              key={item.session_id}
              className={`${styles.historyItem} ${item.session_id === sessionId ? styles.historyItemActive : ''}`}
              onClick={() => handleSessionSelect(item.session_id)}
              type="button"
            >
              <ChatBubbleOutlineIcon fontSize="small" className={styles.sessionIcon} />
              <div className={styles.historyText}>
                <span className={styles.historyTitle}>{item.title}</span>
                {item.preview && <span className={styles.historyPreview}>{item.preview}</span>}
              </div>
            </button>
          ))
        )}
      </div>

      <div className={styles.sidebarFooter}>
        <button
          className={styles.clearBtn}
          onClick={handleClearSession}
          disabled={isLoading || messages.length === 0}
          type="button"
        >
          {isLoading ? 'Clearing...' : 'Clear Session'}
        </button>
      </div>
    </aside>
  );
}
