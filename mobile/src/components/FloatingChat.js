import React, { useState, useRef, useContext } from 'react';
import {
  View, Text, TouchableOpacity, Modal, TextInput,
  FlatList, StyleSheet, KeyboardAvoidingView, Platform,
  ActivityIndicator, SafeAreaView,
} from 'react-native';
import { colors } from '../theme';
import { SessionContext } from '../context/SessionContext';
import { BASE_URL, API_KEYS } from '../api/client';

const ROLE_NAMES = {
  delegate: 'Délégué',
  pharmacy: 'Pharmacie',
  medecin:  'Médecin',
};

export default function FloatingChat({ role = 'delegate', visitId = 541 }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: '0',
      from: 'bot',
      text: '👋 Bonjour ! Je suis votre assistant IA.\nPosez-moi des questions sur vos prédictions, visites, CA ou coaching.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { id: Date.now().toString(), from: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEYS[role] || API_KEYS.delegate,
        },
        body: JSON.stringify({ message: text, role, visit_id: visitId }),
      });
      const json = await res.json();
      setMessages(prev => [
        ...prev,
        { id: Date.now().toString() + 'b', from: 'bot', text: json.reply || '🤖 Réponse non disponible.' },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { id: Date.now().toString() + 'e', from: 'bot', text: '⚠️ Serveur non disponible. Vérifiez votre connexion.' },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const renderMsg = ({ item }) => (
    <View style={[s.bubble, item.from === 'user' ? s.bubbleUser : s.bubbleBot]}>
      <Text style={[s.bubbleText, item.from === 'user' ? s.bubbleTextUser : s.bubbleTextBot]}>
        {item.text}
      </Text>
    </View>
  );

  return (
    <>
      {/* Floating button */}
      <TouchableOpacity style={s.fab} onPress={() => setOpen(true)} activeOpacity={0.85}>
        <Text style={s.fabIcon}>💬</Text>
      </TouchableOpacity>

      {/* Chat Modal */}
      <Modal visible={open} animationType="slide" transparent={false} onRequestClose={() => setOpen(false)}>
        <SafeAreaView style={s.modal}>
          {/* Header */}
          <View style={s.header}>
            <View>
              <Text style={s.headerTitle}>🤖 Assistant IA</Text>
              <Text style={s.headerSub}>{ROLE_NAMES[role] || role} · Orchestrateur</Text>
            </View>
            <TouchableOpacity onPress={() => setOpen(false)} style={s.closeBtn}>
              <Text style={s.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Messages */}
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={item => item.id}
            renderItem={renderMsg}
            contentContainerStyle={s.msgList}
            onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          />

          {loading && (
            <View style={s.typingRow}>
              <ActivityIndicator size="small" color={colors.teal} />
              <Text style={s.typingText}>  Analyse en cours...</Text>
            </View>
          )}

          {/* Input */}
          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.inputRow}>
              <TextInput
                style={s.input}
                placeholder="Posez votre question..."
                placeholderTextColor={colors.t3}
                value={input}
                onChangeText={setInput}
                onSubmitEditing={send}
                returnKeyType="send"
                multiline={false}
              />
              <TouchableOpacity style={s.sendBtn} onPress={send} disabled={loading || !input.trim()}>
                <Text style={s.sendIcon}>➤</Text>
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </>
  );
}

const s = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: 80,
    right: 16,
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.teal,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 6,
    shadowColor: colors.teal,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    zIndex: 999,
  },
  fabIcon: { fontSize: 22 },
  modal: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.bd,
    backgroundColor: colors.s1,
  },
  headerTitle: { fontSize: 15, fontWeight: '700', color: colors.t1 },
  headerSub:   { fontSize: 11, color: colors.teal, marginTop: 2 },
  closeBtn:  { padding: 8 },
  closeText: { fontSize: 16, color: colors.t2 },
  msgList: { paddingHorizontal: 12, paddingVertical: 16, gap: 10 },
  bubble: {
    maxWidth: '82%',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  bubbleUser: { alignSelf: 'flex-end', backgroundColor: colors.teal },
  bubbleBot:  { alignSelf: 'flex-start', backgroundColor: colors.s2, borderWidth: 1, borderColor: colors.bd },
  bubbleText: { fontSize: 13, lineHeight: 19 },
  bubbleTextUser: { color: colors.bg, fontWeight: '500' },
  bubbleTextBot:  { color: colors.t1 },
  typingRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 8 },
  typingText: { fontSize: 11, color: colors.t3 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: colors.bd,
    backgroundColor: colors.s1,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: colors.s2,
    borderWidth: 1,
    borderColor: colors.bd,
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 13,
    color: colors.t1,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.teal,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendIcon: { fontSize: 16, color: colors.bg },
});
