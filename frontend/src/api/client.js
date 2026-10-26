import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 1200000,
});

export const analyzeReview = (text, sessionId) =>
  client.post("/reviews/analyze", { text, session_id: sessionId }).then((r) => r.data);

export const analyzeBatch = (texts, sessionId) =>
  client.post("/reviews/analyze-batch", { texts, session_id: sessionId }).then((r) => r.data);

export const getReviews = (params = {}) =>
  client.get("/reviews", { params }).then((r) => r.data);

export const getSessions = (limit = 20) =>
  client.get("/sessions", { params: { limit } }).then((r) => r.data);

export const clearReviews = () => client.delete("/reviews").then((r) => r.data);

export const deleteReview = (id) => client.delete(`/reviews/${id}`).then((r) => r.data);

export const deleteSession = (sessionId) =>
  client.delete(`/sessions/${encodeURIComponent(sessionId)}`).then((r) => r.data);

export const getStats = () => client.get("/stats").then((r) => r.data);

export const getModelInfo = () => client.get("/model").then((r) => r.data);

export default client;
