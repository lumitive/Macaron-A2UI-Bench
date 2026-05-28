/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */
var __esDecorate = (this && this.__esDecorate) || function (ctor, descriptorIn, decorators, contextIn, initializers, extraInitializers) {
    function accept(f) { if (f !== void 0 && typeof f !== "function") throw new TypeError("Function expected"); return f; }
    var kind = contextIn.kind, key = kind === "getter" ? "get" : kind === "setter" ? "set" : "value";
    var target = !descriptorIn && ctor ? contextIn["static"] ? ctor : ctor.prototype : null;
    var descriptor = descriptorIn || (target ? Object.getOwnPropertyDescriptor(target, contextIn.name) : {});
    var _, done = false;
    for (var i = decorators.length - 1; i >= 0; i--) {
        var context = {};
        for (var p in contextIn) context[p] = p === "access" ? {} : contextIn[p];
        for (var p in contextIn.access) context.access[p] = contextIn.access[p];
        context.addInitializer = function (f) { if (done) throw new TypeError("Cannot add initializers after decoration has completed"); extraInitializers.push(accept(f || null)); };
        var result = (0, decorators[i])(kind === "accessor" ? { get: descriptor.get, set: descriptor.set } : descriptor[key], context);
        if (kind === "accessor") {
            if (result === void 0) continue;
            if (result === null || typeof result !== "object") throw new TypeError("Object expected");
            if (_ = accept(result.get)) descriptor.get = _;
            if (_ = accept(result.set)) descriptor.set = _;
            if (_ = accept(result.init)) initializers.unshift(_);
        }
        else if (_ = accept(result)) {
            if (kind === "field") initializers.unshift(_);
            else descriptor[key] = _;
        }
    }
    if (target) Object.defineProperty(target, contextIn.name, descriptor);
    done = true;
};
var __runInitializers = (this && this.__runInitializers) || function (thisArg, initializers, value) {
    var useValue = arguments.length > 2;
    for (var i = 0; i < initializers.length; i++) {
        value = useValue ? initializers[i].call(thisArg, value) : initializers[i].call(thisArg);
    }
    return useValue ? value : void 0;
};
import { html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { Root } from "./root.js";
import { A2uiMessageProcessor } from "@a2ui/web_core/data/model-processor";
import { structuralStyles } from "./styles.js";
import { extractStringValue } from "./utils/utils.js";
let MultipleChoice = (() => {
    let _classDecorators = [customElement("a2ui-multiplechoice")];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _classSuper = Root;
    let _description_decorators;
    let _description_initializers = [];
    let _description_extraInitializers = [];
    let _options_decorators;
    let _options_initializers = [];
    let _options_extraInitializers = [];
    let _selections_decorators;
    let _selections_initializers = [];
    let _selections_extraInitializers = [];
    let _isOpen_decorators;
    let _isOpen_initializers = [];
    let _isOpen_extraInitializers = [];
    var MultipleChoice = class extends _classSuper {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(_classSuper[Symbol.metadata] ?? null) : void 0;
            _description_decorators = [property()];
            _options_decorators = [property()];
            _selections_decorators = [property()];
            _isOpen_decorators = [state()];
            __esDecorate(this, null, _description_decorators, { kind: "accessor", name: "description", static: false, private: false, access: { has: obj => "description" in obj, get: obj => obj.description, set: (obj, value) => { obj.description = value; } }, metadata: _metadata }, _description_initializers, _description_extraInitializers);
            __esDecorate(this, null, _options_decorators, { kind: "accessor", name: "options", static: false, private: false, access: { has: obj => "options" in obj, get: obj => obj.options, set: (obj, value) => { obj.options = value; } }, metadata: _metadata }, _options_initializers, _options_extraInitializers);
            __esDecorate(this, null, _selections_decorators, { kind: "accessor", name: "selections", static: false, private: false, access: { has: obj => "selections" in obj, get: obj => obj.selections, set: (obj, value) => { obj.selections = value; } }, metadata: _metadata }, _selections_initializers, _selections_extraInitializers);
            __esDecorate(this, null, _isOpen_decorators, { kind: "accessor", name: "isOpen", static: false, private: false, access: { has: obj => "isOpen" in obj, get: obj => obj.isOpen, set: (obj, value) => { obj.isOpen = value; } }, metadata: _metadata }, _isOpen_initializers, _isOpen_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            MultipleChoice = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
        }
        #description_accessor_storage = __runInitializers(this, _description_initializers, null);
        get description() { return this.#description_accessor_storage; }
        set description(value) { this.#description_accessor_storage = value; }
        #options_accessor_storage = (__runInitializers(this, _description_extraInitializers), __runInitializers(this, _options_initializers, []));
        get options() { return this.#options_accessor_storage; }
        set options(value) { this.#options_accessor_storage = value; }
        #selections_accessor_storage = (__runInitializers(this, _options_extraInitializers), __runInitializers(this, _selections_initializers, []));
        get selections() { return this.#selections_accessor_storage; }
        set selections(value) { this.#selections_accessor_storage = value; }
        #isOpen_accessor_storage = (__runInitializers(this, _selections_extraInitializers), __runInitializers(this, _isOpen_initializers, false));
        get isOpen() { return this.#isOpen_accessor_storage; }
        set isOpen(value) { this.#isOpen_accessor_storage = value; }
        static { this.styles = [
            structuralStyles,
            css `
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        position: relative;
        font-family: 'Google Sans', 'Roboto', sans-serif;
      }

      .container {
        display: flex;
        flex-direction: column;
        gap: 4px;
        position: relative;
      }

      /* Header / Trigger */
      .dropdown-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: var(--md-sys-color-surface);
        border: 1px solid var(--md-sys-color-outline-variant);
        border-radius: 8px;
        cursor: pointer;
        user-select: none;
        transition: background-color 0.2s;
        box-shadow: var(--md-sys-elevation-level1);
      }

      .dropdown-header:hover {
        background: var(--md-sys-color-surface-container-low);
      }

      .header-text {
        font-size: 1rem;
        color: var(--md-sys-color-on-surface);
        font-weight: 400;
      }

      .chevron {
        color: var(--md-sys-color-primary);
        font-size: 1.2rem;
        transition: transform 0.2s ease;
      }

      .chevron.open {
        transform: rotate(180deg);
      }

      /* Dropdown List */
      .options-list {
        background: var(--md-sys-color-surface);
        border: 1px solid var(--md-sys-color-outline-variant);
        border-radius: 8px; /* Consistent rounding */
        box-shadow: none; /* Remove shadow for inline feel, or keep subtle */
        overflow-y: auto;
        padding: 0;
        display: none;
        flex-direction: column;
        margin-top: 4px; /* Small gap */
        max-height: 0; /* Animate height? */
        transition: max-height 0.2s ease-out;
      }

      .options-list.open {
        display: flex;
        max-height: 300px; /* Limit height but allow scrolling */
        border: 1px solid var(--md-sys-color-outline-variant); /* efficient border */
      }

      /* Option Item (Checkbox style) */
      .option-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        cursor: pointer;
        color: var(--md-sys-color-on-surface);
        font-size: 0.95rem;
        transition: background-color 0.1s;
      }

      .option-item:hover {
        background: var(--md-sys-color-surface-container-highest);
      }

      /* Custom Checkbox */
      .checkbox {
        width: 18px;
        height: 18px;
        border: 2px solid var(--md-sys-color-outline);
        border-radius: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        flex-shrink: 0;
      }

      .option-item.selected .checkbox {
        background: var(--md-sys-color-primary);
        border-color: var(--md-sys-color-primary);
      }

      .checkbox-icon {
        color: var(--md-sys-color-on-primary);
        font-size: 14px;
        font-weight: bold;
        opacity: 0;
        transform: scale(0.5);
        transition: all 0.2s;
      }

      .option-item.selected .checkbox-icon {
        opacity: 1;
        transform: scale(1);
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-8px); }
        to { opacity: 1; transform: translateY(0); }
      }
    `,
        ]; }
        #setBoundValue(value) {
            if (!this.selections || !this.processor) {
                return;
            }
            if (!("path" in this.selections)) {
                return;
            }
            if (!this.selections.path) {
                return;
            }
            this.processor.setData(this.component, this.selections.path, value, this.surfaceId ?? A2uiMessageProcessor.DEFAULT_SURFACE_ID);
        }
        getCurrentSelections() {
            if (!this.processor || !this.component || Array.isArray(this.selections)) {
                return [];
            }
            const selectionValue = this.processor.getData(this.component, this.selections.path, this.surfaceId ?? A2uiMessageProcessor.DEFAULT_SURFACE_ID);
            return Array.isArray(selectionValue) ? selectionValue : [];
        }
        toggleSelection(value) {
            const current = this.getCurrentSelections();
            if (current.includes(value)) {
                this.#setBoundValue(current.filter((v) => v !== value));
            }
            else {
                this.#setBoundValue([...current, value]);
            }
            this.requestUpdate();
        }
        render() {
            const currentSelections = this.getCurrentSelections();
            const count = currentSelections.length;
            const headerText = count > 0 ? `${count} Selected` : (this.description ?? "Select items");
            return html `
      <div class="container">
        <div 
          class="dropdown-header" 
          @click=${() => this.isOpen = !this.isOpen}
        >
          <span class="header-text">${headerText}</span>
          <span class="chevron ${this.isOpen ? "open" : ""}">
            <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
              <path d="M480-345 240-585l56-56 184 184 184-184 56 56-240 240Z"/>
            </svg>
          </span>
        </div>

        <div class="options-list ${this.isOpen ? "open" : ""}">
          ${this.options.map((option) => {
                const label = extractStringValue(option.label, this.component, this.processor, this.surfaceId);
                const isSelected = currentSelections.includes(option.value);
                return html `
              <div 
                class="option-item ${isSelected ? "selected" : ""}"
                @click=${(e) => {
                    e.stopPropagation();
                    this.toggleSelection(option.value);
                }}
              >
                <div class="checkbox">
                  <span class="checkbox-icon">✓</span>
                </div>
                <span>${label}</span>
              </div>
            `;
            })}
        </div>
      </div>
    `;
        }
        constructor() {
            super(...arguments);
            __runInitializers(this, _isOpen_extraInitializers);
        }
        static {
            __runInitializers(_classThis, _classExtraInitializers);
        }
    };
    return MultipleChoice = _classThis;
})();
export { MultipleChoice };
//# sourceMappingURL=multiple-choice.js.map