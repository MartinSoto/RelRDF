DROP TABLE IF EXISTS `statements`;

CREATE TABLE `statements` (
  `id` integer unsigned NOT NULL auto_increment
	 COMMENT 'Arbitrary numeric statement identifier.',
  `subject` varchar(255) NOT NULL
	 COMMENT 'Statement subject',
  `predicate` varchar(255) NOT NULL
	 COMMENT 'Statement predicate',
  `object_type` mediumint NOT NULL
	 COMMENT 'Statement predicate type',
  `object` longtext NOT NULL COMMENT 'Statement object',
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available statements';


DROP TABLE IF EXISTS `versions`;

CREATE TABLE `versions` (
  `id` integer unsigned NOT NULL auto_increment
	 COMMENT 'Consecutive numeric version identifier',
  `description` varchar(255) NOT NULL
	 COMMENT 'Version description',
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available versions ';


DROP TABLE IF EXISTS `version_statement`;

CREATE TABLE `version_statement` (
  `version_id` integer unsigned NOT NULL
	 COMMENT 'A version identifier',
  `stmt_id` integer unsigned NOT NULL
	 COMMENT 'A statement identifier'
) ENGINE=MyISAM COMMENT='Version version_id contains statement stmt_id';


DROP TABLE IF EXISTS `not_versioned_statements`;

CREATE TABLE `not_versioned_statements` (
  `stmt_id` integer unsigned NOT NULL
	 COMMENT 'A statement identifier'
) ENGINE=MyISAM COMMENT='Statement stmt_id isn\'t versioned';

