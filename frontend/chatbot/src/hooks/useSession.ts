import { useEffect } from 'react';
import { setSessionId } from '../features/chat/chatSlice';
import type { HistoryMessage } from '../types';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { parseMessagePayload } from '../helpers/messageHelpers';

const LEGACY_SESSION_KEY = 'aether_session_id';
const ACTIVE_SESSION_KEY_PREFIX = 'aether_active_session';
const SESSION_INDEX_KEY_PREFIX = 'aether_session_index';
const DEFAULT_SESSION_TITLE = 'New chat';

export interface StoredSessionSummary {
  sessionId: string;
  title: string;
  preview: string;
  updatedAt: number;
  messageCount: number;
}

function getActiveSessionKey(userId?: string): string {
  return userId ? `${ACTIVE_SESSION_KEY_PREFIX}:${userId}` : LEGACY_SESSION_KEY;
}

function getSessionIndexKey(userId: string): string {
  return `${SESSION_INDEX_KEY_PREFIX}:${userId}`;
}

function normalizeText(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function truncateText(value: string, limit: number): string {
  return value.length > limit ? `${value.slice(0, limit - 3).trimEnd()}...` : value;
}

export function generateSessionId(): string {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function getStoredSession(userId?: string): string | null {
  const primaryKey = getActiveSessionKey(userId);
  const stored = localStorage.getItem(primaryKey);

  if (stored) {
    return stored;
  }

  if (userId) {
    return localStorage.getItem(LEGACY_SESSION_KEY);
  }

  return null;
}

export function setStoredSession(sessionId: string, userId?: string): void {
  localStorage.setItem(getActiveSessionKey(userId), sessionId);
  localStorage.setItem(LEGACY_SESSION_KEY, sessionId);
}

export function clearStoredSession(userId?: string): void {
  localStorage.removeItem(getActiveSessionKey(userId));
  localStorage.removeItem(LEGACY_SESSION_KEY);
}

export function getStoredSessionIndex(userId: string): StoredSessionSummary[] {
  const raw = localStorage.getItem(getSessionIndexKey(userId));
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw) as StoredSessionSummary[];

    return parsed
      .filter((item) => typeof item?.sessionId === 'string' && item.sessionId.length > 0)
      .sort((a, b) => b.updatedAt - a.updatedAt);
  } catch {
    return [];
  }
}

function saveStoredSessionIndex(userId: string, sessions: StoredSessionSummary[]): StoredSessionSummary[] {
  const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  localStorage.setItem(getSessionIndexKey(userId), JSON.stringify(sorted));
  return sorted;
}

export function removeStoredSessionSummary(userId: string, sessionId: string): StoredSessionSummary[] {
  const sessions = getStoredSessionIndex(userId).filter((item) => item.sessionId !== sessionId);
  return saveStoredSessionIndex(userId, sessions);
}

export function buildSessionTitle(text: string): string {
  const normalized = normalizeText(text);
  if (!normalized) return DEFAULT_SESSION_TITLE;
  if (normalized.toLowerCase() === 'describe this image') return 'Image analysis';
  return truncateText(normalized, 38);
}

export function buildSessionPreview(text: string): string {
  const normalized = normalizeText(text);
  return normalized ? truncateText(normalized, 56) : '';
}

export function upsertStoredSessionSummary(
  userId: string,
  summary: Partial<StoredSessionSummary> & Pick<StoredSessionSummary, 'sessionId'>,
): StoredSessionSummary[] {
  const sessions = getStoredSessionIndex(userId);
  const existing = sessions.find((item) => item.sessionId === summary.sessionId);

  if (!existing && !summary.preview && !summary.messageCount && !summary.title) {
    return sessions;
  }

  const nextSummary: StoredSessionSummary = {
    sessionId: summary.sessionId,
    title: summary.title || existing?.title || DEFAULT_SESSION_TITLE,
    preview: summary.preview ?? existing?.preview ?? '',
    updatedAt: summary.updatedAt ?? existing?.updatedAt ?? Date.now(),
    messageCount: summary.messageCount ?? existing?.messageCount ?? 0,
  };

  const nextSessions = [
    nextSummary,
    ...sessions.filter((item) => item.sessionId !== summary.sessionId),
  ];

  return saveStoredSessionIndex(userId, nextSessions);
}

export function deriveSessionSummaryFromHistory(
  sessionId: string,
  messages: HistoryMessage[],
  messageCount: number,
): StoredSessionSummary | null {
  if (messageCount === 0) return null;

  const firstHumanMessage = messages.find((message) => message.role === 'human')?.content ?? '';
  const lastMessage = messages.at(-1);
  const parsedLastPreview = lastMessage ? parseMessagePayload(lastMessage.content).content : '';

  return {
    sessionId,
    title: buildSessionTitle(firstHumanMessage || parsedLastPreview),
    preview: buildSessionPreview(parsedLastPreview || firstHumanMessage),
    updatedAt: Date.now(),
    messageCount,
  };
}

export function useSession(userId?: string): string {
  const dispatch = useAppDispatch();
  const sessionId = useAppSelector((state) => state.chat.sessionId);

  useEffect(() => {
    if (sessionId) return;

    const stored = getStoredSession(userId);
    const id = stored ?? generateSessionId();

    if (!stored) {
      setStoredSession(id, userId);
    }

    dispatch(setSessionId(id));
  }, [sessionId, userId, dispatch]);

  return sessionId;
}
