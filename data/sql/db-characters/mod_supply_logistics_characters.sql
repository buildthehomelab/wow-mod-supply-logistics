-- mod-supply-logistics: the Certification titles each account has unlocked.
CREATE TABLE IF NOT EXISTS `mod_supply_logistics_title` (
  `account` INT UNSIGNED NOT NULL,
  `title` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`account`, `title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
