import Badge from '../../../../components/Badge/Badge';
import WeatherCard from '../../../../components/WeatherCard/WeatherCard';
import type { ChatMessage, Style } from '../../../../types';
import { isWeatherResponse, isGeneralResponse } from '../../../../helpers/messageHelpers';
import styles from './AIMessage.module.scss';

interface AIMessageProps {
  readonly message: ChatMessage;
}

function styleBadgeVariant(style: Style): 'style-expert' | 'style-child' {
  return style === 'child' ? 'style-child' : 'style-expert';
}

export default function AIMessage({ message }: AIMessageProps) {
  const { model_used, tool_used, style_applied, response } = message;
  const isChild = style_applied === 'child';

  let body: React.ReactNode;

  if (response && isWeatherResponse(response)) {
    body = (
      <>
        <WeatherCard data={response} style={style_applied ?? undefined} />
        {/* Follow-up text shown below weather card when present */}
        {isGeneralResponse(response) && (response as { answer?: string }).answer && (
          <p className={styles.text}>{(response as { answer: string }).answer}</p>
        )}
      </>
    );
  } else if (response && isGeneralResponse(response)) {
    body = (
      <>
        <p className={styles.text}>{response.answer}</p>
        {response.follow_up && (
          <p className={styles.followUp}>{response.follow_up}</p>
        )}
      </>
    );
  } else {
    body = <p className={styles.text}>{message.content}</p>;
  }

  return (
    <div className={styles.wrapper}>
      {/* Badge row */}
      {(model_used || tool_used || style_applied) && (
        <div className={styles.badges}>
          {model_used && <Badge label={`model: ${model_used}`} variant="model" />}
          {tool_used && <Badge label={tool_used} variant="tool" />}
          {style_applied && (
            <Badge label={style_applied} variant={styleBadgeVariant(style_applied)} />
          )}
        </div>
      )}

      {/* Bubble */}
      <div className={`${styles.bubble} ${isChild ? styles.childBubble : ''}`}>
        {body}
      </div>
    </div>
  );
}
