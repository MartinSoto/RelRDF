DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id integer unsigned NOT NULL auto_increment
	 COMMENT 'Arbitrary numeric statement identifier',
  hash binary(16) NOT NULL
	 COMMENT '128 bit hash value',
  subject varchar(255) NOT NULL
	 COMMENT 'Statement subject',
  predicate varchar(255) NOT NULL
	 COMMENT 'Statement predicate',
  object_type mediumint NOT NULL
	 COMMENT 'Statement object type',
  object longtext NOT NULL COMMENT 'Statement object',
  PRIMARY KEY  (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available statements';

CREATE UNIQUE INDEX statements_unique
  ON statements (hash);

CREATE INDEX statements_subject_index
  ON statements (subject);
CREATE INDEX statements_predicate_index
  ON statements (predicate);

DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id mediumint unsigned NOT NULL auto_increment
	 COMMENT 'Data type identifier',
  uri varchar(255) NOT NULL
	 COMMENT 'URI identifying the type',
  PRIMARY KEY  (id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available data types';

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
) ENGINE=MyISAM COMMENT='Version version_id contains statement stmt_id';


DROP TABLE IF EXISTS not_versioned_statements;

CREATE TABLE not_versioned_statements (
  stmt_id integer unsigned NOT NULL
	 COMMENT 'A statement identifier'
) ENGINE=MyISAM COMMENT='Statement stmt_id isn\'t versioned';


CREATE TABLE IF NOT EXISTS prefixes (
  prefix varchar(31) NOT NULL
         COMMENT 'Namespace prefix',
  namespace varchar(255) NOT NULL
	 COMMENT 'Namespace URI',
  PRIMARY KEY prefix_unique (prefix)
) ENGINE=MyISAM COMMENT='Suggested namespace prefixes';


DROP PROCEDURE IF EXISTS insert_version;

DELIMITER //

CREATE PROCEDURE insert_version(version_id INT)
BEGIN
  INSERT INTO data_types (uri)
    SELECT s.object_type
    FROM statements_temp s
  ON DUPLICATE KEY UPDATE uri = uri;

  INSERT INTO statements (hash, subject, predicate, object_type,
			  object)
    SELECT s.hash, s.subject, s.predicate, dt.id, s.object
    FROM statements_temp s, data_types dt
    WHERE s.object_type = dt.uri
  ON DUPLICATE KEY UPDATE statements.subject = statements.subject;

  INSERT INTO version_statement (version_id, stmt_id)
    SELECT version_id AS v_id, s.id
    FROM statements s, statements_temp st
    WHERE s.hash = st.hash
  ON DUPLICATE KEY UPDATE version_id = version_id;

  DROP TABLE statements_temp;
END
//

DELIMITER ;

