# 🗺️ Production Deployment Blueprint & Architecture Guide

This document contains the complete step-by-step blueprint for deploying the **RAG + Redis Semantic Cache Platform** to production using **Render** (FastAPI Backend), **Upstash** (Managed Cloud Redis), and **Vercel** (React Frontend).

---

## 📐 System Architecture

```text
┌─────────────────────────┐       ┌──────────────────────────────┐
│  React (Vite) Frontend  │ ────> │    FastAPI Backend Server    │
│   (Hosted on Vercel)    │       │      (Hosted on Render)      │
└─────────────────────────┘       └──────────────┬───────────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        │                        │                        │
                        ▼                        ▼                        ▼
              ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
              │  Upstash Cloud   │     │  ChromaDB Vector │     │ Multi-Key LLM    │
              │  Redis Cache     │     │  Embeddings Store│     │ (Groq / Mistral) │
              └──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 🔑 Environment Variables Specification

Set these environment variables on your cloud hosting platform (Render):

| Variable Name | Required | Description & Format |
| :--- | :---: | :--- |
| `GROQ_API_KEYS` | **YES** | Single key or comma-separated keys (`key1,key2,key3`) for key rotation fallback. |
| `MISTRAL_API_KEYS` | Optional | Fallback LLM keys if Groq hits rate limits (`mistral_key1,mistral_key2`). |
| `UPSTASH_REDIS_REST_URL` | **YES** | Upstash REST URL (e.g. `https://cuddly-flea-80300.upstash.io`). |
| `UPSTASH_REDIS_REST_TOKEN` | **YES** | Upstash REST authentication token. |
| `ALLOWED_ORIGINS` | **YES** | Allowed CORS origins (`*` or `https://your-app.vercel.app`). |

---

## 🚀 Part 1: Render Backend Deployment

1. **Push Codebase to GitHub**:
   ```powershell
   git add .
   git commit -m "Deploy: Multi-key resilience, requirements.txt, and blueprint"
   git push origin main
   ```

2. **Create Web Service on Render**:
   - Go to 👉 **[dashboard.render.com](https://dashboard.render.com)**.
   - Click **New +** ➔ **Web Service**.
   - Select repository: **`Satyamrtiwari/RAG_REDIS`**.
   
3. **Render Build & Start Settings**:
   - **Name**: `rag-redis-backend`
   - **Region**: Singapore or Oregon (US West)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.server:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables**:
   Add `GROQ_API_KEYS`, `UPSTASH_REDIS_REST_URL`, and `UPSTASH_REDIS_REST_TOKEN`.

---

## 🌐 Part 2: Vercel Frontend Deployment

1. **Log in to Vercel**:
   - Go to 👉 **[vercel.com](https://vercel.com)** and log in with GitHub.
2. **Add New Project**:
   - Click **"Add New..."** ➔ **"Project"**.
   - Select repository **`Satyamrtiwari/RAG_REDIS`**.
3. **Configure Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. **Deploy**:
   - Click **"Deploy"**. Vercel will deploy your React UI in ~45 seconds!

---

## 🔍 Part 3: Live Verification & Health Probes

Once deployed, verify backend and cache health:
- **Swagger Docs**: `https://<your-render-url>.onrender.com/docs`
- **Health Check**: `GET https://<your-render-url>.onrender.com/health`
- **Cache Stats**: `GET https://<your-render-url>.onrender.com/api/v1/cache/stats`
