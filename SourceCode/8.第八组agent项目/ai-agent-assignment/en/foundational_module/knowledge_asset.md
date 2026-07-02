# 1. Overview

## 1.1 Knowledge Set

> [!important]
> In this specification, the term **knowledge set** refers to a self‑contained, logically coherent unit of knowledge—such as a research paper, a textbook, a course, an encyclopedia entry, an image, etc.

**Criteria for an independent knowledge set** (any one suffices):
- Has a unique identifier (DOI, URL, version number) and is independently accessible
- Has an independent creation date and author / publisher
- Content is self‑contained and understandable without additional context

---

# 2. Classification System

Each knowledge set is labeled with `theme` (topic) and `keywords`, stored in `keywords.json`.

> [!important]
> Themes and keywords must all be in **kebab‑case** format.

## 2.1 Theme Table (Predefined)

**Examples**:

| Theme | Description |
| --- | --- |
| `base` | basic / general |
| `neural‑network` | neural networks |
| `protein‑corona` | protein corona |
| `genomics‑sequencing` | genomics & sequencing |
| `drug‑discovery` | drug discovery |
| `bio‑imaging` | biological imaging |
| `single‑cell‑omics` | single‑cell omics |
| `climate‑science` | climate science |

## 2.2 Keywords

`keywords` should contain only the keywords **actually used** in the knowledge set; do not pad the list.

| Theme | Example Keywords |
| --- | --- |
| `base` | `research`, `review`, `wet‑experiment`, `computational‑model` |
| `protein‑corona` | `protein‑nanoparticle‑interaction`, `metal‑based` |
| `genomics‑sequencing` | `sequence‑analysis`, `multi‑omics`, `phylogenetics` |
| `drug‑discovery` | `virtual‑screening`, `molecular‑docking`, `de‑novo‑design` |
| `bio‑imaging` | `cell‑segmentation`, `tissue‑classification`, `medical‑image‑reconstruction` |
| `single‑cell‑omics` | `cell‑type‑annotation`, `trajectory‑analysis`, `spatial‑transcriptomics` |

## 2.3 Label File Format

```json
{
  "base": ["review"],
  "protein-corona": ["protein-nanoparticle-interaction", "metal-based"]
}
```

---

# 3. Source Types

## 3.1 Types and Permitted Formats

| Type | Folder | Allowed Formats |
| --- | --- | --- |
| Research Papers | `01‑academic/` | PDF, MD, TXT |
| Textbooks | `02‑textbook/` | PDF, MD, TXT, EPUB |
| Course Materials | `03‑course/` | PDF, PPT, MD, Word, TXT |
| Encyclopedia Resources | `04‑encyclopedia/` | PDF, MD, TXT, HTML |
| Project Files | `05‑project/` | any (excluding streaming data) |
| Domain Knowledge Bases | `06‑knowledge‑base/` | any (excluding streaming data) |
| Technical Blogs | `07‑blog/` | PDF, MD, TXT, HTML |
| Domain Forums | `08‑forum/` | PDF, MD, TXT, HTML |

## 3.2 Common Source Examples

| Type | Sources |
| --- | --- |
| Research Papers | Nature, Science, ScienceDirect |
| Textbooks | published textbooks |
| Course Materials | MIT OpenCourseWare, MOOC platforms |
| Encyclopedia Resources | Wikipedia, Baidu Baike |
| Project Files | GitHub, Hugging Face |
| Domain Knowledge Bases | UniProt, Gene Ontology, PDB |
| Technical Blogs | Medium, Zhihu |
| Domain Forums | Reddit, Stack Overflow |

## 3.3 Collection Notes

- Except for resources accessible via public APIs, original files **must be saved locally**
- When scraping web pages, remove irrelevant content (ads, navigation bars, etc.)
- For forum Q&A data, **preserve the complete exchange** of both parties; do not excerpt or delete. Information referenced via external links must be retrieved and included to complete the context
- All collected knowledge sets must be incorporated into the knowledge base, and the agent must be able to retrieve them
- If any knowledge set of type "project file" is collected, it must be packaged as an MCP tool or SKILL, and the agent must be able to use it directly

---

# 4. Source Attribution

Each knowledge set must have a `source.json` file recording source metadata.

## 4.1 Research Papers

At minimum include the following fields:

```json
{
  "doi": "10.18653/v1/2026.findings‑eacl.62",
  "title": "HiGraAgent: Dual‑Agent Adaptive Reasoning over Hierarchical Knowledge Graph ...",
  "journal": "Findings of the Association for Computational Linguistics: EACL 2026",
  "publisher": "Association for Computational Linguistics",
  "volume": "",
  "issue": "",
  "page": "1193‑1217",
  "citation_count": 0,
  "url": "https://doi.org/10.18653/v1/2026.findings‑eacl.62",
  "publication_date": "2026",
  "authors": [
    "Luu, Hung",
    "Nguyen, Long S. T.",
    "Pham, Trung",
    "Pham, Hieu",
    "Quan, Tho"
  ]
}
```

## 4.2 Other Web Resources

```json
{
  "url": "https://example.com/article",
  "date": "2026‑05‑21"
}
```

---

# 5. Storage Structure

```
root/
├── 01‑academic/          # research papers
├── 02‑textbook/          # textbooks
├── 03‑course/            # course materials
├── 04‑encyclopedia/      # encyclopedia resources
├── 05‑project/           # project files
├── 06‑knowledge‑base/    # domain knowledge bases
├── 07‑blog/              # technical blogs
└── 08‑forum/             # domain forums
```

Each knowledge set is organized as a unit `{knowledge_set_id}/` under its type folder:

```
{knowledge_set_id}/
├── content/              # original content
│   ├── xxx
│   └── ...
├── keywords.json         # theme & keyword labels
└── source.json           # source metadata
```

`knowledge_set_id` is the unique identifier of the knowledge set.

---

# 6. Assignment Requirements

## 6.1 Minimum Knowledge Set Count

Each student must collect and organize **at least 20 valid knowledge sets** to receive credit for this assignment.

Each knowledge set must contain all three of the following files without exception:

| Required File | Description |
| --- | --- |
| `content/` | Original content (permitted formats listed in Section 3.1 of this specification) |
| `keywords.json` | Theme and keyword labels (kebab‑case format) |
| `source.json` | Source metadata (research papers must include DOI) |

> [!tip]
> The count is based on actual "valid" knowledge sets. Duplicate submissions of the same content, different IDs pointing to the same source, or missing any of the three required files do not count toward the valid total.

## 6.2 Knowledge Base Integration Requirement

All collected knowledge sets **must be incorporated into the knowledge base**, and the agent must be able to successfully retrieve them. The integration workflow must comply with Section 3.3 and Chapter 5 of this specification.

## 6.3 Project Files Special Requirement

If any knowledge set of type "project file" is collected, the project must be packaged as an **MCP tool** or **SKILL**, and the agent must be able to invoke it directly. Simply uploading raw source code without packaging does not satisfy this requirement.

## 6.4 Theme Consistency Requirement

All knowledge sets must belong to the **same thematic domain**, for example:

- Protein Corona (`protein‑corona`)
- Neural Networks (`neural‑network`)
- Genomics & Sequencing (`genomics‑sequencing`)
- Drug Discovery (`drug‑discovery`)
- Biological Imaging (`bio‑imaging`)
- Single‑Cell Omics (`single‑cell‑omics`)

Cross‑domain knowledge sets (e.g., containing both protein corona and neural networks) should be classified under a broader theme such as `base` (basic / general).

## 6.5 Labeling Quality Requirements

| Dimension | Requirement |
| --- | --- |
| Theme labeling | Must select from the predefined theme vocabulary in Section 2.1 of this specification; no custom theme labels |
| Keyword labeling | Only include keywords **actually present** in the knowledge set; do not pad or over‑generalize; must follow kebab‑case format |
| Source information | Research papers must include DOI or a verifiable URL; web resources must include a valid access link and the date of retrieval |
