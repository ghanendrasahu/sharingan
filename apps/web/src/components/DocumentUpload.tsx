import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X, AlertCircle, CheckCircle } from "lucide-react";
import { cn } from "../lib/utils";
import { documentsApi } from "../lib/documents";

interface UploadState {
  file: File;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
  documentId?: string;
}

interface DocumentUploadProps {
  onUploadComplete?: (documentId: string) => void;
  maxFiles?: number;
  maxSizeMb?: number;
}

export function DocumentUpload({
  onUploadComplete,
  maxFiles = 5,
  maxSizeMb = 50,
}: DocumentUploadProps) {
  const [uploads, setUploads] = useState<UploadState[]>([]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newUploads: UploadState[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: "pending" as const,
      }));

      setUploads((prev) => [...prev, ...newUploads]);

      for (const upload of newUploads) {
        try {
          setUploads((prev) =>
            prev.map((u) =>
              u.file === upload.file ? { ...u, status: "uploading" } : u
            )
          );

          const response = await documentsApi.upload(upload.file, (progress) => {
            setUploads((prev) =>
              prev.map((u) =>
                u.file === upload.file ? { ...u, progress } : u
              )
            );
          });

          setUploads((prev) =>
            prev.map((u) =>
              u.file === upload.file
                ? { ...u, status: "success", documentId: response.id }
                : u
            )
          );

          onUploadComplete?.(response.id);
        } catch (error) {
          setUploads((prev) =>
            prev.map((u) =>
              u.file === upload.file
                ? {
                    ...u,
                    status: "error",
                    error: error instanceof Error ? error.message : "Upload failed",
                  }
                : u
            )
          );
        }
      }
    },
    [onUploadComplete]
  );

  const removeUpload = (file: File) => {
    setUploads((prev) => prev.filter((u) => u.file !== file));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles,
    maxSize: maxSizeMb * 1024 * 1024,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx",
      ],
    },
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          Drag and drop files here, or click to select files
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          PDF or DOCX up to {maxSizeMb}MB
        </p>
      </div>

      {uploads.length > 0 && (
        <div className="space-y-2">
          {uploads.map((upload) => (
            <div
              key={upload.file.name}
              className="flex items-center gap-3 p-3 border rounded-lg"
            >
              <FileText className="h-5 w-5 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.file.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full transition-all",
                        upload.status === "success"
                          ? "bg-green-500"
                          : upload.status === "error"
                          ? "bg-red-500"
                          : "bg-primary"
                      )}
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {upload.progress}%
                  </span>
                </div>
              </div>
              {upload.status === "success" && (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              {upload.status === "error" && (
                <AlertCircle className="h-5 w-5 text-red-500" />
              )}
              <button
                onClick={() => removeUpload(upload.file)}
                className="p-1 hover:bg-muted rounded"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
