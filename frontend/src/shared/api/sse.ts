export type SseEventHandler<TEvent extends string = string> = (
  event: TEvent,
  payload: unknown,
) => void;

export function parseSseJsonPayload(raw: string): unknown {
  if (!raw) {
    return null;
  }

  return JSON.parse(raw);
}
