# LUMI catalog inventory (0.8 Macaron / a2ui_demo → 0.9.1)

Source schemas: `vendor/a2ui_demo/resources/components/schemas/*_schema.json`  
Target catalogId: `lumi.ai:a2ui:lumi-catalog`  
MVP unique in Track 2: **Carousel**

| 0.8_name | class | 0.9.1_name | notes |
|----------|-------|------------|-------|
| Text | map_basic | Text | Official basic |
| Image | map_basic | Image | Official basic |
| Icon | map_basic | Icon | Official basic |
| Video | map_basic | Video | Official basic |
| AudioPlayer | map_basic | AudioPlayer | Official basic |
| Row | map_basic | Row | Official basic |
| Column | map_basic | Column | Official basic |
| List | map_basic | List | Official basic |
| Card | map_basic | Card | Official basic |
| Tabs | map_basic | Tabs | Official basic |
| Modal | map_basic | Modal | Official basic |
| Divider | map_basic | Divider | Official basic |
| Button | map_basic | Button | Official basic |
| TextField | map_basic | TextField | Official basic |
| CheckBox | map_basic | CheckBox | Official basic |
| Slider | map_basic | Slider | Official basic |
| DateTimeInput | map_basic | DateTimeInput | Official basic |
| Label | map_basic | Text | Prefer Text + variant |
| SelectionList | map_basic | ChoicePicker | 0.9.1 selection |
| TickSlider | map_basic | Slider | Map to Slider |
| MarkdownView | map_basic | Text | Or keep unique later if Markdown required |
| DropdownSelection | map_basic | ChoicePicker | |
| MultipleChoice | map_basic | ChoicePicker | |
| Carousel | **lumi_unique** | Carousel | **MVP Track 2**; 0.8 `children.explicitList` → 0.9.1 `ChildList` array |
| SelectionWrap | lumi_unique | SelectionWrap | Future |
| SelectionGrid | lumi_unique | SelectionGrid | Future |
| OrderedSelectionList | lumi_unique | OrderedSelectionList | Future |
| RollPicker | lumi_unique | RollPicker | Future |
| RollPickerCard | lumi_unique | RollPickerCard | Future |
| PasswordKeypad | lumi_unique | PasswordKeypad | Future |
| Map | lumi_unique | Map | Future |
| FilterTags | lumi_unique | FilterTags | Future |
| PhotoInput | lumi_unique | PhotoInput | Future |
| Rating | lumi_unique | Rating | Future |
| BottomBar | lumi_unique | BottomBar | Future |
| TagText | lumi_unique | TagText | Future |
| CircularProgress | lumi_unique | CircularProgress | Future |
| LinearProgress | lumi_unique | LinearProgress | Future |
| FullScreenModal | lumi_unique | FullScreenModal | Future / map Modal |
| OrderedDisplayList | lumi_unique | OrderedDisplayList | Future |
| ActionSelectionList | skip | — | Action envelope helper |
| BooleanAllOf | skip | — | Schema helper |
| Catalog | skip | — | Meta |
| SurfaceUpdate | skip | — | 0.8 envelope |

**map_basic aliases:** classified mappables above map to official basic names in generation guides.  
**lumi_unique authored (MVP):** Carousel only (≥1 required for D3≥1).
