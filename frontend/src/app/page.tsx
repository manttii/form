"use client";

import { useState, useEffect } from "react";
import { ArrowRight, Loader2, Play, CheckCircle2, Settings, FileText, BarChart, Server } from "lucide-react";

// define types
type Field = {
  id: string;
  title: string;
  type: string;
  options: string[];
  config?: string;
  required?: boolean;
};

type FormStructure = {
  url: string;
  action: string;
  hidden_fields: Record<string, string>;
  fields: Field[];
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [structure, setStructure] = useState<FormStructure | null>(null);
  
  const [count, setCount] = useState(10);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<{status: string, progress: number, total: number, success: number, error: number, errors: string[]} | null>(null);

  const getApiUrl = (endpoint: string) => {
    // Detect if running on Vercel or production vs local development
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
      return `/_/backend${endpoint}`;
    }
    // Local development fallback
    return `http://localhost:8000${endpoint}`;
  };

  const fetchStructure = async () => {
    if (!url) {
      setError("Please enter a Google Form URL");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(getApiUrl("/api/parse"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to parse");
      
      // Initialize config based on type
      const initializedFields = data.fields.map((f: any) => {
        let defaultConfig = "Random Words";
        if (f.type === "text" || f.type === "paragraph") {
          const title = f.title.toLowerCase();
          if (title.includes("email")) defaultConfig = "Random Emails";
          else if (title.includes("name")) defaultConfig = "Random Names";
          else if (title.includes("phone")) defaultConfig = "Random Phone";
          else if (title.includes("age")) defaultConfig = "Random Ages";
          else if (title.includes("address")) defaultConfig = "Random Address";
          else if (f.type === "paragraph") defaultConfig = "Random Sentences";
        }
        
        return {
          ...f,
          config: defaultConfig
        };
      });
      
      setStructure({ ...data, fields: initializedFields });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startAutomation = async () => {
    if (!structure) return;
    setLoading(true);
    setError("");
    try {
      const payload = {
        action: structure.action,
        hidden_fields: structure.hidden_fields,
        fields: structure.fields,
        count: count
      };
      
      const res = await fetch(getApiUrl("/api/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start");
      
      setJobId(data.job_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(getApiUrl(`/api/progress/${jobId}`));
        const data = await res.json();
        if (res.ok) {
          setProgress(data);
          if (data.status === "completed" || data.status === "cancelled") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error(err);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [jobId]);

  const updateFieldConfig = (index: number, val: string) => {
    if (!structure) return;
    const newFields = [...structure.fields];
    newFields[index].config = val;
    setStructure({ ...structure, fields: newFields });
  };

  const renderFieldConfig = (field: Field, idx: number) => {
    const isTextLike = field.type === 'text' || field.type === 'paragraph';
    
    if (isTextLike) {
      return (
        <select 
          className="bg-neutral-800 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500 transition-colors"
          value={field.config}
          onChange={(e) => updateFieldConfig(idx, e.target.value)}
        >
          <option>Random Names</option>
          <option>Random Emails</option>
          <option>Random Phone</option>
          <option>Random Ages</option>
          <option>Random Sentences</option>
          <option>Random Words</option>
          <option>Random Address</option>
          <option>Random Company</option>
          <option>Random City</option>
          <option>Random Country</option>
          <option>Random Job</option>
          <option>Random Username</option>
          <option>Random Number</option>
        </select>
      );
    }
    
    if (field.type === 'date') return <div className="text-xs text-blue-400 font-medium bg-blue-900/20 px-2 py-1 rounded">Auto Date Generator</div>;
    if (field.type === 'time') return <div className="text-xs text-purple-400 font-medium bg-purple-900/20 px-2 py-1 rounded">Auto Time Generator</div>;
    
    return (
      <div className="text-xs text-neutral-400 max-w-[200px] truncate bg-neutral-800 px-2 py-1 rounded">
        {field.options.length} options detected
      </div>
    );
  };

  if (jobId && progress) {
    // Progress View
    const percentage = Math.round((progress.progress / progress.total) * 100);
    return (
      <div className="min-h-screen bg-neutral-950 text-white flex flex-col items-center justify-center p-6 font-sans">
        <div className="max-w-xl w-full bg-neutral-900 border border-neutral-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500" style={{ width: `${percentage}%`, transition: 'width 0.5s' }} />
          
          <h2 className="text-3xl font-bold mb-2 tracking-tight text-white flex items-center gap-3">
            {progress.status === 'completed' ? <CheckCircle2 className="text-green-500" /> : <Loader2 className="animate-spin text-blue-500" />}
            {progress.status === 'completed' ? 'Automation Complete' : 'Running Automation'}
          </h2>
          <p className="text-neutral-400 mb-8">Generated {progress.progress} of {progress.total} responses</p>
          
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-neutral-800/50 p-4 rounded-xl border border-neutral-800/80 flex flex-col">
              <span className="text-sm text-neutral-400 mb-1">Successful</span>
              <span className="text-3xl font-semibold text-green-400">{progress.success}</span>
            </div>
            <div className="bg-neutral-800/50 p-4 rounded-xl border border-neutral-800/80 flex flex-col">
              <span className="text-sm text-neutral-400 mb-1">Failed</span>
              <span className="text-3xl font-semibold text-red-400">{progress.error}</span>
            </div>
          </div>
          
          {progress.errors && progress.errors.length > 0 && (
            <div className="mb-6 p-4 bg-red-950/30 border border-red-900/50 rounded-xl">
              <h4 className="text-red-400 font-medium mb-2 text-sm flex items-center gap-2"><Server size={14}/> Recent Errors</h4>
              <ul className="text-xs text-red-300 space-y-1 overflow-y-auto max-h-32">
                {progress.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}
          
          {progress.status === 'completed' && (
            <button 
              onClick={() => { setJobId(null); setProgress(null); }}
              className="w-full py-3 bg-neutral-100 text-neutral-900 font-medium rounded-xl hover:bg-white transition-colors"
            >
              Start New Job
            </button>
          )}
        </div>
      </div>
    );
  }

  if (structure) {
    // Configuration Dashboard View
    return (
      <div className="min-h-screen bg-neutral-950 text-white p-6 md:p-12 font-sans">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight mb-1 text-white flex items-center gap-3">
                <Settings className="text-blue-500" /> Form Configuration
              </h1>
              <p className="text-neutral-400 truncate max-w-lg text-sm">{structure.url}</p>
            </div>
            <button 
              onClick={() => setStructure(null)} 
              className="text-sm text-neutral-400 hover:text-white transition-colors px-4 py-2 bg-neutral-900 rounded-lg border border-neutral-800"
            >
              Back
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-4">
              <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><FileText size={18} className="text-neutral-400"/> Map Fields</h2>
                <div className="space-y-4">
                  {structure.fields.map((field, idx) => (
                    <div key={field.id} className="p-4 bg-neutral-950/50 border border-neutral-800 rounded-xl flex flex-col sm:flex-row gap-4 justify-between sm:items-center">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-neutral-200">{field.title || field.id}</p>
                          {field.required && <span className="text-red-500 text-xs font-bold">* Required</span>}
                        </div>
                        <p className="text-xs text-neutral-500 mt-1 uppercase tracking-wider font-semibold">{field.type.replace('_', ' ')}</p>
                      </div>
                      
                      {renderFieldConfig(field, idx)}
                    </div>
                  ))}
                  {structure.fields.length === 0 && (
                    <p className="text-neutral-500 text-sm">No standard fields detected. The scraper might have missed them or they are unsupported.</p>
                  )}
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl sticky top-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><BarChart size={18} className="text-neutral-400"/> Execution Settings</h2>
                
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm text-neutral-400 mb-2">Number of Responses</label>
                    <input 
                      type="number" 
                      min="1" max="10000"
                      value={count}
                      onChange={(e) => setCount(Number(e.target.value))}
                      className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                </div>
                
                <button 
                  onClick={startAutomation}
                  disabled={loading}
                  className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-900/20 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
                  Start Automation
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Landing View
  return (
    <main className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 font-sans relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-900/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-900/20 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="max-w-2xl w-full z-10 text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white via-neutral-200 to-neutral-500">
            Automate Forms.<br/>At Scale.
          </h1>
          <p className="text-lg text-neutral-400 max-w-lg mx-auto leading-relaxed">
            Instantly generate thousands of realistic responses for your Google Forms. Perfect for load testing and data population.
          </p>
        </div>

        <div className="bg-neutral-900/80 backdrop-blur-xl border border-neutral-800 p-2 rounded-2xl shadow-2xl flex flex-col sm:flex-row gap-2 transition-all focus-within:border-neutral-700">
          <input
            type="url"
            placeholder="Paste Google Form URL here..."
            className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-neutral-600"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button
            onClick={fetchStructure}
            disabled={loading}
            className="bg-white text-neutral-950 px-6 py-3 rounded-xl font-medium hover:bg-neutral-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <>Fetch Structure <ArrowRight size={18} /></>}
          </button>
        </div>
        
        {error && (
          <p className="text-red-400 text-sm bg-red-950/50 inline-block px-4 py-2 rounded-lg border border-red-900/50">
            {error}
          </p>
        )}
      </div>
    </main>
  );
}
