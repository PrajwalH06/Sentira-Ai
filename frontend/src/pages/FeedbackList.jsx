import { useState, useEffect } from 'react';
import { Search, RefreshCw, PenSquare, X, Check, BrainCircuit, ChevronDown, ChevronUp } from 'lucide-react';
import { getFeedbacks, correctFeedback } from '../api';

export default function FeedbackList() {
    const [feedbacks, setFeedbacks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ sentiment: '', category: '', urgency: '' });
    const [search, setSearch] = useState('');
    const [expandedRows, setExpandedRows] = useState(new Set());

    // Correction Modal State
    const [editingFeedback, setEditingFeedback] = useState(null);
    const [correction, setCorrection] = useState({ sentiment: '', category: '', urgency: '' });
    const [saving, setSaving] = useState(false);

    const load = async () => {
        setLoading(true);
        try {
            const params = { limit: 200, ...filters };
            const res = await getFeedbacks(params);
            setFeedbacks(res.data);
        } catch (err) { } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [filters]);

    const handleCorrect = async () => {
        if (!editingFeedback) return;
        setSaving(true);
        try {
            await correctFeedback(editingFeedback.id, correction);
            setFeedbacks(prev => prev.map(f => f.id === editingFeedback.id ? { ...f, ...correction, is_corrected: true } : f));
            setEditingFeedback(null);
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const toggleExpand = (id) => {
        setExpandedRows(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const filtered = feedbacks.filter((fb) => fb.text.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="animate-in">
            <div style={{ marginBottom: 40 }}>
                <h1 className="heading-hero" style={{ fontSize: '3rem' }}>
                    Data <span className="heading-gradient-accent">History.</span>
                </h1>
                <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)' }}>
                    Review past intelligence processing and fine-tune the master AI logic.
                </p>
            </div>

            {/* Premium Filter Bar */}
            <div className="glass-panel" style={{ padding: 24, marginBottom: 32, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 250, position: 'relative' }}>
                    <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                        className="input-field"
                        placeholder="Search specific processing..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ paddingLeft: 48, background: 'rgba(255,255,255,0.02)' }}
                    />
                </div>

                <Select filter={filters.sentiment} setFilter={(val) => setFilters(p => ({ ...p, sentiment: val }))} options={['positive', 'neutral', 'negative']} defaultText="All Sentiments" />
                <Select filter={filters.category} setFilter={(val) => setFilters(p => ({ ...p, category: val }))} options={['UI/UX', 'Bugs', 'Performance', 'Pricing', 'Support', 'Features']} defaultText="All Categories" />
                <Select filter={filters.urgency} setFilter={(val) => setFilters(p => ({ ...p, urgency: val }))} options={['low', 'medium', 'high', 'critical']} defaultText="All Urgencies" />

                <button className="btn-secondary" onClick={() => { setFilters({ sentiment: '', category: '', urgency: '' }); setSearch(''); }} style={{ padding: '16px' }}>
                    <RefreshCw size={18} />
                </button>
            </div>

            {/* Data Table */}
            <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
                {loading ? (
                    <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <div className="spinner" />
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
                                <tr>
                                    <th style={{ width: 60, textAlign: 'center' }}>ID</th>
                                    <th>Data Extract</th>
                                    <th>Sentiment</th>
                                    <th>Category</th>
                                    <th>Urgency</th>
                                    <th style={{ textAlign: 'right' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((fb) => {
                                    const isExpanded = expandedRows.has(fb.id);
                                    const isLong = fb.text.length > 120;
                                    return (
                                        <tr key={fb.id}>
                                            <td style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.8rem', verticalAlign: 'top', paddingTop: 18 }}>#{fb.id}</td>
                                            <td style={{ maxWidth: 500, color: 'var(--text-primary)' }}>
                                                <div>
                                                    {fb.is_corrected && (
                                                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--success)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', marginRight: 8, background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: 4 }}>
                                                            <Check size={10} /> Human Verified
                                                        </span>
                                                    )}
                                                    <span style={!isExpanded && isLong ? { display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' } : {}}>
                                                        {fb.text}
                                                    </span>
                                                    {isLong && (
                                                        <button
                                                            onClick={() => toggleExpand(fb.id)}
                                                            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 4 }}
                                                        >
                                                            {isExpanded ? <><ChevronUp size={12} /> Show less</> : <><ChevronDown size={12} /> Show more</>}
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                            <td style={{ verticalAlign: 'top', paddingTop: 18 }}>
                                                <span className={`badge badge-${fb.sentiment}`}>{fb.sentiment}</span>
                                                {fb.secondary_sentiments?.map((s, i) => (
                                                    <span key={i} className={`badge badge-${s.label}`} style={{ opacity: 0.5, marginLeft: 4, fontSize: '0.6rem' }}>
                                                        {s.label} {(s.confidence * 100).toFixed(0)}%
                                                    </span>
                                                ))}
                                            </td>
                                            <td style={{ verticalAlign: 'top', paddingTop: 18 }}>
                                                <span className="badge" style={{ borderColor: 'var(--border)' }}>{fb.category}</span>
                                                {fb.secondary_categories?.map((c, i) => (
                                                    <span key={i} className="badge" style={{ opacity: 0.5, marginLeft: 4, fontSize: '0.6rem', borderColor: 'var(--border)' }}>
                                                        {c.label} {(c.confidence * 100).toFixed(0)}%
                                                    </span>
                                                ))}
                                            </td>
                                            <td style={{ verticalAlign: 'top', paddingTop: 18 }}><span className={`badge badge-${fb.urgency}`}>{fb.urgency}</span></td>
                                            <td style={{ textAlign: 'right', verticalAlign: 'top', paddingTop: 14 }}>
                                                <button
                                                    onClick={() => { setEditingFeedback(fb); setCorrection({ sentiment: fb.sentiment, category: fb.category, urgency: fb.urgency }); }}
                                                    className="btn-secondary"
                                                    style={{ padding: '6px 12px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: 6, opacity: fb.is_corrected ? 0.5 : 1 }}
                                                >
                                                    <BrainCircuit size={14} /> Correct AI
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Correction Modal */}
            {editingFeedback && (
                <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(10,10,15,0.8)', backdropFilter: 'blur(8px)' }}>
                    <div className="glass-panel" style={{ width: '100%', maxWidth: 500, padding: 32, animation: 'fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                                <PenSquare size={20} color="var(--primary)" /> Tune AI Logic
                            </h2>
                            <button onClick={() => setEditingFeedback(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={20} /></button>
                        </div>

                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 24, fontStyle: 'italic', padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8, borderLeft: '2px solid var(--primary)', maxHeight: 200, overflowY: 'auto' }}>
                            "{editingFeedback.text}"
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 32 }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Sentiment</label>
                                <Select filter={correction.sentiment} setFilter={(val) => setCorrection(p => ({ ...p, sentiment: val }))} options={['positive', 'neutral', 'negative']} />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Category</label>
                                <Select filter={correction.category} setFilter={(val) => setCorrection(p => ({ ...p, category: val }))} options={['UI/UX', 'Bugs', 'Performance', 'Pricing', 'Support', 'Features']} />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', fontWeight: 600 }}>Urgency</label>
                                <Select filter={correction.urgency} setFilter={(val) => setCorrection(p => ({ ...p, urgency: val }))} options={['low', 'medium', 'high', 'critical']} />
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                            <button className="btn-secondary" onClick={() => setEditingFeedback(null)}>Cancel</button>
                            <button className="btn-primary" onClick={handleCorrect} disabled={saving}>
                                {saving ? 'Updating Matrix...' : 'Train AI'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function Select({ filter, setFilter, options, defaultText }) {
    return (
        <select
            className="input-field"
            style={{ width: 'auto', background: 'rgba(255,255,255,0.02)', padding: '16px', minWidth: 160 }}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
        >
            {defaultText && <option value="" style={{ background: 'var(--bg-secondary)' }}>{defaultText}</option>}
            {options.map(opt => (
                <option key={opt} value={opt} style={{ background: 'var(--bg-secondary)', textTransform: 'capitalize' }}>
                    {opt}
                </option>
            ))}
        </select>
    );
}
