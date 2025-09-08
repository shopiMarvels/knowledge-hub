'use client'
import { useState } from 'react'

interface Citation {
  document_id: number
  chunk_index: number
}

interface ContextHit {
  document_id: number
  chunk_index: number
  score: number
  preview: string
}

interface QAResponse {
  answer: string
  citations: Citation[]
  hits: ContextHit[]
}

export default function ChatPage() {
  const [query, setQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [answer, setAnswer] = useState<string>('')
  const [citations, setCitations] = useState<Citation[]>([])
  const [hits, setHits] = useState<ContextHit[]>([])
  const [error, setError] = useState<string>('')

  const ask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
    setError('')
    setAnswer('')
    setCitations([])
    setHits([])

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: query.trim(), 
          k: 6, 
          max_tokens: 384 
        })
      })

      if (!response.ok) {
        throw new Error(`Request failed: ${response.statusText}`)
      }

      const data: QAResponse = await response.json()
      setAnswer(data.answer || '')
      setCitations(data.citations || [])
      setHits(data.hits || [])

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number): string => {
    if (score > 0.8) return 'text-green-600'
    if (score > 0.6) return 'text-blue-600'
    if (score > 0.4) return 'text-yellow-600'
    return 'text-gray-600'
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Ask your Knowledge Hub</h1>
            <p className="text-lg text-gray-600">Get AI-powered answers with citations from your documents</p>
          </div>

          {/* Chat Form */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <form onSubmit={ask} className="space-y-4">
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {loading ? 'Thinking...' : 'Ask'}
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

          {/* Answer Section */}
          {answer && (
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                  <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900">Answer</h2>
              </div>
              
              <div className="prose max-w-none mb-4">
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {answer}
                </div>
              </div>

              {/* Citations */}
              {citations.length > 0 && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Citations:</h3>
                  <div className="flex flex-wrap gap-2">
                    {citations.map((citation, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                      >
                        Doc {citation.document_id} #{citation.chunk_index}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Context Sources */}
          {hits.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Source Context ({hits.length} chunks)
              </h2>
              
              <div className="space-y-4">
                {hits.map((hit, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          #{index + 1}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          Document {hit.document_id} • Chunk {hit.chunk_index}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${getScoreColor(hit.score)}`}>
                        {(hit.score * 100).toFixed(1)}% relevance
                      </span>
                    </div>
                    
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {hit.preview}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          {!answer && !loading && !error && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">How to use Q&A</h3>
              <div className="space-y-3 text-gray-600">
                <p>• Ask natural language questions about your uploaded documents</p>
                <p>• The AI will find relevant information and provide cited answers</p>
                <p>• Citations show exactly which documents and chunks were used</p>
                <p>• The system only uses information from your documents - no hallucination</p>
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Example questions:</strong><br/>
                  "What are the main technical skills mentioned?"<br/>
                  "Summarize the work experience"<br/>
                  "What projects were worked on at Hub Group?"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
