# Course Assignment Grading Criteria

## 1. Overall Grading

The total score is **100 points**, consisting of three parts:

| Module | Full Score | Description |
|------|------|------|
| **Knowledge Assets** | 35 points | Independently graded |
| **Evaluation Benchmark** | 35 points | Independently graded |
| **Knowledge Q&A Project** | 30 points | Score from optional modules |

**Total Score = Knowledge Assets Score + Evaluation Benchmark Score + Knowledge Q&A Project Score**

---

## 2. Knowledge Assets Module (35 points)

### 2.1 Basic Requirements (21 points)
| Requirement | Full Score | Description |
| -------- | --- | ------------------------------------------------- |
| **Quantity Met** | 7 points | At least 20 valid knowledge sets (each containing content/, keywords.json, source.json) |
| **Files Complete** | 7 points | All three files present for each knowledge set, no missing files |
| **Format Standard** | 7 points | All use kebab-case format, no format errors |

### 2.2 Quality Requirements (14 points)
| Requirement | Full Score | Description |
|------|------|------|
| **Domain Breadth** | 5 points | Covers different types within the selected domain (e.g., computational experiments, wet experiments, reviews, domain introductions, etc.) |
| **Substantial Content** | 5 points | Knowledge set content is complete, not empty shells |
| **Reliable Sources** | 4 points | Academic papers have DOIs, web resources have valid URLs |

**Note**: Valid knowledge sets refer to those with substantial content, traceable sources, and compliant with specifications.

---

## 3. Evaluation Benchmark Module (35 points)

### 3.1 Basic Requirements (21 points)
| Requirement | Full Score | Description |
|------|------|------|
| **Question Quantity** | 7 points | At least 20 valid questions |
| **Answer Accuracy** | 7 points | All questions have correct answers |
| **Format Standard** | 7 points | Correct JSON format, all required fields present |

### 3.2 Quality Requirements (14 points)
| Requirement | Full Score | Description |
|------|------|------|
| **Question Quality** | 5 points | Questions are clearly stated, unambiguous |
| **Source Citation** | 5 points | Each question has accurate source citation |
| **Topic Classification** | 4 points | Topic classification is correct, using predefined topic terms |

**Note**: Valid questions refer to those that can be clearly answered, have accurate sources, and are correctly formatted.

---

## 4. Knowledge Q&A Project (30 points, from optional modules)

### 4.1 Optional Module Selection
Students select several tasks from optional modules, each with a **difficulty value i** (1=Basic, 2=Intermediate, 3=Challenge), **and the total sum of selected difficulty values must be 4**.

### 4.2 Score Calculation
1. **Each module is graded independently** (0-100 points), mainly assessing:
   - Whether the project can run successfully
   - Whether it passes the evaluation benchmark tests
   - Whether running results are demonstrated

2. **Weight Calculation**:
   ```
   Total Difficulty Sum = Sum of difficulty values of all selected modules
   Module Weight = Module Difficulty Value / Total Difficulty Sum
   ```

3. **Knowledge Q&A Project Score**:
   ```
   Weighted Total Score = Σ(Module Score × Module Weight)
   Knowledge Q&A Project Final Score = Weighted Total Score × 0.3
   ```

### 4.3 Example
Student selected:
- Module A (Difficulty 2, Score 80)
- Module B (Difficulty 1, Score 70)
- Module C (Difficulty 3, Score 90)

Calculation:
- Total Difficulty Sum = 2 + 1 + 3 = 6
- Module A Weight = 2/6 ≈ 0.333
- Module B Weight = 1/6 ≈ 0.167
- Module C Weight = 3/6 = 0.5
- Weighted Total Score = 80×0.333 + 70×0.167 + 90×0.5 = 26.64 + 11.69 + 45 = 83.33 points
- Knowledge Q&A Project Score = 83.33 × 0.3 = 25.0 points

---

## 5. Optional Module Difficulty Description

### 5.1 Difficulty 1 (Basic)
- Implement basic functionality
- Pass evaluation benchmarks
- Demonstrate basic results

### 5.2 Difficulty 2 (Intermediate)
- Optimize upon the basics
- Handle more edge cases
- Deeper result analysis

### 5.3 Difficulty 3 (Challenge)
- Technically challenging
- Implement innovative features
- In-depth analysis of results

---

## 6. Total Score Calculation Example

Assuming a student:
- Knowledge Assets Module: 30 points (out of 35)
- Evaluation Benchmark Module: 28 points (out of 35)
- Knowledge Q&A Project: 25 points (Weighted Total 83.33 × 0.3)

**Total Score = 30 + 28 + 25 = 83 points**
