import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import {
  AttachFile as AttachFileIcon,
  Send as SendIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { addToast } from '../../../features/chat/chatSlice';
import { ERROR_MESSAGES } from '../../../helpers/errorHelpers';
import { generateMessageId } from '../../../helpers/messageHelpers';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import styles from './InputBar.module.scss';

interface InputBarProps {
  onSend?: (message: string, file?: File) => void;
}

const ALLOWED_TYPES = ['image/jpeg', 'image/png'];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;

export default function InputBar({ onSend }: InputBarProps) {
  const dispatch = useAppDispatch();
  const isLoading = useAppSelector((state) => state.chat.isLoading);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [text, setText] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!attachedFile) {
      setPreviewUrl(null);
      return;
    }

    const nextPreviewUrl = URL.createObjectURL(attachedFile);
    setPreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [attachedFile]);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      const message = ERROR_MESSAGES.UNSUPPORTED_FORMAT;
      setAttachedFile(null);
      setFileError(message);
      dispatch(addToast({ id: generateMessageId(), message, variant: 'warning' }));
      e.target.value = '';
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      const message = ERROR_MESSAGES.IMAGE_TOO_LARGE;
      setAttachedFile(null);
      setFileError(message);
      dispatch(addToast({ id: generateMessageId(), message, variant: 'warning' }));
      e.target.value = '';
      return;
    }

    setFileError(null);
    setAttachedFile(file);
  }

  function removeFile() {
    setAttachedFile(null);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed && !attachedFile) return;
    if (isLoading) return;

    onSend?.(trimmed, attachedFile ?? undefined);
    setText('');
    removeFile();
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const canSend = (text.trim().length > 0 || attachedFile !== null) && !isLoading;
  const placeholder = attachedFile
    ? 'Ask a question about the image, or send to get a description'
    : 'Type your message...';

  return (
    <div className={styles.wrapper}>
      {fileError && <p className={styles.fileError}>{fileError}</p>}

      {attachedFile && (
        <div className={styles.filePreview}>
          {previewUrl && (
            <img
              className={styles.previewImage}
              src={previewUrl}
              alt={attachedFile.name}
            />
          )}

          <div className={styles.fileMeta}>
            <span className={styles.fileLabel}>Attached image</span>
            <span className={styles.fileName}>{attachedFile.name}</span>
          </div>

          <button
            className={styles.removeFile}
            onClick={removeFile}
            aria-label="Remove attachment"
            type="button"
          >
            <CloseIcon fontSize="small" />
          </button>
        </div>
      )}

      <div className={styles.inputRow}>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className={styles.hiddenInput}
          onChange={handleFileChange}
          aria-label="Attach image"
        />

        <button
          className={styles.iconBtn}
          onClick={() => fileInputRef.current?.click()}
          type="button"
          aria-label="Attach image"
          disabled={isLoading}
        >
          <AttachFileIcon fontSize="small" />
        </button>

        <input
          className={styles.textInput}
          type="text"
          placeholder={placeholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          maxLength={2000}
          aria-label="Message input"
        />

        <button
          className={`${styles.sendBtn} ${canSend ? styles.sendBtnActive : ''}`}
          onClick={handleSend}
          type="button"
          disabled={!canSend}
          aria-label="Send message"
        >
          {isLoading
            ? <span className={styles.spinner} />
            : <SendIcon fontSize="small" />
          }
        </button>
      </div>
    </div>
  );
}
