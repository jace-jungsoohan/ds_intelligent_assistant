"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
    LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    data?: any[];
    sql?: string;
    agent?: string;
}

const SUGGESTIONS = [
    "📉 상하이(CNSHG)행 총 물량 및 파손율",
    "🔥 구간별 충격 리스크 히트맵 분석",
    "⚠️ 누적 충격 피로도 Top 5 운송 건",
    "🍬 오사카행 온도 이탈 평균 지속 시간",
    "📊 포장 타입별 파손율 및 안전 점수 비교",
    "🛳️ 해상 운송 중 5G 이상 충격 발생 비율",
    "📍 베트남 경로 습도 취약 구간 분석",
    "❄️ 영하 온도에서 발생한 충격 건수",
    "🏆 운송사별 배송 품질 벤치마킹",
    "🚨 최근 1주일 High Risk 등급 운송 건",
    "📦 포장재별 평균 온도 유지 성능",
    "✈️ 항공 운송 중 과도한 기울기(Tilt) 발생 건수",
    "📅 월별 화물 무사고(파손 0) 비율 추이",
    "🚛 트럭 운송 시 평균 충격량(G) 통계",
    "🌡️ 여름철(7-8월) 온도 이탈 화물 집중 분석"
];

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! Willog AI Assistant입니다. 무엇을 도와드릴까요?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async (text?: string) => {
        const contentToUse = text || input;
        if (!contentToUse.trim() || loading) return;

        // Clear input if typed
        if (!text) setInput('');

        const userMessage: Message = { role: 'user', content: contentToUse };
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: newMessages }),
            });

            if (!response.ok) throw new Error('Failed');

            const resData = await response.json();
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: resData.answer,
                data: resData.data,
                sql: resData.sql,
                agent: resData.agent
            }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: '서버 연결에 실패했습니다.' }]);
        } finally {
            setLoading(false);
        }
    };

    const renderVisualization = (data: any[], agent: string | undefined) => {
        if (!data || data.length === 0) return null;

        const columns = Object.keys(data[0]);

        const dateCol = columns.find(c => c.includes('date') || c.includes('day') || c.includes('time'));
        const numCol = columns.find(c => typeof data[0][c] === 'number');
        const catCol = columns.find(c => typeof data[0][c] === 'string');

        // 1. Time Series (Line Chart)
        if (dateCol && numCol) {
            return (
                <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                    <h4 style={{ marginBottom: 10, color: '#444' }}>📈 Trend Analysis</h4>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={dateCol} fontSize={12} tickMargin={10} />
                            <YAxis fontSize={12} />
                            <Tooltip contentStyle={{ borderRadius: 8 }} />
                            <Legend />
                            <Line type="monotone" dataKey={numCol} stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        // 2. Geospatial (Scatter Chart)
        const latCol = columns.find(c => /lat/i.test(c));
        const lonCol = columns.find(c => /lon|lng/i.test(c));

        if (latCol && lonCol) {
            // Robust Data Mapping: standardizing x/y keys and ensuring numbers
            const chartData = data
                .filter(d =>
                    d[latCol] != null && !isNaN(Number(d[latCol])) &&
                    d[lonCol] != null && !isNaN(Number(d[lonCol]))
                )
                .map((d, i) => ({
                    id: i,
                    x: Number(d[lonCol]), // Longitude as X
                    y: Number(d[latCol]), // Latitude as Y
                    ...d // Keep original data for tooltip
                }));

            if (chartData.length === 0) return null;

            return (
                <div style={{ height: 400, width: '100%', marginTop: 20 }}>
                    <h4 style={{ marginBottom: 10, color: '#444' }}>🗺️ Geospatial Distribution</h4>
                    <div style={{ background: '#f9f9f9', borderRadius: 12, padding: 10, height: '100%', border: '1px solid #eee' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" dataKey="x" name="Longitude" domain={['auto', 'auto']} fontSize={12} unit="°" />
                                <YAxis type="number" dataKey="y" name="Latitude" domain={['auto', 'auto']} fontSize={12} unit="°" />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ borderRadius: 8 }} />
                                <Legend />
                                <Scatter name="Locations" data={chartData} fill="#ff7300" isAnimationActive={false} />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                    <div style={{ textAlign: 'center', fontSize: '0.8rem', color: '#999', marginTop: 5 }}>
                        * Displaying {chartData.length} valid points
                    </div>
                </div>
            );
        }

        // 3. Comparison (Bar Chart)
        if (catCol && numCol) {
            return (
                <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                    <h4 style={{ marginBottom: 10, color: '#444' }}>📊 Comparison</h4>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={catCol} fontSize={12} tickMargin={10} />
                            <YAxis fontSize={12} />
                            <Tooltip contentStyle={{ borderRadius: 8 }} />
                            <Legend />
                            <Bar dataKey={numCol} fill="#82ca9d" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        return null;
    };

    return (
        <div style={{ maxWidth: '900px', margin: '0 auto', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
            <header style={{
                position: 'sticky', top: 0, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)',
                padding: '16px 20px', borderBottom: '1px solid #eaeaea', zIndex: 100
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 24, height: 24, background: '#007AFF', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: 14 }}>W</div>
                    <h1 style={{ margin: 0, fontSize: '1.1rem', color: '#111', fontWeight: 600 }}>Willog AI Assistant</h1>
                </div>
            </header>

            <div style={{ padding: '20px 20px 100px 20px', minHeight: 'calc(100vh - 140px)' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{
                        marginBottom: '24px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}>
                        <div style={{
                            padding: '14px 18px',
                            borderRadius: '18px',
                            borderBottomRightRadius: msg.role === 'user' ? '4px' : '18px',
                            borderBottomLeftRadius: msg.role === 'user' ? '18px' : '4px',
                            background: msg.role === 'user' ? '#007AFF' : '#F2F2F7',
                            color: msg.role === 'user' ? '#fff' : '#111',
                            maxWidth: '85%',
                            lineHeight: '1.6',
                            whiteSpace: 'pre-wrap',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                            fontSize: '0.95rem'
                        }}>
                            {msg.content}
                        </div>

                        {/* SQL Debug Block */}
                        {msg.sql && (
                            <details style={{ marginTop: 8, maxWidth: '85%', width: '100%' }}>
                                <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: '#888', listStyle: 'none' }}>🛠️ Generated SQL</summary>
                                <pre style={{
                                    background: '#f8f9fa', padding: 12, borderRadius: 8, marginTop: 4,
                                    fontSize: '0.75rem', overflowX: 'auto', border: '1px solid #eee', color: '#333'
                                }}>
                                    {msg.sql}
                                </pre>
                            </details>
                        )}

                        {/* Data Visualization & Table */}
                        {msg.data && (
                            <div style={{ width: '100%', marginTop: 12, maxWidth: '100%' }}>
                                {/* Charts */}
                                {renderVisualization(msg.data, msg.agent)}

                                {/* Table */}
                                <div style={{ marginTop: 20, overflow: 'hidden', border: '1px solid #eee', borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                                    <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
                                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: 600 }}>
                                            <thead style={{ position: 'sticky', top: 0, background: '#f9fafb' }}>
                                                <tr>
                                                    {Object.keys(msg.data[0]).map(key => (
                                                        <th key={key} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#555', borderBottom: '1px solid #eee' }}>{key}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {msg.data.slice(0, 10).map((row, i) => (
                                                    <tr key={i} style={{ borderBottom: '1px solid #f5f5f5', background: 'white' }}>
                                                        {Object.values(row).map((val: any, j) => (
                                                            <td key={j} style={{ padding: '10px 14px', color: '#333' }}>
                                                                {val !== null ? String(val) : '-'}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                    {msg.data.length > 10 && (
                                        <div style={{ padding: '8px', textAlign: 'center', fontSize: '0.75rem', color: '#888', background: '#fafafa', borderTop: '1px solid #eee' }}>
                                            Showing first 10 rows of {msg.data.length}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                    </div>
                ))}

                {loading && (
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
                        <div style={{ color: '#888', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span className="spinner"></span> Thinking...
                        </div>
                        <style jsx>{`
              .spinner {
                width: 16px; height: 16px; border: 2px solid #ddd; border-top-color: #007AFF; 
                border-radius: 50%; animation: spin 0.8s linear infinite;
              }
              @keyframes spin { to { transform: rotate(360deg); } }
            `}</style>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Suggested Queries */}
            <div style={{
                position: 'fixed', bottom: 80, left: 0, right: 0,
                zIndex: 10, maxWidth: '900px', margin: '0 auto', pointerEvents: 'none'
            }}>
                <div style={{ padding: '0 20px', display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 10, pointerEvents: 'auto', scrollbarWidth: 'none' }}>
                    {SUGGESTIONS.map((s, i) => (
                        <button key={i} onClick={() => handleSend(s)} disabled={loading} style={{
                            background: 'white', border: '1px solid #e5e5e5', borderRadius: '20px',
                            padding: '8px 16px', fontSize: '0.85rem', color: '#333', cursor: 'pointer',
                            whiteSpace: 'nowrap', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', transition: 'transform 0.1s',
                            opacity: loading ? 0.5 : 1
                        }}
                            onMouseEnter={(e) => e.currentTarget.style.borderColor = '#007AFF'}
                            onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e5e5e5'}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Input Area */}
            <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                background: '#fff', padding: '16px 20px', borderTop: '1px solid #eaeaea',
                display: 'flex', gap: 12, maxWidth: '900px', margin: '0 auto', zIndex: 20
            }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="데이터에 대해 질문해보세요..."
                    disabled={loading}
                    style={{
                        flex: 1, padding: '12px 18px', borderRadius: '24px',
                        border: '1px solid #e1e1e1', fontSize: '0.95rem', outline: 'none',
                        background: '#f9f9f9', transition: 'border-color 0.2s, background 0.2s'
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = '#007AFF'; e.currentTarget.style.background = 'white'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = '#e1e1e1'; e.currentTarget.style.background = '#f9f9f9'; }}
                />
                <button
                    onClick={() => handleSend()}
                    disabled={loading || !input.trim()}
                    style={{
                        width: 46, height: 46, borderRadius: '50%', border: 'none',
                        background: '#007AFF', color: '#fff', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        opacity: loading || !input.trim() ? 0.5 : 1, transition: 'opacity 0.2s'
                    }}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        </div>
    );
}
