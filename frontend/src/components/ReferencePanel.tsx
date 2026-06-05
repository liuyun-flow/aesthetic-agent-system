"use client";

import { useState, useEffect } from "react";

interface RefCase {
  id: number;
  title: string;
  aesthetic_level: string | null;
  category: string | null;
  style_tags: string | null;
  price_band: string | null;
  notes: string | null;
  score: number | null;
}

export default function ReferencePanel() {
  const [cases, setCases] = useState<RefCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // New case form
  const [title, setTitle] = useState("");
  const [level, setLevel] = useState("unknown");
  const [category, setCategory] = useState("");
  const [priceBand, setPriceBand] = useState("");
  const [notes, setNotes] = useState("");
  const [score, setScore] = useState("");
  const [saving, setSaving] = useState(false);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${base}/reference-cases?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setCases(data.cases ?? []);
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchCases(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCreate = async () => {
    if (!title.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${base}/reference-cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          aesthetic_level: level,
          category: category.trim() || null,
          price_band: priceBand.trim() || null,
          notes: notes.trim() || null,
          score: score ? parseInt(score, 10) : null,
        }),
      });
      if (res.ok) {
        setTitle(""); setLevel("unknown"); setCategory("");
        setPriceBand(""); setNotes(""); setScore("");
        setShowForm(false);
        fetchCases();
      }
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const levelBadge = (l: string | null) => {
    const colors: Record<string, string> = {
      high: "bg-green-100 text-green-700",
      medium: "bg-amber-100 text-amber-700",
      low: "bg-red-100 text-red-700",
      unknown: "bg-gray-100 text-gray-500",
    };
    return colors[l ?? "unknown"] ?? colors.unknown;
  };

  return (
    <section className="rounded border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-gray-800">Reference Cases</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-xs text-blue-600 hover:text-blue-800 underline"
        >
          {showForm ? "Cancel" : "+ Add Case"}
        </button>
      </div>

      {showForm && (
        <div className="mb-4 space-y-2 rounded border bg-gray-50 p-3">
          <input value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="Title" className="w-full rounded border px-2 py-1 text-sm" />
          <div className="flex gap-2">
            <select value={level} onChange={(e) => setLevel(e.target.value)}
              className="rounded border px-2 py-1 text-sm">
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="unknown">Unknown</option>
            </select>
            <input value={category} onChange={(e) => setCategory(e.target.value)}
              placeholder="Category (e.g. web, print)" className="flex-1 rounded border px-2 py-1 text-sm" />
          </div>
          <div className="flex gap-2">
            <input value={priceBand} onChange={(e) => setPriceBand(e.target.value)}
              placeholder="Price band" className="flex-1 rounded border px-2 py-1 text-sm" />
            <input value={score} onChange={(e) => setScore(e.target.value)}
              type="number" min={0} max={100} placeholder="Score 0-100"
              className="w-24 rounded border px-2 py-1 text-sm" />
          </div>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
            rows={2} placeholder="Notes..."
            className="w-full rounded border px-2 py-1 text-sm" />
          <button onClick={handleCreate} disabled={saving || !title.trim()}
            className="rounded bg-blue-600 px-4 py-1 text-xs text-white hover:bg-blue-700 disabled:bg-gray-300">
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      )}

      {loading ? (
        <p className="text-xs text-gray-400">Loading...</p>
      ) : cases.length === 0 ? (
        <p className="text-xs text-gray-400">No reference cases yet. Add high, medium, and low examples.</p>
      ) : (
        <div className="space-y-1 max-h-60 overflow-y-auto">
          {cases.map((c) => (
            <div key={c.id} className="flex items-center gap-2 rounded border px-2 py-1 text-xs">
              <span className={`rounded px-1 py-0.5 font-medium ${levelBadge(c.aesthetic_level)}`}>
                {c.aesthetic_level ?? "?"}
              </span>
              <span className="flex-1 truncate">{c.title}</span>
              {c.score != null && <span className="text-gray-400">{c.score}</span>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
