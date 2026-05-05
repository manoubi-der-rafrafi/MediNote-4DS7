from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StructuredReport(Base):
    __tablename__ = "structured_reports"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_corrige: Mapped[str] = mapped_column(Text, nullable=False)
    mouvement: Mapped[str] = mapped_column(String(50), nullable=False)
    potentiel: Mapped[str] = mapped_column(String(50), nullable=False)
    conseil: Mapped[str] = mapped_column(String(50), nullable=False)
    emplacement_proximite: Mapped[str] = mapped_column(String(50), nullable=False)
    emplacement_qualite: Mapped[str] = mapped_column(String(50), nullable=False)
    personnel_attitude: Mapped[str] = mapped_column(String(50), nullable=False)
    mise_en_place: Mapped[str] = mapped_column(String(50), nullable=False)
    invitations: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_disponibilite: Mapped[str] = mapped_column(String(50), nullable=False)
    type_pharmacie: Mapped[str] = mapped_column(String(50), nullable=False)
    eligibilite_animation: Mapped[str] = mapped_column(String(50), nullable=False)
    aucun_point_fort: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_image: Mapped[str] = mapped_column(Text, nullable=False)
    description_post: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occasion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occasion_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_mode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    produit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_generation_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audio_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    music_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_occasion: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_publication: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    video_path: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_vdo: Mapped[str] = mapped_column(Text, nullable=False)
    description_post: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occasion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generation_mode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    produit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    produit_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_article: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_occasion: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_publication: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="Nouvelle discussion", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ConversationMessage(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ConversationTask(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    infos_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    missing_fields_json: Mapped[list] = mapped_column(JSON, nullable=False)
    last_message_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
