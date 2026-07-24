export {};

declare global {
  interface Window {
    __A2UI_RENDER__?: {
      reset(): void;
      processTurn(messages: unknown[]): Promise<{ shouldCapture: boolean }>;
    };
  }
}
