'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

async function fetchDoc(id: string) {
  const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/documents/' + id, { cache: 'no-store' })
  return res.json()
}

export default function DocPage() {
  const params = useParams() as { id: string }
  const id = params.id
  const [doc, setDoc] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const refresh = async () => setDoc(await fetchDoc(id))

  useEffect(() => { refresh() }, [id])

  const trigger = async (path: string) => {
    setLoading(true)
    await fetch(process.env.NEXT_PUBLIC_API_URL + path, { method: 'POST' })
    setLoading(false)
    setTimeout(refresh, 1200)
  }

  if (!doc) return <main className="p-6">Loading…</main>
  return (
    <main className="p-6 space-y-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold">{doc.filename}</h1>
      <div className="text-sm text-gray-600">Doc #{doc.id} • {doc.chunks} chunks</div>

      <div className="flex gap-2 mt-2">
        <button className="px-3 py-2 bg-black text-white rounded" onClick={()=>trigger(`/documents/${id}/tag`)} disabled={loading}>
          {loading ? 'Tagging…' : 'Run Auto‑Tagging'}
        </button>
        <button className="px-3 py-2 bg-black text-white rounded" onClick={()=>trigger(`/documents/${id}/summarize`)} disabled={loading}>
          {loading ? 'Summarizing…' : 'Run Summarization'}
        </button>
      </div>

      <section>
        <h2 className="font-semibold mt-4">Tags</h2>
        <div className="flex gap-2 flex-wrap mt-1">
          {(doc.tags||[]).map((t:string, i:number)=> (
            <span key={i} className="px-2 py-1 text-sm rounded-full border">{t}</span>
          ))}
          {(!doc.tags || doc.tags.length===0) && <span className="text-sm text-gray-500">No tags yet</span>}
        </div>
      </section>

      <section>
        <h2 className="font-semibold mt-4">Summary</h2>
        <div className="border rounded p-3 whitespace-pre-wrap min-h-[80px]">{doc.summary || 'No summary yet'}</div>
      </section>
    </main>
  )
}