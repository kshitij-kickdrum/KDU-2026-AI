import styles from './Badge.module.scss';

export type BadgeVariant = 'model' | 'tool' | 'style-expert' | 'style-child';

interface BadgeProps {
  label: string;
  variant: BadgeVariant;
}

export default function Badge({ label, variant }: BadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[variant]}`}>
      {label}
    </span>
  );
}
