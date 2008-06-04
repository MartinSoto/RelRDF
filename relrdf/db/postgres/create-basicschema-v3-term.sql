
DROP TABLE IF EXISTS relrdf_schema_version;

CREATE TABLE relrdf_schema_version (
  name varchar(255),
  version integer
);

INSERT INTO relrdf_schema_version (name, version)
  VALUES ('basic', 3);

DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
  id SERIAL PRIMARY KEY,
  subject rdf_term NOT NULL,
  predicate rdf_term NOT NULL,
  object rdf_term NOT NULL,
);

CREATE INDEX statements_subject_predicate_index
  ON statements (subject_text, predicate_text);
  
DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id SERIAL,
  uri varchar(255) NOT NULL,
  PRIMARY KEY  (id)
);

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

INSERT INTO data_types (id, uri)
  VALUES (1, 'http://www.w3.org/2000/01/rdf-schema#Resource'), (2, 'http://www.w3.org/2000/01/rdf-schema#Literal');


DROP TABLE IF EXISTS version_statement;

CREATE TABLE version_statement (
  version_id integer NOT NULL,
  stmt_id integer NOT NULL,
  PRIMARY KEY (version_id, stmt_id)
);

CREATE INDEX version_statement_stmt_id_index
  ON version_statement (stmt_id);
  
DROP TABLE IF EXISTS twoway;

CREATE TABLE twoway (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  stmt_id integer NOT NULL,
  context char(2) NOT NULL,
  PRIMARY KEY (version_a, version_b, stmt_id)
);


DROP TABLE IF EXISTS twoway_use_time;

CREATE TABLE twoway_use_time (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  time timestamp NOT NULL,
  PRIMARY KEY (version_a, version_b)
);


DROP TABLE IF EXISTS twoway_conns;

CREATE TABLE twoway_conns (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  connection integer NOT NULL
);


DROP TABLE IF EXISTS threeway;

CREATE TABLE threeway (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  stmt_id integer NOT NULL,
  context char(3) NOT NULL,
  PRIMARY KEY (version_a, version_b, version_c, stmt_id)
);


DROP TABLE IF EXISTS threeway_use_time;

CREATE TABLE threeway_use_time (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  time timestamp NOT NULL,
  PRIMARY KEY (version_a, version_b, version_c)
);


DROP TABLE IF EXISTS threeway_conns;

CREATE TABLE threeway_conns (
  version_a integer NOT NULL,
  version_b integer NOT NULL,
  version_c integer NOT NULL,
  connection integer NOT NULL
);

DROP TABLE IF EXISTS prefixes;

CREATE TABLE prefixes (
  prefix varchar(31) NOT NULL PRIMARY KEY,
  namespace varchar(255) NOT NULL
);

INSERT INTO prefixes (prefix, namespace)
  VALUES ('vmxt', 'http://www.v-modell-xt.de/schema/1#'), ('vmxti', 'http://www.v-modell-xt.de/model/1#');
  
  

