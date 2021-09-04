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

CREATE TABLE IF NOT EXISTS `xp` (
  `guild` BIGINT,
  `userid` BIGINT NOT NULL,
  `xp` INT DEFAULT 0,
  `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (guild, userid)
);
CREATE INDEX IF NOT EXISTS idx_xp_guild ON `xp` (`guild`);

CREATE TABLE IF NOT EXISTS `roles_levels` (
  `guild` BIGINT NOT NULL,
  `role` BIGINT NOT NULL,
  `level` INT NOT NULL,
  `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (guild, role)
);
CREATE INDEX IF NOT EXISTS idx_rolesrewards_guild ON `roles_levels` (`guild`);

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

CREATE TABLE IF NOT EXISTS `groups` (
  `guild` BIGINT NOT NULL,
  `roleID` BIGINT NOT NULL,
  `ownerID` BIGINT NOT NULL,
  `channelID` BIGINT DEFAULT NULL,
  `privacy` BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_groups_guild ON `groups` (`guild`);

CREATE TABLE IF NOT EXISTS `archive` (
  `guild` BIGINT NOT NULL,
  `channel` BIGINT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_archive_guild ON `archive` (`guild`);

CREATE TABLE IF NOT EXISTS `wormhole_list` (
  `name` TEXT PRIMARY KEY NOT NULL,
  `privacy` BOOLEAN NOT NULL DEFAULT 0,
  `webhook_name` TEXT NOT NULL,
  `webhook_pp` BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_wormhole_list ON `wormhole_list` (`name`);

CREATE TABLE IF NOT EXISTS `wormhole_admin` (
  `name` TEXT NOT NULL,
  `admin` BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wormhole_admin ON `wormhole_admin` (`name`);

CREATE TABLE IF NOT EXISTS `wormhole_channel` (
    `name` TEXT NOT NULL,
    `channelID` BIGINT NOT NULL,
    `guildID` BIGINT NOT NULL,
    `type` TEXT NOT NULL,
    `webhookID` BIGINT NOT NULL,
    `webhookTOKEN` TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wormhole_channel ON `wormhole_channel` (`name`);
