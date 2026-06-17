# Gwadar City Guide Chatbot

A RAG-powered tourist assistant for Gwadar, Balochistan.
Answers questions about places, transport, restaurants, and emergencies.

## Features
- Tourist places with Google Maps links
- Car rental filter by budget
- Bus schedules and ticket prices
- Emergency numbers with 24/7 info
- Restaurant suggestions
- Follow-up question suggestions

## Setup (Local)

### 1. Get your Groq API key
Go to https://console.groq.com → Sign in → Get an API key.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Add your API key
```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 4. Add your JSON files to the data/ folder
Place these files inside the `data/` folder:
- `gwadar_places.json`
- `gwadar_transport_services.json`
- `gwadar_emergency_numbers.json`
- `gwadar_restaurants.json`

### 5. Run the app
```bash
streamlit run app.py
```
---

## Deploy to Streamlit Cloud (Free Public Link)

1. Push this project to GitHub (don't include .env file!)
2. Go to https://share.streamlit.io
3. Click "New app" → Select your repo → Main file: `app.py`
4. Go to Settings → Secrets → Add:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Click Deploy → Get your public link in 2-3 minutes!

---

## Project Structure
```
gwadar_chatbot/
├── app.py               ← Streamlit UI
├── rag_engine.py        ← RAG logic + Groq
├── requirements.txt     ← Dependencies
├── .env.example         ← API key template
├── data/
│   ├── gwadar_places.json
│   ├── gwadar_transport_services.json
│   ├── gwadar_emergency_numbers.json
│   └── gwadar_restaurants.json
└── README.md
```

## How It Works
1. User types a question
2. Groq classifies intent (places / transport / emergency / restaurant / general)
3. System searches the relevant JSON file
4. Groq formats a clean, friendly answer
5. 3 follow-up suggestions are shown as clickable buttons

## Adding More JSON Data
Just drop any new `.json` file in the `data/` folder and update `rag_engine.py` to load and search it.
