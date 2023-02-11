-- Ce programme est régi par la licence CeCILL soumise au droit français et
-- respectant les principes de diffusion des logiciels libres. Vous pouvez
-- utiliser, modifier et/ou redistribuer ce programme sous les conditions
-- de la licence CeCILL diffusée sur le site "http://www.cecill.info".

CREATE TABLE IF NOT EXISTS `group_roles` (
  `guild` BIGINT NOT NULL,
  `action` SMALLINT NOT NULL DEFAULT 0,
  `target` BIGINT NOT NULL,
  `trigger` SMALLINT NOT NULL,
  `trigger-roles`BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grouproles_guild ON `group_roles` (`guild`);