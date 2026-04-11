import { useCallback } from 'react';
import { useSendImageMutation } from '../api/api';
import { addMessage, addToast, setLoading } from '../features/chat/chatSlice';
import { setImageResult, setUploadedFileName } from '../features/imageAnalysis/imageSlice';
import { getErrorMessage } from '../helpers/errorHelpers';
import { generateMessageId } from '../helpers/messageHelpers';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import type { ApiError, ChatMessage } from '../types';

export function useImageUpload(sessionId: string) {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.auth.profile);
  const activeStyle = useAppSelector((state) => state.chat.activeStyle);
  const [sendImage] = useSendImageMutation();

  const uploadImage = useCallback(
    async (file: File, prompt?: string) => {
      if (!profile || !sessionId) return;

      const normalizedPrompt = prompt?.trim() ?? '';
      const humanMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'human',
        content: normalizedPrompt || 'Describe this image',
        intent: 'image',
        timestamp: Date.now(),
      };

      dispatch(addMessage(humanMessage));

      const formData = new FormData();
      formData.append('image', file);
      formData.append('user_id', profile.user_id);
      formData.append('session_id', sessionId);
      formData.append('style', activeStyle);
      if (normalizedPrompt) {
        formData.append('prompt', normalizedPrompt);
      }

      dispatch(setLoading(true));

      try {
        const result = await sendImage(formData).unwrap();

        dispatch(setUploadedFileName(file.name));
        dispatch(setImageResult(result));

        const aiMessage: ChatMessage = {
          id: generateMessageId(),
          role: 'ai',
          content: result.response.description,
          model_used: result.model_used,
          tool_used: result.tool_used,
          style_applied: result.style_applied,
          response: result.response,
          intent: 'image',
          timestamp: Date.now(),
        };
        dispatch(addMessage(aiMessage));
      } catch (err: unknown) {
        const error = err as { status?: number; data?: ApiError };
        const errorCode = error?.status === 429 ? 'RATE_LIMIT_EXCEEDED' : error?.data?.code;

        dispatch(addToast({
          id: generateMessageId(),
          message: getErrorMessage(errorCode, 'Image upload failed. Please try again.'),
          variant: 'error',
        }));
      } finally {
        dispatch(setLoading(false));
      }
    },
    [activeStyle, profile, sessionId, dispatch, sendImage],
  );

  return { uploadImage };
}
