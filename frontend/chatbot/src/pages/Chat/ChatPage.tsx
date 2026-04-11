import { useEffect } from 'react';
import { useGetHistoryQuery } from '../../api/api';
import ImageAnalysisPanel from '../../components/ImageAnalysisPanel/ImageAnalysisPanel';
import { setMessages } from '../../features/chat/chatSlice';
import ToastContainer from '../../components/Toast/ToastContainer';
import { hydrateHistoryMessages } from '../../helpers/messageHelpers';
import { useChat } from '../../hooks/useChat';
import { useImageUpload } from '../../hooks/useImageUpload';
import { useSession } from '../../hooks/useSession';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import Header from './Header/Header';
import InputBar from './InputBar/InputBar';
import MessageThread from './MessageThread/MessageThread';
import Sidebar from './Sidebar/Sidebar';
import styles from './ChatPage.module.scss';

export default function ChatPage() {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.auth.profile);
  const sessionId = useSession(profile?.user_id);
  const isPanelOpen = useAppSelector((state) => state.image.isOpen);
  const { sendMessage, threadRef } = useChat(sessionId);
  const { uploadImage } = useImageUpload(sessionId);
  const { data: historyData } = useGetHistoryQuery(
    { session_id: sessionId, user_id: profile?.user_id ?? '' },
    { skip: !sessionId || !profile },
  );

  useEffect(() => {
    if (!historyData) return;

    dispatch(setMessages(hydrateHistoryMessages(historyData.messages)));
  }, [dispatch, historyData]);

  function handleSend(message: string, file?: File) {
    if (file) {
      void uploadImage(file, message);
      return;
    }

    if (message.trim()) {
      void sendMessage(message);
    }
  }

  return (
    <div className={styles.layout}>
      <Header />
      <ToastContainer />

      <div className={styles.body}>
        <Sidebar sessionId={sessionId} />

        <main className={`${styles.main} ${isPanelOpen ? styles.mainShifted : ''}`}>
          <MessageThread threadRef={threadRef} />
          <InputBar onSend={handleSend} />
        </main>

        <aside className={`${styles.rightPanel} ${isPanelOpen ? styles.rightPanelOpen : ''}`}>
          <ImageAnalysisPanel />
        </aside>
      </div>
    </div>
  );
}
