# CogniSent

A sentiment analysis console for shoe reviews, built around a single trained
**CNN (Conv1D + embeddings)** model served by a FastAPI backend, with a
React + Tailwind frontend styled in a teal / beige / sky-blue palette.

Trained on `backend/data/nike_shoe_review.xlsx`, combined with a small
hand-written augmentation set (`backend/scripts/augment_data.py`) that
fills in common English sentiment vocabulary (worst, awful, poor,
disappointing, etc.) missing from the original data. The model is
already trained and saved under `backend/models/cnn/` — you don't need
to retrain anything to run the app.

## Two screens, on purpose

- **Analyze** — the home screen. Paste a single review or a batch, or
  upload a CSV, and get an instant prediction with a half-circle
  confidence gauge. Both modes have their own "Clear" button.
- **Dashboard** — total stats, a sentiment distribution chart, and your
  full review history grouped **by session**. Each session is one
  continuous visit to the app; click a session to expand and see every
  review analyzed during it. "Clear all history" permanently wipes
  everything (with a confirmation prompt).

## Persistent history

Every review you analyze is saved to a local SQLite database
(`backend/data/history.db`) and survives server restarts and browser
sessions ending. It only clears if you explicitly hit "Clear all
history" on the Dashboard.

## CSV upload

Batch mode auto-detects a `review`/`text`/`comment` column in uploaded
CSVs (or uses the first column if there's no matching header).

## Project layout

`backend/` is a FastAPI service, `frontend/` is a Create React App client.

## Running the backend

```bash
cd backend
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows:     .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
vnv changed

Set-Location "C:\Users\Vishwa Kheni\OneDrive\Desktop\CogniSent\backend"
>> .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Set-Location "C:\Users\Vishwa Kheni\OneDrive\Desktop\CogniSent\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

The serving requirements use the lightweight VADER/rule-based inference
path by default so the backend can run on a 512 MB Render instance. Set
`USE_CNN=true` only on a larger instance after installing
`requirements-training.txt` instead.

For Render, create a Python web service with `backend` as its root directory,
`pip install -r requirements.txt` as its build command, and
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` as its start command. Set
`CORS_ORIGINS` to the deployed frontend URL.

The CNN model is preloaded at startup — wait for `Application startup
complete` before using the frontend. Check it's alive at
http://localhost:8000/docs.

## Running the frontend

```bash
cd frontend
npm install
npm start
```

Opens http://localhost:3000, wired to `http://localhost:8000/api` by
default. Override with a `.env` file in `frontend/`:

```
REACT_APP_API_URL=http://localhost:8000/api
```

## Retraining the model

```bash
cd backend
pip install -r requirements-training.txt
python scripts/augment_data.py   # regenerates the augmented dataset
python scripts/train_cnn.py      # retrains the CNN
# or both at once:
python scripts/train_models.py
```

This refreshes `backend/models/cnn/` and `backend/models/registry.json`
with fresh benchmark scores. It does **not** touch your saved review
history in `history.db`.

## API overview

| Method | Endpoint                     | Description                              |
|--------|-------------------------------|-------------------------------------------|
| POST   | `/api/reviews/analyze`        | Analyze a single review                  |
| POST   | `/api/reviews/analyze-batch`  | Analyze a list of reviews                |
| GET    | `/api/reviews`                | List saved reviews (paginated, filterable by `session_id`, `label`) |
| GET    | `/api/sessions`                | List recent sessions with summaries      |
| DELETE | `/api/reviews`                | Permanently clear saved history          |
| GET    | `/api/stats`                  | Aggregate sentiment stats                |
| GET    | `/api/model`                  | CNN model info + benchmark scores        |

A `session_id` is generated client-side once per page load and sent
along with every analyze request, which is how the Dashboard groups
history by session.

## Notes

- Review history lives in `backend/data/history.db` (SQLite). Back this
  file up if you want to preserve history across machines/deployments.
- If you want to reset everything, either use "Clear all history" in
  the UI, call `DELETE /api/reviews`, or delete
  `backend/data/history.db` directly — it's recreated automatically.
