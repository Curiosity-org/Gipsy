# Ce programme est régi par la licence CeCILL soumise au droit français et
# respectant les principes de diffusion des logiciels libres. Vous pouvez
# utiliser, modifier et/ou redistribuer ce programme sous les conditions
# de la licence CeCILL diffusée sur le site "http://www.cecill.info".

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