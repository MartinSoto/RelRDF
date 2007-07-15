DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 3);


DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id integer unsigned NOT NULL auto_increment
	 COMMENT 'Arbitrary numeric statement identifier',
  hash binary(16) NOT NULL
	 COMMENT '128 bit hash value for the whole statement',
  subject binary(16) NOT NULL
	 COMMENT '128 bit hash value for the subject',
  predicate binary(16) NOT NULL
	 COMMENT '128 bit hash value for the predicate',
  object binary(16) NOT NULL
	 COMMENT '128 bit hash value for the object',
  subject_text longtext NOT NULL
	 COMMENT 'Statement subject text',
  predicate_text longtext NOT NULL
	 COMMENT 'Statement predicate text',
  object_type mediumint NOT NULL
	 COMMENT 'Statement object type',
  object_text longtext NOT NULL COMMENT 'Statement object text',
  PRIMARY KEY  (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Available statements';

CREATE UNIQUE INDEX statements_unique
  ON statements (hash);

CREATE INDEX statements_subject_index
  ON statements (subject);
CREATE INDEX statements_predicate_index
  ON statements (predicate);
CREATE INDEX statements_object_index
  ON statements (object);

DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id mediumint unsigned NOT NULL auto_increment
	 COMMENT 'Data type identifier',
  uri varchar(255) NOT NULL
	 COMMENT 'URI identifying the type',
  PRIMARY KEY  (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Available data types';

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

INSERT INTO data_types (id, uri)
  VALUES (1, '<RESOURCE>'), (2, '<BLANKNODE>'), (3, '<LITERAL>');


DROP TABLE IF EXISTS version_statement;

CREATE TABLE version_statement (
  version_id integer unsigned NOT NULL
	 COMMENT 'A version identifier',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier',
  KEY (stmt_id),
  UNIQUE KEY version_statement_unique (version_id, stmt_id)
) ENGINE=InnoDB COMMENT='Version version_id contains statement stmt_id';


DROP TABLE IF EXISTS twoway;

CREATE TABLE twoway (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier',
  context char(2) NOT NULL
	 COMMENT 'Comparison context',
  UNIQUE KEY version_statement_unique (version_a, version_b, stmt_id),
  KEY (stmt_id),
  KEY (context)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS threeway;

CREATE TABLE threeway (
  version_a integer unsigned NOT NULL
	 COMMENT 'Version identifier of the first compared version',
  version_b integer unsigned NOT NULL
	 COMMENT 'Version identifier of the second compared version',
  version_c integer unsigned NOT NULL
	 COMMENT 'Version identifier of the third compared version',
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier',
  context char(3) NOT NULL
	 COMMENT 'Comparison context',
  UNIQUE KEY version_statement_unique (version_a, version_b, version_c,
                                       stmt_id),
  KEY (stmt_id),
  KEY (context)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS prefixes (
  prefix varchar(31) NOT NULL
         COMMENT 'Namespace prefix',
  namespace varchar(255) NOT NULL
	 COMMENT 'Namespace URI',
  PRIMARY KEY prefix_unique (prefix)
) ENGINE=InnoDB COMMENT='Suggested namespace prefixes';


