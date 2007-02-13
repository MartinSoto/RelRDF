DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 2);


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
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Available statements';

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
  UPDATE statements_temp
    SET hash = unhex(md5(concat(subject_text, predicate_text, object_text)));

  INSERT INTO data_types (uri)
    SELECT s.object_type
    FROM statements_temp s
  ON DUPLICATE KEY UPDATE uri = uri;

  INSERT INTO statements (hash, subject, predicate, object,
                          subject_text, predicate_text, object_type,
                          object_text)
    SELECT s.hash, unhex(md5(subject_text)), unhex(md5(predicate_text)),
           unhex(md5(object_text)), s.subject_text, s.predicate_text,
           dt.id, s.object_text
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

