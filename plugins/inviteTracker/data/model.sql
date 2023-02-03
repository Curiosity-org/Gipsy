-- Ce programme est régi par la licence CeCILL soumise au droit français et
-- respectant les principes de diffusion des logiciels libres. Vous pouvez
-- utiliser, modifier et/ou redistribuer ce programme sous les conditions
-- de la licence CeCILL diffusée sur le site "http://www.cecill.info".

CREATE TABLE IF NOT EXISTS `invites` (
    `guild` BIGINT NOT NULL, 
    `channel` BIGINT NOT NULL,
    `user` BIGINT NOT NULL, /*The people who created the invite*/
    `id` BIGINT NOT NULL,
    `code` TINYTEXT NOT NULL,
    `uses` INT NOT NULL, /*Needed to detect an invitation use*/
    `description` TEXT /*Custom description such as "website" or "about me"...*/
)