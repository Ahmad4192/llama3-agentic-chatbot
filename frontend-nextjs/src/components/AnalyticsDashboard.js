"use client";

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
