import type { WeatherResponse, Style } from '../../types';
import styles from './WeatherCard.module.scss';

interface WeatherCardProps {
  data: WeatherResponse;
  style?: Style;
}

// Maps summary keywords to an emoji for child mode
function getWeatherEmoji(summary: string): string {
  const s = summary.toLowerCase();
  if (s.includes('rain') || s.includes('drizzle')) return '🌧️';
  if (s.includes('storm') || s.includes('thunder')) return '⛈️';
  if (s.includes('snow'))  return '❄️';
  if (s.includes('cloud')) return '☁️';
  if (s.includes('fog') || s.includes('mist')) return '🌫️';
  if (s.includes('hot') || s.includes('sunny') || s.includes('clear')) return '☀️';
  if (s.includes('wind')) return '💨';
  return '🌡️';
}

export default function WeatherCard({ data, style }: WeatherCardProps) {
  const isChild = style === 'child';
  const emoji = getWeatherEmoji(data.summary);

  return (
    <div className={`${styles.card} ${isChild ? styles.childCard : ''}`}>
      {/* Header row */}
      <div className={styles.header}>
        <div>
          <h3 className={styles.location}>{data.location}</h3>
          <p className={styles.summary}>
            {isChild ? `${emoji} ${data.summary}` : data.summary}
          </p>
        </div>
        <span className={styles.emojiIcon} aria-hidden="true">
          {emoji}
        </span>
      </div>

      {/* Temperature */}
      <div className={styles.tempRow}>
        <span className={styles.temperature}>{data.temperature}</span>
        <span className={styles.feelsLike}>
          Feels like {data.feels_like}
        </span>
      </div>

      {/* Advice */}
      {data.advice && (
        <div className={styles.advice}>
          <span className={styles.adviceIcon}>💡</span>
          <p className={styles.adviceText}>{data.advice}</p>
        </div>
      )}
    </div>
  );
}
