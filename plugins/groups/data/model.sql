-- Ce programme est régi par la licence CeCILL soumise au droit français et
-- respectant les principes de diffusion des logiciels libres. Vous pouvez
-- utiliser, modifier et/ou redistribuer ce programme sous les conditions
-- de la licence CeCILL diffusée sur le site "http://www.cecill.info".

CREATE TABLE IF NOT EXISTS `groups` (
  `guild` BIGINT NOT NULL,
  `roleID` BIGINT NOT NULL,
  `ownerID` BIGINT NOT NULL,
  `channelID` BIGINT DEFAULT NULL,
  `privacy` BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_groups_guild ON `groups` (`guild`);