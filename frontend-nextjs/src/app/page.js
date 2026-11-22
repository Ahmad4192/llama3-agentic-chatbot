"use client";

import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AnalyticsDashboard from "../components/AnalyticsDashboard";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function HomePage() {
  const [userId] = useState("user_ahmad_01");
  const [sessionId, setSessionId] = useState(null);
  const [viewedSessionId, setViewedSessionId] = useState(null);
  const [pendingInteractionId, setPendingInteractionId] = useState(null);
  const [analyticsRefreshKey, setAnalyticsRefreshKey] = useState(0);

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: 'Click "Start Session" to chat with local LLaMA 3. Submit feedback after each reply to unlock chat.',
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);

  const [rating, setRating] = useState("");
  const [correctness, setCorrectness] = useState("");
  const [lengthType, setLengthType] = useState("");

  const isLocked = Boolean(pendingInteractionId) || !sessionId || loading;

  const startSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          email: "local_user@example.com",
          name: "Local User",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start session");

      setSessionId(data.session_id);
      setViewedSessionId(data.session_id);
      setPendingInteractionId(null);
      setAnalyticsRefreshKey((k) => k + 1);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: `Session started: ${data.session_id}` },
      ]);
    } catch (err) {
      alert(err.message);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !sessionId || pendingInteractionId) return;

    const userMsg = inputText.trim();
    setInputText("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          message: userMsg,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat error");

      setPendingInteractionId(data.interaction_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.response,
          meta: `Turn #${data.turn_number} | Topic: ${data.topic_label} | Latency: ${data.response_time_sec}s`,
          agentAction: data.agent_action,
        },
      ]);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async () => {
    if (!rating || !correctness || !lengthType || !pendingInteractionId) {
      alert("Please select Rating (1-4), Correctness, and Length Type.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interaction_id: pendingInteractionId,
          session_id: sessionId,
          rating: Number(rating),
          correctness,
          length_type: lengthType,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Feedback error");

      setPendingInteractionId(null);
      setRating("");
      setCorrectness("");
      setLengthType("");
      setAnalyticsRefreshKey((k) => k + 1);
    } catch (err) {
      alert(err.message);
    }
  };

  const endSession = async () => {
    if (!sessionId) return;
    const endedId = sessionId;
    try {
      const res = await fetch(`${API_BASE}/session/end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: endedId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to end session");

      setViewedSessionId(endedId);
      setSessionId(null);
      setPendingInteractionId(null);
      setAnalyticsRefreshKey((k) => k + 1);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Session completed and analytics summary saved." },
      ]);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <Box sx={{ maxWidth: 1100, mx: "auto", px: { xs: 2, md: 3 }, py: 3 }}>
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, md: 3 },
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            background: "linear-gradient(135deg, #1e1b4b 0%, #3730a3 55%, #0284c7 100%)",
            color: "#ffffff",
            p: { xs: 2, md: 2.5 },
            borderRadius: 2.5,
            mb: 2.5,
          }}
        >
          <Stack
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            alignItems={{ xs: "flex-start", sm: "center" }}
            spacing={2}
          >
            <Box>
              <Stack direction="row" alignItems="center" spacing={1.5} flexWrap="wrap">
                <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: "-0.01em" }}>
                  Multi-Turn Agentic Chatbot
                </Typography>
                <Chip
                  size="small"
                  label={sessionId ? "ACTIVE SESSION" : "STANDBY"}
                  sx={{
                    fontFamily: "var(--font-mono), monospace",
                    fontWeight: 700,
                    fontSize: "0.7rem",
                    bgcolor: sessionId ? "rgba(34, 197, 94, 0.22)" : "rgba(255, 255, 255, 0.16)",
                    color: sessionId ? "#bbf7d0" : "#e2e8f0",
                    border: sessionId
                      ? "1px solid rgba(74, 222, 128, 0.5)"
                      : "1px solid rgba(255, 255, 255, 0.25)",
                  }}
                />
              </Stack>
              <Typography
                variant="caption"
                sx={{
                  display: "block",
                  mt: 0.75,
                  color: "rgba(226, 232, 240, 0.9)",
                  fontFamily: sessionId ? "var(--font-mono), monospace" : "inherit",
                }}
              >
                {sessionId
                  ? `Session ID: ${sessionId} • Local Ollama (LLaMA 3)`
                  : "Start a session to test topic shifts, mandatory feedback, and live analytics"}
              </Typography>
            </Box>

            <Stack direction="row" spacing={1.25}>
              <Button
                variant="contained"
                onClick={startSession}
                disabled={Boolean(sessionId)}
                sx={{
                  bgcolor: "#ffffff",
                  color: "#1e1b4b",
                  fontWeight: 700,
                  "&:hover": { bgcolor: "#f1f5f9" },
                  "&.Mui-disabled": {
                    bgcolor: "rgba(255, 255, 255, 0.25)",
                    color: "rgba(255, 255, 255, 0.65)",
                  },
                }}
              >
                Start Session
              </Button>
              <Button
                variant="outlined"
                onClick={endSession}
                disabled={!sessionId}
                sx={{
                  color: "#fecaca",
                  borderColor: "rgba(254, 202, 202, 0.5)",
                  fontWeight: 600,
                  "&:hover": {
                    borderColor: "#fca5a5",
                    bgcolor: "rgba(239, 68, 68, 0.16)",
                  },
                  "&.Mui-disabled": {
                    color: "rgba(255, 255, 255, 0.35)",
                    borderColor: "rgba(255, 255, 255, 0.18)",
                  },
                }}
              >
                End Session
              </Button>
            </Stack>
          </Stack>
        </Box>

        <Box
          sx={{
            height: 380,
            overflowY: "auto",
            p: 2.5,
            bgcolor: "#f8fafc",
            borderRadius: 2.5,
            border: "1px solid #e2e8f0",
            mb: 2.5,
          }}
        >
          {messages.map((m, idx) => (
            <Box
              key={idx}
              sx={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                mb: 1.75,
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 1.75,
                  maxWidth: "82%",
                  borderRadius: m.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  background:
                    m.role === "user"
                      ? "linear-gradient(135deg, #4f46e5 0%, #2563eb 100%)"
                      : "#ffffff",
                  color: m.role === "user" ? "#ffffff" : "#0f172a",
                  border: m.role === "user" ? "none" : "1px solid #e2e8f0",
                  boxShadow:
                    m.role === "user"
                      ? "0 6px 16px -4px rgba(37, 99, 235, 0.35)"
                      : "0 2px 8px -2px rgba(15, 23, 42, 0.05)",
                  whiteSpace: "pre-wrap",
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                  {m.text}
                </Typography>

                {m.meta && (
                  <Typography
                    variant="caption"
                    sx={{
                      display: "block",
                      mt: 1,
                      pt: 0.75,
                      borderTop:
                        m.role === "user"
                          ? "1px solid rgba(255,255,255,0.2)"
                          : "1px dashed #cbd5e1",
                      fontFamily: "var(--font-mono), monospace",
                      fontSize: "0.72rem",
                      fontVariantNumeric: "tabular-nums",
                      color: m.role === "user" ? "rgba(255,255,255,0.9)" : "#475569",
                    }}
                  >
                    {m.meta}
                  </Typography>
                )}

                {m.agentAction && m.agentAction !== "standard_multi_turn" && (
                  <Chip
                    size="small"
                    label={`Agent: ${m.agentAction}`}
                    sx={{
                      mt: 1,
                      fontFamily: "var(--font-mono), monospace",
                      fontWeight: 600,
                      fontSize: "0.7rem",
                      bgcolor: "#e0e7ff",
                      color: "#3730a3",
                      border: "1px solid #c7d2fe",
                    }}
                  />
                )}
              </Paper>
            </Box>
          ))}

          {loading && (
            <Stack direction="row" alignItems="center" spacing={1} sx={{ py: 0.5 }}>
              <Chip
                size="small"
                label="LLaMA 3 Thinking..."
                sx={{
                  fontFamily: "var(--font-mono), monospace",
                  bgcolor: "#eef2ff",
                  color: "#4338ca",
                  fontWeight: 600,
                }}
              />
            </Stack>
          )}
        </Box>

        {pendingInteractionId && (
          <Card
            elevation={0}
            sx={{
              mb: 2.5,
              borderRadius: 2.5,
              bgcolor: "#fffbeb",
              border: "1px solid #f59e0b",
            }}
          >
            <CardContent sx={{ p: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "#92400e", mb: 1.5 }}>
                Mandatory Feedback Required to Unlock Input
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2} mb={2}>
                <FormControl fullWidth size="small" sx={{ bgcolor: "#ffffff", borderRadius: 1.5 }}>
                  <InputLabel>Rating (1-4)</InputLabel>
                  <Select
                    value={rating}
                    label="Rating (1-4)"
                    onChange={(e) => setRating(e.target.value)}
                  >
                    <MenuItem value={1}>1</MenuItem>
                    <MenuItem value={2}>2</MenuItem>
                    <MenuItem value={3}>3</MenuItem>
                    <MenuItem value={4}>4</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ bgcolor: "#ffffff", borderRadius: 1.5 }}>
                  <InputLabel>Correctness</InputLabel>
                  <Select
                    value={correctness}
                    label="Correctness"
                    onChange={(e) => setCorrectness(e.target.value)}
                  >
                    <MenuItem value="Correct">Correct</MenuItem>
                    <MenuItem value="Partial">Partial</MenuItem>
                    <MenuItem value="Incorrect">Incorrect</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ bgcolor: "#ffffff", borderRadius: 1.5 }}>
                  <InputLabel>Length Type</InputLabel>
                  <Select
                    value={lengthType}
                    label="Length Type"
                    onChange={(e) => setLengthType(e.target.value)}
                  >
                    <MenuItem value="Short">Short</MenuItem>
                    <MenuItem value="To the Point">To the Point</MenuItem>
                    <MenuItem value="Lengthy">Lengthy</MenuItem>
                  </Select>
                </FormControl>
              </Stack>
              <Button
                variant="contained"
                color="success"
                onClick={submitFeedback}
                sx={{ fontWeight: 700, px: 2.5 }}
              >
                Submit Feedback & Unlock
              </Button>
            </CardContent>
          </Card>
        )}

        <Divider sx={{ mb: 2 }} />

        <Stack direction="row" spacing={1.25}>
          <TextField
            fullWidth
            size="small"
            placeholder={
              pendingInteractionId
                ? "Submit feedback above to unlock input..."
                : sessionId
                  ? "Type your message for LLaMA 3..."
                  : "Click 'Start Session' above to begin..."
            }
            value={inputText}
            disabled={isLocked}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                bgcolor: "#ffffff",
                borderRadius: 2.5,
              },
            }}
          />
          <Button
            variant="contained"
            disabled={isLocked}
            onClick={sendMessage}
            sx={{ px: 3, fontWeight: 700, borderRadius: 2.5 }}
          >
            Send
          </Button>
        </Stack>
      </Paper>

      <Box sx={{ mt: 3 }}>
        <AnalyticsDashboard
          key={`${viewedSessionId}-${analyticsRefreshKey}`}
          apiBase={API_BASE}
          sessionId={viewedSessionId}
        />
      </Box>
    </Box>
  );
}