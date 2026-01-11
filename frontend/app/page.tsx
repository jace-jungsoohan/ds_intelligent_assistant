"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    data?: any[];
    sql?: string;
    agent?: string;
}

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

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = { role: 'user', content: input };
        setInput('');
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

        // Simple heuristic for chart type
        // If 'date' in columns, use Line Chart
        const dateCol = columns.find(c => c.includes('date') || c.includes('day') || c.includes('time'));
        const numCol = columns.find(c => typeof data[0][c] === 'number');

        if (dateCol && numCol) {
            return (
                <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                    <h4>Time Series Analysis</h4>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={dateCol} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey={numCol} stroke="#8884d8" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        // If categorical and numeric, use Bar Chart
        const catCol = columns.find(c => typeof data[0][c] === 'string');
        if (catCol && numCol) {
            return (
                <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                    <h4>Category Analysis</h4>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={catCol} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey={numCol} fill="#82ca9d" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        return null;
    };

    return (
        <div style={{ maxWidth: '900px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui' }}>
            <header style={{
                position: 'sticky', top: 0, background: 'rgba(255,255,255,0.9)',
                padding: '15px 0', borderBottom: '1px solid #eee', zIndex: 10, marginBottom: 20
            }}>
                <h1 style={{ margin: 0, fontSize: '1.2rem', color: '#111' }}>Willog AI Assistant</h1>
            </header>

            <div style={{ paddingBottom: '80px' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{
                        marginBottom: '20px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}>
                        <div style={{
                            padding: '12px 18px',
                            borderRadius: '16px',
                            borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
                            borderBottomLeftRadius: msg.role === 'user' ? '16px' : '4px',
                            background: msg.role === 'user' ? '#007AFF' : '#F2F2F7',
                            color: msg.role === 'user' ? '#fff' : '#000',
                            maxWidth: '85%',
                            lineHeight: '1.5',
                            whiteSpace: 'pre-wrap',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                            {msg.content}
                        </div>

                        {/* SQL Debug Block */}
                        {msg.sql && (
                            <details style={{ marginTop: 8, maxWidth: '85%', width: '100%' }}>
                                <summary style={{ cursor: 'pointer', fontSize: '0.8rem', color: '#666' }}>View SQL Query</summary>
                                <pre style={{
                                    background: '#f5f5f5', padding: 10, borderRadius: 8,
                                    fontSize: '0.75rem', overflowX: 'auto', border: '1px solid #ddd'
                                }}>
                                    {msg.sql}
                                </pre>
                            </details>
                        )}

                        {/* Data Visualization & Table */}
                        {msg.data && (
                            <div style={{ width: '100%', marginTop: 10, maxWidth: '100%' }}>
                                {/* Charts */}
                                {renderVisualization(msg.data, msg.agent)}

                                {/* Table */}
                                <div style={{ marginTop: 20, overflowX: 'auto', border: '1px solid #eee', borderRadius: 8 }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ background: '#f9f9f9', textAlign: 'left' }}>
                                                {Object.keys(msg.data[0]).map(key => (
                                                    <th key={key} style={{ padding: '8px 12px', borderBottom: '1px solid #ddd' }}>{key}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {msg.data.slice(0, 10).map((row, i) => (
                                                <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                                                    {Object.values(row).map((val: any, j) => (
                                                        <td key={j} style={{ padding: '8px 12px' }}>
                                                            {val !== null ? String(val) : '-'}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                    {msg.data.length > 10 && (
                                        <div style={{ padding: 10, textAlign: 'center', fontSize: '0.8rem', color: '#666' }}>
                                            Showing first 10 rows of {msg.data.length}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                    </div>
                ))}
                {loading && <div style={{ textAlign: 'center', color: '#888', padding: 20 }}>Generating response...</div>}
                <div ref={bottomRef} />
            </div>

            <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                background: '#fff', padding: '15px', borderTop: '1px solid #eee',
                display: 'flex', gap: 10, maxWidth: '900px', margin: '0 auto', zIndex: 20
            }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask about Willog logistics data..."
                    disabled={loading}
                    style={{
                        flex: 1, padding: '12px 16px', borderRadius: '24px',
                        border: '1px solid #ddd', fontSize: '1rem', outline: 'none'
                    }}
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    style={{
                        padding: '12px 24px', borderRadius: '24px', border: 'none',
                        background: '#007AFF', color: '#fff', fontWeight: 'bold', cursor: 'pointer',
                        opacity: loading ? 0.6 : 1
                    }}
                >
                    Send
                </button>
            </div>
        </div>
    );
}
