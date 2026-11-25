# 🎓 UniFlow — The AI-Powered Academic Hub

> **Status**: 🚀 Fully Operational. *From static PDFs to interactive knowledge in seconds.*  
> 🔗 **Live Demo**: [**uni-flow-seven.vercel.app**](https://uni-flow-seven.vercel.app/)

---

## ✨ Experience Modern Academic AI
UniFlow is a premium, bento-style classroom platform designed to turn your study materials into a living, breathing knowledge base. It bridge the gap between static files and deep understanding using the latest in **Google Gemini AI** and **LaTeX-ready** math rendering.

### 🖼️ Interactive Product Slideshow

<!-- Slideshow Navigation Strip -->
<div align="center">
  <p><em>Click any slide below to explore each platform module:</em></p>
</div>

<details open>
<summary><b>🎞️ Slide 1 of 5: Student Bento Dashboard (Home Hub)</b></summary>
<p align="center">
  <a href="https://uni-flow-seven.vercel.app/" target="_blank">
    <img src="frontend/demo/Screenshot%202026-11-25%20111652.png" alt="Student Bento Dashboard" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
  </a>
  <br/>
  <b>Dashboard Overview:</b> Glassmorphic bento grid displaying enrolled classroom hubs, teacher badges, real-time activity indicators, and instant navigation.
</p>
</details>

<details>
<summary><b>🎞️ Slide 2 of 5: Secure Classroom Protocol (Join Network)</b></summary>
<p align="center">
  <a href="https://uni-flow-seven.vercel.app/" target="_blank">
    <img src="frontend/demo/Screenshot%202026-11-25%20111734.png" alt="Join Network Modal" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
  </a>
  <br/>
  <b>Instant Enrollment:</b> Secure 6-character access-code verification for frictionless onboarding into instructor classrooms.
</p>
</details>

<details>
<summary><b>🎞️ Slide 3 of 5: Classroom Hub & Live Resource Stream</b></summary>
<p align="center">
  <a href="https://uni-flow-seven.vercel.app/" target="_blank">
    <img src="frontend/demo/Screenshot%202026-11-25%20111746.png" alt="Classroom Hub" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
  </a>
  <br/>
  <b>Course Resource Stream:</b> Real-time feed featuring teacher announcements, uploaded syllabus notes, PDF documents, and automated AI ingestion status.
</p>
</details>

<details>
<summary><b>🎞️ Slide 4 of 5: AI-Powered Study Assistant (Agentic RAG)</b></summary>
<p align="center">
  <a href="https://uni-flow-seven.vercel.app/" target="_blank">
    <img src="frontend/demo/Screenshot%202026-11-25%20111812.png" alt="Study Assistant" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
  </a>
  <br/>
  <b>Intelligent Tutoring:</b> Multimodal study assistant grounded in uploaded course notes with real-time SSE token streaming, LaTeX mathematical formulas, and exact source references.
</p>
</details>

<details>
<summary><b>🎞️ Slide 5 of 5: Student Profile & Preferences Hub</b></summary>
<p align="center">
  <a href="https://uni-flow-seven.vercel.app/" target="_blank">
    <img src="frontend/demo/Screenshot%202026-11-25%20111926.png" alt="Profile Settings" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);" />
  </a>
  <br/>
  <b>Centralized Preferences:</b> Academic credentials, student roll number verification, role management, and notification settings.
</p>
</details>

---

## 🌟 Premium Features

### 🧠 AI-Powered Study Assistant
Not just a chatbot, but a specialized tutor for your classroom.
- **KaTeX Professional Math**: Beautiful, human-readable math notation ($\sigma(z)$ vs `$$\sigma(z)$$`).
- **Contextual Ingestion**: AI "reads" your PDFs and images to provide exact page citations.
- **Recent Material Awareness**: Deep integration with MongoDB to prioritize your latest uploads.

### 🍱 Bento-Style Dashboard
A stunning, glassmorphic interface that puts your learning first.
- **Classroom Cards**: Quick access to your academic hubs with instructor visibility.
- **Glassmorphic UI**: Sophisticated blur effects and a lightweight, premium feel.
- **Confetti Celebrations**: Modern micro-interactions for successful uploads and actions.

### ⚙️ High-Performance Engine
Built on a "state-of-the-art" technical foundation:
- **FastAPI Backend**: Rapid, asynchronous Python API with Server-Sent Events (SSE) token streaming.
- **Celery Worker Ingestion**: Non-blocking background file processing and multimodal extraction.
- **Vector Search Engine**: MongoDB Atlas Vector Search (`$vectorSearch` in cloud) / ChromaDB (local dev).
- **Google Gemini 2.5 AI**: Multi-key pool rotation for zero rate-limit interruptions.
- **Cloudinary CDN**: Persistent media delivery for seamless global student access.

---

## 🏗️ Technical Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 15+ (App Router), React 19, Tailwind CSS 4, Framer Motion, Vercel Edge |
| **Backend** | FastAPI, Python 3.11+, Celery, Starlette WebSockets |
| **AI / Agentic RAG** | Google Gemini 2.5 Flash, LangGraph v2, KaTeX Math Rendering |
| **Vector Search** | MongoDB Atlas Vector Search (Production) / ChromaDB (Local Dev) |
| **Database & Cache** | MongoDB Atlas (Cloud NoSQL), Upstash Redis (TLS Broker, Caching & Pub/Sub) |
| **Media & Storage** | Cloudinary CDN (Persistent Files), Container-Local Ephemeral Disk Cache |

---

## 🚀 Quick Start

### 🔧 Prerequisites
- **Node.js** (v20+)
- **Python** (v3.10+)
- **MongoDB** & **Redis** (Local or Cloud)
- **Google Gemini API Key**

### 💻 Local Development

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   # Setup .env with Gemini/Mongo keys
   python run.py
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Background Workers**:
   ```bash
   cd backend
   celery -A core.worker worker --loglevel=info
   ```

---

## 📚 Learn More
For a detailed log of the project's evolution and all implemented features from day one, see:
👉 **[The Full Update Timeline (UPDATES.md)](./UPDATES.md)**

---

##  Summary
UniFlow is more than a classroom hub; it’s an **intelligent ecosystem** for students and teachers. It combines a premium user experience with powerful AI automation to make learning more efficient, interactive, and visually stunning.
