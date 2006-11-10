DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id integer PRIMARY KEY,          /* Arbitrary numeric statement
				      identifier. */
  hash binary(16) NOT NULL,        /* 128 bit hash value. */
  subject varchar(255) NOT NULL,   /* Statement subject. */
  predicate varchar(255) NOT NULL, /* Statement predicate. */
  object_type mediumint NOT NULL,  /* Statement object type. */
  object longtext NOT NULL         /* Statement object. */
);

CREATE UNIQUE INDEX statements_unique
  ON statements (hash);

CREATE INDEX statements_subject_index
  ON statements (subject);
CREATE INDEX statements_predicate_index
  ON statements (predicate);

DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id integer PRIMARY KEY,   /* Data type identifier */
  uri varchar(255) NOT NULL /* URI identifying the type */
);

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

INSERT INTO data_types (id, uri) VALUES (1, '<RESOURCE>');
INSERT INTO data_types (id, uri) VALUES (2, '<BLANKNODE>');
INSERT INTO data_types (id, uri) VALUES (3, '<LITERAL>');


DROP TABLE IF EXISTS version_statement;

CREATE TABLE version_statement (
  version_id integer unsigned NOT NULL, /* A version identifier */
  stmt_id integer unsigned NOT NULL     /* A statement identifier */
);

CREATE UNIQUE INDEX version_statement_unique
  ON version_statement (version_id, stmt_id);
CREATE INDEX version_statement_stmt_id
  ON version_statement (stmt_id);


CREATE TABLE IF NOT EXISTS prefixes (
  prefix varchar(31) PRIMARY KEY NOT NULL, /* Namespace prefix */
  namespace varchar(255) NOT NULL          /* Namespace URI */
);

