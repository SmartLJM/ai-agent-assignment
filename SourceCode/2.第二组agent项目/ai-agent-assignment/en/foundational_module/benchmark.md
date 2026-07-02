# 1. Overview

Question metadata is organized in JSON format, each question saved as an independent `.json` file with the following common fields:

---

# 2. Common Fields

| Field        | Type    | Required | Description                                                                                                 |
| ------------ | ------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `id`         | string  | yes      | Unique identifier, format `Q{NNNN}`, e.g., `Q0001`                                                          |
| `question`   | string  | yes      | Complete question text, with options embedded for multiple‑choice questions (e.g., `"...\nA. ...\nB. ..."`) |
| `type`       | string  | yes      | `short‑answer` / `true‑false` / `single‑choice` / `multiple‑choice`                                         |
| `difficulty` | integer | yes      | Difficulty score 1–10                                                                                       |
| `answer`     | object  | yes      | Answer object, structure varies by question type, see 2.1                                                   |
| `sources`    | array   | yes      | Answer sources, see 2.2                                                                                     |
| `theme`      | array   | yes      | Theme and keywords, see 2.3                                                                                 |

## 2.1 `answer` — Answer Object

`answer` is an object that contains two required fields `type` and `content`, and may include additional fields depending on the question type.

### Quick Reference

| `answer.type` | Applicable Question Types | `answer.content` Type | Additional Fields |
| --- | --- | --- | --- |
| `exact` | true‑false | boolean | — |
| `exact` | single‑choice | string (e.g., `"A"`) | — |
| `exact` | multiple‑choice | array (e.g., `["A","C"]`) | — |
| `similar` | short‑answer | string | — |
| `keypoint` | short‑answer | string | `keypoints` |
| `similar` / `keypoint` | short‑answer (multi‑hop reasoning) | string | `reasoning_steps` |

### Field Details

**`keypoints`** — scoring‑point list (only for `type: "keypoint"`)

```json
"keypoints": [
  {"point": "Scoring point description", "score": point‑value}
]
```

**`reasoning_steps`** — reasoning‑step list (for multi‑hop reasoning questions)

```json
"reasoning_steps": [
  {
    "step": 1,
    "description": "Description of this reasoning step's goal",
    "source": {
      "knowledge_set_id": "...",
      "original_text": "..."
    }
  }
]
```

## 2.2 `sources` — Answer Sources

```json
"sources": [
  {
    "knowledge_set_id": "knowledge‑set ID",
    "original_text": "quoted original text fragment"
  }
]
```

## 2.3 `theme` — Theme Classification

List where each element is `{theme‑name: [keywords‑list]}`. All in kebab‑case.

```json
"theme": [
  {"climate‑science": ["greenhouse‑effect", "radiative‑forcing"]}
]
```

---

# 3. Complete Examples

## 3.1 Short‑Answer — Keypoint Scoring

```json
{
  "id": "Q0001",
  "question": "What is the main mechanism of the greenhouse effect?",
  "type": "short‑answer",
  "difficulty": 4,
  "answer": {
    "type": "keypoint",
    "content": "Greenhouse gases in the atmosphere (such as CO₂, CH₄) absorb long‑wave radiation emitted from the Earth’s surface and re‑emit it back toward the ground, raising surface temperatures.",
    "keypoints": [
      {"point": "Greenhouse gases absorb long‑wave radiation", "score": 3},
      {"point": "Re‑emit toward the ground", "score": 3},
      {"point": "Surface temperature rises", "score": 4}
    ]
  },
  "sources": [
    {
      "knowledge_set_id": "encyclopedia_001",
      "original_text": "Greenhouse gases absorb and re‑emit infrared radiation from Earth’s surface..."
    }
  ],
  "theme": [
    {"climate‑science": ["greenhouse‑effect", "radiative‑forcing", "climate"]}
  ]
}
```

## 3.2 Multiple‑Choice

```json
{
  "id": "Q0005",
  "question": "Which of the following are renewable energy sources?\nA. Solar energy\nB. Natural gas\nC. Wind energy\nD. Oil",
  "type": "multiple‑choice",
  "difficulty": 3,
  "answer": {
    "type": "exact",
    "content": ["A", "C"]
  },
  "sources": [
    {
      "knowledge_set_id": "encyclopedia_002",
      "original_text": "Renewable energy sources include solar, wind, hydro..."
    }
  ],
  "theme": [
    {"general": ["renewable‑energy", "solar‑energy", "wind‑energy", "fossil‑fuel"]}
  ]
}
```

## 3.3 Multi‑Hop Reasoning

```json
{
  "id": "Q0010",
  "question": "Why does the equatorial region have a small annual temperature range while inland regions have a large annual temperature range?",
  "type": "short‑answer",
  "difficulty": 6,
  "answer": {
    "type": "similar",
    "content": "Equatorial regions experience minimal seasonal variation in solar radiation, and the high specific heat of the ocean moderates temperatures; inland areas lack the moderating influence of oceans and, at higher latitudes, receive larger seasonal differences in solar radiation.",
    "reasoning_steps": [
      {
        "step": 1,
        "description": "Seasonal variation of solar radiation at the equator",
        "source": {
          "knowledge_set_id": "textbook_geography_001",
          "original_text": "Solar radiation at the equator remains relatively constant year‑round..."
        }
      },
      {
        "step": 2,
        "description": "Difference in specific heat between ocean and land and its effect on temperature moderation",
        "source": {
          "knowledge_set_id": "textbook_geography_001",
          "original_text": "Water has a higher specific heat capacity than land, moderating coastal temperatures..."
        }
      },
      {
        "step": 3,
        "description": "Inland regions lack ocean‑moderating influence",
        "source": {
          "knowledge_set_id": "textbook_geography_001",
          "original_text": "Inland regions lack the moderating influence of oceans, leading to greater temperature extremes..."
        }
      }
    ]
  },
  "sources": [
    {
      "knowledge_set_id": "textbook_geography_001",
      "original_text": "Equatorial regions experience minimal temperature variation..."
    }
  ],
  "theme": [
    {"general": ["latitude", "solar‑radiation", "climate"]},
    {"oceanography": ["ocean", "heat‑capacity"]}
  ]
}
```

---

# 4. File Organization

All question metadata files are stored in the same folder:

```
base‑module/
└── benchmark/
    ├── Q0001.json
    ├── Q0002.json
    └── ...
```

> `knowledge_set_id` should match the folder name in the knowledge‑set directory structure.