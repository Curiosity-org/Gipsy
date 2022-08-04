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
