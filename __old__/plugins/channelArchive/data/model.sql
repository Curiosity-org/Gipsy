CREATE TABLE IF NOT EXISTS `archive` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_archive_guild ON `archive` (`guild`);