import api from "./api";

export interface Document {
  id: string;
  name: string;
  file_type: string;
  file_size: number;
  status: "uploaded" | "processing" | "completed" | "failed";
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  name: string;
  file_type: string;
  status: string;
  message: string;
}

export interface PaginatedDocuments {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export const documentsApi = {
  async list(page = 1, pageSize = 10): Promise<PaginatedDocuments> {
    const response = await api.get("/documents", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async get(documentId: string): Promise<Document> {
    const response = await api.get(`/documents/${documentId}`);
    return response.data;
  },

  async upload(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  async delete(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);
  },

  async download(documentId: string): Promise<Blob> {
    const response = await api.get(`/documents/${documentId}/download`, {
      responseType: "blob",
    });
    return response.data;
  },
};
