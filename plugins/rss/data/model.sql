CREATE TABLE IF NOT EXISTS `rss_flows` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `structure` VARCHAR(1000) NOT NULL,
  `type` VARCHAR(5) NOT NULL,
  `link` TEXT NOT NULL,
  `date` DATETIME,
  `roles` BLOB,
  `use_embed` BOOLEAN DEFAULT 0,
  `embed_structure` BLOB,
  `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rssflows_guild ON `rss_flows` (`guild`);