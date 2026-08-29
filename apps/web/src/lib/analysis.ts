import api from "./api";

export interface RiskFinding {
  id: string;
  clause_id: string;
  risk_level: "high" | "medium" | "low";
  category: string;
  description: string;
  recommendation: string;
}

export interface KeyTerm {
  term: string;
  definition: string;
  clause_id: string;
}

export interface DocumentSummary {
  executive_summary: string;
  key_points: string[];
  parties_involved: string[];
  effective_date: string | null;
  termination_date: string | null;
}

export interface AnalysisResult {
  analysis_id: string;
  document_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  overall_risk_score: number;
  risk_level: "high" | "medium" | "low";
  summary: DocumentSummary | null;
  risks: RiskFinding[];
  key_terms: KeyTerm[];
  created_at: string;
  completed_at: string | null;
}

export interface StartAnalysisRequest {
  document_id: string;
  analysis_type?: string;
}

export interface AnalysisListResponse {
  analyses: AnalysisResult[];
  total: number;
}

export const analysisApi = {
  async startAnalysis(request: StartAnalysisRequest): Promise<AnalysisResult> {
    const response = await api.post("/analysis/analyze", request);
    return response.data;
  },

  async getAnalysisStatus(analysisId: string): Promise<AnalysisResult> {
    const response = await api.get(`/analysis/${analysisId}/status`);
    return response.data;
  },

  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    const response = await api.get(`/analysis/${analysisId}/result`);
    return response.data;
  },

  async listAnalyses(
    documentId?: string,
    page = 1,
    pageSize = 10
  ): Promise<AnalysisListResponse> {
    const response = await api.get("/analysis", {
      params: { document_id: documentId, page, page_size: pageSize },
    });
    return response.data;
  },

  async cancelAnalysis(analysisId: string): Promise<void> {
    await api.post(`/analysis/${analysisId}/cancel`);
  },
};
