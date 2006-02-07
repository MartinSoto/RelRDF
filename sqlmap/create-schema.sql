DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id integer unsigned NOT NULL auto_increment
	 COMMENT 'Arbitrary numeric statement identifier.',
  subject varchar(255) NOT NULL
	 COMMENT 'Statement subject',
  predicate varchar(255) NOT NULL
	 COMMENT 'Statement predicate',
  object_type mediumint NOT NULL
	 COMMENT 'Statement predicate type',
  object longtext NOT NULL COMMENT 'Statement object',
  PRIMARY KEY  (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available statements';

CREATE UNIQUE INDEX statements_unique
  ON statements (subject(60), predicate(60), object_type, object(100));


DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id mediumint unsigned NOT NULL auto_increment
	 COMMENT 'Data type identifier',
  uri varchar(255) NOT NULL
	 COMMENT 'URI identifying the type',
  PRIMARY KEY  (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available statements';

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

INSERT INTO data_types (uri)
  VALUES ('<RESOURCE>'), ('<BLANKNODE>'), ('<LITERAL>');


DROP TABLE IF EXISTS version_statement;

CREATE TABLE version_statement (
  version_id integer unsigned NOT NULL
	 COMMENT 'A version identifier',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier'
) ENGINE=MyISAM COMMENT='Version version_id contains statement stmt_id';

CREATE UNIQUE INDEX version_statement_unique
  ON version_statement (version_id, stmt_id);


DROP TABLE IF EXISTS not_versioned_statements;

CREATE TABLE not_versioned_statements (
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier'
) ENGINE=MyISAM COMMENT='Statement stmt_id isn\'t versioned';
