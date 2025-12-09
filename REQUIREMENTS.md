# Project Requirements and Specifications

## 1. Overview
This document outlines the requirements and specifications for the IFRS Document Translation System. The system translates Japanese IFRS documents into English, maintaining strict compliance with IFRS terminology and formatting standards.

## 2. Process Flow
**Word → JSON → Translation → Word Reconstruction**

The system operates as a pipeline of generic technology components:
1.  **Decomposition**: Breaking down the Word file into manageable JSON segments.
2.  **Transformation (Translation)**: Using AWS Bedrock (Claude 3/4.5) to translate content.
3.  **Reconstruction**: Reassembling the Word document while preserving:
    *   Text decorations/styles.
    *   Layout structure.
    *   Highlighting of attention-needed areas in the translation result.

## 3. Core Functionalities (Foundation Model Agents)
The Foundation Model (FM) performs three critical roles via a multi-agent approach:
1.  **Context Extraction**: Extracting company-specific vocabulary from past financial reports (e.g., Director names, industry terms, proper nouns).
2.  **IFRS Translation**: executing faithful machine translation compliant with IFRS standards.
3.  **Validation & Highlighting**: Checking numbers, translation consistency, and highlighting areas requiring human review in the output Word document.

**Goal**: Deliver high-precision translation and highlight alerts for users, keeping the architecture modular to adapt to the fast-evolving FM landscape.

## 4. Detailed Translation Rules

### 4.1. Terminology Compliance
Must use official IFRS English terminology.
*   `「当期純利益」` → **"Profit for the period"**
*   `「営業利益」` → **"Operating profit"**
*   `「減損損失」` → **"Impairment loss"**

### 4.2. Financial Statement Structure
*   **Balance Sheet**: Proper classification of Assets, Liabilities, and Equity.
*   **Income Statement**: Proper classification of Revenue and Expenses.
*   **Consistency**: Item names must align with IFRS presentation requirements.

### 4.3. Numeric Formatting & Units
*   **Scale Conversion**: Japanese "Ten thousand" base → English "Million" base.
    *   Typically displayed in **Millions of yen**.
    *   Decimal places: Generally 3 digits if needed.
    *   Use commas for thousands separators.
*   **Negative Numbers**: Convert `▲` to `( )` style (e.g., `▲100` → `(100)`).
*   **Conversion Table**:
    *   ¥1,000 → 0.001 million yen
    *   ¥1,000,000 → 1 million yen
    *   ¥100,000,000 (1 Oku) → 100 million yen
    *   ¥1,000,000,000 (10 Oku) → 1,000 million yen
    *   ¥1,000,000,000,000 (1 Cho) → 1,000,000 million yen

### 4.4. Notes & Qualitative Information
*   **Accounting Policies**: Accurate translation of policy descriptions.
*   **Estimates/Judgments**: Clear expression of estimation uncertainty.
*   **Cross-referencing**: Correct correspondence of note numbers and references.

### 4.5. Quality & Coherence
*   **Consistency**: Unified terminology throughout the document.
*   **Tense**: Appropriate use of past/present (especially for "Current Period" vs "Prior Period").
*   **Style**: Natural English phrasing for bullet points and paragraph structures.
*   **Legal/Audit**:
    *   Compliance with statutory disclosure requirements.
    *   Audit report wording suitable for IFRS audits.
    *   Inclusion of additional disclosures required by local regulators.

## 5. Configuration

### 5.1. AI Model
*   **Platform**: AWS Bedrock
*   **Model**: Anthropic Claude 3 Opus (referred to as "4.5" in requests, mapping to Opus for capabilities).
    *   *Note: Ensure `BEDROCK_MODEL_ID` is updated to the latest available Opus model.*

### 5.2. Environment Variables
*   `GOOGLE_API_KEY`: For auxiliary services.
*   `AWS_ACCESS_KEY_ID`: AWS Credential.
*   `AWS_SECRET_ACCESS_KEY`: AWS Credential.
*   `AWS_REGION`: `us-east-1` (or relevant region supporting the model).
*   `BEDROCK_MODEL_ID`: e.g., `anthropic.claude-3-opus-20240229-v1:0`.