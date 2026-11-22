from pathlib import Path

BASE_DIR = Path(".")
COMP_DIR = BASE_DIR / "frontend-nextjs" / "src" / "components"
APP_DIR = BASE_DIR / "frontend-nextjs" / "src" / "app"

COMP_DIR.mkdir(parents=True, exist_ok=True)
APP_DIR.mkdir(parents=True, exist_ok=True)

dashboard_code = """"use client";

import React, { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Divider,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed"];

export default function AnalyticsDashboard({ apiBase, sessionId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    let active = true;

    async function loadAnalytics() {
      setLoading(true);
      try {
        const res = await fetch(`${apiBase}/analytics/${sessionId}`);
        const json = await res.json();
        if (res.ok && active) {
          setData(json);
        }
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAnalytics();
    return () => {
      active = false;
    };
  }, [apiBase, sessionId]);

  if (!sessionId) {
    return (
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Start or select a session to view session analytics, 6 tables, and 7 graphs.
        </Typography>
      </Paper>
    );
  }

  if (loading || !data) {
    return (
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="body2">Loading analytics...</Typography>
      </Paper>
    );
  }

  const m = data.metrics || {};
  const t = data.tables || {};
  const g = data.graphs || {};

  const topicPieData = (g.topic_distribution_pie?.labels || []).map((label, i) => ({
    name: label,
    value: g.topic_distribution_pie.values[i] || 0,
  }));

  const accuracyPerTopicData = (g.accuracy_per_topic_bar?.x || []).map((xVal, i) => ({
    topic: xVal,
    accuracy: g.accuracy_per_topic_bar.y[i] || 0,
  }));

  const accuracyPhaseData = (g.accuracy_vs_phase_line?.x || []).map((xVal, i) => ({
    phase: xVal,
    accuracy: g.accuracy_vs_phase_line.y[i] || 0,
  }));

  const correctnessReplyData = (g.correctness_per_reply_bar?.x || []).map((xVal, i) => ({
    turn: xVal,
    score: g.correctness_per_reply_bar.y[i] || 0,
    status: g.correctness_per_reply_bar.labels?.[i] || "",
  }));

  const rtTrendData = (g.response_time_trend_line?.x || []).map((xVal, i) => ({
    turn: xVal,
    seconds: g.response_time_trend_line.y[i] || 0,
  }));

  const ratingBarData = (g.rating_distribution_bar?.x || []).map((xVal, i) => ({
    rating: xVal,
    count: g.rating_distribution_bar.y[i] || 0,
  }));

  const lengthPieData = (g.length_preference_pie?.labels || []).map((label, i) => ({
    name: label,
    value: g.length_preference_pie.values[i] || 0,
  }));

  return (
    <Box sx={{ mt: 3 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h6" fontWeight="bold" mb={0.5}>
          Session Analytics Dashboard
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Session ID: {data.session_id} | Total Turns: {data.total_turns}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2} mb={3}>
          <Grid item xs={6} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">Overall Correctness</Typography>
                <Typography variant="h6" fontWeight="bold">{m.overall_correctness_pct ?? 0}%</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">Average Rating</Typography>
                <Typography variant="h6" fontWeight="bold">{m.avg_rating ?? 0} / 4</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">Avg Response Time</Typography>
                <Typography variant="h6" fontWeight="bold">{m.avg_response_time_sec ?? 0}s</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">C / P / I Counts</Typography>
                <Typography variant="subtitle1" fontWeight="bold">
                  {m.correct_count ?? 0} / {m.partial_count ?? 0} / {m.incorrect_count ?? 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Typography variant="subtitle1" fontWeight="bold" mb={1.5}>
          Visual Analytics (7 Graphs)
        </Typography>

        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>1. Topic Distribution (Pie)</Typography>
                <Box sx={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={topicPieData} dataKey="value" nameKey="name" outerRadius={75} label>
                        {topicPieData.map((_, idx) => (
                          <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>2. Accuracy per Topic (Bar)</Typography>
                <Box sx={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={accuracyPerTopicData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="topic" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="accuracy" fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>3. Accuracy vs Phase (Line)</Typography>
                <Box sx={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={accuracyPhaseData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="phase" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="accuracy" stroke="#16a34a" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>4. Correctness per Reply (Bar)</Typography>
                <Box sx={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={correctnessReplyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="turn" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="score" fill="#f59e0b" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>5. Response Time Trend (Line)</Typography>
                <Box sx={{ height: 220 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={rtTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="turn" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="seconds" stroke="#dc2626" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>6. Rating Distribution (Bar)</Typography>
                <Box sx={{ height: 220 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={ratingBarData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="rating" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#7c3aed" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" mb={1}>7. Length Preference (Pie)</Typography>
                <Box sx={{ height: 220 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={lengthPieData} dataKey="value" nameKey="name" outerRadius={65} label>
                        {lengthPieData.map((_, idx) => (
                          <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Typography variant="subtitle1" fontWeight="bold" mb={1.5}>
          Tabular Analytics (6 Tables)
        </Typography>

        <Stack spacing={2.5}>
          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>1. Topic vs Accuracy</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Topic</TableCell>
                    <TableCell>Turns</TableCell>
                    <TableCell>Accuracy (%)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.topic_vs_accuracy || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.topic_label}</TableCell>
                      <TableCell>{row.turns}</TableCell>
                      <TableCell>{row.accuracy_pct}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>2. Reply Correctness Table</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Turn</TableCell>
                    <TableCell>Topic</TableCell>
                    <TableCell>Correctness</TableCell>
                    <TableCell>Score (%)</TableCell>
                    <TableCell>Rating</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.reply_correctness || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.turn_number}</TableCell>
                      <TableCell>{row.topic_label}</TableCell>
                      <TableCell>{row.correctness}</TableCell>
                      <TableCell>{row.accuracy_pct ?? "-"}</TableCell>
                      <TableCell>{row.rating ?? "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>3. Phase-Wise Accuracy</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Phase</TableCell>
                    <TableCell>Turns</TableCell>
                    <TableCell>Accuracy (%)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.phase_wise_accuracy || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.phase}</TableCell>
                      <TableCell>{row.turns}</TableCell>
                      <TableCell>{row.accuracy_pct}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>4. Response Time Summary</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Min (sec)</TableCell>
                    <TableCell>Avg (sec)</TableCell>
                    <TableCell>Max (sec)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.response_time_summary || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.min_sec}</TableCell>
                      <TableCell>{row.avg_sec}</TableCell>
                      <TableCell>{row.max_sec}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>5. Rating Distribution</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Rating (1-4)</TableCell>
                    <TableCell>Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.rating_distribution || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.rating}</TableCell>
                      <TableCell>{row.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight="bold" mb={0.5}>6. Length Preference</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Length Type</TableCell>
                    <TableCell>Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(t.length_preference || []).map((row, i) => (
                    <TableRow key={i}>
                      <TableCell>{row.length_type}</TableCell>
                      <TableCell>{row.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}
"""

page_code = """"use client";

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
    <Box sx={{ maxWidth: 1050, mx: "auto", p: 3 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              Multi-Turn AI Chatbot (LLaMA 3)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {sessionId ? `Active Session: ${sessionId}` : "Session Not Active"}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={startSession} disabled={Boolean(sessionId)}>
              Start Session
            </Button>
            <Button variant="outlined" color="error" onClick={endSession} disabled={!sessionId}>
              End Session
            </Button>
          </Stack>
        </Stack>

        <Divider sx={{ mb: 2 }} />

        <Box
          sx={{
            height: 360,
            overflowY: "auto",
            p: 2,
            bgcolor: "#f8fafc",
            borderRadius: 1,
            mb: 2,
          }}
        >
          {messages.map((m, idx) => (
            <Box
              key={idx}
              sx={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                mb: 1.5,
              }}
            >
              <Paper
                sx={{
                  p: 1.5,
                  maxWidth: "80%",
                  bgcolor: m.role === "user" ? "#2563eb" : "#e5e7eb",
                  color: m.role === "user" ? "#fff" : "#111827",
                  whiteSpace: "pre-wrap",
                }}
              >
                <Typography variant="body2">{m.text}</Typography>
                {m.meta && (
                  <Typography variant="caption" sx={{ display: "block", mt: 0.5, opacity: 0.85 }}>
                    {m.meta}
                  </Typography>
                )}
                {m.agentAction && m.agentAction !== "standard_multi_turn" && (
                  <Chip
                    size="small"
                    label={`Agent: ${m.agentAction}`}
                    sx={{ mt: 0.75, bgcolor: "#dbeafe", color: "#1e3a8a" }}
                  />
                )}
              </Paper>
            </Box>
          ))}
          {loading && (
            <Typography variant="caption" color="text.secondary">
              LLaMA 3 is generating response...
            </Typography>
          )}
        </Box>

        {pendingInteractionId && (
          <Card sx={{ mb: 2, bgcolor: "#fffbeb", border: "1px solid #f59e0b" }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight="bold" mb={1.5}>
                Mandatory Feedback Required to Unlock Input
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2} mb={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Rating (1-4)</InputLabel>
                  <Select value={rating} label="Rating (1-4)" onChange={(e) => setRating(e.target.value)}>
                    <MenuItem value={1}>1</MenuItem>
                    <MenuItem value={2}>2</MenuItem>
                    <MenuItem value={3}>3</MenuItem>
                    <MenuItem value={4}>4</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
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

                <FormControl fullWidth size="small">
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
              <Button variant="contained" color="success" onClick={submitFeedback}>
                Submit Feedback & Unlock
              </Button>
            </CardContent>
          </Card>
        )}

        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            size="small"
            placeholder={
              pendingInteractionId
                ? "Submit feedback above to unlock input..."
                : "Type your message..."
            }
            value={inputText}
            disabled={isLocked}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <Button variant="contained" disabled={isLocked} onClick={sendMessage}>
            Send
          </Button>
        </Stack>
      </Paper>

      <AnalyticsDashboard
        key={`${viewedSessionId}-${analyticsRefreshKey}`}
        apiBase={API_BASE}
        sessionId={viewedSessionId}
      />
    </Box>
  );
}
"""


def main():
    (COMP_DIR / "AnalyticsDashboard.js").write_text(dashboard_code, encoding="utf-8")
    (APP_DIR / "page.js").write_text(page_code, encoding="utf-8")
    print("Created AnalyticsDashboard.js and updated page.js successfully.")


if __name__ == "__main__":
    main()