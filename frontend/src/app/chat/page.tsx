"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSendMessage, useChatHistory } from "@/lib/hooks";
import { useChatStore } from "@/lib/stores";
import type { ChatMessage } from "@/lib/types";

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const { sessionId, setSessionId } = useChatStore();
  const sendMessage = useSendMessage();
  const { data: history } = useChatHistory(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const allMessages = history || localMessages;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [allMessages]);

  const handleSend = async () => {
    if (!message.trim()) return;
    const userMsg = message;
    setMessage("");

    // Optimistic add
    setLocalMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        session_id: sessionId || 0,
        role: "user",
        content: userMsg,
        tool_calls: [],
        created_at: new Date().toISOString(),
      },
    ]);

    const response = await sendMessage.mutateAsync({
      message: userMsg,
      sessionId: sessionId ?? undefined,
    });

    if (response.session_id && !sessionId) {
      setSessionId(response.session_id);
    }

    setLocalMessages((prev) => [...prev, response]);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-[var(--border)] p-4">
        <h1 className="text-lg font-semibold">Chat with BrainyBuddy</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Add tasks, adjust your plan, or ask questions
        </p>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {allMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <Card
              className={`max-w-[80%] ${
                msg.role === "user"
                  ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                  : ""
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.tool_calls?.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.tool_calls.map((tc, i) => (
                    <Badge key={i} variant="secondary" className="mr-1">
                      {tc.name}
                    </Badge>
                  ))}
                </div>
              )}
            </Card>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-[var(--border)] p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message... (e.g., 'Add a 3-hour lab report due Friday')"
            className="flex-1"
          />
          <Button type="submit" disabled={sendMessage.isPending}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
