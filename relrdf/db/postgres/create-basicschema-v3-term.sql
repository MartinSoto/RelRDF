
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
  
DROP TABLE IF EXISTS types;
DROP TABLE IF EXISTS data_types;

CREATE TABLE types (
  id int PRIMARY KEY,
  type_uri varchar(255),
  lang_tag varchar(255)
);

CREATE UNIQUE INDEX types_type_uri_index
  ON types (type_uri);
CREATE UNIQUE INDEX types_lang_tag_index
  ON types (lang_tag);

INSERT INTO types VALUES

  (1*4096+0, 'http://www.w3.org/2001/XMLSchema#integer', NULL),
  (1*4096+1, 'http://www.w3.org/2001/XMLSchema#decimal', NULL),
  (1*4096+2, 'http://www.w3.org/2001/XMLSchema#float', NULL),
  (1*4096+3, 'http://www.w3.org/2001/XMLSchema#double', NULL),
  (1*4096+4, 'http://www.w3.org/2001/XMLSchema#positiveInteger', NULL),
  (1*4096+5, 'http://www.w3.org/2001/XMLSchema#negativeInteger', NULL),
  (1*4096+6, 'http://www.w3.org/2001/XMLSchema#nonPositiveInteger', NULL),
  (1*4096+7, 'http://www.w3.org/2001/XMLSchema#nonNegativeInteger', NULL),
  (1*4096+8, 'http://www.w3.org/2001/XMLSchema#long', NULL),
  (1*4096+9, 'http://www.w3.org/2001/XMLSchema#int', NULL),
  (1*4096+10, 'http://www.w3.org/2001/XMLSchema#short', NULL),
  (1*4096+11, 'http://www.w3.org/2001/XMLSchema#byte', NULL),
  (1*4096+12, 'http://www.w3.org/2001/XMLSchema#unsignedLong', NULL),
  (1*4096+13, 'http://www.w3.org/2001/XMLSchema#unsignedInt', NULL),
  (1*4096+14, 'http://www.w3.org/2001/XMLSchema#unsignedShort', NULL),
  (1*4096+15, 'http://www.w3.org/2001/XMLSchema#unsignedByte', NULL),

  (2*4096+0, 'http://www.w3.org/2001/XMLSchema#boolean', NULL),

  (3*4096+0, 'http://www.w3.org/2001/XMLSchema#dateTime', NULL),
  (3*4096+256, 'http://www.w3.org/2001/XMLSchema#date', NULL),
  (3*4096+2*256, 'http://www.w3.org/2001/XMLSchema#time', NULL),

  (4*4096+0, 'http://www.w3.org/2001/XMLSchema#string', NULL);

DROP SEQUENCE IF EXISTS data_types_id_seq;
CREATE SEQUENCE data_types_id_seq
  INCREMENT BY 256
  START WITH 17152
  NO CYCLE;

DROP SEQUENCE IF EXISTS language_tags_id_seq;
CREATE SEQUENCE language_tags_id_seq
  INCREMENT BY 1
  START WITH 2
  NO CYCLE;
  
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
  
GRANT ALL ON types, data_types_id_seq, language_tags_id_seq, prefixes, relrdf_schema_version, statements, statements_id_seq, twoway, twoway_conns, twoway_use_time, threeway, threeway_conns, threeway_use_time, version_statement TO vmodell;

/* Stored utility procedures */

CREATE LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION rdf_term_literal_type_to_id(uri text, tag text) RETURNS int4 AS $$
  DECLARE
    type_id int4;
  BEGIN
    SELECT INTO type_id id FROM types WHERE type_uri = uri OR lang_tag = tag;
    IF NOT FOUND THEN
      IF uri != '' THEN
        type_id := nextval('data_types_id_seq');
      ELSE
        type_id := nextval('language_tags_id_seq');
      END IF;
      INSERT INTO types VALUES (type_id, uri, tag);
    END IF;
    RETURN type_id;
  END
$$ LANGUAGE 'plpgsql' VOLATILE STRICT;

CREATE OR REPLACE FUNCTION rdf_term_create(val text, is_res int, type_uri text, lang_tag text) RETURNS rdf_term AS $$
  DECLARE
    type_id int4;
  BEGIN
    IF is_res != 0 THEN
      type_id = 0;
    ELSIF type_uri = '' AND lang_tag = '' THEN
      type_id = 1;
    ELSE
      type_id = rdf_term_literal_type_to_id(type_uri, lang_tag);
    END IF;
    RETURN rdf_term(type_id, val);
  END
$$ LANGUAGE 'plpgsql' VOLATILE STRICT;

CREATE OR REPLACE FUNCTION rdf_term_resource(uri text) RETURNS rdf_term AS $$
  BEGIN RETURN rdf_term(0, uri); END
$$ LANGUAGE 'plpgsql' IMMUTABLE STRICT;

