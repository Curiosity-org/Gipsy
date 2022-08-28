CREATE TABLE IF NOT EXISTS `groups` (
  `guild` BIGINT NOT NULL,
  `roleID` BIGINT NOT NULL,
  `ownerID` BIGINT NOT NULL,
  `channelID` BIGINT DEFAULT NULL,
  `privacy` BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_groups_guild ON `groups` (`guild`);