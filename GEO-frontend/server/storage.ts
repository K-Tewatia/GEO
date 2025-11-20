import { 
  analyses, 
  analysisResults,
  sharedLinks,
  type Analysis, 
  type InsertAnalysis,
  type AnalysisResult,
  type InsertAnalysisResult,
  type SharedLink,
  type InsertSharedLink,
  type AnalysisResults
} from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  // Analysis operations
  createAnalysis(analysis: InsertAnalysis): Promise<Analysis>;
  getAnalysis(id: string): Promise<Analysis | undefined>;
  getAnalysisBySessionId(sessionId: string): Promise<Analysis | undefined>;
  getAllAnalyses(): Promise<Analysis[]>;
  
  // Analysis results operations
  saveAnalysisResults(result: InsertAnalysisResult): Promise<AnalysisResult>;
  getAnalysisResults(analysisId: string): Promise<AnalysisResult | undefined>;
  
  // Shared links operations
  createSharedLink(link: InsertSharedLink): Promise<SharedLink>;
  getSharedLinkByToken(token: string): Promise<SharedLink | undefined>;
  getSharedLinksForAnalysis(analysisId: string): Promise<SharedLink[]>;
}

export class DatabaseStorage implements IStorage {
  async createAnalysis(insertAnalysis: InsertAnalysis): Promise<Analysis> {
    const [analysis] = await db
      .insert(analyses)
      .values(insertAnalysis)
      .returning();
    return analysis;
  }

  async getAnalysis(id: string): Promise<Analysis | undefined> {
    const [analysis] = await db
      .select()
      .from(analyses)
      .where(eq(analyses.id, id));
    return analysis || undefined;
  }

  async getAnalysisBySessionId(sessionId: string): Promise<Analysis | undefined> {
    const [analysis] = await db
      .select()
      .from(analyses)
      .where(eq(analyses.sessionId, sessionId));
    return analysis || undefined;
  }

  async getAllAnalyses(): Promise<Analysis[]> {
    return await db
      .select()
      .from(analyses)
      .orderBy(desc(analyses.createdAt));
  }

  async saveAnalysisResults(insertResult: InsertAnalysisResult): Promise<AnalysisResult> {
    const [result] = await db
      .insert(analysisResults)
      .values(insertResult)
      .returning();
    return result;
  }

  async getAnalysisResults(analysisId: string): Promise<AnalysisResult | undefined> {
    const [result] = await db
      .select()
      .from(analysisResults)
      .where(eq(analysisResults.analysisId, analysisId));
    return result || undefined;
  }

  async createSharedLink(insertLink: InsertSharedLink): Promise<SharedLink> {
    const [link] = await db
      .insert(sharedLinks)
      .values(insertLink)
      .returning();
    return link;
  }

  async getSharedLinkByToken(token: string): Promise<SharedLink | undefined> {
    const [link] = await db
      .select()
      .from(sharedLinks)
      .where(eq(sharedLinks.token, token));
    return link || undefined;
  }

  async getSharedLinksForAnalysis(analysisId: string): Promise<SharedLink[]> {
    return await db
      .select()
      .from(sharedLinks)
      .where(eq(sharedLinks.analysisId, analysisId));
  }
}

export const storage = new DatabaseStorage();
