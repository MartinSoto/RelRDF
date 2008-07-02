
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
  object rdf_term NOT NULL
);

CREATE INDEX statements_predicate_index
  ON statements (predicate);  
CREATE INDEX statements_subject_predicate_index
  ON statements (subject, predicate);

CREATE INDEX statements_subject_hash_index
  ON statements USING hash (subject);
CREATE INDEX statements_predicate_hash_index
  ON statements USING hash (predicate);
CREATE INDEX statements_object_hash_index
  ON statements USING hash (object);
  
DROP TABLE IF EXISTS data_types;

CREATE TABLE data_types (
  id SERIAL PRIMARY KEY,
  uri varchar(255) NOT NULL
);

CREATE UNIQUE INDEX data_types_unique
  ON data_types (uri);

INSERT INTO data_types (id, uri) VALUES
  (0, 'http://www.w3.org/2000/01/rdf-schema#Resource'),
  
  (4096, 'http://www.w3.org/2001/XMLSchema#integer'),
  (4097, 'http://www.w3.org/2001/XMLSchema#decimal'),
  (4098, 'http://www.w3.org/2001/XMLSchema#float'),
  (4099, 'http://www.w3.org/2001/XMLSchema#double'),
  (4100, 'http://www.w3.org/2001/XMLSchema#positiveInteger'),
  (4101, 'http://www.w3.org/2001/XMLSchema#negativeInteger'),
  (4102, 'http://www.w3.org/2001/XMLSchema#nonPositiveInteger'),
  (4103, 'http://www.w3.org/2001/XMLSchema#nonNegativeInteger'),
  (4104, 'http://www.w3.org/2001/XMLSchema#long'),
  (4105, 'http://www.w3.org/2001/XMLSchema#int'),
  (4106, 'http://www.w3.org/2001/XMLSchema#short'),
  (4107, 'http://www.w3.org/2001/XMLSchema#byte'),
  (4108, 'http://www.w3.org/2001/XMLSchema#unsignedLong'),
  (4109, 'http://www.w3.org/2001/XMLSchema#unsignedInt'),
  (4110, 'http://www.w3.org/2001/XMLSchema#unsignedShort'),
  (4111, 'http://www.w3.org/2001/XMLSchema#unsignedByte'),

  (8192, 'http://www.w3.org/2001/XMLSchema#boolean'),

  (8448, 'http://www.w3.org/2001/XMLSchema#dateTime'),

  (8704, 'http://www.w3.org/2001/XMLSchema#string'),
  
  (8960, 'http://www.w3.org/2000/01/rdf-schema#Literal');

ALTER SEQUENCE data_types_id_seq
  INCREMENT BY 256
  START WITH 16384
  NO CYCLE;
  
CREATE FUNCTION format_rdf_term(t rdf_term) RETURNS text AS $$
  SELECT rdf_term_to_string($1) || '^^' || d.uri
   FROM data_types d WHERE d.id = rdf_term_get_type_id($1);
$$ LANGUAGE SQL;

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
  
GRANT ALL ON data_types, data_types_id_seq, prefixes, relrdf_schema_version, statements, statements_id_seq, twoway, twoway_conns, twoway_use_time, threeway, threeway_conns, threeway_use_time, version_statement TO vmodell;

