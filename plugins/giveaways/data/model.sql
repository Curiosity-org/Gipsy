-- Ce programme est régi par la licence CeCILL soumise au droit français et
-- respectant les principes de diffusion des logiciels libres. Vous pouvez
-- utiliser, modifier et/ou redistribuer ce programme sous les conditions
-- de la licence CeCILL diffusée sur le site "http://www.cecill.info".

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