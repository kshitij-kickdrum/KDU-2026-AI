import type {
  ChatMessage,
  GeneralResponse,
  HistoryMessage,
  ImageResponse,
  IntentType,
  ParsedResponse,
  WeatherResponse,
} from '../types';

export function isWeatherResponse(response: ParsedResponse): response is WeatherResponse {
  return 'temperature' in response && 'feels_like' in response && 'summary' in response;
}

export function isImageResponse(response: ParsedResponse): response is ImageResponse {
  return 'description' in response && 'objects_detected' in response;
}

export function isGeneralResponse(response: ParsedResponse): response is GeneralResponse {
  return 'answer' in response;
}

export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function getResponsePreview(response: ParsedResponse): string {
  if (isWeatherResponse(response)) return `${response.temperature} - ${response.summary}`;
  if (isImageResponse(response)) return response.description;
  if (isGeneralResponse(response)) return response.answer;
  return '';
}

function unwrapJsonFence(content: string): string {
  const fencedMatch = content.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  return fencedMatch ? fencedMatch[1].trim() : content;
}

export function parseMessagePayload(content: string): {
  content: string;
  response?: ParsedResponse;
  intent?: IntentType;
} {
  const trimmed = unwrapJsonFence(content.trim());
  if (!trimmed) {
    return { content: '' };
  }

  try {
    const parsed = JSON.parse(trimmed) as ParsedResponse;

    if (isWeatherResponse(parsed)) {
      return {
        content: getResponsePreview(parsed),
        response: parsed,
        intent: 'weather',
      };
    }

    if (isImageResponse(parsed)) {
      return {
        content: getResponsePreview(parsed),
        response: parsed,
        intent: 'image',
      };
    }

    if (isGeneralResponse(parsed)) {
      return {
        content: getResponsePreview(parsed),
        response: parsed,
        intent: 'general',
      };
    }
  } catch {
    // History can contain plain text; leave it untouched.
  }

  return { content };
}

export function hydrateHistoryMessages(messages: HistoryMessage[]): ChatMessage[] {
  const baseTimestamp = Date.now();

  return messages.map((message, index) => {
    if (message.role === 'human') {
      return {
        id: generateMessageId(),
        role: 'human',
        content: message.content,
        timestamp: baseTimestamp + index,
      };
    }

    const parsed = parseMessagePayload(message.content);

    return {
      id: generateMessageId(),
      role: 'ai',
      content: parsed.content,
      response: parsed.response,
      intent: parsed.intent,
      timestamp: baseTimestamp + index,
    };
  });
}
