import { useNavigate } from 'react-router-dom';
import { AutoAwesome as AutoAwesomeIcon, Logout as LogoutIcon } from '@mui/icons-material';
import { clearProfile } from '../../../features/auth/authSlice';
import { clearMessages, setActiveStyle, setSessionId } from '../../../features/chat/chatSlice';
import { clearImageState } from '../../../features/imageAnalysis/imageSlice';
import { clearStoredSession } from '../../../hooks/useSession';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import type { Style } from '../../../types';
import styles from './Header.module.scss';

const STYLE_OPTIONS: { value: Style; label: string }[] = [
  { value: 'expert', label: 'Expert' },
  { value: 'child', label: 'Child' },
];

export default function Header() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const profile = useAppSelector((state) => state.auth.profile);
  const activeStyle = useAppSelector((state) => state.chat.activeStyle);

  function handleStyleChange(style: Style) {
    dispatch(setActiveStyle(style));
  }

  function handleLogout() {
    clearStoredSession(profile?.user_id);
    dispatch(clearImageState());
    dispatch(clearMessages());
    dispatch(setSessionId(''));
    dispatch(setActiveStyle('expert'));
    dispatch(clearProfile());
    navigate('/', { replace: true });
  }

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <div className={styles.logoIcon}>
          <AutoAwesomeIcon fontSize="small" />
        </div>
        <span className={styles.appName}>Aether AI</span>

        {profile && (
          <div className={styles.userPill}>
            <span className={styles.userPillText}>
              {profile.name} - {profile.location}
            </span>
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <nav className={styles.styleToggle} aria-label="Response style">
          {STYLE_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              className={`${styles.styleBtn} ${activeStyle === value ? styles.styleBtnActive : ''}`}
              onClick={() => handleStyleChange(value)}
              aria-pressed={activeStyle === value}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>

        <button
          className={styles.logoutBtn}
          onClick={handleLogout}
          type="button"
        >
          <LogoutIcon fontSize="small" />
          Logout
        </button>
      </div>
    </header>
  );
}
