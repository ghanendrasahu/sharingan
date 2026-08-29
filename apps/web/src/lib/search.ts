import api from "./api";

export interface SearchHit {
  content: string;
  score: number;
  document_id: string | null;
  clause_id: string | null;
  metadata: Record<string, string>;
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchHit[];
  total_results: number;
  processing_time_ms: number | null;
}

export interface SearchFilters {
  document_id?: string;
  risk_level?: string;
  clause_type?: string;
}

export const searchApi = {
  async semanticSearch(
    query: string,
    topK = 10,
    filters?: SearchFilters
  ): Promise<SemanticSearchResponse> {
    const response = await api.post("/search/semantic", {
      query,
      top_k: topK,
      filters,
    });
    return response.data;
  },

  async clauseSearch(
    query: string,
    documentId?: string,
    topK = 10
  ): Promise<SemanticSearchResponse> {
    const response = await api.post("/search/clauses", {
      query,
      document_id: documentId,
      top_k: topK,
    });
    return response.data;
  },

  async indexDocument(
    documentId: string
  ): Promise<{ status: string; message: string }> {
    const response = await api.post("/search/index", {
      document_id: documentId,
    });
    return response.data;
  },

  async getStats(): Promise<{
    total_documents: number;
    total_clauses: number;
    total_embeddings: number;
  }> {
    const response = await api.get("/search/stats");
    return response.data;
  },
};
