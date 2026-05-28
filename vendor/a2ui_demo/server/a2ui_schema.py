# A2UI Schema - Auto-generated from resources/components/schemas
import json

A2UI_SCHEMA = r"""
{
  "title": "A2UI Message Schema",
  "description": "Describes a JSON payload for an A2UI (Agent to UI) message, which is used to dynamically construct and update user interfaces. A message MUST contain exactly ONE of the action properties: 'beginRendering', 'surfaceUpdate', 'dataModelUpdate', or 'deleteSurface'.",
  "type": "object",
  "properties": {
    "beginRendering": {
      "type": "object",
      "description": "Signals the client to begin rendering a surface with a root component and specific styles.",
      "properties": {
        "surfaceId": {
          "type": "string",
          "description": "The unique identifier for the UI surface to be rendered."
        },
        "root": {
          "type": "string",
          "description": "The ID of the root component to render."
        },
        "styles": {
          "type": "object",
          "description": "Styling information for the UI.",
          "properties": {
            "font": {
              "type": "string",
              "description": "The primary font for the UI."
            },
            "primaryColor": {
              "type": "string",
              "description": "The primary UI color as a hexadecimal code (e.g., '#00BFFF').",
              "pattern": "^#[0-9a-fA-F]{6}$"
            }
          }
        }
      },
      "required": [
        "root",
        "surfaceId"
      ]
    },
    "surfaceUpdate": {
      "type": "object",
      "description": "Updates a surface with a new set of components.",
      "properties": {
        "surfaceId": {
          "type": "string",
          "description": "The unique identifier for the UI surface to be updated. If you are adding a new surface this *must* be a new, unique identified that has never been used for any existing surfaces shown."
        },
        "components": {
          "type": "array",
          "description": "A list containing all UI components for the surface.",
          "minItems": 1,
          "items": {
            "type": "object",
            "description": "Represents a *single* component in a UI widget tree. This component could be one of many supported types.",
            "properties": {
              "id": {
                "type": "string",
                "description": "The unique identifier for this component."
              },
              "weight": {
                "type": "number",
                "description": "The relative weight of this component within a Row or Column. This corresponds to the CSS 'flex-grow' property. Note: this may ONLY be set when the component is a direct descendant of a Row or Column."
              },
              "component": {
                "type": "object",
                "description": "A wrapper object that MUST contain exactly one key, which is the name of the component type (e.g., 'Text'). The value is an object containing the properties for that specific component.",
                "properties": {
                  "AudioPlayer": {
                    "type": "object",
                    "properties": {
                      "url": {
                        "type": "object",
                        "description": "The URL of the audio to play.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "required": [
                      "url"
                    ]
                  },
                  "TickSlider": {
                    "type": "object",
                    "properties": {
                      "value": {
                        "type": "object",
                        "description": "Current value bound to data model. Runtime snaps to the nearest tick of max/5 and writes back to value.path.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "max": {
                        "type": "object",
                        "description": "Maximum value bound to data model. The slider always divides this range into 5 equal steps.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    "required": [
                      "value",
                      "max"
                    ]
                  },
                  "Image": {
                    "type": "object",
                    "properties": {
                      "url": {
                        "type": "object",
                        "description": "Network URL or asset path for the image.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "size": {
                        "type": "string",
                        "description": "Image display size. \"small\" (40x40), \"medium\" (80x80), \"large\" (120x120), \"full\" (fills parent width, 1:1 ratio). Defaults to \"medium\".",
                        "enum": [
                          "small",
                          "medium",
                          "large",
                          "full"
                        ]
                      }
                    },
                    "required": [
                      "url"
                    ]
                  },
                  "Slider": {
                    "type": "object",
                    "properties": {
                      "value": {
                        "type": "object",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "minValue": {
                        "type": "number"
                      },
                      "maxValue": {
                        "type": "number"
                      }
                    },
                    "required": [
                      "value"
                    ]
                  },
                  "Button": {
                    "type": "object",
                    "properties": {
                      "child": {
                        "type": "string",
                        "description": "The ID of a child widget. This should always be set, e.g. to the ID of a Label widget."
                      },
                      "action": {
                        "type": "object",
                        "properties": {
                          "name": {
                            "type": "string"
                          },
                          "context": {
                            "type": "array",
                            "description": "A list of name-value pairs to be sent with the action to include data associated with the action, e.g. values that are submitted.",
                            "items": {
                              "type": "object",
                              "properties": {
                                "key": {
                                  "type": "string"
                                },
                                "value": {
                                  "type": "object",
                                  "properties": {
                                    "path": {
                                      "type": "string",
                                      "description": "A path in the data model which should be bound to an input element, e.g. a string reference for a text field, or number reference for a slider."
                                    },
                                    "literalString": {
                                      "type": "string",
                                      "description": "A literal string relevant to the action"
                                    },
                                    "literalNumber": {
                                      "type": "number",
                                      "description": "A literal number relevant to the action"
                                    },
                                    "literalBoolean": {
                                      "type": "boolean",
                                      "description": "A literal boolean relevant to the action"
                                    }
                                  }
                                }
                              },
                              "required": [
                                "key",
                                "value"
                              ]
                            }
                          }
                        },
                        "required": [
                          "name"
                        ]
                      },
                      "style": {
                        "type": "string",
                        "description": "The visual style of the button. \"primary\" renders a gradient background, \"secondary\" renders a white outlined button, \"plain\" renders a text-only button with no background. Defaults to \"primary\".",
                        "enum": [
                          "primary",
                          "secondary",
                          "plain"
                        ]
                      },
                      "enabled": {
                        "type": "object",
                        "description": "Whether the button is enabled. Binds to a boolean in the data model. Defaults to true when omitted.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      }
                    },
                    "required": [
                      "child",
                      "action"
                    ]
                  },
                  "ActionSelectionList": {
                    "type": "object",
                    "description": "A single-select list with built-in action dispatch. On first valid selection, it writes selection data and sends an action with selectedValue and selectedIndex injected into context.",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "Single-select value container. Although this is an array, only the first valid value is used for rendering.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "action": {
                        "type": "object",
                        "description": "Action emitted on first valid selection. Automatically enriched with selectedValue and selectedIndex.",
                        "properties": {
                          "name": {
                            "type": "string"
                          },
                          "context": {
                            "type": "array",
                            "description": "A list of name-value pairs to be sent with the action to include data associated with the action, e.g. values that are submitted.",
                            "items": {
                              "type": "object",
                              "properties": {
                                "key": {
                                  "type": "string"
                                },
                                "value": {
                                  "type": "object",
                                  "properties": {
                                    "path": {
                                      "type": "string",
                                      "description": "A path in the data model which should be bound to an input element, e.g. a string reference for a text field, or number reference for a slider."
                                    },
                                    "literalString": {
                                      "type": "string",
                                      "description": "A literal string relevant to the action"
                                    },
                                    "literalNumber": {
                                      "type": "number",
                                      "description": "A literal number relevant to the action"
                                    },
                                    "literalBoolean": {
                                      "type": "boolean",
                                      "description": "A literal boolean relevant to the action"
                                    }
                                  }
                                }
                              },
                              "required": [
                                "key",
                                "value"
                              ]
                            }
                          }
                        },
                        "required": [
                          "name"
                        ]
                      },
                      "items": {
                        "type": "array",
                        "description": "Selectable list items rendered as capsule containers.",
                        "items": {
                          "type": "object",
                          "properties": {
                            "value": {
                              "type": "string",
                              "description": "Unique value of this option."
                            },
                            "child": {
                              "type": "string",
                              "description": "ID of the child component rendered in this item."
                            }
                          },
                          "required": [
                            "value",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "action",
                      "items"
                    ]
                  },
                  "Label": {
                    "type": "object",
                    "properties": {
                      "text": {
                        "type": "object",
                        "description": "The text content to display.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "color": {
                        "type": "string",
                        "description": "The color level of the label text. Defaults to \"label\" (primary text color).",
                        "enum": [
                          "label",
                          "secondary",
                          "tertiary"
                        ]
                      },
                      "variant": {
                        "type": "string",
                        "description": "The typographic variant. Defaults to \"body\" (Noto Serif, regular, 16px). Each variant defines a fixed combination of font family, weight, size, and line height.",
                        "enum": [
                          "title",
                          "body",
                          "bodySemibold",
                          "bodySans",
                          "bodySansSemibold",
                          "subheadline",
                          "subheadlineSemibold",
                          "caption",
                          "captionSemibold"
                        ]
                      }
                    },
                    "required": [
                      "text"
                    ]
                  },
                  "OrderedSelectionList": {
                    "type": "object",
                    "description": "An ordered vertical selector for Macaron. Use it when selection order matters and should be visible as 1..n. Selected rows render a red circular order badge.",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "The currently selected option values, bound to a string-array path in the data model. Array order determines displayed ranks.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "maxSelection": {
                        "type": "integer",
                        "description": "Maximum number of items that can be selected. Once reached, unselected rows become disabled. Defaults to 1 (single-select)."
                      },
                      "requiredSelection": {
                        "type": "integer",
                        "description": "Minimum number of selections required to satisfy submission. When met, hasSelection is set to true. Defaults to 1."
                      },
                      "hasSelection": {
                        "type": "object",
                        "description": "Optional. Automatically set to true when the number of selected items reaches requiredSelection, false otherwise. Useful for enabling/disabling a related Button.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      },
                      "items": {
                        "type": "array",
                        "description": "Selectable options rendered as stacked rows. Each selected row shows a red order badge containing its 1-based rank from the current selection array.",
                        "items": {
                          "type": "object",
                          "properties": {
                            "value": {
                              "type": "string",
                              "description": "Unique value for this option."
                            },
                            "child": {
                              "type": "string",
                              "description": "ID of the child component rendered in this row. Suitable for longer labels or mixed text layouts."
                            }
                          },
                          "required": [
                            "value",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "items"
                    ]
                  },
                  "MultipleChoice": {
                    "type": "object",
                    "properties": {
                      "selections": {
                        "type": "object",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "options": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "label": {
                              "type": "object",
                              "properties": {
                                "path": {
                                  "type": "string",
                                  "description": "A relative or absolute path in the data model."
                                },
                                "literalString": {
                                  "type": "string"
                                }
                              }
                            },
                            "value": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "label",
                            "value"
                          ]
                        }
                      },
                      "maxAllowedSelections": {
                        "type": "integer"
                      }
                    },
                    "required": [
                      "selections",
                      "options"
                    ]
                  },
                  "Row": {
                    "type": "object",
                    "properties": {
                      "children": {
                        "type": "object",
                        "description": "Either an explicit list of widget IDs for the children, or a template with a data binding to the list of children.",
                        "properties": {
                          "explicitList": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "template": {
                            "type": "object",
                            "properties": {
                              "componentId": {
                                "type": "string"
                              },
                              "dataBinding": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "componentId",
                              "dataBinding"
                            ]
                          }
                        }
                      },
                      "distribution": {
                        "type": "string",
                        "enum": [
                          "start",
                          "center",
                          "end",
                          "spaceBetween",
                          "spaceAround",
                          "spaceEvenly"
                        ]
                      },
                      "alignment": {
                        "type": "string",
                        "enum": [
                          "start",
                          "center",
                          "end",
                          "stretch",
                          "baseline"
                        ]
                      }
                    },
                    "required": [
                      "children"
                    ]
                  },
                  "Video": {
                    "type": "object",
                    "properties": {
                      "url": {
                        "type": "object",
                        "description": "The URL of the video to play.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "required": [
                      "url"
                    ]
                  },
                  "Text": {
                    "type": "object",
                    "properties": {
                      "text": {
                        "type": "object",
                        "description": "While simple Markdown is supported (without HTML or image references), utilizing dedicated UI components is generally preferred for a richer and more structured presentation.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "usageHint": {
                        "type": "string",
                        "description": "A usage hint for the base text style.",
                        "enum": [
                          "h1",
                          "h2",
                          "h3",
                          "h4",
                          "h5",
                          "caption",
                          "body"
                        ]
                      }
                    },
                    "required": [
                      "text"
                    ]
                  },
                  "TagText": {
                    "type": "object",
                    "properties": {
                      "segments": {
                        "type": "object",
                        "description": "Array source for tag-style text segments. Supports either a data-model path or a literal array.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model pointing to an array of `{ text, style? }` objects."
                          },
                          "literalArray": {
                            "type": "array",
                            "description": "Literal array of text segments rendered in order and joined with ` \u00b7 `.",
                            "items": {
                              "type": "object",
                              "properties": {
                                "text": {
                                  "type": "string",
                                  "description": "Text content for this segment."
                                },
                                "style": {
                                  "type": "string",
                                  "description": "Optional color style for this segment. Defaults to `default`.",
                                  "enum": [
                                    "default",
                                    "secondary",
                                    "tertiary",
                                    "highlight"
                                  ]
                                }
                              },
                              "required": [
                                "text"
                              ]
                            }
                          }
                        }
                      }
                    },
                    "required": [
                      "segments"
                    ]
                  },
                  "SelectionWrap": {
                    "type": "object",
                    "description": "A horizontal flow selector for Macaron. Items wrap to new rows when space is insufficient. Selection state is shown by each item container (selected border + Label style linkage).",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "The currently selected option values, bound to a string-array path in the data model.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "maxSelection": {
                        "type": "integer",
                        "description": "Maximum number of items that can be selected. Once reached, unselected items become disabled. Defaults to 1 (single-select)."
                      },
                      "requiredSelection": {
                        "type": "integer",
                        "description": "Minimum number of selections required to satisfy submission. When met, hasSelection is set to true. Defaults to 1."
                      },
                      "hasSelection": {
                        "type": "object",
                        "description": "Optional. Automatically set to true when the number of selected items reaches requiredSelection, false otherwise. Useful for enabling/disabling a related Button.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      },
                      "items": {
                        "type": "array",
                        "description": "Selectable options rendered as wrapping chips. Each item uses its own child component and container-selected styling (no separate checkmark icon).",
                        "items": {
                          "type": "object",
                          "properties": {
                            "value": {
                              "type": "string",
                              "description": "Unique value for this option."
                            },
                            "child": {
                              "type": "string",
                              "description": "ID of the child component rendered inside this chip. Label descendants can react to selected state."
                            }
                          },
                          "required": [
                            "value",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "items"
                    ]
                  },
                  "DateTimeInput": {
                    "type": "object",
                    "properties": {
                      "value": {
                        "type": "object",
                        "description": "The selected date and/or time.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "enableDate": {
                        "type": "boolean"
                      },
                      "enableTime": {
                        "type": "boolean"
                      },
                      "firstDate": {
                        "type": "string",
                        "description": "The earliest selectable date (YYYY-MM-DD). Defaults to -9999-01-01."
                      },
                      "lastDate": {
                        "type": "string",
                        "description": "The latest selectable date (YYYY-MM-DD). Defaults to 9999-12-31."
                      }
                    },
                    "required": [
                      "value"
                    ]
                  },
                  "Map": {
                    "type": "object",
                    "properties": {
                      "latitude": {
                        "type": "object",
                        "description": "Latitude of the marker center. Must be finite. Values are normalized into [-90, 90].",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "longitude": {
                        "type": "object",
                        "description": "Longitude of the marker center. Must be finite. Values are normalized into [-180, 180].",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "zoom": {
                        "type": "object",
                        "description": "Initial map zoom. Optional. Defaults to 14 and clamps to [1, 19].",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "tileUrlTemplate": {
                        "type": "object",
                        "description": "Optional tile URL template. Defaults to OpenStreetMap https://tile.openstreetmap.org/{z}/{x}/{y}.png.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "required": [
                      "latitude",
                      "longitude"
                    ]
                  },
                  "List": {
                    "type": "object",
                    "properties": {
                      "children": {
                        "type": "object",
                        "properties": {
                          "explicitList": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "template": {
                            "type": "object",
                            "properties": {
                              "componentId": {
                                "type": "string"
                              },
                              "dataBinding": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "componentId",
                              "dataBinding"
                            ]
                          }
                        }
                      },
                      "direction": {
                        "type": "string",
                        "enum": [
                          "vertical",
                          "horizontal"
                        ]
                      },
                      "alignment": {
                        "type": "string",
                        "enum": [
                          "start",
                          "center",
                          "end",
                          "stretch"
                        ]
                      }
                    },
                    "required": [
                      "children"
                    ]
                  },
                  "DropdownSelection": {
                    "type": "object",
                    "description": "A button-like single selector for Macaron. Before selection, it shows a placeholder. On tap, it opens an anchored dropdown menu with plain-string options.",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "A string-array reference used as single-select storage. Runtime uses the first valid value for rendering.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "items": {
                        "type": "array",
                        "description": "Available options as plain strings. Item display and stored value are the same.",
                        "items": {
                          "type": "string"
                        }
                      },
                      "placeholder": {
                        "type": "object",
                        "description": "Optional placeholder text shown before valid selection. Defaults to \"Select location\".",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "hasSelection": {
                        "type": "object",
                        "description": "Optional boolean reference auto-updated by valid selection state.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "items"
                    ]
                  },
                  "Icon": {
                    "type": "object",
                    "properties": {
                      "name": {
                        "type": "object",
                        "description": "The name of the icon to display. This can be a literal string ('literalString') or a reference to a value in the data model ('path', e.g. '/icon/name').",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model.",
                            "enum": [
                              "abdominal",
                              "afferent",
                              "alarm",
                              "alarm-clock",
                              "all-application",
                              "anguished-face",
                              "application-effect",
                              "arrow-circle-down",
                              "arrow-circle-left",
                              "arrow-circle-right",
                              "arrow-circle-up",
                              "arrow-left",
                              "arrow-right",
                              "avocado-one",
                              "birthday-cake",
                              "book",
                              "book-one",
                              "book-open",
                              "bowl",
                              "calendar-thirty",
                              "camera",
                              "cheese",
                              "chef-hat-one",
                              "cook",
                              "copy",
                              "disappointed-face",
                              "dislike",
                              "emotion-unhappy",
                              "equalizer",
                              "fire",
                              "goblet",
                              "grinning-face-with-tightly-closed-eyes-open-mouth",
                              "hamburger-button",
                              "history",
                              "home",
                              "hourglass-null",
                              "knife-fork",
                              "leaves-two",
                              "left-c",
                              "lightning",
                              "like",
                              "link",
                              "local-two",
                              "mail-open",
                              "more",
                              "more-one",
                              "notes",
                              "phone-telephone",
                              "pic-one",
                              "platte",
                              "pot",
                              "preview-close-one",
                              "preview-open",
                              "protection",
                              "refresh",
                              "refrigerator",
                              "right-c",
                              "rss",
                              "search",
                              "setting-three",
                              "share",
                              "share-two",
                              "shopping-bag-one",
                              "sleep",
                              "smiling-face-with-squinting-eyes",
                              "star",
                              "stopwatch",
                              "success",
                              "tea-drink",
                              "thumbs-down",
                              "thumbs-up",
                              "time",
                              "tips"
                            ]
                          },
                          "literalString": {
                            "type": "string",
                            "enum": [
                              "abdominal",
                              "afferent",
                              "alarm",
                              "alarm-clock",
                              "all-application",
                              "anguished-face",
                              "application-effect",
                              "arrow-circle-down",
                              "arrow-circle-left",
                              "arrow-circle-right",
                              "arrow-circle-up",
                              "arrow-left",
                              "arrow-right",
                              "avocado-one",
                              "birthday-cake",
                              "book",
                              "book-one",
                              "book-open",
                              "bowl",
                              "calendar-thirty",
                              "camera",
                              "cheese",
                              "chef-hat-one",
                              "cook",
                              "copy",
                              "disappointed-face",
                              "dislike",
                              "emotion-unhappy",
                              "equalizer",
                              "fire",
                              "goblet",
                              "grinning-face-with-tightly-closed-eyes-open-mouth",
                              "hamburger-button",
                              "history",
                              "home",
                              "hourglass-null",
                              "knife-fork",
                              "leaves-two",
                              "left-c",
                              "lightning",
                              "like",
                              "link",
                              "local-two",
                              "mail-open",
                              "more",
                              "more-one",
                              "notes",
                              "phone-telephone",
                              "pic-one",
                              "platte",
                              "pot",
                              "preview-close-one",
                              "preview-open",
                              "protection",
                              "refresh",
                              "refrigerator",
                              "right-c",
                              "rss",
                              "search",
                              "setting-three",
                              "share",
                              "share-two",
                              "shopping-bag-one",
                              "sleep",
                              "smiling-face-with-squinting-eyes",
                              "star",
                              "stopwatch",
                              "success",
                              "tea-drink",
                              "thumbs-down",
                              "thumbs-up",
                              "time",
                              "tips"
                            ]
                          }
                        }
                      }
                    },
                    "required": [
                      "name"
                    ]
                  },
                  "Divider": {
                    "type": "object",
                    "properties": {
                      "axis": {
                        "type": "string",
                        "enum": [
                          "horizontal",
                          "vertical"
                        ]
                      }
                    }
                  },
                  "CircularProgress": {
                    "type": "object",
                    "properties": {
                      "value": {
                        "type": "object",
                        "description": "Current progress value.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "max": {
                        "type": "object",
                        "description": "Maximum progress value.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "style": {
                        "type": "string",
                        "description": "Progress color style. \"positive\" uses #8CA62A and \"danger\" uses #F63B39. Defaults to \"positive\".",
                        "enum": [
                          "positive",
                          "danger"
                        ]
                      },
                      "iconName": {
                        "type": "object",
                        "description": "Optional icon name for center content. Uses the same icon name set as the standard Icon component.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "required": [
                      "value",
                      "max"
                    ]
                  },
                  "TextField": {
                    "type": "object",
                    "description": "A text input field.",
                    "properties": {
                      "text": {
                        "type": "object",
                        "description": "The initial value of the text field.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "label": {
                        "type": "object",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "textFieldType": {
                        "type": "string",
                        "enum": [
                          "shortText",
                          "longText",
                          "number",
                          "date",
                          "obscured"
                        ]
                      },
                      "validationRegexp": {
                        "type": "string"
                      },
                      "onSubmittedAction": {
                        "type": "object",
                        "properties": {
                          "name": {
                            "type": "string"
                          },
                          "context": {
                            "type": "array",
                            "description": "A list of name-value pairs to be sent with the action to include data associated with the action, e.g. values that are submitted.",
                            "items": {
                              "type": "object",
                              "properties": {
                                "key": {
                                  "type": "string"
                                },
                                "value": {
                                  "type": "object",
                                  "properties": {
                                    "path": {
                                      "type": "string",
                                      "description": "A path in the data model which should be bound to an input element, e.g. a string reference for a text field, or number reference for a slider."
                                    },
                                    "literalString": {
                                      "type": "string",
                                      "description": "A literal string relevant to the action"
                                    },
                                    "literalNumber": {
                                      "type": "number",
                                      "description": "A literal number relevant to the action"
                                    },
                                    "literalBoolean": {
                                      "type": "boolean",
                                      "description": "A literal boolean relevant to the action"
                                    }
                                  }
                                }
                              },
                              "required": [
                                "key",
                                "value"
                              ]
                            }
                          }
                        },
                        "required": [
                          "name"
                        ]
                      }
                    }
                  },
                  "Rating": {
                    "type": "object",
                    "properties": {
                      "rating": {
                        "type": "object",
                        "description": "Rating value in the range 0 to 5. Runtime rounds and clamps out-of-range values.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalNumber": {
                            "type": "number"
                          }
                        }
                      },
                      "text": {
                        "type": "object",
                        "description": "Optional label displayed to the right of the stars.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "required": [
                      "rating"
                    ]
                  },
                  "Column": {
                    "type": "object",
                    "properties": {
                      "distribution": {
                        "type": "string",
                        "description": "How children are aligned on the main axis. ",
                        "enum": [
                          "start",
                          "center",
                          "end",
                          "spaceBetween",
                          "spaceAround",
                          "spaceEvenly"
                        ]
                      },
                      "alignment": {
                        "type": "string",
                        "description": "How children are aligned on the cross axis. ",
                        "enum": [
                          "start",
                          "center",
                          "end",
                          "stretch",
                          "baseline"
                        ]
                      },
                      "children": {
                        "type": "object",
                        "description": "Either an explicit list of widget IDs for the children, or a template with a data binding to the list of children.",
                        "properties": {
                          "explicitList": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "template": {
                            "type": "object",
                            "properties": {
                              "componentId": {
                                "type": "string"
                              },
                              "dataBinding": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "componentId",
                              "dataBinding"
                            ]
                          }
                        }
                      }
                    }
                  },
                  "Card": {
                    "type": "object",
                    "properties": {
                      "child": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "child"
                    ]
                  },
                  "SelectionList": {
                    "type": "object",
                    "description": "A vertical, list-style selector for Macaron. Best for options with longer text or richer row content. Each row shows a check indicator plus custom child content.",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "The currently selected option values, bound to a string-array path in the data model.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "maxSelection": {
                        "type": "integer",
                        "description": "Maximum number of items that can be selected. Once reached, unselected rows become disabled. Defaults to 1 (single-select)."
                      },
                      "requiredSelection": {
                        "type": "integer",
                        "description": "Minimum number of selections required to satisfy submission. When met, hasSelection is set to true. Defaults to 1."
                      },
                      "hasSelection": {
                        "type": "object",
                        "description": "Optional. Automatically set to true when the number of selected items reaches requiredSelection, false otherwise. Useful for enabling/disabling a related Button.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      },
                      "items": {
                        "type": "array",
                        "description": "Selectable options rendered as stacked rows. Prefer SelectionList for reading-heavy options.",
                        "items": {
                          "type": "object",
                          "properties": {
                            "value": {
                              "type": "string",
                              "description": "Unique value for this option."
                            },
                            "child": {
                              "type": "string",
                              "description": "ID of the child component rendered in this row. Suitable for longer labels or mixed text layouts."
                            }
                          },
                          "required": [
                            "value",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "items"
                    ]
                  },
                  "Modal": {
                    "type": "object",
                    "properties": {
                      "entryPointChild": {
                        "type": "string",
                        "description": "The widget that opens the modal."
                      },
                      "contentChild": {
                        "type": "string",
                        "description": "The widget to display in the modal."
                      }
                    },
                    "required": [
                      "entryPointChild",
                      "contentChild"
                    ]
                  },
                  "SelectionGrid": {
                    "type": "object",
                    "description": "An adaptive up-to-three-column selector for Macaron. Best for compact options that benefit from fast visual comparison. Each cell overlays a check indicator at the top-right without affecting child layout width.",
                    "properties": {
                      "selection": {
                        "type": "object",
                        "description": "The currently selected option values, bound to a string-array path in the data model.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalArray": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        }
                      },
                      "maxSelection": {
                        "type": "integer",
                        "description": "Maximum number of items that can be selected. Once reached, unselected cells become disabled. Defaults to 1 (single-select)."
                      },
                      "requiredSelection": {
                        "type": "integer",
                        "description": "Minimum number of selections required to satisfy submission. When met, hasSelection is set to true. Defaults to 1."
                      },
                      "hasSelection": {
                        "type": "object",
                        "description": "Optional. Automatically set to true when the number of selected items reaches requiredSelection, false otherwise. Useful for enabling/disabling a related Button.",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      },
                      "items": {
                        "type": "array",
                        "description": "Selectable options rendered as up-to-three-column grid cells. A top-right check indicator is overlaid with a 2px inset and does not occupy content space. Prefer SelectionGrid for short labels and compact content.",
                        "items": {
                          "type": "object",
                          "properties": {
                            "value": {
                              "type": "string",
                              "description": "Unique value for this option."
                            },
                            "child": {
                              "type": "string",
                              "description": "ID of the child component rendered in this grid cell. Suitable for compact labels or short mixed content."
                            }
                          },
                          "required": [
                            "value",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "selection",
                      "items"
                    ]
                  },
                  "Tabs": {
                    "type": "object",
                    "properties": {
                      "tabItems": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "title": {
                              "type": "object",
                              "properties": {
                                "path": {
                                  "type": "string",
                                  "description": "A relative or absolute path in the data model."
                                },
                                "literalString": {
                                  "type": "string"
                                }
                              }
                            },
                            "child": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "title",
                            "child"
                          ]
                        }
                      }
                    },
                    "required": [
                      "tabItems"
                    ]
                  },
                  "CheckBox": {
                    "type": "object",
                    "properties": {
                      "label": {
                        "type": "object",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalString": {
                            "type": "string"
                          }
                        }
                      },
                      "value": {
                        "type": "object",
                        "properties": {
                          "path": {
                            "type": "string",
                            "description": "A relative or absolute path in the data model."
                          },
                          "literalBoolean": {
                            "type": "boolean"
                          }
                        }
                      }
                    },
                    "required": [
                      "label",
                      "value"
                    ]
                  }
                }
              }
            },
            "required": [
              "id",
              "component"
            ]
          }
        }
      },
      "required": [
        "surfaceId",
        "components"
      ]
    },
    "dataModelUpdate": {
      "type": "object",
      "description": "Updates the data model for a surface.",
      "properties": {
        "surfaceId": {
          "type": "string",
          "description": "The unique identifier for the UI surface this data model update applies to."
        },
        "path": {
          "type": "string",
          "description": "An optional path to a location within the data model (e.g., '/user/name'). If omitted, or set to '/', the entire data model will be replaced."
        },
        "contents": {
          "type": "array",
          "description": "An array of data entries. Each entry must contain a 'key' and exactly one corresponding typed 'value*' property.",
          "items": {
            "type": "object",
            "description": "A single data entry. Exactly one 'value*' property should be provided alongside the key.",
            "properties": {
              "key": {
                "type": "string",
                "description": "The key for this data entry."
              },
              "valueString": {
                "type": "string"
              },
              "valueNumber": {
                "type": "number"
              },
              "valueBoolean": {
                "type": "boolean"
              },
              "valueMap": {
                "description": "Represents a map as an adjacency list.",
                "type": "array",
                "items": {
                  "type": "object",
                  "description": "One entry in the map. Exactly one 'value*' property should be provided alongside the key.",
                  "properties": {
                    "key": {
                      "type": "string"
                    },
                    "valueString": {
                      "type": "string"
                    },
                    "valueNumber": {
                      "type": "number"
                    },
                    "valueBoolean": {
                      "type": "boolean"
                    }
                  },
                  "required": [
                    "key"
                  ]
                }
              }
            },
            "required": [
              "key"
            ]
          }
        }
      },
      "required": [
        "contents",
        "surfaceId"
      ]
    },
    "deleteSurface": {
      "type": "object",
      "description": "Signals the client to delete the surface identified by 'surfaceId'.",
      "properties": {
        "surfaceId": {
          "type": "string",
          "description": "The unique identifier for the UI surface to be deleted."
        }
      },
      "required": [
        "surfaceId"
      ]
    }
  }
}
"""
