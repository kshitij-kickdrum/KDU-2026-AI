import { Close as CloseIcon } from '@mui/icons-material';
import { closePanel } from '../../features/imageAnalysis/imageSlice';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import styles from './ImageAnalysisPanel.module.scss';

const CONFIDENCE_LABELS = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
} as const;

const CONFIDENCE_CLASS_MAP = {
  high: 'confidenceHigh',
  medium: 'confidenceMedium',
  low: 'confidenceLow',
} as const;

export default function ImageAnalysisPanel() {
  const dispatch = useAppDispatch();
  const { isOpen, result } = useAppSelector((state) => state.image);

  if (!isOpen || !result) return null;

  return (
    <section className={styles.panel} aria-label="Image analysis panel">
      <div className={styles.header}>
        <h2 className={styles.title}>Vision Insight</h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={() => dispatch(closePanel())}
          aria-label="Close image analysis panel"
        >
          <CloseIcon fontSize="small" />
        </button>
      </div>

      <div className={styles.body}>
        <section className={styles.section}>
          <span className={styles.label}>Description</span>
          <p className={styles.description}>{result.response.description}</p>
        </section>

        <section className={styles.section}>
          <span className={styles.label}>Objects Detected</span>
          <div className={styles.chips}>
            {result.response.objects_detected.map((item) => (
              <span key={item} className={styles.chip}>
                {item}
              </span>
            ))}
          </div>
        </section>

        <section className={styles.metadataCard}>
          <div className={styles.metadataRow}>
            <span className={styles.metadataLabel}>Scene type</span>
            <span className={styles.metadataValue}>{result.response.scene_type}</span>
          </div>

          <div className={styles.metadataRow}>
            <span className={styles.metadataLabel}>Confidence</span>
            <span className={styles.confidenceValue}>
              <span
                className={`${styles.confidenceDot} ${styles[CONFIDENCE_CLASS_MAP[result.response.confidence]]}`}
                aria-hidden="true"
              />
              {CONFIDENCE_LABELS[result.response.confidence]}
            </span>
          </div>
        </section>
      </div>
    </section>
  );
}
