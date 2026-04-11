import { useRef, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { addMessage, setLoading, addToast } from '../features/chat/chatSlice';
import { useSendChatMutation } from '../api/api';
import { getErrorMessage } from '../helpers/errorHelpers';
import { generateMessageId, getResponsePreview } from '../helpers/messageHelpers';
import type { ChatMessage, ApiError } from '../types';

export function useChat(sessionId: string) {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.auth.profile);
  const activeStyle = useAppSelector((state) => state.chat.activeStyle);
  const threadRef = useRef<HTMLDivElement | null>(null);

  const [sendChat] = useSendChatMutation();

  const scrollToBottom = useCallback(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!profile || !sessionId || !text.trim()) return;

      // Append human message immediately
      const humanMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'human',
        content: text.trim(),
        timestamp: Date.now(),
      };
      dispatch(addMessage(humanMessage));
      dispatch(setLoading(true));
      setTimeout(scrollToBottom, 50);

      try {
        const result = await sendChat({
          user_id: profile.user_id,
          session_id: sessionId,
          message: text.trim(),
          style: activeStyle,
        }).unwrap();

        const aiMessage: ChatMessage = {
          id: generateMessageId(),
          role: 'ai',
          content: getResponsePreview(result.response),
          model_used: result.model_used,
          tool_used: result.tool_used,
          style_applied: result.style_applied,
          response: result.response,
          timestamp: Date.now(),
        };
        dispatch(addMessage(aiMessage));
        setTimeout(scrollToBottom, 50);
      } catch (err: unknown) {
        const error = err as { status?: number; data?: ApiError };
        const errorCode = error?.status === 429 ? 'RATE_LIMIT_EXCEEDED' : error?.data?.code;

        dispatch(addToast({
          id: generateMessageId(),
          message: getErrorMessage(errorCode, 'Something went wrong. Please try again.'),
          variant: 'error',
        }));
      } finally {
        dispatch(setLoading(false));
      }
    },
    [profile, sessionId, activeStyle, dispatch, sendChat, scrollToBottom],
  );

  return { sendMessage, threadRef };
}
