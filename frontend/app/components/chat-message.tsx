import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
    const isUser = role === 'user';

    return (
        <div className={`flex w-full gap-4 p-6 ${isUser ? "flex-row-reverse bg-white" : "flex-row bg-gray-50"}`}>
            <div className={`flex h-10 w-10 shrink-0 select-none items-center justify-center rounded-full border shadow-sm ${isUser ? "bg-gray-100" : "bg-blue-600"}`}>
                {isUser ? <User className="h-6 w-6 text-gray-600" /> : <Bot className="h-6 w-6 text-white" />}
            </div>

            <div className={`flex-1 space-y-2 overflow-hidden max-w-4xl`}>
                <div className="prose prose-slate max-w-none break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-4 prose-pre:bg-gray-800 prose-pre:rounded-lg">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    );
}
