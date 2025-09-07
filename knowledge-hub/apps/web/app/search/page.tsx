'use client'
import { useState } from 'react'

interface ChunkResult {
  id: number
  text: string
  chunk_index: number
  document_id: number
  filename: string
  similarity_score: number
}

interface SearchResponse {
  query: string
  results: ChunkResult[]
  total_results: number
}

export default function SearchPage() {
  const [query, setQuery] = useState<string>('')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim(), k: 10 })
      })

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
      }

      const data: SearchResponse = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  const highlightText = (text: string, query: string): string => {
    if (!query.trim()) return text
    
    const regex = new RegExp(`(${query.trim().split(' ').join('|')})`, 'gi')
    return text.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>')
  }

  const getScoreColor = (score: number): string => {
    if (score > 0.8) return 'text-green-600'
    if (score > 0.6) return 'text-blue-600'
    if (score > 0.4) return 'text-yellow-600'
    return 'text-gray-600'
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Semantic Search</h1>
            <p className="text-lg text-gray-600">Find relevant information across your documents</p>
          </div>

          {/* Search Form */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your search query..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </form>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Search Results
                </h2>
                <span className="text-sm text-gray-500">
                  {results.total_results} result{results.total_results !== 1 ? 's' : ''} for "{results.query}"
                </span>
              </div>

              {results.total_results === 0 ? (
                <div className="text-center py-8">
                  <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <p className="text-gray-500 text-lg">No results found</p>
                  <p className="text-gray-400 text-sm mt-2">Try different keywords or check if documents have been embedded</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.results.map((result, index) => (
                    <div key={result.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                            #{index + 1}
                          </span>
                          <h3 className="font-medium text-gray-900">{result.filename}</h3>
                          <span className="text-sm text-gray-500">
                            Chunk {result.chunk_index + 1}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-sm font-medium ${getScoreColor(result.similarity_score)}`}>
                            {(result.similarity_score * 100).toFixed(1)}% match
                          </span>
                        </div>
                      </div>
                      
                      <div className="text-gray-700 leading-relaxed">
                        <div 
                          dangerouslySetInnerHTML={{ 
                            __html: highlightText(result.text, results.query) 
                          }}
                        />
                      </div>
                      
                      <div className="mt-3 flex items-center text-xs text-gray-500">
                        <span>Document ID: {result.document_id}</span>
                        <span className="mx-2">•</span>
                        <span>Chunk ID: {result.id}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Instructions */}
          {!results && !loading && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">How to use Semantic Search</h3>
              <div className="space-y-3 text-gray-600">
                <p>• Enter natural language queries to find relevant content</p>
                <p>• The search uses AI embeddings to understand meaning, not just keywords</p>
                <p>• Results are ranked by semantic similarity to your query</p>
                <p>• Make sure your documents have been uploaded and processed first</p>
              </div>
              
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Documents need to be embedded before they can be searched. 
                  Use the embedding API endpoint to process your documents first.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
