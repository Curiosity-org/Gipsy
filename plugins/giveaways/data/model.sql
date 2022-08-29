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