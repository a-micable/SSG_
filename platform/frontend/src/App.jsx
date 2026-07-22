import React, {useState} from 'react'

export default function App(){
  const [path, setPath] = useState('.')
  const [report, setReport] = useState(null)

  async function runAnalyze(){
    const res = await fetch('/api/analyze', {method: 'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({path})})
    const data = await res.json()
    setReport(data.report)
  }

  return (
    <div style={{padding:20}}>
      <h1>Company Code Quality Platform (MVP)</h1>
      <div>
        <label>Path: </label>
        <input value={path} onChange={e=>setPath(e.target.value)} />
        <button onClick={runAnalyze}>Analyze</button>
      </div>
      {report && (
        <pre style={{marginTop:20, maxHeight:400, overflow:'auto'}}>{JSON.stringify(report, null, 2)}</pre>
      )}
    </div>
  )
}
