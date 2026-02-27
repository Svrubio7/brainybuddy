import React, { useCallback, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import type { ChatMessage } from "../../lib/types";
import { api } from "../../lib/api";

// ── Message Bubble ───────────────────────────────────────────────

interface BubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: BubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <View style={styles.systemBubble}>
        <Text style={styles.systemText}>{message.content}</Text>
      </View>
    );
  }

  return (
    <View
      style={[
        styles.bubbleRow,
        isUser ? styles.bubbleRowUser : styles.bubbleRowAssistant,
      ]}
    >
      {!isUser && (
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>BB</Text>
        </View>
      )}
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <Text
          style={[
            styles.bubbleText,
            isUser ? styles.userBubbleText : styles.assistantBubbleText,
          ]}
        >
          {message.content}
        </Text>

        {/* Tool call indicators */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <View style={styles.toolCallsContainer}>
            {message.tool_calls.map((tc, idx) => (
              <View key={idx} style={styles.toolCallChip}>
                <Ionicons name="build-outline" size={12} color="#6B7280" />
                <Text style={styles.toolCallText}>{tc.name}</Text>
              </View>
            ))}
          </View>
        )}

        <Text style={styles.timestamp}>
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </Text>
      </View>
    </View>
  );
}

// ── Chat Screen ──────────────────────────────────────────────────

export default function ChatScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const flatListRef = useRef<FlatList<ChatMessage>>(null);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    // Optimistic user message
    const optimistic: ChatMessage = {
      id: -(Date.now()),
      session_id: sessionId || 0,
      role: "user",
      content: text,
      tool_calls: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimistic]);
    setInput("");
    setSending(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    try {
      const response = await api.sendMessage(text, sessionId);

      // Set session from first response
      if (!sessionId && response.session_id) {
        setSessionId(response.session_id);
      }

      // Replace optimistic message with server-confirmed and add assistant reply
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.id !== optimistic.id);
        // The server response is the assistant message; re-add the user message properly
        const userMsg: ChatMessage = {
          ...optimistic,
          id: response.id - 1, // approximate
          session_id: response.session_id,
        };
        return [...withoutOptimistic, userMsg, response];
      });
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: -(Date.now() + 1),
        session_id: sessionId || 0,
        role: "system",
        content:
          "Failed to send message. Check your connection and try again.",
        tool_calls: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  }, [input, sending, sessionId]);

  const loadHistory = useCallback(async () => {
    if (!sessionId) return;
    try {
      const history = await api.getChatHistory(sessionId);
      setMessages(history);
    } catch {
      // Offline
    }
  }, [sessionId]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.messagesList}
        onContentSizeChange={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
        ListEmptyComponent={
          <View style={styles.emptyChat}>
            <View style={styles.emptyAvatar}>
              <Text style={styles.emptyAvatarText}>BB</Text>
            </View>
            <Text style={styles.emptyChatTitle}>BrainyBuddy</Text>
            <Text style={styles.emptyChatSubtitle}>
              Hi there! I can help you manage your study schedule, create tasks,
              or answer questions about your courses. What would you like to do?
            </Text>
            <View style={styles.suggestionsContainer}>
              {[
                "What should I study next?",
                "Create a task for my exam",
                "Reschedule my plan",
                "How am I doing this week?",
              ].map((suggestion) => (
                <Pressable
                  key={suggestion}
                  style={styles.suggestionChip}
                  onPress={() => {
                    setInput(suggestion);
                  }}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        }
      />

      {/* Input Bar */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.textInput}
          placeholder="Ask BrainyBuddy..."
          placeholderTextColor="#9CA3AF"
          value={input}
          onChangeText={setInput}
          onSubmitEditing={sendMessage}
          returnKeyType="send"
          multiline
          maxLength={2000}
          editable={!sending}
        />
        <Pressable
          style={[
            styles.sendButton,
            (!input.trim() || sending) && styles.sendButtonDisabled,
          ]}
          onPress={sendMessage}
          disabled={!input.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Ionicons name="send" size={20} color="#FFFFFF" />
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

// ── Styles ───────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
    flexGrow: 1,
  },

  // Bubbles
  bubbleRow: {
    flexDirection: "row",
    marginBottom: 12,
    maxWidth: "85%",
  },
  bubbleRowUser: {
    alignSelf: "flex-end",
  },
  bubbleRowAssistant: {
    alignSelf: "flex-start",
  },
  avatarCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#4F46E5",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 8,
    marginTop: 2,
  },
  avatarText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  bubble: {
    borderRadius: 16,
    padding: 12,
    maxWidth: "100%",
  },
  userBubble: {
    backgroundColor: "#4F46E5",
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: "#FFFFFF",
    borderBottomLeftRadius: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 21,
  },
  userBubbleText: {
    color: "#FFFFFF",
  },
  assistantBubbleText: {
    color: "#111827",
  },
  timestamp: {
    fontSize: 10,
    color: "#9CA3AF",
    marginTop: 4,
    alignSelf: "flex-end",
  },
  systemBubble: {
    alignSelf: "center",
    backgroundColor: "#FEF3C7",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginBottom: 12,
  },
  systemText: {
    fontSize: 13,
    color: "#92400E",
  },

  // Tool calls
  toolCallsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 4,
    marginTop: 8,
  },
  toolCallChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#F3F4F6",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  toolCallText: {
    fontSize: 11,
    color: "#6B7280",
  },

  // Empty state
  emptyChat: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
    paddingTop: 60,
  },
  emptyAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#4F46E5",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
  },
  emptyAvatarText: {
    fontSize: 24,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  emptyChatTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
  },
  emptyChatSubtitle: {
    fontSize: 15,
    color: "#6B7280",
    textAlign: "center",
    marginTop: 8,
    lineHeight: 22,
  },
  suggestionsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 8,
    marginTop: 24,
  },
  suggestionChip: {
    backgroundColor: "#EEF2FF",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#C7D2FE",
  },
  suggestionText: {
    fontSize: 13,
    color: "#4F46E5",
    fontWeight: "500",
  },

  // Input bar
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 12,
    paddingBottom: Platform.OS === "ios" ? 28 : 12,
    backgroundColor: "#FFFFFF",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#E5E7EB",
    gap: 8,
  },
  textInput: {
    flex: 1,
    backgroundColor: "#F3F4F6",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
    color: "#111827",
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#4F46E5",
    justifyContent: "center",
    alignItems: "center",
  },
  sendButtonDisabled: {
    backgroundColor: "#C7D2FE",
  },
});
