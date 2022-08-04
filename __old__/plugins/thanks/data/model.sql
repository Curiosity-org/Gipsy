CREATE TABLE IF NOT EXISTS `thanks` (
  `guild` BIGINT NOT NULL,
  `user` BIGINT NOT NULL,
  `author` BIGINT DEFAULT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_thanks_guild ON `thanks` (`guild`);

CREATE TABLE IF NOT EXISTS `thanks_levels` (
  `guild` BIGINT NOT NULL,
  `role` BIGINT NOT NULL,
  `level` BIGINT DEFAULT 1,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_thankslevels_guild ON `thanks_levels` (`guild`);