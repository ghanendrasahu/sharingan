import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Search, FileText, BookOpen, Loader2 } from "lucide-react";
import { searchApi, type SearchHit } from "../lib/search";

export function SemanticSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchHit[]>([]);
  const [searchTime, setSearchTime] = useState<number | null>(null);

  const searchMutation = useMutation({
    mutationFn: async (searchQuery: string) => {
      const response = await searchApi.semanticSearch(searchQuery, 10);
      return response;
    },
    onSuccess: (data) => {
      setResults(data.results);
      setSearchTime(data.processing_time_ms);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      searchMutation.mutate(query.trim());
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search across all documents..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border rounded-md"
          />
        </div>
        <button
          type="submit"
          disabled={searchMutation.isPending || !query.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {searchMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Search"
          )}
        </button>
      </form>

      {searchTime !== null && (
        <p className="text-sm text-muted-foreground">
          Found {results.length} results in {searchTime.toFixed(0)}ms
        </p>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((hit, index) => (
            <SearchResultCard key={index} hit={hit} />
          ))}
        </div>
      )}

      {searchMutation.isPending && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {!searchMutation.isPending && results.length === 0 && query && (
        <div className="text-center py-8 text-muted-foreground">
          No results found for "{query}"
        </div>
      )}
    </div>
  );
}

function SearchResultCard({ hit }: { hit: SearchHit }) {
  const getIcon = () => {
    if (hit.clause_id) {
      return <BookOpen className="h-5 w-5 text-primary" />;
    }
    return <FileText className="h-5 w-5 text-muted-foreground" />;
  };

  return (
    <div className="border rounded-lg p-4 hover:bg-muted/50 transition-colors">
      <div className="flex items-start gap-3">
        {getIcon()}
        <div className="flex-1">
          <p className="text-sm">{hit.content}</p>
          <div className="flex items-center gap-4 mt-2">
            <span className="text-xs text-muted-foreground">
              Score: {(hit.score * 100).toFixed(1)}%
            </span>
            {hit.document_id && (
              <span className="text-xs text-muted-foreground">
                Doc: {hit.document_id.slice(0, 8)}...
              </span>
            )}
            {hit.clause_id && (
              <span className="text-xs text-primary">
                Clause: {hit.clause_id}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
