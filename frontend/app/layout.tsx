import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Willog AI Assistant",
    description: "Advanced Logistics AI",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ko">
            <body style={{ fontFamily: 'system-ui, -apple-system, sans-serif', margin: 0 }}>
                {children}
            </body>
        </html>
    );
}
