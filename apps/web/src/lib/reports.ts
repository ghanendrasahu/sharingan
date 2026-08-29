import api from "./api";

export interface ReportSection {
  title: string;
  content: string;
  section_type: string;
}

export interface RiskSummary {
  total_risks: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  risk_level: string;
}

export interface Report {
  report_id: string;
  document_id: string;
  report_type: string;
  generated_at: string;
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  risk_summary: RiskSummary | null;
}

export interface ReportListResponse {
  document_id: string;
  reports: Report[];
  total_count: number;
}

export const reportsApi = {
  async generateReport(
    documentId: string,
    reportType = "full_analysis"
  ): Promise<Report> {
    const response = await api.post("/reports/generate", {
      document_id: documentId,
      report_type: reportType,
    });
    return response.data;
  },

  async listReports(documentId: string): Promise<ReportListResponse> {
    const response = await api.get(`/reports/${documentId}`);
    return response.data;
  },

  async getReport(reportId: string): Promise<Report> {
    const response = await api.get(`/reports/detail/${reportId}`);
    return response.data;
  },

  async exportReport(
    reportId: string,
    format: "json" | "html" | "markdown"
  ): Promise<{ report_id: string; format: string; content: string }> {
    const response = await api.post("/reports/export", {
      report_id: reportId,
      format,
    });
    return response.data;
  },

  async deleteReport(reportId: string): Promise<void> {
    await api.delete(`/reports/${reportId}`);
  },

  async getStats(): Promise<{
    total_reports: number;
    reports_by_type: Record<string, number>;
  }> {
    const response = await api.get("/reports/stats/overview");
    return response.data;
  },
};
