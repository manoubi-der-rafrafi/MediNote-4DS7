import mysql, { type Pool, type RowDataPacket } from "mysql2/promise";

let pool: Pool | undefined;
let initPromise: Promise<void> | undefined;

export function getPool() {
  if (!pool) {
    pool = mysql.createPool({
      host: process.env.DB_HOST || "127.0.0.1",
      port: Number(process.env.DB_PORT || 3306),
      user: process.env.DB_USER || "root",
      password: process.env.DB_PASSWORD || "",
      database: process.env.DB_NAME || "vital",
      waitForConnections: true,
      connectionLimit: 10,
      namedPlaceholders: true,
      charset: "utf8mb4"
    });
  }

  return pool;
}

export async function queryRows<T extends RowDataPacket>(
  sql: string,
  params: Record<string, unknown> = {}
) {
  await ensureConversationSchema();
  const [rows] = await getPool().execute<T[]>(sql, params as never);
  return rows;
}

export async function queryOne<T extends RowDataPacket>(
  sql: string,
  params: Record<string, unknown> = {}
) {
  const rows = await queryRows<T>(sql, params);
  return rows[0] ?? null;
}

export async function ensureConversationSchema() {
  if (!initPromise) {
    initPromise = initializeConversationSchema();
  }

  await initPromise;
}

async function initializeConversationSchema() {
  const db = getPool();

  await db.query(`
    CREATE TABLE IF NOT EXISTS users (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      role VARCHAR(50) NOT NULL DEFAULT 'user',
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);

  await db.query(`
    CREATE TABLE IF NOT EXISTS browser_sessions (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      user_id BIGINT UNSIGNED NOT NULL,
      session_token VARCHAR(255) NOT NULL,
      user_agent TEXT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_browser_sessions_token (session_token),
      KEY idx_browser_sessions_user_id (user_id),
      CONSTRAINT fk_front_browser_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);

  await db.query(`
    CREATE TABLE IF NOT EXISTS conversations (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      user_id BIGINT UNSIGNED NOT NULL,
      title VARCHAR(255) NOT NULL DEFAULT 'Nouvelle discussion',
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      KEY idx_conversations_user_id (user_id),
      CONSTRAINT fk_front_conversations_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);

  await db.query(`
    CREATE TABLE IF NOT EXISTS messages (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      conversation_id BIGINT UNSIGNED NOT NULL,
      role VARCHAR(50) NOT NULL,
      text LONGTEXT NOT NULL,
      asset_url TEXT NULL,
      asset_kind VARCHAR(50) NULL,
      display_json JSON NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      KEY idx_messages_conversation_id (conversation_id),
      KEY idx_messages_created_at (created_at),
      CONSTRAINT fk_front_messages_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);

  await ensureOptionalMessageColumns(db);

  await db.query(`
    CREATE TABLE IF NOT EXISTS tasks (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      conversation_id BIGINT UNSIGNED NOT NULL,
      intent VARCHAR(100) NOT NULL,
      action VARCHAR(100) NOT NULL,
      status VARCHAR(50) NOT NULL DEFAULT 'draft',
      infos_json JSON NOT NULL,
      missing_fields_json JSON NOT NULL,
      last_message_id BIGINT UNSIGNED NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      KEY idx_tasks_conversation_intent_action_status (conversation_id, intent, action, status),
      KEY idx_tasks_last_message_id (last_message_id),
      CONSTRAINT fk_front_tasks_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE,
      CONSTRAINT fk_front_tasks_last_message
        FOREIGN KEY (last_message_id) REFERENCES messages(id)
        ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `);
}

async function ensureOptionalMessageColumns(db: Pool) {
  const [assetUrlColumns] = await db.query<RowDataPacket[]>(
    `SELECT COLUMN_NAME
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = 'messages'
       AND COLUMN_NAME IN ('asset_url', 'asset_kind', 'display_json')`
  );

  const existingColumns = new Set(
    assetUrlColumns.map((row) => String(row.COLUMN_NAME).toLowerCase())
  );

  if (!existingColumns.has("asset_url")) {
    await db.query("ALTER TABLE messages ADD COLUMN asset_url TEXT NULL AFTER text");
  }

  if (!existingColumns.has("asset_kind")) {
    await db.query("ALTER TABLE messages ADD COLUMN asset_kind VARCHAR(50) NULL AFTER asset_url");
  }

  if (!existingColumns.has("display_json")) {
    await db.query("ALTER TABLE messages ADD COLUMN display_json JSON NULL AFTER asset_kind");
  }
}
