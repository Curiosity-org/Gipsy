CREATE TABLE IF NOT EXISTS `voices_chats` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_voiceschats_guild ON `voices_chats` (`guild`);
