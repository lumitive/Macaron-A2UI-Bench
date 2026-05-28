import { SignalWatcher } from "@lit-labs/signals";
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import { provide } from "@lit/context";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";
import { theme as defaultTheme } from "./theme.js";

type A2UIModelProcessorInstance = InstanceType<
  typeof v0_8.Data.A2uiMessageProcessor
>;

@customElement("a2ui-theme-provider")
export class A2UIThemeProvider extends SignalWatcher(LitElement) {
  @provide({ context: UI.Context.themeContext })
  theme: v0_8.Types.Theme = defaultTheme;

  @property({ type: String })
  surfaceId: string = "";

  @property({ type: Object })
  surface: v0_8.Types.Surface | undefined;

  @property({ type: Object })
  processor: A2UIModelProcessorInstance | undefined;

  static styles = css`
    :host {
      display: block;
    }
  `;

  render() {
    if (!this.surface || !this.processor) {
      return html``;
    }

    return html`
      <a2ui-surface
        .surfaceId=${this.surfaceId}
        .surface=${this.surface}
        .processor=${this.processor}
      ></a2ui-surface>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "a2ui-theme-provider": A2UIThemeProvider;
  }
}
