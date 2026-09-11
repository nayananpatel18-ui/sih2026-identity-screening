# AI-Powered Identity Screening & Fraud Resilience System

**Problem Statement ID:** SIH26188  
**Organization:** Ministry of Home Affairs (MHA) — Sashastra Seema Bal (SSB), Police II Division  
**Category:** Software | **Theme:** Blockchain & Cybersecurity  

---

## 🎯 Overview

An AI-driven decision-assist system built for border security officers. It analyzes identity documents and person biometrics, performs visual forensics and structural validations, correlates evidence across documents, produces a transparent risk & uncertainty assessment (GREEN / AMBER / RED / GREY), and provides clear human-readable explanations.

The system assists—never replaces—human officers, operating strictly on the principle of evidence-backed decision support.

---

## 🏗️ System Architecture

```
[ Primary Doc ] + [ Secondary Doc ] + [ Person Photo ]
                         │
                         ▼
             [ Data Adapter Layer ]
       (Synthetic / MIDV / DocTamper / IDNet)
                         │
                         ▼
          [ Multimodal Forensic Pipeline ]
   ├── Document Intelligence (OCR & Field Extraction)
   ├── Visual Forensics (Tampering, Photo Swap, Noise)
   ├── Structural Validation (MRZ, Checksums, Dates)
   ├── Biometric Verification (Face Embedding Comparison)
   └── Cross-Document Consistency (Passport ↔ Visa ↔ Person)
                         │
                         ▼
        [ Risk & Uncertainty Engine ]
             (GREEN / AMBER / RED / GREY)
                         │
                         ▼
            [ Explanation Panel & Graph ]
                         │
                         ▼
               [ Human Officer Review ]
```

---

## 📁 Repository Structure

```
c:\Projects\AIFakeDocDetector\
├── backend/                  # FastAPI Python Service
│   ├── app/
│   │   ├── api/              # API Endpoints (Health, Screening, Data)
│   │   ├── core/             # App Config & Firebase Service Setup
│   │   ├── data/             # Canonical Models & Data Adapters
│   │   └── services/         # Forensic & Biometric Engines
│   └── requirements.txt
├── frontend/                 # React + Vite + TypeScript Dashboard
│   ├── src/
│   │   ├── components/       # UI Components & Evidence Displays
│   │   ├── pages/            # Screening Dashboard & Lab Pages
│   │   └── services/         # API Client Integration
│   └── package.json
├── datasets/                 # Controlled Synthetic Demo Cases
│   └── synthetic/            # Genuine, Tampered, & Uncertain cases
└── README.md
```

---

## 🚀 Quickstart Guide

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API docs available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI available at: `http://localhost:5173`

---

## 🔒 Technical & Ethical Honesty
- **No Direct Government System Access**: Operating on synthetic/de-identified demo documents.
- **Decision Assist Only**: AI generates structured risk & evidence; final action remains with the officer.
- **Low Quality ≠ Fraud**: Insufficient image quality results in `GREY` (Human Review Required), avoiding false accusations.
