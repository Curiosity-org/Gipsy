CREATE TABLE IF NOT EXISTS `group_roles` (
  `guild` BIGINT NOT NULL,
  `action` SMALLINT NOT NULL DEFAULT 0,
  `target` BIGINT NOT NULL,
  `trigger` SMALLINT NOT NULL,
  `trigger-roles`BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grouproles_guild ON `group_roles` (`guild`);