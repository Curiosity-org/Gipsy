CREATE TABLE IF NOT EXISTS `voices_chats` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_voiceschats_guild ON `voices_chats` (`guild`);

CREATE TABLE IF NOT EXISTS `thanks` (
  `guild` BIGINT NOT NULL,
  `user` BIGINT NOT NULL,
  `author` BIGINT DEFAULT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_thanks_guild ON `thanks` (`guild`);

CREATE TABLE IF NOT EXISTS `contact_channels` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT PRIMARY KEY NOT NULL,
  `author` BIGINT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_contactchannels_guild ON `contact_channels` (`guild`);

CREATE TABLE IF NOT EXISTS `thanks_levels` (
  `guild` BIGINT NOT NULL,
  `role` BIGINT NOT NULL,
  `level` BIGINT DEFAULT 1,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_thankslevels_guild ON `thanks_levels` (`guild`);

CREATE TABLE IF NOT EXISTS `group_roles` (
  `guild` BIGINT NOT NULL,
  `action` SMALLINT NOT NULL DEFAULT 0,
  `target` BIGINT NOT NULL,
  `trigger` SMALLINT NOT NULL,
  `trigger-roles`BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grouproles_guild ON `group_roles` (`guild`);

CREATE TABLE IF NOT EXISTS `giveaways` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `max_entries` INT DEFAULT 0,
  `ends_at` TIMESTAMP DEFAULT NULL,
  `message` BIGINT DEFAULT NULL,
  `running` BOOLEAN DEFAULT 1,
  `users` BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_giveaways_guild ON `giveaways` (`guild`);