import { useState, useRef } from 'react';
import { Send, Upload, Sparkles, Loader2, FileText, X } from 'lucide-react';
import { submitFeedback, uploadCSV, analyzeFeedback } from '../api';

export default function SubmitFeedback() {
    const [text, setText] = useState('');
    const [preview, setPreview] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);

    // CSV State
    const [csvFile, setCsvFile] = useState(null);
    const [csvResults, setCsvResults] = useState(null);
    const [dragActive, setDragActive] = useState(false);
    const fileRef = useRef();
    const debounceRef = useRef();

    const handleTextChange = (e) => {
        const val = e.target.value;
        if (val.length > 5000) return; // limit
        setText(val);
        setResult(null);

        if (debounceRef.current) clearTimeout(debounceRef.current);
        if (val.trim().length > 10) {
            debounceRef.current = setTimeout(async () => {
                try {
                    setAnalyzing(true);
                    const res = await analyzeFeedback(val);
                    setPreview(res.data);
                } catch { } // ignore
                finally {
                    setAnalyzing(false);
                }
            }, 600);
        } else {
            setPreview(null);
        }
    };

    const handleSubmit = async () => {
        if (!text.trim()) return;
        setSubmitting(true);
        try {
            const res = await submitFeedback(text);
            setResult(res.data);
            setPreview(null);
        } catch (err) {
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleCSVUpload = async (file) => {
        if (!file) return;
        setCsvFile(file);
        setSubmitting(true);
        try {
            const res = await uploadCSV(file);
            setCsvResults(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="animate-in">
            {/* Hero Header */}
            <div style={{ maxWidth: 800, marginBottom: 40 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 10px', borderRadius: 8, background: 'rgba(20, 184, 166, 0.1)', border: '1px solid rgba(20, 184, 166, 0.2)', marginBottom: 20 }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--primary)' }} />
                    <span style={{ fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--primary)', textTransform: 'uppercase' }}>
                        Sentira Terminal
                    </span>
                </div>

                <h1 className="heading-hero">
                    Feedback <br />
                    <span className="heading-gradient">Analysis.</span>
                </h1>
                <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: 600 }}>
                    Evaluate customer sentiment, urgency, and category intent automatically using local processing.
                </p>
            </div>

            {/* Split View */}
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(0, 1fr)', gap: 32 }}>

                {/* Left: Input Area */}
                <div className="glass-input-area" style={{ display: 'flex', flexDirection: 'column', minHeight: 400 }}>
                    <textarea
                        className="input-field"
                        style={{ flex: 1, minHeight: 300 }}
                        placeholder="Articulate customer feedback here..."
                        value={text}
                        onChange={handleTextChange}
                    />

                    {/* Bottom Action Bar inside Textarea */}
                    <div style={{ padding: '16px 24px', background: 'rgba(255, 255, 255, 0.02)', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {text.length} / 5,000 characters
                        </span>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                            {analyzing && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                    <Loader2 size={14} className="animate-spin" /> Thinking...
                                </div>
                            )}
                            <button
                                className="btn-primary"
                                disabled={!text.trim() || submitting}
                                onClick={handleSubmit}
                            >
                                {submitting ? 'Analyzing...' : 'Run Analysis'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right: Options & Results panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

                    {/* Live Preview / Result Card */}
                    {(preview || result) && (
                        <div className="glass-panel" style={{ padding: 24, background: result ? 'rgba(16, 185, 129, 0.05)' : undefined, borderColor: result ? 'rgba(16, 185, 129, 0.2)' : undefined }}>
                            <h3 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Sparkles size={14} color={result ? "var(--success)" : "var(--accent-light)"} />
                                {result ? "Final Analysis" : "Live Prediction"}
                            </h3>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <PredictionRow label="Sentiment" value={(result || preview).sentiment} confidence={(result || preview).sentiment_confidence} />
                                <PredictionRow label="Category" value={(result || preview).category} confidence={(result || preview).category_confidence} />
                                <PredictionRow label="Urgency" value={(result || preview).urgency} confidence={(result || preview).urgency_confidence} />
                            </div>
                        </div>
                    )}

                    {/* Batch Upload Area */}
                    <div className="glass-panel" style={{ padding: 24 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                            <Upload size={16} color="var(--text-muted)" />
                            <h3 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Batch Processing
                            </h3>
                        </div>

                        <div
                            style={{
                                border: `1px dashed ${dragActive ? 'var(--primary)' : 'var(--border)'}`,
                                background: dragActive ? 'rgba(20, 184, 166, 0.05)' : 'rgba(255, 255, 255, 0.01)',
                                borderRadius: 8,
                                padding: 32,
                                textAlign: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                            onDragLeave={() => setDragActive(false)}
                            onDrop={(e) => {
                                e.preventDefault();
                                setDragActive(false);
                                if (e.dataTransfer.files[0]?.name.endsWith('.csv')) {
                                    handleCSVUpload(e.dataTransfer.files[0]);
                                }
                            }}
                            onClick={() => fileRef.current?.click()}
                        >
                            <FileText size={24} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                Drop CSV to analyze bulk logic
                            </p>
                        </div>
                        <input
                            ref={fileRef}
                            type="file"
                            accept=".csv"
                            style={{ display: 'none' }}
                            onChange={(e) => handleCSVUpload(e.target.files[0])}
                        />

                        {csvResults && (
                            <div style={{ marginTop: 16, fontSize: '0.85rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Sparkles size={14} /> Processed {csvResults.length} rows successfully.
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
}

function PredictionRow({ label, value, confidence }) {
    return (
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: 12, border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{label}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--primary-light)' }}>
                    {confidence ? `${(confidence * 100).toFixed(0)}% conf` : ''}
                </span>
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                {value}
            </div>
        </div>
    );
}
