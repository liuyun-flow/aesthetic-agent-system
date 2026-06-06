"use client";

import { useState, useEffect, useRef } from "react";
import { useT } from "@/i18n";

interface RefCase {
  id: number;
  title: string;
  aesthetic_level: string | null;
  category: string | null;
  style_tags: string | null;
  target_audience: string | null;
  price_band: string | null;
  image_id: number | null;
  image_url: string | null;
  image_description: string | null;
  ai_description: string | null;
  notes: string | null;
  score: number | null;
  premium_sources: string | null;
  cheapness_sources: string | null;
  learn_from_this: string | null;
  avoid_copying: string | null;
}

const EMPTY_FORM = { title: "", level: "unknown", category: "", priceBand: "", score: "", notes: "", styleTags: "", audience: "", premiumSources: "", cheapnessSources: "", learnFrom: "", avoidCopying: "", imageDesc: "" };

export default function ReferencePanel() {
  const { t } = useT();
  const [cases, setCases] = useState<RefCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [f, setF] = useState(EMPTY_FORM);

  // Image upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [imageId, setImageId] = useState<number | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [describing, setDescribing] = useState(false);

  // Detail modal
  const [detail, setDetail] = useState<RefCase | null>(null);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${base}/reference-cases?limit=30`);
      if (res.ok) setCases((await res.json()).cases ?? []);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchCases(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true); setUploadError(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(`${base}/upload`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setImageId(data.image_id);
      setImageUrl(data.url.startsWith("http") ? data.url : `${base}${data.url}`);
    } catch (err: unknown) { setUploadError(err instanceof Error ? err.message : "Upload failed"); }
    finally { setUploading(false); }
  };

  const handleAutoDescribe = async () => {
    if (!imageId) return;
    setDescribing(true);
    try {
      const res = await fetch(`${base}/images/${imageId}/describe`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setF(prev => ({ ...prev, imageDesc: data.description?.suggested_prompt_text || prev.imageDesc }));
      }
    } catch { /* ignore */ }
    finally { setDescribing(false); }
  };

  const resetForm = () => { setF(EMPTY_FORM); setImageId(null); setImageUrl(null); setShowForm(false); };

  const handleCreate = async () => {
    if (!f.title.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${base}/reference-cases`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: f.title.trim(), category: f.category.trim() || null,
          aesthetic_level: f.level, style_tags: f.styleTags.trim() || null,
          target_audience: f.audience.trim() || null, price_band: f.priceBand.trim() || null,
          image_id: imageId, image_description: f.imageDesc.trim() || null,
          notes: f.notes.trim() || null, score: f.score ? parseInt(f.score, 10) : null,
          premium_sources: f.premiumSources.trim() || null,
          cheapness_sources: f.cheapnessSources.trim() || null,
          learn_from_this: f.learnFrom.trim() || null,
          avoid_copying: f.avoidCopying.trim() || null,
        }),
      });
      if (res.ok) { resetForm(); fetchCases(); }
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const levelBadge = (l: string | null) => {
    const m: Record<string, string> = { high: "bg-green-100 text-green-700", medium: "bg-amber-100 text-amber-700", low: "bg-red-100 text-red-700", unknown: "bg-gray-100 text-gray-500" };
    return m[l ?? "unknown"] ?? m.unknown;
  };
  const levelLabel = (l: string | null) => {
    const m: Record<string, string> = { high: t.reference.high, medium: t.reference.medium, low: t.reference.low };
    return m[l ?? ""] ?? t.reference.unknown;
  };

  const imgSrc = (c: RefCase) => c.image_url ? (c.image_url.startsWith("http") ? c.image_url : `${base}${c.image_url}`) : null;

  return (
    <section className="rounded border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-gray-800">{t.reference.title}</h2>
        <button onClick={() => { setShowForm(!showForm); if (showForm) resetForm(); }}
          className="text-xs text-blue-600 hover:text-blue-800 underline">
          {showForm ? t.reference.cancel : t.reference.addCase}
        </button>
      </div>

      {showForm && (
        <div className="mb-4 space-y-2 rounded border bg-gray-50 p-3 max-h-[70vh] overflow-y-auto">
          <input value={f.title} onChange={e => setF(p => ({...p, title: e.target.value}))} placeholder={t.reference.titleField} className="w-full rounded border px-2 py-1 text-sm" />

          {/* Image upload */}
          <div className="rounded border bg-white p-2">
            <p className="text-xs text-gray-500 mb-1">案例图片</p>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleUpload} className="text-xs" />
            {uploading && <p className="text-xs text-blue-500">上传中…</p>}
            {uploadError && <p className="text-xs text-red-500">{uploadError}</p>}
            {imageUrl && (
              <div className="mt-1">
                <img src={imageUrl} alt="Preview" className="max-h-32 rounded border" />
                <button type="button" onClick={handleAutoDescribe} disabled={describing}
                  className="mt-1 rounded bg-purple-600 px-2 py-0.5 text-xs text-white disabled:bg-gray-300">
                  {describing ? "生成中…" : "自动生成图片描述"}
                </button>
              </div>
            )}
            <textarea rows={2} value={f.imageDesc} onChange={e => setF(p => ({...p, imageDesc: e.target.value}))}
              placeholder="图片描述…" className="mt-1 w-full rounded border px-2 py-1 text-xs" />
          </div>

          <div className="flex gap-2">
            <select value={f.level} onChange={e => setF(p => ({...p, level: e.target.value}))} className="rounded border px-2 py-1 text-sm">
              <option value="high">{t.reference.high}</option><option value="medium">{t.reference.medium}</option>
              <option value="low">{t.reference.low}</option><option value="unknown">{t.reference.unknown}</option>
            </select>
            <input value={f.category} onChange={e => setF(p => ({...p, category: e.target.value}))} placeholder={t.reference.category} className="flex-1 rounded border px-2 py-1 text-sm" />
          </div>
          <div className="flex gap-2">
            <input value={f.priceBand} onChange={e => setF(p => ({...p, priceBand: e.target.value}))} placeholder={t.reference.priceBand} className="flex-1 rounded border px-2 py-1 text-sm" />
            <input value={f.score} onChange={e => setF(p => ({...p, score: e.target.value}))} type="number" min={0} max={100} placeholder={t.reference.scoreField} className="w-28 rounded border px-2 py-1 text-sm" />
          </div>
          <input value={f.styleTags} onChange={e => setF(p => ({...p, styleTags: e.target.value}))} placeholder="风格标签（逗号分隔）" className="w-full rounded border px-2 py-1 text-sm" />
          <input value={f.audience} onChange={e => setF(p => ({...p, audience: e.target.value}))} placeholder="目标用户" className="w-full rounded border px-2 py-1 text-sm" />
          <textarea rows={1} value={f.premiumSources} onChange={e => setF(p => ({...p, premiumSources: e.target.value}))} placeholder="高级感来源…" className="w-full rounded border px-2 py-1 text-sm" />
          <textarea rows={1} value={f.cheapnessSources} onChange={e => setF(p => ({...p, cheapnessSources: e.target.value}))} placeholder="廉价感来源…" className="w-full rounded border px-2 py-1 text-sm" />
          <textarea rows={1} value={f.learnFrom} onChange={e => setF(p => ({...p, learnFrom: e.target.value}))} placeholder="值得学习什么…" className="w-full rounded border px-2 py-1 text-sm" />
          <textarea rows={1} value={f.avoidCopying} onChange={e => setF(p => ({...p, avoidCopying: e.target.value}))} placeholder="不能误学什么…" className="w-full rounded border px-2 py-1 text-sm" />
          <textarea rows={2} value={f.notes} onChange={e => setF(p => ({...p, notes: e.target.value}))} placeholder={t.reference.notes} className="w-full rounded border px-2 py-1 text-sm" />
          <button onClick={handleCreate} disabled={saving || !f.title.trim()}
            className="rounded bg-blue-600 px-4 py-1 text-xs text-white hover:bg-blue-700 disabled:bg-gray-300">
            {saving ? t.reference.saving : t.reference.save}
          </button>
        </div>
      )}

      {loading ? <p className="text-xs text-gray-400">{t.reference.loading}</p>
      : cases.length === 0 ? <p className="text-xs text-gray-400">{t.reference.empty}</p>
      : (
        <div className="space-y-2 max-h-[50vh] overflow-y-auto">
          {cases.map(c => (
            <div key={c.id} className="flex items-center gap-2 rounded border px-2 py-1 text-xs cursor-pointer hover:bg-gray-50"
              onClick={() => setDetail(c)}>
              {imgSrc(c) && <img src={imgSrc(c)!} alt="" className="h-10 w-10 rounded object-cover" />}
              <span className={`rounded px-1 py-0.5 font-medium ${levelBadge(c.aesthetic_level)}`}>{levelLabel(c.aesthetic_level)}</span>
              <span className="flex-1 truncate font-medium">{c.title}</span>
              {c.category && <span className="text-gray-400">{c.category}</span>}
              {c.score != null && <span className="text-gray-400">{c.score}</span>}
              <span className="text-blue-400">详情</span>
            </div>
          ))}
        </div>
      )}

      {/* Detail modal */}
      {detail && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-10 bg-black/40" onClick={() => setDetail(null)}>
          <div className="relative max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-xl" onClick={e => e.stopPropagation()}>
            <button onClick={() => setDetail(null)} className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 text-xl">✕</button>
            <div className="space-y-3 text-sm">
              {imgSrc(detail) && <img src={imgSrc(detail)!} alt="" className="w-full max-h-64 rounded object-cover" />}
              <h3 className="text-lg font-semibold">{detail.title}</h3>
              <div className="flex gap-2 text-xs">
                <span className={`rounded px-2 py-0.5 font-medium ${levelBadge(detail.aesthetic_level)}`}>{levelLabel(detail.aesthetic_level)}</span>
                {detail.category && <span className="text-gray-500">{detail.category}</span>}
                {detail.price_band && <span className="text-gray-500">{detail.price_band}</span>}
                {detail.score != null && <span className="text-gray-500">评分 {detail.score}</span>}
              </div>
              <KV label="风格标签" value={detail.style_tags} />
              <KV label="目标用户" value={detail.target_audience} />
              <KV label="图片描述" value={detail.image_description || detail.ai_description} />
              <KV label="高级感来源" value={detail.premium_sources} />
              <KV label="廉价感来源" value={detail.cheapness_sources} />
              <KV label="值得学习" value={detail.learn_from_this} />
              <KV label="不能误学" value={detail.avoid_copying} />
              <KV label="备注" value={detail.notes} />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function KV({ label, value }: { label: string; value: string | null | undefined }) {
  const display = value && value.trim() ? value : "暂无";
  return (
    <div>
      <span className="text-xs font-medium text-gray-500">{label}</span>
      <p className={`text-gray-700 whitespace-pre-wrap ${!value?.trim() ? "italic text-gray-400" : ""}`}>{display}</p>
    </div>
  );
}
