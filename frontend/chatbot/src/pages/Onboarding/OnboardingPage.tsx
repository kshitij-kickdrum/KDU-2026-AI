import { useState, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AutoAwesome as AutoAwesomeIcon, ArrowForward as ArrowForwardIcon } from '@mui/icons-material';
import { useRegisterUserMutation } from '../../api/api';
import { useAppDispatch } from '../../store/hooks';
import { setProfile } from '../../features/auth/authSlice';
import { setActiveStyle } from '../../features/chat/chatSlice';
import { deriveStyle } from '../../helpers/styleHelpers';
import styles from './OnboardingPage.module.scss';

interface FormValues {
  name: string;
  location: string;
  age: string;
}

interface FormErrors {
  name?: string;
  location?: string;
  age?: string;
}

function validate(values: FormValues): FormErrors {
  const errors: FormErrors = {};

  if (!values.name.trim() || values.name.trim().length < 2) {
    errors.name = 'Name must be at least 2 characters';
  } else if (values.name.trim().length > 50) {
    errors.name = 'Name must be 50 characters or fewer';
  }

  if (!values.location.trim() || values.location.trim().length < 2) {
    errors.location = 'Location must be at least 2 characters';
  } else if (values.location.trim().length > 100) {
    errors.location = 'Location must be 100 characters or fewer';
  }

  const age = Number(values.age);
  if (!values.age || Number.isNaN(age) || !Number.isInteger(age) || age < 5 || age > 120) {
    errors.age = 'Please enter a valid age (5–120)';
  }

  return errors;
}

export default function OnboardingPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [registerUser, { isLoading }] = useRegisterUserMutation();

  const [values, setValues] = useState<FormValues>({ name: '', location: '', age: '' });
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
    setApiError(null);
  }

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    const fieldErrors = validate(values);
    if (Object.keys(fieldErrors).length > 0) {
      setErrors(fieldErrors);
      return;
    }

    try {
      const age = Number(values.age);
      const result = await registerUser({
        name: values.name.trim(),
        location: values.location.trim(),
        age,
      }).unwrap();

      dispatch(setProfile(result));
      dispatch(setActiveStyle(deriveStyle(age)));
      navigate('/chat');
    } catch (err: unknown) {
      const error = err as { data?: { message?: string } };
      setApiError(error?.data?.message ?? 'Something went wrong. Please try again.');
    }
  }

  return (
    <div className={styles.page}>
      {/* Ambient glows */}
      <div className={`${styles.glow} ${styles.glowBottomLeft}`} />
      <div className={`${styles.glow} ${styles.glowTopRight}`} />

      <main className={styles.card}>
        {/* Logo */}
        <div className={styles.logoSection}>
          <div className={styles.logoIcon}>
            <AutoAwesomeIcon fontSize="small" />
          </div>
          <h1 className={styles.appName}>Aether AI</h1>
          <p className={styles.appSubtitle}>Your intelligent assistant</p>
        </div>

        {/* Form */}
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <div className={styles.fieldGroup}>
            <label className={styles.label} htmlFor="name">Your Name</label>
            <input
              className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
              id="name"
              name="name"
              type="text"
              placeholder="E.g. Julian Vane"
              value={values.name}
              onChange={handleChange}
              autoComplete="given-name"
            />
            {errors.name && <p className={styles.errorText}>{errors.name}</p>}
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label} htmlFor="location">Your Location</label>
            <input
              className={`${styles.input} ${errors.location ? styles.inputError : ''}`}
              id="location"
              name="location"
              type="text"
              placeholder="E.g. London, UK"
              value={values.location}
              onChange={handleChange}
              autoComplete="address-level2"
            />
            {errors.location && <p className={styles.errorText}>{errors.location}</p>}
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label} htmlFor="age">Your Age</label>
            <input
              className={`${styles.input} ${errors.age ? styles.inputError : ''}`}
              id="age"
              name="age"
              type="number"
              placeholder="E.g. 28"
              value={values.age}
              onChange={handleChange}
              min={5}
              max={120}
            />
            {errors.age
              ? <p className={styles.errorText}>{errors.age}</p>
              : <p className={styles.hint}>We use your age to personalize how the assistant talks to you.</p>
            }
          </div>

          {apiError && <p className={styles.apiError}>{apiError}</p>}

          <button
            className={styles.submitBtn}
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? 'Setting up...' : 'Get Started'}
            {!isLoading && <ArrowForwardIcon fontSize="small" />}
          </button>
        </form>

        {/* Decorative dots */}
        <div className={styles.decorDots}>
          <span className={`${styles.dot} ${styles.dotActive}`} />
          <span className={styles.dot} />
          <span className={styles.dot} />
        </div>
      </main>
    </div>
  );
}
