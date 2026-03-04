import { useState, useEffect } from 'react';
import { Activity, MessageSquare, AlertCircle, TrendingUp, Sparkles, CheckCircle, Clock } from 'lucide-react';
import { getOverview, getFeedbacks } from '../api';

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [recent, setRecent] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [statsRes, feedRes] = await Promise.all([
                    getOverview(),
                    getFeedbacks({ limit: 8 })
                ]);
                setStats(statsRes.data);
                setRecent(feedRes.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    if (loading) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 16 }}>
                <div className="spinner" style={{ borderTopColor: 'var(--primary)' }} />
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Loading Intelligence...</p>
            </div>
        );
    }

    return (
        <div className="animate-in">
            <div style={{ marginBottom: 40 }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 10px', borderRadius: 8, background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', marginBottom: 20 }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)' }} />
                    <span style={{ fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--accent)', textTransform: 'uppercase' }}>
                        Platform Overview
                    </span>
                </div>
                <h1 className="heading-hero">
                    <span className="heading-gradient-accent">Macro-level</span> <br />
                    Intelligence.
                </h1>
                <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', maxWidth: 600 }}>
                    Real-time metrics on customer sentiment, critical issues, and AI confidence levels.
                </p>
            </div>

            {/* Premium Stat Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24, marginBottom: 40 }}>
                <StatCard
                    title="Total Feedbacks"
                    value={stats.total_feedbacks.toLocaleString()}
                    icon={MessageSquare}
                    color="var(--primary)"
                    bg="rgba(20, 184, 166, 0.05)"
                />
                <StatCard
                    title="Avg AI Confidence"
                    value={`${(stats.avg_sentiment_confidence * 100).toFixed(1)}%`}
                    icon={Sparkles}
                    color="var(--accent)"
                    bg="rgba(245, 158, 11, 0.05)"
                />
                <StatCard
                    title="Critical Issues"
                    value={stats.urgency_distribution.critical || 0}
                    icon={AlertCircle}
                    color="#ef4444"
                    bg="rgba(239, 68, 68, 0.05)"
                />
                <StatCard
                    title="Positive Sentiment"
                    value={stats.sentiment_distribution.positive || 0}
                    icon={CheckCircle}
                    color="#10b981"
                    bg="rgba(16, 185, 129, 0.05)"
                />
            </div>

            {/* Split Content: Recent Feedback (Left) and Sentiment Distribution (Right) */}
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 32 }}>

                {/* Recent Feedbacks */}
                <div className="glass-panel" style={{ padding: 32 }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Clock size={16} /> Latest Inferences
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        {recent.map(fb => (
                            <div key={fb.id} style={{ padding: '16px 20px', background: 'rgba(255,255,255,0.02)', borderRadius: 12, border: '1px solid var(--border)' }}>
                                <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: 12, lineHeight: 1.5 }}>
                                    "{fb.text}"
                                </p>
                                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                                    <span className={`badge badge-${fb.sentiment}`}>{fb.sentiment}</span>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{fb.category}</span>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>• {(fb.sentiment_confidence * 100).toFixed(0)}% conf</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Simplified Sentiment Distribution (No heavy charts) */}
                <div className="glass-panel" style={{ padding: 32, height: 'fit-content' }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Activity size={16} /> Sentiment Distribution
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        <DistributionBar label="Positive" value={stats.sentiment_distribution.positive || 0} total={stats.total_feedbacks} color="#10b981" />
                        <DistributionBar label="Neutral" value={stats.sentiment_distribution.neutral || 0} total={stats.total_feedbacks} color="#f59e0b" />
                        <DistributionBar label="Negative" value={stats.sentiment_distribution.negative || 0} total={stats.total_feedbacks} color="#ef4444" />
                    </div>
                </div>

            </div>
        </div>
    );
}

function StatCard({ title, value, icon: Icon, color, bg }) {
    return (
        <div className="glass-panel" style={{ padding: 24, position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {title}
                </span>
                <div style={{ padding: 8, borderRadius: 10, background: bg, color: color }}>
                    <Icon size={18} />
                </div>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                {value}
            </div>
            {/* Glowing orb accent */}
            <div style={{ position: 'absolute', bottom: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: color, filter: 'blur(40px)', opacity: 0.15 }} />
        </div>
    );
}

function DistributionBar({ label, value, total, color }) {
    const percentage = total > 0 ? (value / total) * 100 : 0;

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{value} ({percentage.toFixed(1)}%)</span>
            </div>
            <div style={{ height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${percentage}%`, background: color, borderRadius: 3, transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)' }} />
            </div>
        </div>
    );
}
