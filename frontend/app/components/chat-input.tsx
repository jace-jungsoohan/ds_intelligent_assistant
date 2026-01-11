import React, { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (!input.trim() || disabled) return;
        onSend(input);
        setInput('');
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="fixed bottom-0 left-0 w-full bg-white/80 backdrop-blur-md border-t p-4 pb-8 z-50">
            <div className="mx-auto max-w-3xl relative flex items-center gap-2">
                <div className="relative flex-1">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="궁금한 내용을 입력해주세요..."
                        disabled={disabled}
                        className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-4 pr-12 text-sm shadow-sm transition-all focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={disabled || !input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-blue-600 disabled:hover:text-gray-400 transition-colors"
                    >
                        {disabled ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                    </button>
                </div>
            </div>
        </div>
    );
}
