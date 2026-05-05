"use client";

import Image from "next/image";
import {
  Bot,
  Clock3,
  LoaderCircle,
  MessageSquareText,
  Mic,
  PanelLeftClose,
  Plus,
  RefreshCw,
  Send,
  Square,
  Volume2,
  VolumeX,
  Trash2,
  UserRound,
  X
} from "lucide-react";
import type { CSSProperties, ReactNode } from "react";
import { FormEvent, useEffect, useRef, useState } from "react";
import type { DisplayPayload } from "@/lib/flask";

type Conversation = {
  id: number;
  title: string;
  message_count?: number;
  created_at?: string;
  updated_at?: string;
};

type Message = {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  text: string;
  asset_url?: string | null;
  asset_kind?: string | null;
  display?: DisplayPayload | null;
  created_at?: string;
};

type SessionPayload = {
  user: {
    id: number;
    role: string;
  };
};

type OrchestratorResult = {
  status?: string;
  message?: string;
};

type AudioResponse = {
  available?: boolean;
  mime_type?: string;
  encoding?: string;
  content?: string;
};

type VoicePanelState = "idle" | "recording" | "processing" | "playing";

const VOICE_BAR_COUNT = 7;
const IDLE_VOICE_LEVELS = [0.26, 0.4, 0.6, 0.78, 0.58, 0.38, 0.26];

export default function HomePage() {
  const [session, setSession] = useState<SessionPayload["user"] | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [recording, setRecording] = useState(false);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bootError, setBootError] = useState<string | null>(null);
  const [voicePanelState, setVoicePanelState] = useState<VoicePanelState>("idle");
  const [voiceModeOpen, setVoiceModeOpen] = useState(false);
  const [voiceLevels, setVoiceLevels] = useState<number[]>(IDLE_VOICE_LEVELS);
  const endRef = useRef<HTMLDivElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioPlaybackUrlRef = useRef<string | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const discardNextRecordingRef = useRef(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const analyserDataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    void bootstrap();
    // Initial bootstrap intentionally runs once for the browser session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    return () => {
      cleanupVoiceRecorder();
      releaseAudioPlayback();
    };
    // Cleanup only needs the recorder refs captured for this browser session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      void loadMessages(activeConversationId);
    }
  }, [activeConversationId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function bootstrap() {
    setLoading(true);
    setBootError(null);
    try {
      const sessionResponse = await fetch("/api/session", { cache: "no-store" });
      if (!sessionResponse.ok) {
        const payload = (await sessionResponse.json().catch(() => ({}))) as { error?: string };
        throw new Error(payload.error || "Session unavailable");
      }
      const sessionPayload = (await sessionResponse.json()) as SessionPayload;
      setSession(sessionPayload.user);

      const loadedConversations = await loadConversations();
      if (loadedConversations.length > 0) {
        setActiveConversationId(loadedConversations[0].id);
      } else {
        const created = await createConversation();
        setActiveConversationId(created.id);
      }
    } catch (error) {
      setBootError(error instanceof Error ? error.message : "Erreur de chargement.");
    } finally {
      setLoading(false);
    }
  }

  async function loadConversations() {
    const response = await fetch("/api/conversations", { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Conversations unavailable");
    }
    const payload = (await response.json()) as { conversations: Conversation[] };
    setConversations(payload.conversations);
    return payload.conversations;
  }

  async function createConversation() {
    const response = await fetch("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!response.ok) {
      throw new Error("Conversation creation failed");
    }
    const payload = (await response.json()) as { conversation: Conversation };
    setConversations((current) => {
      const withoutExisting = current.filter((item) => item.id !== payload.conversation.id);
      return [payload.conversation, ...withoutExisting];
    });
    setMessages([]);
    return payload.conversation;
  }

  async function deleteConversation(id: number) {
    const response = await fetch(`/api/conversations/${id}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      return;
    }

    const next = conversations.filter((conversation) => conversation.id !== id);
    setConversations(next);
    setMessages([]);

    if (next.length > 0) {
      setActiveConversationId(next[0].id);
    } else {
      const created = await createConversation();
      setActiveConversationId(created.id);
    }
  }

  async function loadMessages(conversationId: number) {
    const response = await fetch(`/api/conversations/${conversationId}/messages`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { messages: Message[] };
    setMessages(payload.messages);
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !activeConversationId || sending || recording) {
      return;
    }

    setSending(true);
    setComposerError(null);
    setDraft("");

    try {
      const response = await fetch(`/api/conversations/${activeConversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (!response.ok) {
        throw new Error("Send failed");
      }
      const payload = (await response.json()) as {
        messages: Message[];
        result: OrchestratorResult;
      };
      setMessages((current) => [...current, ...payload.messages]);
      void loadConversations();
    } finally {
      setSending(false);
    }
  }

  async function toggleVoiceRecording() {
    if (recording) {
      stopVoiceRecording();
      return;
    }

    if (!activeConversationId || sending) {
      return;
    }

    if (voicePanelState === "playing") {
      stopAudioPlayback();
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setComposerError("L'enregistrement vocal n'est pas disponible dans ce navigateur.");
      return;
    }

    setComposerError(null);
    setVoiceModeOpen(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getPreferredAudioMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      audioChunksRef.current = [];
      audioStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      startVoiceVisualizer(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const chunks = audioChunksRef.current;
        const type = recorder.mimeType || mimeType || "audio/webm";
        const audioBlob = new Blob(chunks, { type });
        const shouldDiscard = discardNextRecordingRef.current;
        discardNextRecordingRef.current = false;
        cleanupVoiceRecorder();
        setRecording(false);
        if (shouldDiscard) {
          setVoicePanelState("idle");
          return;
        }
        setVoicePanelState("processing");
        void sendVoiceMessage(audioBlob, type);
      };

      recorder.start();
      setRecording(true);
      setVoicePanelState("recording");
    } catch (error) {
      cleanupVoiceRecorder();
      setRecording(false);
      setVoicePanelState("idle");
      setComposerError(
        error instanceof Error && error.name === "NotAllowedError"
          ? "Autorisation du micro refusee."
          : "Impossible de demarrer l'enregistrement vocal."
      );
    }
  }

  function stopVoiceRecording() {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      return;
    }

    cleanupVoiceRecorder();
    setRecording(false);
    setVoicePanelState("idle");
  }

  async function sendVoiceMessage(audioBlob: Blob, mimeType: string) {
    if (!activeConversationId || audioBlob.size === 0) {
      setComposerError("Aucun audio n'a ete enregistre.");
      return;
    }

    setSending(true);
    setComposerError(null);

    try {
      const extension = mimeType.includes("ogg") ? "ogg" : "webm";
      const audioFile = new File([audioBlob], `voice.${extension}`, { type: mimeType });
      const formData = new FormData();
      formData.append("voice", audioFile);

      const response = await fetch(`/api/conversations/${activeConversationId}/voice`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { error?: string };
        throw new Error(payload.error || "Envoi vocal echoue");
      }

      const payload = (await response.json()) as {
        messages: Message[];
        result: OrchestratorResult;
        transcription: string;
        audio_response?: AudioResponse | null;
      };
      setMessages((current) => [...current, ...payload.messages]);
      const audioStarted = playAudioResponse(payload.audio_response);
      if (!audioStarted) {
        setVoicePanelState("idle");
      }
      void loadConversations();
    } catch (error) {
      setVoicePanelState("idle");
      setComposerError(error instanceof Error ? error.message : "Envoi vocal echoue");
    } finally {
      setSending(false);
    }
  }

  function cleanupVoiceRecorder() {
    stopVoiceVisualizer();
    audioStreamRef.current?.getTracks().forEach((track) => track.stop());
    audioStreamRef.current = null;
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  }

  function releaseAudioPlayback() {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.onended = null;
      audioElementRef.current.onerror = null;
      audioElementRef.current = null;
    }

    if (audioPlaybackUrlRef.current) {
      URL.revokeObjectURL(audioPlaybackUrlRef.current);
      audioPlaybackUrlRef.current = null;
    }
  }

  function stopAudioPlayback() {
    releaseAudioPlayback();
    setVoiceLevels(IDLE_VOICE_LEVELS);
    setVoicePanelState("idle");
  }

  function closeVoiceMode() {
    if (recording) {
      discardNextRecordingRef.current = true;
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.stop();
      } else {
        cleanupVoiceRecorder();
        setRecording(false);
      }
    }

    releaseAudioPlayback();
    setVoicePanelState("idle");
    setVoiceModeOpen(false);
  }

  function playAudioResponse(audioResponse?: AudioResponse | null) {
    if (
      !audioResponse?.available ||
      audioResponse.encoding !== "base64" ||
      !audioResponse.content
    ) {
      return false;
    }

    try {
      releaseAudioPlayback();
      const byteCharacters = atob(audioResponse.content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let index = 0; index < byteCharacters.length; index += 1) {
        byteNumbers[index] = byteCharacters.charCodeAt(index);
      }

      const audioBlob = new Blob([new Uint8Array(byteNumbers)], {
        type: audioResponse.mime_type || "audio/wav"
      });
      const audioUrl = URL.createObjectURL(audioBlob);
      audioPlaybackUrlRef.current = audioUrl;

      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;
      setVoicePanelState("playing");
      audio.onended = stopAudioPlayback;
      audio.onerror = stopAudioPlayback;
      void audio.play().catch(() => {
        stopAudioPlayback();
      });
      return true;
    } catch {
      stopAudioPlayback();
      return false;
    }
  }

  function startVoiceVisualizer(stream: MediaStream) {
    stopVoiceVisualizer();

    if (typeof window === "undefined") {
      return;
    }

    const AudioContextCtor =
      window.AudioContext ||
      (window as Window & typeof globalThis & { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!AudioContextCtor) {
      setVoiceLevels(IDLE_VOICE_LEVELS);
      return;
    }

    try {
      const audioContext = new AudioContextCtor();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.82;

      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      const data = new Uint8Array(analyser.frequencyBinCount);
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      analyserDataRef.current = data;

      const tick = () => {
        const currentAnalyser = analyserRef.current;
        const currentData = analyserDataRef.current;
        if (!currentAnalyser || !currentData) {
          return;
        }

        currentAnalyser.getByteFrequencyData(currentData);
        setVoiceLevels(buildVoiceLevels(currentData));
        animationFrameRef.current = window.requestAnimationFrame(tick);
      };

      tick();
    } catch {
      setVoiceLevels(IDLE_VOICE_LEVELS);
    }
  }

  function stopVoiceVisualizer() {
    if (typeof window !== "undefined" && animationFrameRef.current !== null) {
      window.cancelAnimationFrame(animationFrameRef.current);
    }

    animationFrameRef.current = null;
    analyserDataRef.current = null;
    analyserRef.current = null;

    if (audioContextRef.current) {
      void audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    setVoiceLevels(IDLE_VOICE_LEVELS);
  }

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId
  );

  const hasEmptyConversation = conversations.some((conversation) => (conversation.message_count || 0) === 0);
  const showVoicePanel = voicePanelState !== "idle" && !voiceModeOpen;

  return (
    <main className="shell">
      <aside className={`sidebar ${sidebarOpen ? "is-open" : "is-closed"}`}>
        <div className="brand">
          <div className="brand-mark">
            <Image src="/logo.png" alt="Vital" width={72} height={72} priority />
          </div>
          <div>
            <h1>Vital Chat</h1>
            <p>Utilisateur navigateur #{session?.id ?? "..."}</p>
          </div>
        </div>

        <div className="sidebar-actions">
          <button
            className="primary-button"
            type="button"
            disabled={hasEmptyConversation}
            onClick={async () => {
              const created = await createConversation();
              setActiveConversationId(created.id);
            }}
            title="Nouvelle discussion"
          >
            <Plus size={18} />
            <span>Nouvelle discussion</span>
          </button>
          <button
            className="icon-button"
            type="button"
            onClick={() => void loadConversations()}
            title="Actualiser"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        <nav className="conversation-list">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={`conversation-item ${
                conversation.id === activeConversationId ? "is-active" : ""
              }`}
              onClick={() => setActiveConversationId(conversation.id)}
            >
              <MessageSquareText size={18} />
              <span>{conversation.title}</span>
              <small>{conversation.message_count || 0}</small>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <button
            type="button"
            className="icon-button"
            onClick={() => setSidebarOpen((value) => !value)}
            title="Afficher ou masquer les discussions"
          >
            <PanelLeftClose size={19} />
          </button>
          <div className="topbar-title">
            <span>Discussion active</span>
            <strong>{activeConversation?.title ?? "Chargement..."}</strong>
          </div>
          {activeConversationId ? (
            <button
              type="button"
              className="danger-button"
              title="Supprimer la discussion"
              onClick={() => void deleteConversation(activeConversationId)}
            >
              <Trash2 size={18} />
            </button>
          ) : null}
        </header>

        <div className={`main-grid ${voiceModeOpen ? "is-voice-mode" : ""}`}>
          {voiceModeOpen ? (
            <section className={`voice-mode is-${voicePanelState}`}>
              <div className="voice-mode-top">
                <div>
                  <span>Mode vocal</span>
                  <strong>{activeConversation?.title ?? "Discussion active"}</strong>
                </div>
                <button
                  type="button"
                  className="icon-button"
                  onClick={closeVoiceMode}
                  title="Revenir a la discussion ecrite"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="voice-mode-stage">
                <VoiceWaveform state={voicePanelState} levels={voiceLevels} />
                <h2>{getVoicePanelTitle(voicePanelState)}</h2>
                <p>{getVoicePanelText(voicePanelState)}</p>
              </div>

              <div className="voice-mode-controls">
                <button
                  className={`voice-control-button ${recording ? "is-danger" : ""}`}
                  type="button"
                  disabled={voicePanelState === "processing" || sending}
                  onClick={() => void toggleVoiceRecording()}
                  title={recording ? "Envoyer le vocal" : "Parler"}
                >
                  {recording ? <Square size={22} /> : <Mic size={22} />}
                </button>
                <button
                  className="voice-control-secondary"
                  type="button"
                  disabled={voicePanelState !== "playing"}
                  onClick={stopAudioPlayback}
                  title="Arreter la reponse vocale"
                >
                  <VolumeX size={20} />
                  <span>Arreter</span>
                </button>
              </div>
            </section>
          ) : (
          <section className="chat-panel">
            {showVoicePanel ? (
              <div className={`voice-session-panel is-${voicePanelState}`}>
                <div className="voice-session-main">
                  <div className="voice-session-icon">
                    {voicePanelState === "playing" ? <Volume2 size={22} /> : <Mic size={22} />}
                  </div>
                  <div>
                    <strong>{getVoicePanelTitle(voicePanelState)}</strong>
                    <span>{getVoicePanelText(voicePanelState)}</span>
                  </div>
                </div>
                <button
                  className="voice-stop-button"
                  type="button"
                  onClick={voicePanelState === "recording" ? stopVoiceRecording : stopAudioPlayback}
                  disabled={voicePanelState === "processing"}
                  title={voicePanelState === "playing" ? "Arreter la reponse vocale" : "Arreter l'enregistrement"}
                >
                  {voicePanelState === "playing" ? <VolumeX size={18} /> : <Square size={18} />}
                  <span>{voicePanelState === "playing" ? "Arreter" : "Stop"}</span>
                </button>
              </div>
            ) : null}
            <div className="messages">
              {loading ? (
                <div className="empty-state">Chargement de la session...</div>
              ) : bootError ? (
                <div className="empty-state">
                  <Bot size={30} />
                  <span>{bootError}</span>
                  <button className="primary-button" type="button" onClick={() => void bootstrap()}>
                    <RefreshCw size={18} />
                    <span>Reessayer</span>
                  </button>
                </div>
              ) : messages.length === 0 ? (
                <div className="empty-state">
                  <Bot size={30} />
                  <span>Commencez une demande.</span>
                </div>
              ) : (
                messages.map((message) => (
                  <article key={message.id} className={`message ${message.role}`}>
                    <div className="message-avatar">
                      {message.role === "user" ? <UserRound size={18} /> : <Bot size={18} />}
                    </div>
                    <div className="message-body">
                      <div className="message-text">
                        <MessageContent text={message.text} display={message.display} />
                      </div>
                      {message.asset_kind === "image" && message.asset_url ? (
                        <div className="message-asset-card">
                          <img src={message.asset_url} alt="Image generee" className="message-inline-image" />
                          <a href={message.asset_url} target="_blank" rel="noreferrer" className="message-asset-link">
                            Ouvrir l&apos;image
                          </a>
                        </div>
                      ) : null}
                      <time>
                        <Clock3 size={13} />
                        {formatDate(message.created_at)}
                      </time>
                    </div>
                  </article>
                ))
              )}
              {sending ? (
                <article className="message assistant is-loading">
                  <div className="message-avatar">
                    <Bot size={18} />
                  </div>
                  <div className="message-body loading-bubble">
                    <div className="loading-row">
                      <LoaderCircle size={16} className="spin" />
                      <span>Traitement en cours...</span>
                    </div>
                  </div>
                </article>
              ) : null}
              <div ref={endRef} />
            </div>

            <form className="composer" onSubmit={sendMessage}>
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ecrire une demande..."
                rows={2}
                disabled={recording}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
              />
              <button
                className={`voice-button ${recording ? "is-recording" : ""}`}
                type="button"
                disabled={sending && !recording}
                aria-pressed={recording}
                onClick={() => void toggleVoiceRecording()}
                title={recording ? "Arreter l'enregistrement" : "Enregistrer un message vocal"}
              >
                {recording ? <Square size={18} /> : <Mic size={18} />}
              </button>
              <button className="send-button" type="submit" disabled={sending || recording || !draft.trim()}>
                {sending ? <LoaderCircle size={18} className="spin" /> : <Send size={18} />}
                <span>{sending ? "Attente" : "Envoyer"}</span>
              </button>
              {composerError ? <p className="composer-error">{composerError}</p> : null}
            </form>
          </section>
          )}
        </div>
      </section>
    </main>
  );
}

function formatDate(value?: string) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function getVoicePanelTitle(state: VoicePanelState) {
  if (state === "idle") {
    return "Pret a parler";
  }

  if (state === "recording") {
    return "Discussion vocale active";
  }

  if (state === "processing") {
    return "Analyse du message vocal";
  }

  if (state === "playing") {
    return "Reponse vocale en lecture";
  }

  return "";
}

function getVoicePanelText(state: VoicePanelState) {
  if (state === "idle") {
    return "Appuyez sur le micro pour commencer un message vocal.";
  }

  if (state === "recording") {
    return "Le micro est ouvert. Arretez pour envoyer le message.";
  }

  if (state === "processing") {
    return "Transcription, reponse et sauvegarde des messages en cours.";
  }

  if (state === "playing") {
    return "La reponse est aussi affichee dans la discussion.";
  }

  return "";
}

function getPreferredAudioMimeType() {
  const supportedTypes = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg"
  ];

  return supportedTypes.find((type) => MediaRecorder.isTypeSupported(type)) ?? "";
}

function buildVoiceLevels(data: Uint8Array<ArrayBuffer>) {
  if (!data.length) {
    return IDLE_VOICE_LEVELS;
  }

  const bucketSize = Math.max(1, Math.floor(data.length / VOICE_BAR_COUNT));

  return Array.from({ length: VOICE_BAR_COUNT }, (_, index) => {
    const start = index * bucketSize;
    const end =
      index === VOICE_BAR_COUNT - 1
        ? data.length
        : Math.min(data.length, start + bucketSize);
    let sum = 0;
    let count = 0;

    for (let cursor = start; cursor < end; cursor += 1) {
      sum += data[cursor];
      count += 1;
    }

    const average = count ? sum / count : 0;
    const normalized = average / 255;
    return Math.min(1, Math.max(0.18, normalized * 1.55));
  });
}

function VoiceWaveform({
  state,
  levels
}: {
  state: VoicePanelState;
  levels: number[];
}) {
  return (
    <div className={`voice-wave is-${state}`} aria-hidden="true">
      {levels.map((level, index) => (
        <span
          key={index}
          className={state === "recording" ? "is-live" : ""}
          style={{ "--voice-level": `${level}` } as CSSProperties}
        />
      ))}
    </div>
  );
}

type MarkdownBlock =
  | { type: "heading"; level: 2 | 3; content: string }
  | { type: "paragraph"; content: string }
  | { type: "list"; items: string[] }
  | { type: "table"; headers: string[]; rows: string[][] };

function MessageContent({
  text,
  display
}: {
  text: string;
  display?: DisplayPayload | null;
}) {
  const blocks = parseMarkdown(text);

  return (
    <div className="message-markdown">
      {blocks.map((block, index) => renderMarkdownBlock(block, index))}
      {display?.type === "table" ? <StructuredTable display={display} /> : null}
    </div>
  );
}

function StructuredTable({ display }: { display: DisplayPayload }) {
  const columns = Array.isArray(display.columns) ? display.columns : [];
  const rows = Array.isArray(display.rows) ? display.rows : [];
  if (!columns.length || !rows.length) {
    return null;
  }

  return (
    <div className="message-table-card">
      <div className="message-table-scroll">
        <table className="message-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`${rowIndex}-${columns.map((column) => row[column.key]).join("|")}`}>
                {columns.map((column) => (
                  <td key={column.key}>{row[column.key] || ""}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {display.truncated ? (
        <p className="message-table-note">Seule une partie des resultats est affichee.</p>
      ) : null}
    </div>
  );
}

function renderMarkdownBlock(block: MarkdownBlock, index: number) {
  if (block.type === "heading") {
    if (block.level === 2) {
      return <h2 key={index}>{renderInlineMarkdown(block.content)}</h2>;
    }

    return <h3 key={index}>{renderInlineMarkdown(block.content)}</h3>;
  }

  if (block.type === "list") {
    return (
      <ul key={index}>
        {block.items.map((item, itemIndex) => (
          <li key={`${index}-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ul>
    );
  }

  if (block.type === "table") {
    return (
      <div key={index} className="message-table-scroll">
        <table className="message-table is-inline-markdown">
          <thead>
            <tr>
              {block.headers.map((header, headerIndex) => (
                <th key={`${index}-h-${headerIndex}`}>{renderInlineMarkdown(header)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, rowIndex) => (
              <tr key={`${index}-r-${rowIndex}`}>
                {row.map((cell, cellIndex) => (
                  <td key={`${index}-c-${rowIndex}-${cellIndex}`}>
                    {renderInlineMarkdown(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return <p key={index}>{renderInlineMarkdown(block.content)}</p>;
}

function renderInlineMarkdown(content: string): ReactNode[] {
  const parts = content.split(/(\*\*.*?\*\*)/g);

  return parts
    .filter(Boolean)
    .map((part, index) => {
      const boldMatch = part.match(/^\*\*(.*)\*\*$/);
      if (boldMatch) {
        return <strong key={index}>{boldMatch[1]}</strong>;
      }

      return <span key={index}>{part}</span>;
    });
}

function parseMarkdown(text: string): MarkdownBlock[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const headingMatch = line.match(/^(#{2,3})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length as 2 | 3,
        content: headingMatch[2].trim()
      });
      index += 1;
      continue;
    }

    if (
      line.includes("|") &&
      index + 1 < lines.length &&
      /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[index + 1])
    ) {
      const headers = splitMarkdownTableRow(lines[index]);
      const rows: string[][] = [];
      index += 2;

      while (index < lines.length) {
        const rowLine = lines[index].trim();
        if (!rowLine || !rowLine.includes("|")) {
          break;
        }
        rows.push(splitMarkdownTableRow(rowLine));
        index += 1;
      }

      blocks.push({ type: "table", headers, rows });
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length) {
        const itemLine = lines[index].trim();
        const match = itemLine.match(/^[-*]\s+(.*)$/);
        if (!match) {
          break;
        }
        items.push(match[1].trim());
        index += 1;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length) {
      const paragraphLine = lines[index].trim();
      if (!paragraphLine) {
        break;
      }
      if (/^(#{2,3})\s+/.test(paragraphLine) || /^[-*]\s+/.test(paragraphLine)) {
        break;
      }
      if (
        paragraphLine.includes("|") &&
        index + 1 < lines.length &&
        /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[index + 1])
      ) {
        break;
      }
      paragraphLines.push(paragraphLine);
      index += 1;
    }
    blocks.push({ type: "paragraph", content: paragraphLines.join(" ") });
  }

  return blocks;
}

function splitMarkdownTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}
