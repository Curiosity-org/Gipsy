CREATE TABLE IF NOT EXISTS `invites` (
    `guild` BIGINT, 
    `channel` BIGINT NOT NULL,
    `user` BIGINT, /*The people who created the invite*/
    `id` BIGINT NOT NULL,
    `code` TINYTEXT NOT NULL,
    `uses` INT NOT NULL, /*Needed to detect an invitation use*/
    `description` TEXT /*Custom description such as "website" or "about me"...*/
)