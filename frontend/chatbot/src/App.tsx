import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppSelector } from './store/hooks';
import OnboardingPage from './pages/Onboarding/OnboardingPage';
import ChatPage from './pages/Chat/ChatPage';

function App() {
  const profile = useAppSelector((state) => state.auth.profile);

  return (
    <Routes>
      <Route path="/" element={<OnboardingPage />} />
      <Route
        path="/chat"
        element={profile ? <ChatPage /> : <Navigate to="/" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
