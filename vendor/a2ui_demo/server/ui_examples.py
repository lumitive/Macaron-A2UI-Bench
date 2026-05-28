"""Few-shot examples for teaching the LLM how to construct A2UI JSON."""

EMAIL_LIST_EXAMPLE = r"""
Example: User asks "Show me my recent emails"
Tool returns a list of emails. Generate A2UI to display them as cards in a scrollable list.

IMPORTANT: In template children, use RELATIVE paths (without leading /) like "subject", "from".
These resolve relative to each template item, e.g. /emails/email1/subject, /emails/email2/subject.

Text response:
Here are your recent emails:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "emails-surface-1",
      "root": "root-col",
      "styles": {"primaryColor": "#1976D2"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "emails-surface-1",
      "components": [
        {
          "id": "root-col",
          "component": {
            "Column": {
              "children": {"explicitList": ["title-text", "email-list"]}
            }
          }
        },
        {
          "id": "title-text",
          "component": {
            "Text": {
              "text": {"literalString": "Recent Emails"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "email-list",
          "component": {
            "List": {
              "children": {
                "template": {
                  "componentId": "email-card",
                  "dataBinding": "/emails"
                }
              },
              "direction": "vertical"
            }
          }
        },
        {
          "id": "email-card",
          "component": {
            "Card": {"child": "email-card-content"}
          }
        },
        {
          "id": "email-card-content",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["email-subject", "email-from", "email-snippet"]
              }
            }
          }
        },
        {
          "id": "email-subject",
          "component": {
            "Text": {
              "text": {"path": "subject"},
              "usageHint": "h4"
            }
          }
        },
        {
          "id": "email-from",
          "component": {
            "Text": {
              "text": {"path": "from"},
              "usageHint": "caption"
            }
          }
        },
        {
          "id": "email-snippet",
          "component": {
            "Text": {
              "text": {"path": "snippet"},
              "usageHint": "body"
            }
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "emails-surface-1",
      "path": "/",
      "contents": [
        {
          "key": "emails",
          "valueMap": [
            {
              "key": "email1",
              "valueMap": [
                {"key": "subject", "valueString": "Meeting Tomorrow"},
                {"key": "from", "valueString": "alice@example.com"},
                {"key": "snippet", "valueString": "Hi, just a reminder about our meeting..."}
              ]
            },
            {
              "key": "email2",
              "valueMap": [
                {"key": "subject", "valueString": "Project Update"},
                {"key": "from", "valueString": "bob@example.com"},
                {"key": "snippet", "valueString": "The latest build is ready for review..."}
              ]
            }
          ]
        }
      ]
    }
  }
]
"""

NEWS_CARDS_EXAMPLE = r"""
Example: User asks "Search for latest AI news"
Tool returns news articles. Generate A2UI to display them as rich cards.

IMPORTANT: In template children, use RELATIVE paths (without leading /) like "title", "source".
These resolve relative to each template item, e.g. /articles/a1/title, /articles/a2/title.

Text response:
Here are the latest AI news articles I found:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "news-surface-1",
      "root": "root-col",
      "styles": {"primaryColor": "#FF5722"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "news-surface-1",
      "components": [
        {
          "id": "root-col",
          "component": {
            "Column": {
              "children": {"explicitList": ["title-text", "news-list"]}
            }
          }
        },
        {
          "id": "title-text",
          "component": {
            "Text": {
              "text": {"literalString": "AI News"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "news-list",
          "component": {
            "List": {
              "children": {
                "template": {
                  "componentId": "news-card",
                  "dataBinding": "/articles"
                }
              },
              "direction": "vertical"
            }
          }
        },
        {
          "id": "news-card",
          "component": {
            "Card": {"child": "news-card-content"}
          }
        },
        {
          "id": "news-card-content",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["news-title", "news-source", "news-desc", "news-action-row"]
              }
            }
          }
        },
        {
          "id": "news-title",
          "component": {
            "Text": {
              "text": {"path": "title"},
              "usageHint": "h4"
            }
          }
        },
        {
          "id": "news-source",
          "component": {
            "Text": {
              "text": {"path": "source"},
              "usageHint": "caption"
            }
          }
        },
        {
          "id": "news-desc",
          "component": {
            "Text": {
              "text": {"path": "description"},
              "usageHint": "body"
            }
          }
        },
        {
          "id": "news-action-row",
          "component": {
            "Row": {
              "children": {"explicitList": ["read-more-btn"]},
              "distribution": "end"
            }
          }
        },
        {
          "id": "read-more-btn",
          "component": {
            "Button": {
              "child": "read-more-text",
              "primary": true,
              "action": {
                "name": "read_article",
                "context": [
                  {"key": "title", "value": {"path": "title"}}
                ]
              }
            }
          }
        },
        {
          "id": "read-more-text",
          "component": {
            "Text": {
              "text": {"literalString": "Read More"}
            }
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "news-surface-1",
      "path": "/",
      "contents": [
        {
          "key": "articles",
          "valueMap": [
            {
              "key": "a1",
              "valueMap": [
                {"key": "title", "valueString": "GPT-5 Released with Major Improvements"},
                {"key": "source", "valueString": "TechCrunch - 2 hours ago"},
                {"key": "description", "valueString": "OpenAI announces the next generation model with breakthrough reasoning capabilities."}
              ]
            },
            {
              "key": "a2",
              "valueMap": [
                {"key": "title", "valueString": "Google DeepMind Achieves New Milestone"},
                {"key": "source", "valueString": "The Verge - 5 hours ago"},
                {"key": "description", "valueString": "DeepMind's latest research shows significant progress in scientific discovery."}
              ]
            }
          ]
        }
      ]
    }
  }
]
"""

SIMPLE_DATA_EXAMPLE = r"""
Example: User asks "What's the weather like?"
Tool returns simple data. Use plain text with a small card for key info.
For non-list data, use literalString directly instead of data binding.

Text response:
The current weather in Beijing is sunny with a temperature of 25 degrees.

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "weather-surface-1",
      "root": "root-card",
      "styles": {"primaryColor": "#4CAF50"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "weather-surface-1",
      "components": [
        {
          "id": "root-card",
          "component": {
            "Card": {"child": "weather-col"}
          }
        },
        {
          "id": "weather-col",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["weather-icon-row", "temp-text", "desc-text"]
              }
            }
          }
        },
        {
          "id": "weather-icon-row",
          "component": {
            "Row": {
              "children": {"explicitList": ["weather-icon", "city-text"]},
              "alignment": "center"
            }
          }
        },
        {
          "id": "weather-icon",
          "component": {
            "Icon": {
              "name": {"literalString": "locationOn"}
            }
          }
        },
        {
          "id": "city-text",
          "component": {
            "Text": {
              "text": {"literalString": "Beijing"},
              "usageHint": "h3"
            }
          }
        },
        {
          "id": "temp-text",
          "component": {
            "Text": {
              "text": {"literalString": "25 C - Sunny"},
              "usageHint": "h1"
            }
          }
        },
        {
          "id": "desc-text",
          "component": {
            "Text": {
              "text": {"literalString": "Clear skies throughout the day"},
              "usageHint": "body"
            }
          }
        }
      ]
    }
  }
]
"""

# New example: Tabs for categorized content
TABS_EXAMPLE = r"""
Example: User asks "Show me different categories of products"
Use Tabs to organize content into multiple views.

Text response:
Here are the products organized by category:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "products-tabs-1",
      "root": "root-col",
      "styles": {"primaryColor": "#9C27B0"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "products-tabs-1",
      "components": [
        {
          "id": "root-col",
          "component": {
            "Column": {
              "children": {"explicitList": ["title-text", "product-tabs"]}
            }
          }
        },
        {
          "id": "title-text",
          "component": {
            "Text": {
              "text": {"literalString": "Product Categories"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "product-tabs",
          "component": {
            "Tabs": {
              "tabItems": [
                {"title": {"literalString": "Electronics"}, "child": "electronics-content"},
                {"title": {"literalString": "Books"}, "child": "books-content"},
                {"title": {"literalString": "Clothing"}, "child": "clothing-content"}
              ]
            }
          }
        },
        {
          "id": "electronics-content",
          "component": {
            "Column": {
              "children": {"explicitList": ["elec-item1", "elec-item2"]}
            }
          }
        },
        {
          "id": "elec-item1",
          "component": {
            "Text": {"text": {"literalString": "- iPhone 15 Pro - $999"}, "usageHint": "body"}
          }
        },
        {
          "id": "elec-item2",
          "component": {
            "Text": {"text": {"literalString": "- MacBook Air M3 - $1299"}, "usageHint": "body"}
          }
        },
        {
          "id": "books-content",
          "component": {
            "Column": {
              "children": {"explicitList": ["book-item1", "book-item2"]}
            }
          }
        },
        {
          "id": "book-item1",
          "component": {
            "Text": {"text": {"literalString": "- Clean Code - $45"}, "usageHint": "body"}
          }
        },
        {
          "id": "book-item2",
          "component": {
            "Text": {"text": {"literalString": "- Design Patterns - $55"}, "usageHint": "body"}
          }
        },
        {
          "id": "clothing-content",
          "component": {
            "Column": {
              "children": {"explicitList": ["cloth-item1"]}
            }
          }
        },
        {
          "id": "cloth-item1",
          "component": {
            "Text": {"text": {"literalString": "- Winter Jacket - $120"}, "usageHint": "body"}
          }
        }
      ]
    }
  }
]
"""

# New example: Form with TextField, CheckBox, Slider, MultipleChoice
FORM_EXAMPLE = r"""
Example: User asks "Create a feedback form" or needs user input
Use TextField, CheckBox, Slider, MultipleChoice for interactive forms.
Form values are bound to data model paths for bidirectional updates.

Text response:
Please fill out this feedback form:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "feedback-form-1",
      "root": "root-card",
      "styles": {"primaryColor": "#2196F3"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "feedback-form-1",
      "components": [
        {
          "id": "root-card",
          "component": {
            "Card": {"child": "form-col"}
          }
        },
        {
          "id": "form-col",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["form-title", "name-field", "email-field", "rating-section", "features-section", "subscribe-check", "divider1", "submit-btn"]
              }
            }
          }
        },
        {
          "id": "form-title",
          "component": {
            "Text": {
              "text": {"literalString": "Feedback Form"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "name-field",
          "component": {
            "TextField": {
              "label": {"literalString": "Your Name"},
              "text": {"path": "/form/name"},
              "textFieldType": "shortText"
            }
          }
        },
        {
          "id": "email-field",
          "component": {
            "TextField": {
              "label": {"literalString": "Email Address"},
              "text": {"path": "/form/email"},
              "textFieldType": "shortText",
              "validationRegexp": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            }
          }
        },
        {
          "id": "rating-section",
          "component": {
            "Column": {
              "children": {"explicitList": ["rating-label", "rating-slider"]}
            }
          }
        },
        {
          "id": "rating-label",
          "component": {
            "Text": {
              "text": {"literalString": "Rate your experience (1-10):"},
              "usageHint": "body"
            }
          }
        },
        {
          "id": "rating-slider",
          "component": {
            "Slider": {
              "value": {"path": "/form/rating"},
              "minValue": 1,
              "maxValue": 10
            }
          }
        },
        {
          "id": "features-section",
          "component": {
            "Column": {
              "children": {"explicitList": ["features-label", "features-choice"]}
            }
          }
        },
        {
          "id": "features-label",
          "component": {
            "Text": {
              "text": {"literalString": "Which features do you like?"},
              "usageHint": "body"
            }
          }
        },
        {
          "id": "features-choice",
          "component": {
            "MultipleChoice": {
              "selections": {"path": "/form/features"},
              "options": [
                {"label": {"literalString": "Speed"}, "value": "speed"},
                {"label": {"literalString": "Design"}, "value": "design"},
                {"label": {"literalString": "Features"}, "value": "features"},
                {"label": {"literalString": "Support"}, "value": "support"}
              ],
              "maxAllowedSelections": 3
            }
          }
        },
        {
          "id": "subscribe-check",
          "component": {
            "CheckBox": {
              "label": {"literalString": "Subscribe to newsletter"},
              "value": {"path": "/form/subscribe"}
            }
          }
        },
        {
          "id": "divider1",
          "component": {
            "Divider": {"axis": "horizontal"}
          }
        },
        {
          "id": "submit-btn",
          "component": {
            "Button": {
              "child": "submit-text",
              "primary": true,
              "action": {
                "name": "submit_feedback",
                "context": [
                  {"key": "name", "value": {"path": "/form/name"}},
                  {"key": "email", "value": {"path": "/form/email"}},
                  {"key": "rating", "value": {"path": "/form/rating"}},
                  {"key": "features", "value": {"path": "/form/features"}},
                  {"key": "subscribe", "value": {"path": "/form/subscribe"}}
                ]
              }
            }
          }
        },
        {
          "id": "submit-text",
          "component": {
            "Text": {"text": {"literalString": "Submit Feedback"}}
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "feedback-form-1",
      "path": "/",
      "contents": [
        {
          "key": "form",
          "valueMap": [
            {"key": "name", "valueString": ""},
            {"key": "email", "valueString": ""},
            {"key": "rating", "valueNumber": 5},
            {"key": "subscribe", "valueBoolean": false}
          ]
        }
      ]
    }
  }
]
"""

# New example: Image gallery with horizontal list
IMAGE_GALLERY_EXAMPLE = r"""
Example: User asks "Show me photos" or tool returns images
Use Image component with horizontal List for gallery display.

Text response:
Here are the photos from your gallery:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "gallery-1",
      "root": "root-col",
      "styles": {"primaryColor": "#E91E63"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "gallery-1",
      "components": [
        {
          "id": "root-col",
          "component": {
            "Column": {
              "children": {"explicitList": ["gallery-title", "gallery-list", "selected-info"]}
            }
          }
        },
        {
          "id": "gallery-title",
          "component": {
            "Text": {
              "text": {"literalString": "Photo Gallery"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "gallery-list",
          "component": {
            "List": {
              "children": {
                "template": {
                  "componentId": "photo-card",
                  "dataBinding": "/photos"
                }
              },
              "direction": "horizontal"
            }
          }
        },
        {
          "id": "photo-card",
          "component": {
            "Card": {"child": "photo-content"}
          }
        },
        {
          "id": "photo-content",
          "component": {
            "Column": {
              "children": {"explicitList": ["photo-image", "photo-caption"]}
            }
          }
        },
        {
          "id": "photo-image",
          "component": {
            "Image": {
              "url": {"path": "url"},
              "usageHint": "mediumFeature",
              "fit": "cover"
            }
          }
        },
        {
          "id": "photo-caption",
          "component": {
            "Text": {
              "text": {"path": "caption"},
              "usageHint": "caption"
            }
          }
        },
        {
          "id": "selected-info",
          "component": {
            "Text": {
              "text": {"literalString": "Tap a photo to view details"},
              "usageHint": "caption"
            }
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "gallery-1",
      "path": "/",
      "contents": [
        {
          "key": "photos",
          "valueMap": [
            {
              "key": "p1",
              "valueMap": [
                {"key": "url", "valueString": "https://picsum.photos/200/200?random=1"},
                {"key": "caption", "valueString": "Sunset Beach"}
              ]
            },
            {
              "key": "p2",
              "valueMap": [
                {"key": "url", "valueString": "https://picsum.photos/200/200?random=2"},
                {"key": "caption", "valueString": "Mountain View"}
              ]
            },
            {
              "key": "p3",
              "valueMap": [
                {"key": "url", "valueString": "https://picsum.photos/200/200?random=3"},
                {"key": "caption", "valueString": "City Lights"}
              ]
            }
          ]
        }
      ]
    }
  }
]
"""

# New example: DateTimeInput for scheduling
DATETIME_EXAMPLE = r"""
Example: User asks "Schedule a meeting" or needs date/time selection
Use DateTimeInput for date and time picking.

Text response:
Please select a date and time for your meeting:

A2UI JSON:
[
  {
    "beginRendering": {
      "surfaceId": "schedule-1",
      "root": "root-card",
      "styles": {"primaryColor": "#009688"}
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "schedule-1",
      "components": [
        {
          "id": "root-card",
          "component": {
            "Card": {"child": "schedule-col"}
          }
        },
        {
          "id": "schedule-col",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["schedule-title", "date-section", "time-section", "confirm-btn"]
              }
            }
          }
        },
        {
          "id": "schedule-title",
          "component": {
            "Text": {
              "text": {"literalString": "Schedule Meeting"},
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "date-section",
          "component": {
            "Column": {
              "children": {"explicitList": ["date-label", "date-picker"]}
            }
          }
        },
        {
          "id": "date-label",
          "component": {
            "Text": {
              "text": {"literalString": "Select Date:"},
              "usageHint": "body"
            }
          }
        },
        {
          "id": "date-picker",
          "component": {
            "DateTimeInput": {
              "value": {"path": "/meeting/date"},
              "enableDate": true,
              "enableTime": false,
              "outputFormat": "yyyy-MM-dd"
            }
          }
        },
        {
          "id": "time-section",
          "component": {
            "Column": {
              "children": {"explicitList": ["time-label", "time-picker"]}
            }
          }
        },
        {
          "id": "time-label",
          "component": {
            "Text": {
              "text": {"literalString": "Select Time:"},
              "usageHint": "body"
            }
          }
        },
        {
          "id": "time-picker",
          "component": {
            "DateTimeInput": {
              "value": {"path": "/meeting/time"},
              "enableDate": false,
              "enableTime": true,
              "outputFormat": "HH:mm"
            }
          }
        },
        {
          "id": "confirm-btn",
          "component": {
            "Button": {
              "child": "confirm-text",
              "primary": true,
              "action": {
                "name": "confirm_meeting",
                "context": [
                  {"key": "date", "value": {"path": "/meeting/date"}},
                  {"key": "time", "value": {"path": "/meeting/time"}}
                ]
              }
            }
          }
        },
        {
          "id": "confirm-text",
          "component": {
            "Text": {"text": {"literalString": "Confirm Meeting"}}
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "schedule-1",
      "path": "/",
      "contents": [
        {
          "key": "meeting",
          "valueMap": [
            {"key": "date", "valueString": ""},
            {"key": "time", "valueString": ""}
          ]
        }
      ]
    }
  }
]
"""


def get_all_examples() -> str:
    return f"""
{EMAIL_LIST_EXAMPLE}

---

{NEWS_CARDS_EXAMPLE}

---

{SIMPLE_DATA_EXAMPLE}

---

{TABS_EXAMPLE}

---

{FORM_EXAMPLE}

---

{IMAGE_GALLERY_EXAMPLE}

---

{DATETIME_EXAMPLE}
"""
