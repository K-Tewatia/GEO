import type { Express } from "express";
import { createServer, type Server } from "http";
import axios from "axios";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || "http://localhost:8000";

export async function registerRoutes(app: Express): Promise<Server> {
  // Proxy route for starting analysis
  app.post("/api/analysis/run", async (req, res) => {
    try {
      const response = await axios.post(`${FASTAPI_BASE_URL}/api/analysis/run`, req.body, {
        headers: {
          "Content-Type": "application/json",
        },
      });
      res.json(response.data);
    } catch (error) {
      console.error("Error starting analysis:", error);
      if (axios.isAxiosError(error)) {
        res.status(error.response?.status || 500).json({
          error: error.response?.data?.detail || "Failed to start analysis",
        });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  });

  // Proxy route for checking analysis status
  app.get("/api/analysis/status/:sessionId", async (req, res) => {
    try {
      const { sessionId } = req.params;
      const response = await axios.get(`${FASTAPI_BASE_URL}/api/analysis/status/${sessionId}`);
      res.json(response.data);
    } catch (error) {
      console.error("Error fetching status:", error);
      if (axios.isAxiosError(error)) {
        res.status(error.response?.status || 500).json({
          error: error.response?.data?.detail || "Failed to fetch analysis status",
        });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  });

  // Proxy route for getting analysis results
  app.get("/api/results/:sessionId", async (req, res) => {
    try {
      const { sessionId } = req.params;
      const response = await axios.get(`${FASTAPI_BASE_URL}/api/results/${sessionId}`);
      res.json(response.data);
    } catch (error) {
      console.error("Error fetching results:", error);
      if (axios.isAxiosError(error)) {
        res.status(error.response?.status || 500).json({
          error: error.response?.data?.detail || "Failed to fetch analysis results",
        });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
